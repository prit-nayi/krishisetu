"""
decisions/services/combined_analysis.py — Phase 4+5+6: Combined Market Analysis + Decision.

Joins MarketAnalysisService (financial) with ForecastService (price forecasting)
and DecisionService (SELL/HOLD/PARTIAL_SELL) to produce a single ranked result.

Markets are ranked primarily by net_revenue (descending).
A SELL/HOLD recommendation is computed for the BEST market only (Phase 6).
"""
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from .market_analysis import MarketAnalysisService, MarketAnalysisResult, MarketFinancialResult
from .forecast_service import ForecastService, ForecastResult
from .decision_service import DecisionService, DecisionResult
from apps.agents.ai_explanation_service import ai_explanation_service

logger = logging.getLogger("krishilink")


@dataclass
class CombinedMarketEntry:
    """One row in the combined analysis table (financial + forecast)."""
    # ── Market ────────────────────────────────────────────────────────────────
    market_id:          int
    market_name:        str
    district:           str
    state:              str
    distance_km:        Optional[float]

    # ── Current price ─────────────────────────────────────────────────────────
    modal_price:        float
    price_date:         Optional[str]

    # ── Financial analysis ────────────────────────────────────────────────────
    quantity_quintal:   float
    gross_revenue:      float
    transport_cost:     float
    net_revenue:        float

    # ── Forecast ──────────────────────────────────────────────────────────────
    forecast_confidence_level:  str              # INSUFFICIENT_DATA | LOW | MEDIUM | HIGH
    forecast_confidence_score:  float            # 0.0 – 1.0
    forecast_model:             str
    forecast_data_points:       int

    # ── Financial defaults ────────────────────────────────────────────────────
    other_costs:        float = 0.0
    total_cost:         float = 0.0

    # ── Forecast defaults ─────────────────────────────────────────────────────
    forecast_method:    str = ""                 # alias for forecast_model
    predicted_price:    Optional[float] = None
    predicted_prices:   List[float]     = field(default_factory=list)
    lower_band:         List[float]     = field(default_factory=list)
    upper_band:         List[float]     = field(default_factory=list)
    price_change:       Optional[float] = None
    price_change_pct:   Optional[float] = None
    trend_direction:    str             = "flat"

    # ── Rank (filled after sorting) ───────────────────────────────────────────
    rank:               int = 0


@dataclass
class CombinedAnalysisResult:
    """Full result from CombinedAnalysisService.run()."""
    crop_lot_id:        int
    commodity:          str
    quantity_quintal:   float
    farmer_lat:         Optional[float]
    farmer_lon:         Optional[float]

    markets:            List[CombinedMarketEntry] = field(default_factory=list)
    skipped_markets:    list                       = field(default_factory=list)
    best_market:        Optional[CombinedMarketEntry] = None

    # ── AI Explanation (IBM Granite Demo/Mock) ───────────────────────────────
    ai_explanation:     Optional[dict]             = None

    # ── Phase 6: SELL/HOLD decision for best market ───────────────────────────
    decision:           Optional[DecisionResult]   = None

    errors:             List[str]                  = field(default_factory=list)


