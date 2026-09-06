"""
agents/ai_explanation_service.py — AI Explanation Service (IBM Granite integration layer).

Provides natural-language synthesis of market analysis, financial calculations,
and price forecasts for farmers.

Architecture:
    AIExplanationService
            │
            ├── MockGraniteProvider        (Active in Demo/Mock Mode)
            │
            └── FutureRealGraniteProvider  (watsonx.ai live API when credentials configured)

In accordance with project requirements:
- In demo/hackathon mode (AI_DEMO_MODE=True or IBM_GRANITE_MODE="mock"),
  MockGraniteProvider simulates an IBM Granite response using ACTUAL calculated data.
- Does NOT invent market prices or financial numbers.
- Explicitly tags output with mode="DEMO_MOCK" and provider="IBM Granite Demo".
- Never falsely claims a live API call was made.
"""
import abc
import logging
from typing import Any, Dict, List, Optional
from django.conf import settings

logger = logging.getLogger("krishilink")


class BaseAIExplanationProvider(abc.ABC):
    """Abstract base class for AI explanation providers."""

    @abc.abstractmethod
    def generate_explanation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured AI explanation from calculated market analysis context.

        Args:
            context: Dictionary containing:
                - crop_lot_id, commodity, quantity_quintal
                - best_market: dict (market_name, district, modal_price, distance_km, gross_revenue, transport_cost, net_revenue)
                - markets: list of market dicts
                - forecast_days, forecast_method, forecast_confidence_level, forecast_confidence_score
                - predicted_price, price_change, price_change_pct, trend_direction
                - language: "english" | "gujarati" | "hindi" (default "english")

        Returns:
            dict with keys:
                - mode: "DEMO_MOCK" | "LIVE_API"
                - provider: str
                - explanation: str
                - key_factors: List[str]
                - market_summary: str
                - risk_notes: List[str]
        """
        pass


class MockGraniteProvider(BaseAIExplanationProvider):
    """
    Mock IBM Granite provider that constructs realistic, farmer-grounded explanations
    using REAL computed analysis figures.
    """

    def generate_explanation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        commodity = (context.get("commodity") or "crop").upper()
        quantity = context.get("quantity_quintal", 0.0)
        best_market = context.get("best_market") or {}
        market_count = len(context.get("markets") or [])

        market_name = best_market.get("market_name", "Nearest APMC")
        district = best_market.get("district", "Gujarat")
        modal_price = best_market.get("modal_price", 0.0)
        distance_km = best_market.get("distance_km")
        gross_rev = best_market.get("gross_revenue", 0.0)
        transport_cost = best_market.get("transport_cost", 0.0)
        other_costs = best_market.get("other_costs", 0.0)
        total_cost = best_market.get("total_cost", transport_cost + other_costs)
        net_rev = best_market.get("net_revenue", gross_rev - total_cost)

        forecast_confidence = context.get("forecast_confidence_level", "LOW")
        confidence_score = context.get("forecast_confidence_score", 0.0)
        trend_direction = context.get("trend_direction", "flat")
        price_change_pct = context.get("price_change_pct", 0.0)
        predicted_price = context.get("predicted_price")
        forecast_days = context.get("forecast_days", 7)
        model_name = context.get("forecast_method") or context.get("forecast_model") or "linear_regression"

        # ── 1. Market Summary ─────────────────────────────────────────────────
        if market_count > 1:
            market_summary = (
                f"{market_name} in {district} offers the highest net return among "
                f"{market_count} Gujarat APMCs evaluated."
            )
        elif market_count == 1:
            market_summary = (
                f"{market_name} in {district} was evaluated for your {commodity.title()} lot."
            )
        else:
            market_summary = "No active APMC market prices currently found for this commodity."

        # ── 2. Explanation ────────────────────────────────────────────────────
        distance_phrase = (
            f"located {distance_km:.1f} km away"
            if distance_km is not None
            else "at your local APMC"
        )
        transport_pct = (
            f"{(transport_cost / gross_rev * 100):.1f}%"
            if gross_rev > 0
            else "minimal"
        )

        trend_phrase = {
            "up": f"projected to rise by {abs(price_change_pct):.1f}% over the next {forecast_days} days",
            "down": f"projected to ease by {abs(price_change_pct):.1f}% over the next {forecast_days} days",
            "flat": f"expected to remain steady around ₹{modal_price:,.0f}/quintal",
        }.get(trend_direction, f"expected to trend {trend_direction}")

        if predicted_price is not None and forecast_confidence != "INSUFFICIENT_DATA":
            forecast_phrase = (
                f"Our {model_name.replace('_', ' ')} forecast suggests prices could reach ₹{predicted_price:,.0f}/quintal "
                f"({trend_phrase}) with {forecast_confidence.lower()} confidence ({confidence_score * 100:.0f}%)."
            )
        else:
            forecast_phrase = (
                "Historical arrivals are currently insufficient for a high-confidence forecast; "
                "selling decisions should be evaluated against prevailing mandi spot rates."
            )

        explanation = (
            f"Based on real-time APMC price analysis for your {quantity:.1f} quintals of {commodity.title()}, "
            f"{market_name} ({distance_phrase}) yields the highest estimated net return of ₹{net_rev:,.0f}. "
            f"Gross value is ₹{gross_rev:,.0f} at ₹{modal_price:,.0f}/quintal, with transport deductions of ₹{transport_cost:,.0f} "
            f"({transport_pct} of total crop value). {forecast_phrase}"
        )

        # ── 3. Key Factors ────────────────────────────────────────────────────
        key_factors = [
            f"Top Net Revenue: ₹{net_rev:,.0f} at {market_name} ({district})",
            f"Current APMC Modal Rate: ₹{modal_price:,.0f}/quintal",
            f"Transport Cost: ₹{transport_cost:,.0f} ({transport_pct} of gross revenue)",
        ]
        if distance_km is not None:
            key_factors.append(f"Transit Distance: {distance_km:.1f} km from registered farm location")
        if forecast_confidence != "INSUFFICIENT_DATA":
            key_factors.append(
                f"Market Price Outlook: Trend is {trend_direction.upper()} "
                f"({price_change_pct:+.1f}%) over {forecast_days} days"
            )
            key_factors.append(
                f"Forecast Confidence: {forecast_confidence} ({confidence_score * 100:.0f}%) using {model_name}"
            )
        else:
            key_factors.append("Forecast: Historical arrival data is insufficient (< 7 price records)")

        # ── 4. Risk Notes ─────────────────────────────────────────────────────
        risk_notes = []
        if transport_cost > (gross_rev * 0.10) and gross_rev > 0:
            risk_notes.append(
                f"High Transport Burden: Transit represents {transport_pct} of crop value. "
                "Consider pooling loads with nearby farmers to reduce per-quintal freight."
            )
        if distance_km is None:
            risk_notes.append(
                "Missing Location Coordinates: Farm coordinates are not registered; "
                "exact transport cost cannot be calculated until profile coordinates are updated."
            )
        if forecast_confidence in ("LOW", "INSUFFICIENT_DATA"):
            risk_notes.append(
                "Arrival Volatility: Price trend confidence is limited by sample size. "
                "Verify actual morning auction arrivals before dispatching cargo."
            )
        if not risk_notes:
            risk_notes.append("Market conditions appear stable; verify local APMC auction timing before dispatch.")

        return {
            "mode": "DEMO_MOCK",
            "provider": "IBM Granite Demo",
            "explanation": explanation,
            "key_factors": key_factors,
            "market_summary": market_summary,
            "risk_notes": risk_notes,
        }


class FutureRealGraniteProvider(BaseAIExplanationProvider):
    """
    Placeholder for live IBM watsonx.ai Granite integration.
    Will be activated once IBM_WATSONX credentials and endpoint are provisioned.
    """

    def generate_explanation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError(
            "Live IBM Granite API is not configured. Enable AI_DEMO_MODE=True to use MockGraniteProvider."
        )


class AIExplanationService:
    """
    Unified AI Explanation service.
    Directs requests to MockGraniteProvider or FutureRealGraniteProvider
    based on environment configuration.
    """

    def __init__(self):
        self.mode = getattr(settings, "IBM_GRANITE_MODE", "mock").lower()
        self.demo_mode = getattr(settings, "AI_DEMO_MODE", True)

        if self.demo_mode or self.mode == "mock":
            self.provider = MockGraniteProvider()
        else:
            # Check if live credentials exist
            has_creds = bool(
                getattr(settings, "IBM_WATSONX_API_KEY", "")
                and getattr(settings, "IBM_WATSONX_URL", "")
                and getattr(settings, "IBM_WATSONX_PROJECT_ID", "")
            )
            if has_creds:
                self.provider = FutureRealGraniteProvider()
            else:
                logger.info("Live IBM Granite credentials not found; falling back to MockGraniteProvider.")
                self.provider = MockGraniteProvider()

    def generate_explanation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured AI explanation."""
        try:
            return self.provider.generate_explanation(context)
        except Exception as exc:
            logger.warning("AIExplanationService error (%s), using MockGraniteProvider fallback", exc)
            return MockGraniteProvider().generate_explanation(context)


# Global singleton instance
ai_explanation_service = AIExplanationService()
