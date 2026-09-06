"""
decisions/services/forecast_service.py — Phase 5: Price Forecasting Service.

Retrieves historical MarketPrice records for a commodity + market,
selects the appropriate forecasting method based on data quantity,
generates predictions, and optionally persists Forecast records.

Forecasting strategy (data-aware fallback):
    0 – 6 records   → INSUFFICIENT_DATA  (no forecast generated)
    7 – 29 records   → moving_average     (LOW confidence)
    30 – 89 records  → linear_regression  (MEDIUM confidence)
    90+ records      → linear_regression  (HIGH confidence)
                       SARIMAX reserved for Phase 7+

All calculation logic is delegated to tools/forecast_tools.py.
This service only orchestrates data retrieval and persistence.
"""
import logging
import statistics
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from apps.markets.models import MarketPrice
from apps.forecasting.models import Forecast
from tools.forecast_tools import generate_price_forecast, calculate_price_trend

logger = logging.getLogger("krishilink")

# ── Thresholds ────────────────────────────────────────────────────────────────
_INSUFFICIENT_THRESHOLD = 7    # < 7 records → no forecast
_LOW_THRESHOLD          = 30   # 7–29 → moving average / low confidence
_MEDIUM_THRESHOLD       = 90   # 30–89 → linear regression / medium confidence
                               # 90+   → linear regression / high confidence

_CONFIDENCE_MAP = {
    "INSUFFICIENT_DATA": 0.0,
    "LOW":               0.3,
    "MEDIUM":            0.6,
    "HIGH":              0.85,
}

_MODEL_MAP = {
    "LOW":    "moving_average",
    "MEDIUM": "linear_regression",
    "HIGH":   "linear_regression",
}


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class ForecastResult:
    """Forecast outcome for one commodity + market + horizon."""
    market_id:          int
    market_name:        str
    commodity:          str
    horizon_days:       int

    # Strategy
    data_points:        int
    confidence_level:   str                  # INSUFFICIENT_DATA | LOW | MEDIUM | HIGH
    confidence_score:   float                # 0.0 – 1.0
    model_name:         str                  # moving_average | linear_regression

    # Predictions (None if INSUFFICIENT_DATA)
    predicted_price:    Optional[float]      # price at end of horizon
    price_change:       Optional[float]      # predicted - current modal
    price_change_pct:   Optional[float]
    current_price:      Optional[float]
    predictions:        List[float]          = field(default_factory=list)
    lower_band:         List[float]          = field(default_factory=list)
    upper_band:         List[float]          = field(default_factory=list)
    trend_direction:    str                  = "flat"

    # Error / warning
    error:              str                  = ""


# ── Service ───────────────────────────────────────────────────────────────────