class CombinedAnalysisService:
    """
    Orchestrates Phase 4 (financial) + Phase 5 (forecast) + Phase 6 (decision).

    Usage::

        result = CombinedAnalysisService().run(
            crop_lot_id=5,
            user=request.user,
            forecast_days=7,
            save_forecasts=False,
        )
    """

    def __init__(self):
        self._market_svc   = MarketAnalysisService()
        self._forecast_svc = ForecastService()
        self._decision_svc = DecisionService()
        self._ai_svc       = ai_explanation_service

    def run(
        self,
        crop_lot_id:    int,
        user,
        forecast_days:  int  = 7,
        save_forecasts: bool = False,
    ) -> CombinedAnalysisResult:
        """
        Full pipeline:
        1. Run financial analysis for all markets.
        2. For each financially-analysed market, run price forecast.
        3. Merge results and return ranked combined list.
        4. Run SELL/HOLD decision for the best market (rank 1).
        5. Generate IBM Granite Demo/Mock explanation based on real data.
        """
        # ── Phase 4: financial analysis ───────────────────────────────────────
        fin_result: MarketAnalysisResult = self._market_svc.run(
            crop_lot_id=crop_lot_id, user=user
        )

        if fin_result.errors and not fin_result.markets:
            return CombinedAnalysisResult(
                crop_lot_id=crop_lot_id,
                commodity=fin_result.commodity,
                quantity_quintal=fin_result.quantity_quintal,
                farmer_lat=fin_result.farmer_lat,
                farmer_lon=fin_result.farmer_lon,
                errors=fin_result.errors,
                skipped_markets=[_skipped_entry(s) for s in fin_result.skipped_markets],
            )

        combined_result = CombinedAnalysisResult(
            crop_lot_id=crop_lot_id,
            commodity=fin_result.commodity,
            quantity_quintal=fin_result.quantity_quintal,
            farmer_lat=fin_result.farmer_lat,
            farmer_lon=fin_result.farmer_lon,
            errors=fin_result.errors,
            skipped_markets=[_skipped_entry(s) for s in fin_result.skipped_markets],
        )

        # ── Phase 5: forecast per market ──────────────────────────────────────
        forecast_by_market: dict = {}
        for mfr in fin_result.markets:
            try:
                fc: ForecastResult = self._forecast_svc.run(
                    market_id=mfr.market_id,
                    market_name=mfr.market_name,
                    commodity=fin_result.commodity,
                    horizon_days=forecast_days,
                    save=save_forecasts,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "CombinedAnalysisService: forecast failed for market %d: %s",
                    mfr.market_id, exc,
                )
                fc = ForecastResult(
                    market_id=mfr.market_id,
                    market_name=mfr.market_name,
                    commodity=fin_result.commodity,
                    horizon_days=forecast_days,
                    data_points=0,
                    confidence_level="INSUFFICIENT_DATA",
                    confidence_score=0.0,
                    model_name="none",
                    predicted_price=None,
                    price_change=None,
                    price_change_pct=None,
                    current_price=mfr.modal_price,
                    error=str(exc),
                )

            forecast_by_market[mfr.market_id] = fc

            entry = CombinedMarketEntry(
                market_id=mfr.market_id,
                market_name=mfr.market_name,
                district=mfr.district,
                state=mfr.state,
                distance_km=mfr.distance_km,
                modal_price=mfr.modal_price,
                price_date=mfr.price_date,
                quantity_quintal=mfr.quantity_quintal,
                gross_revenue=mfr.gross_revenue,
                transport_cost=mfr.transport_cost,
                other_costs=mfr.other_costs,
                total_cost=mfr.total_cost,
                net_revenue=mfr.net_revenue,
                forecast_confidence_level=fc.confidence_level,
                forecast_confidence_score=fc.confidence_score,
                forecast_model=fc.model_name,
                forecast_method=fc.model_name,
                forecast_data_points=fc.data_points,
                predicted_price=fc.predicted_price,
                predicted_prices=fc.predictions,
                lower_band=fc.lower_band,
                upper_band=fc.upper_band,
                price_change=fc.price_change,
                price_change_pct=fc.price_change_pct,
                trend_direction=fc.trend_direction,
            )
            combined_result.markets.append(entry)

        # ── Rank by net_revenue DESC ──────────────────────────────────────────
        combined_result.markets.sort(key=lambda x: x.net_revenue, reverse=True)
        for i, entry in enumerate(combined_result.markets, start=1):
            entry.rank = i

        if combined_result.markets:
            combined_result.best_market = combined_result.markets[0]

        # ── Phase 6: SELL/HOLD decision for best market ───────────────────────
        if combined_result.best_market and fin_result.markets:
            best_fin = next(
                (m for m in fin_result.markets
                 if m.market_id == combined_result.best_market.market_id),
                None,
            )
            if best_fin is not None:
                best_fc = forecast_by_market.get(combined_result.best_market.market_id)
                combined_result.decision = self._compute_decision(
                    crop_lot_id=crop_lot_id,
                    fin=best_fin,
                    fc=best_fc,
                    forecast_days=forecast_days,
                )

        # ── AI Explanation (IBM Granite Demo/Mock) ───────────────────────────
        if combined_result.best_market:
            explanation_context = {
                "crop_lot_id": crop_lot_id,
                "commodity": combined_result.commodity,
                "quantity_quintal": combined_result.quantity_quintal,
                "best_market": {
                    "market_id": combined_result.best_market.market_id,
                    "market_name": combined_result.best_market.market_name,
                    "district": combined_result.best_market.district,
                    "modal_price": combined_result.best_market.modal_price,
                    "distance_km": combined_result.best_market.distance_km,
                    "gross_revenue": combined_result.best_market.gross_revenue,
                    "transport_cost": combined_result.best_market.transport_cost,
                    "other_costs": combined_result.best_market.other_costs,
                    "total_cost": combined_result.best_market.total_cost,
                    "net_revenue": combined_result.best_market.net_revenue,
                },
                "markets": [
                    {
                        "market_id": m.market_id,
                        "market_name": m.market_name,
                        "net_revenue": m.net_revenue,
                        "modal_price": m.modal_price,
                    }
                    for m in combined_result.markets
                ],
                "forecast_days": forecast_days,
                "forecast_method": combined_result.best_market.forecast_method or combined_result.best_market.forecast_model,
                "forecast_confidence_level": combined_result.best_market.forecast_confidence_level,
                "forecast_confidence_score": combined_result.best_market.forecast_confidence_score,
                "predicted_price": combined_result.best_market.predicted_price,
                "price_change": combined_result.best_market.price_change,
                "price_change_pct": combined_result.best_market.price_change_pct,
                "trend_direction": combined_result.best_market.trend_direction,
            }
            try:
                combined_result.ai_explanation = self._ai_svc.generate_explanation(explanation_context)
            except Exception as exc:
                logger.warning("CombinedAnalysisService: AI explanation generation failed: %s", exc)
                combined_result.ai_explanation = None

        logger.info(
            "CombinedAnalysisService: crop_lot=%d %d markets | decision=%s",
            crop_lot_id,
            len(combined_result.markets),
            combined_result.decision.recommendation if combined_result.decision else "N/A",
        )
        return combined_result

    # ------------------------------------------------------------------

    def _compute_decision(
        self,
        crop_lot_id: int,
        fin: MarketFinancialResult,
        fc: Optional[ForecastResult],
        forecast_days: int,
    ) -> Optional[DecisionResult]:
        """Run DecisionService for the best-market financial + forecast result."""
        from apps.crops.models import CropLot
        try:
            crop_lot = CropLot.objects.get(pk=crop_lot_id, is_active=True)
        except CropLot.DoesNotExist:
            logger.warning("CombinedAnalysisService: crop_lot %d not found for decision", crop_lot_id)
            return None

        forecast_price      = fc.predicted_price if fc else None
        forecast_confidence = fc.confidence_score if fc else 0.0

        try:
            return self._decision_svc.run(
                crop_lot=crop_lot,
                current_net_value=max(fin.net_revenue, 0.01),
                quantity_quintal=fin.quantity_quintal,
                gross_revenue=fin.gross_revenue,
                transport_cost=fin.transport_cost,
                forecast_price=forecast_price,
                forecast_confidence=forecast_confidence,
                forecast_days=forecast_days,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("CombinedAnalysisService: decision failed for crop_lot %d: %s",
                             crop_lot_id, exc)
            return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _skipped_entry(mfr: MarketFinancialResult) -> dict:
    return {
        "market_id":   mfr.market_id,
        "market_name": mfr.market_name,
        "district":    mfr.district,
        "skip_reason": mfr.skip_reason,
    }
