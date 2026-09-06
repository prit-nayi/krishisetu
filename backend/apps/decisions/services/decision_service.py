"""
decisions/services/decision_service.py — Phase 6: SELL/HOLD Decision Engine.

Combines:
  • Current net value (from MarketAnalysisService best market)
  • Storage cost (from financial_tools.calculate_storage_cost)
  • Capital/opportunity cost (from financial_tools.calculate_capital_cost)
  • Expected future value (from financial_tools.calculate_expected_future_value)
  • SELL/HOLD/PARTIAL_SELL rule (from financial_tools.recommend_sell_or_hold)
  • Partial sell strategy (from financial_tools.calculate_partial_sell_strategy)

All calculation logic is delegated to tools/financial_tools.py.
This service only orchestrates data retrieval + tool calls.
"""
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from tools.financial_tools import (
    calculate_storage_cost,
    calculate_capital_cost,
    calculate_expected_future_value,
    recommend_sell_or_hold,
    calculate_partial_sell_strategy,
)

logger = logging.getLogger("krishilink")

# ── Quality adjustment mapping ────────────────────────────────────────────────
# Grade A: no adjustment; Grade B: −2%; Grade C: −5%
_QUALITY_ADJUSTMENT_PCT = {
    "A": 0.00,
    "B": -0.02,
    "C": -0.05,
}


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class DecisionResult:
    """
    Full SELL/HOLD decision for one crop lot at one (best) market.

    All monetary values are in Indian Rupees (INR).
    """

    # ── Recommendation ────────────────────────────────────────────────────────
    recommendation:        str              # SELL_NOW | HOLD | PARTIAL_SELL
    confidence:            float            # 0.0 – 1.0 (derived from forecast confidence)
    rule_version:          str = "1.0.0"

    # ── Current value ─────────────────────────────────────────────────────────
    current_net_value:           float = 0.0
    gross_revenue:               float = 0.0
    transport_cost:              float = 0.0

    # ── Storage & capital costs ───────────────────────────────────────────────
    storage_days:                int   = 0
    storage_type:                str   = "farm"
    storage_cost:                float = 0.0
    capital_cost:                float = 0.0

    # ── Future value ──────────────────────────────────────────────────────────
    forecast_price:              Optional[float] = None
    quality_adjustment:          float = 0.0
    expected_future_gross:       float = 0.0
    expected_future_net_value:   float = 0.0
    total_future_deductions:     float = 0.0

    # ── Decision margin ───────────────────────────────────────────────────────
    margin:                      float = 0.0
    margin_pct:                  float = 0.0
    threshold_pct:               float = 5.0

    # ── Partial sell strategy (only when PARTIAL_SELL) ────────────────────────
    sell_now_quantity_quintal:   Optional[float] = None
    hold_quantity_quintal:       Optional[float] = None
    sell_now_value:              Optional[float] = None
    hold_expected_value:         Optional[float] = None
    partial_sell_rationale:      str = ""

    # ── Reasoning factors (for storage in Recommendation.reasoning_factors) ──
    reasoning_factors:           dict = field(default_factory=dict)

    # ── Error ─────────────────────────────────────────────────────────────────
    error:                       str = ""


# ── Service ───────────────────────────────────────────────────────────────────