class ForecastService:
    """
    Generate a price forecast for a commodity at a specific market.

    Usage::

        result = ForecastService().run(
            market_id=5,
            market_name="Gondal APMC",
            commodity="GROUNDNUT",
            horizon_days=7,
            save=True,
        )
    """

    def run(
        self,
        market_id: int,
        market_name: str,
        commodity: str,
        horizon_days: int = 7,
        save: bool = False,
    ) -> ForecastResult:
        """
        Execute the forecast pipeline.

        Steps:
        1. Load historical price records.
        2. Select strategy by data quantity.
        3. Generate forecast using tools/forecast_tools.py.
        4. Optionally persist Forecast record.
        5. Return ForecastResult.
        """
        commodity_upper = commodity.upper()

        # ── 1. Historical prices ──────────────────────────────────────────────
        history_qs = (
            MarketPrice.objects
            .filter(market_id=market_id, commodity=commodity_upper)
            .order_by("price_date")
            .values("price_date", "modal_price")
        )
        history = [
            {"price_date": str(r["price_date"]), "modal_price": float(r["modal_price"])}
            for r in history_qs
        ]
        n = len(history)

        # ── 2. Strategy selection ─────────────────────────────────────────────
        if n < _INSUFFICIENT_THRESHOLD:
            return ForecastResult(
                market_id=market_id,
                market_name=market_name,
                commodity=commodity_upper,
                horizon_days=horizon_days,
                data_points=n,
                confidence_level="INSUFFICIENT_DATA",
                confidence_score=0.0,
                model_name="none",
                predicted_price=None,
                price_change=None,
                price_change_pct=None,
                current_price=float(history[-1]["modal_price"]) if history else None,
                error=f"Insufficient data: {n} records (need at least {_INSUFFICIENT_THRESHOLD}).",
            )

        confidence_level = (
            "LOW"    if n < _LOW_THRESHOLD    else
            "MEDIUM" if n < _MEDIUM_THRESHOLD else
            "HIGH"
        )
        model_name = _MODEL_MAP[confidence_level]

        # ── 3. Apply moving-average smoothing for LOW-confidence path ─────────
        if confidence_level == "LOW":
            smoothed_history = _apply_moving_average(history, window=3)
        else:
            smoothed_history = history

        # ── 4. Generate forecast using existing tool ──────────────────────────
        try:
            raw = generate_price_forecast(
                smoothed_history,
                horizon_days=horizon_days,
                model_name=model_name,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("ForecastService generate_price_forecast failed: %s", exc)
            return ForecastResult(
                market_id=market_id,
                market_name=market_name,
                commodity=commodity_upper,
                horizon_days=horizon_days,
                data_points=n,
                confidence_level=confidence_level,
                confidence_score=_CONFIDENCE_MAP[confidence_level],
                model_name=model_name,
                predicted_price=None,
                price_change=None,
                price_change_pct=None,
                current_price=float(history[-1]["modal_price"]),
                error=f"Forecast calculation failed: {exc}",
            )

        # ── 5. Compute summary stats ──────────────────────────────────────────
        predictions   = raw.get("predictions", [])
        lower_band    = raw.get("confidence_band", {}).get("lower", [])
        upper_band    = raw.get("confidence_band", {}).get("upper", [])
        current_price = float(history[-1]["modal_price"])
        predicted_price = predictions[-1] if predictions else current_price
        price_change    = round(predicted_price - current_price, 2)
        price_change_pct = round((price_change / current_price * 100) if current_price else 0.0, 2)

        trend_data = calculate_price_trend(history)
        trend_direction = trend_data.get("trend_direction", "flat")

        confidence_score = _CONFIDENCE_MAP[confidence_level]

        result = ForecastResult(
            market_id=market_id,
            market_name=market_name,
            commodity=commodity_upper,
            horizon_days=horizon_days,
            data_points=n,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            model_name=model_name,
            predicted_price=round(predicted_price, 2),
            price_change=price_change,
            price_change_pct=price_change_pct,
            current_price=current_price,
            predictions=predictions,
            lower_band=lower_band,
            upper_band=upper_band,
            trend_direction=trend_direction,
        )

        # ── 6. Persist forecast record ────────────────────────────────────────
        if save and predictions:
            self._save_forecast(result)

        logger.info(
            "ForecastService: market=%d commodity=%s n=%d level=%s predicted=%.2f",
            market_id, commodity_upper, n, confidence_level, predicted_price,
        )
        return result

    # ------------------------------------------------------------------

    @staticmethod
    def _save_forecast(result: ForecastResult) -> None:
        """Persist (or update) a Forecast record for the terminal forecast date."""
        from django.utils import timezone
        from apps.markets.models import Market

        try:
            market = Market.objects.get(pk=result.market_id)
        except Market.DoesNotExist:
            logger.warning("ForecastService._save_forecast: market %d not found.", result.market_id)
            return

        forecast_date = date.today() + timedelta(days=result.horizon_days)
        predicted     = Decimal(str(result.predicted_price))
        lower         = Decimal(str(result.lower_band[-1])) if result.lower_band else predicted * Decimal("0.95")
        upper         = Decimal(str(result.upper_band[-1])) if result.upper_band else predicted * Decimal("1.05")

        Forecast.objects.update_or_create(
            commodity=result.commodity,
            market=market,
            forecast_date=forecast_date,
            defaults={
                "predicted_price":  predicted,
                "lower_bound":      lower,
                "upper_bound":      upper,
                "confidence_score": Decimal(str(result.confidence_score)),
                "model_name":       result.model_name,
                "model_version":    "1.0.0-phase5",
                "horizon_days":     result.horizon_days,
                "is_mock":          False,
            },
        )


# ── Helper ────────────────────────────────────────────────────────────────────

def _apply_moving_average(history: list, window: int = 3) -> list:
    """
    Smooth price history with a simple moving average.
    Returns a new list of the same length with smoothed modal_price values.
    """
    prices = [h["modal_price"] for h in history]
    smoothed = []
    for i in range(len(prices)):
        start = max(0, i - window + 1)
        smoothed.append({"price_date": history[i]["price_date"],
                         "modal_price": statistics.mean(prices[start:i + 1])})
    return smoothed