class DecisionService:
    """
    Compute a SELL/HOLD/PARTIAL_SELL recommendation for a crop lot.

    Usage::

        from apps.crops.models import CropLot
        from apps.decisions.services.decision_service import DecisionService

        decision = DecisionService().run(
            crop_lot=crop_lot,
            current_net_value=85000.0,
            quantity_quintal=20.0,
            gross_revenue=90000.0,
            transport_cost=5000.0,
            forecast_price=4800.0,          # None if INSUFFICIENT_DATA
            forecast_confidence=0.6,
            forecast_days=7,
        )

    The caller (CombinedAnalysisService) is responsible for providing
    financial inputs already computed by MarketAnalysisService.
    """

    def run(
        self,
        crop_lot,
        current_net_value:   float,
        quantity_quintal:    float,
        gross_revenue:       float,
        transport_cost:      float,
        forecast_price:      Optional[float],
        forecast_confidence: float,
        forecast_days:       int   = 7,
        threshold_pct:       float = 5.0,
    ) -> DecisionResult:
        """
        Execute the decision pipeline.

        Steps:
        1. Calculate storage cost (from crop lot storage_type + days stored).
        2. Calculate capital/opportunity cost.
        3. Compute quality adjustment.
        4. If forecast available: compute expected future net value.
        5. Apply SELL/HOLD/PARTIAL_SELL rule.
        6. If PARTIAL_SELL: compute partial sell strategy.
        7. Return DecisionResult.
        """

        # ── 1. Storage days ───────────────────────────────────────────────────
        storage_type = crop_lot.storage_status  # farm | warehouse | cold_storage
        storage_days = _compute_storage_days(crop_lot)

        try:
            sc = calculate_storage_cost(storage_type, storage_days, quantity_quintal)
            storage_cost = sc["total_storage_cost"]
        except ValueError as exc:
            logger.warning("DecisionService: storage cost calculation failed: %s", exc)
            storage_cost = 0.0

        # ── 2. Capital / opportunity cost ─────────────────────────────────────
        try:
            cc = calculate_capital_cost(
                current_net_value=current_net_value,
                holding_days=max(storage_days, forecast_days),
            )
            capital_cost = cc["capital_cost"]
        except Exception as exc:  # noqa: BLE001
            logger.warning("DecisionService: capital cost calculation failed: %s", exc)
            capital_cost = 0.0

        # ── 3. Quality adjustment ─────────────────────────────────────────────
        quality_grade = getattr(crop_lot, "quality_grade", None) or "A"
        quality_pct   = _QUALITY_ADJUSTMENT_PCT.get(quality_grade, 0.0)
        # quality_adjustment is a price deduction (negative = discount)
        quality_adjustment = abs(gross_revenue * quality_pct)  # positive deduction amount

        # ── 4. Expected future value ──────────────────────────────────────────
        # If no forecast: compare current_net_value with itself minus holding
        # costs → effectively pushes toward SELL.
        if forecast_price is not None and forecast_price > 0:
            try:
                efv = calculate_expected_future_value(
                    forecast_price=forecast_price,
                    quantity_quintal=quantity_quintal,
                    transport_cost=transport_cost,
                    storage_cost=storage_cost,
                    capital_cost=capital_cost,
                    quality_adjustment=quality_adjustment,
                )
                expected_future_net_value  = efv["expected_net_value"]
                expected_future_gross      = efv["gross_future_revenue"]
                total_future_deductions    = efv["total_deductions"]
            except Exception as exc:  # noqa: BLE001
                logger.warning("DecisionService: expected future value failed: %s", exc)
                expected_future_net_value = current_net_value - storage_cost - capital_cost
                expected_future_gross     = 0.0
                total_future_deductions   = storage_cost + capital_cost + quality_adjustment
        else:
            # No forecast — future value = current minus holding costs
            expected_future_net_value = current_net_value - storage_cost - capital_cost - quality_adjustment
            expected_future_gross     = 0.0
            total_future_deductions   = storage_cost + capital_cost + quality_adjustment

        # ── 5. SELL/HOLD/PARTIAL_SELL rule ────────────────────────────────────
        try:
            rec = recommend_sell_or_hold(
                current_net_value=max(current_net_value, 0.01),  # guard against zero
                expected_future_net_value=expected_future_net_value,
                threshold_pct=threshold_pct,
            )
            recommendation = rec["recommendation"]
            margin         = rec["margin"]
            margin_pct     = rec["margin_pct"]
        except ValueError as exc:
            logger.warning("DecisionService: recommend_sell_or_hold failed: %s", exc)
            recommendation = "SELL_NOW"
            margin         = 0.0
            margin_pct     = 0.0

        # ── 6. Partial sell strategy ──────────────────────────────────────────
        sell_now_qty = hold_qty = sell_now_val = hold_expected_val = None
        partial_rationale = ""
        if recommendation == "PARTIAL_SELL":
            try:
                ps = calculate_partial_sell_strategy(
                    quantity_quintal=quantity_quintal,
                    current_net_value=current_net_value,
                    expected_future_net_value=expected_future_net_value,
                )
                sell_now_qty      = ps["sell_now_quantity_quintal"]
                hold_qty          = ps["hold_quantity_quintal"]
                sell_now_val      = ps["sell_now_value"]
                hold_expected_val = ps["hold_expected_value"]
                partial_rationale = ps["rationale"]
            except ValueError as exc:
                logger.warning("DecisionService: partial sell strategy failed: %s", exc)

        # ── 7. Confidence: blend forecast confidence with data availability ───
        # If no forecast, confidence is capped at 0.3 (LOW)
        if forecast_price is None:
            confidence = min(forecast_confidence, 0.3)
        else:
            confidence = forecast_confidence

        # ── 8. Reasoning factors ──────────────────────────────────────────────
        reasoning_factors = {
            "current_net_value":        round(current_net_value, 2),
            "expected_future_net_value": round(expected_future_net_value, 2),
            "margin":                   round(margin, 2),
            "margin_pct":               round(margin_pct, 2),
            "threshold_pct":            threshold_pct,
            "storage_type":             storage_type,
            "storage_days":             storage_days,
            "storage_cost":             round(storage_cost, 2),
            "capital_cost":             round(capital_cost, 2),
            "quality_grade":            quality_grade,
            "quality_adjustment":       round(quality_adjustment, 2),
            "forecast_price":           round(forecast_price, 2) if forecast_price else None,
            "forecast_confidence":      forecast_confidence,
            "forecast_days":            forecast_days,
        }

        logger.info(
            "DecisionService: crop_lot=%d %s | current=%.2f future=%.2f "
            "margin_pct=%.1f%% → %s (confidence=%.2f)",
            crop_lot.pk,
            crop_lot.commodity.upper(),
            current_net_value,
            expected_future_net_value,
            margin_pct,
            recommendation,
            confidence,
        )

        return DecisionResult(
            recommendation=recommendation,
            confidence=round(confidence, 3),
            rule_version="1.0.0",
            current_net_value=round(current_net_value, 2),
            gross_revenue=round(gross_revenue, 2),
            transport_cost=round(transport_cost, 2),
            storage_days=storage_days,
            storage_type=storage_type,
            storage_cost=round(storage_cost, 2),
            capital_cost=round(capital_cost, 2),
            forecast_price=round(forecast_price, 2) if forecast_price else None,
            quality_adjustment=round(quality_adjustment, 2),
            expected_future_gross=round(expected_future_gross, 2),
            expected_future_net_value=round(expected_future_net_value, 2),
            total_future_deductions=round(total_future_deductions, 2),
            margin=round(margin, 2),
            margin_pct=round(margin_pct, 2),
            threshold_pct=threshold_pct,
            sell_now_quantity_quintal=round(sell_now_qty, 4) if sell_now_qty is not None else None,
            hold_quantity_quintal=round(hold_qty, 4) if hold_qty is not None else None,
            sell_now_value=round(sell_now_val, 2) if sell_now_val is not None else None,
            hold_expected_value=round(hold_expected_val, 2) if hold_expected_val is not None else None,
            partial_sell_rationale=partial_rationale,
            reasoning_factors=reasoning_factors,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _compute_storage_days(crop_lot) -> int:
    """
    Compute how many days the crop lot has been in storage.

    Uses storage_start_date if set; falls back to harvest_date.
    Returns 0 if neither date is available.
    """
    start = crop_lot.storage_start_date or crop_lot.harvest_date
    if start is None:
        return 0
    delta = date.today() - start
    return max(delta.days, 0)
