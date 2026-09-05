"""
agents/granite_client.py — IBM Granite client stub with fallback.

In Phase 7, this will be wired to IBM watsonx.ai.
Until then, the fallback template explanation is used.
"""
import logging
from django.conf import settings

logger = logging.getLogger("krishilink")


class GraniteClient:
    """Wrapper around IBM watsonx.ai Granite model for generating farmer-friendly explanations."""

    FALLBACK_TEMPLATE = (
        "Based on current market data, the recommendation for your {commodity} lot "
        "({quantity} {unit}) is to {action}. "
        "Current net value: ₹{current_net_value:,.0f}. "
        "Expected future net value: ₹{expected_future_net_value:,.0f}. "
        "Key factors: {factors}."
    )

    def __init__(self):
        self.api_key    = getattr(settings, "IBM_WATSONX_API_KEY",    "")
        self.url        = getattr(settings, "IBM_WATSONX_URL",        "")
        self.project_id = getattr(settings, "IBM_WATSONX_PROJECT_ID", "")
        self.model_id   = getattr(settings, "IBM_GRANITE_MODEL_ID",   "ibm/granite-13b-instruct-v2")
        self._client    = None

    @property
    def is_configured(self):
        return bool(self.api_key and self.url and self.project_id)

    def generate_explanation(self, context: dict, language: str = "english") -> dict:
        """
        Generate a natural-language explanation of a SELL/HOLD/PARTIAL_SELL recommendation.

        Args:
            context: Structured JSON bundle from the orchestrator.
            language: "english" | "gujarati" | "hindi"

        Returns:
            {"explanation": str, "source": "granite" | "fallback", "language": str}
        """
        if not self.is_configured:
            return self._fallback_explanation(context, language)

        try:
            return self._call_granite(context, language)
        except Exception as exc:
            logger.warning("Granite API call failed, using fallback: %s", exc)
            return self._fallback_explanation(context, language)

    def _call_granite(self, context: dict, language: str) -> dict:
        """Make actual watsonx.ai API call. Implemented in Phase 7."""
        raise NotImplementedError("Granite API integration implemented in Phase 7.")

    def _fallback_explanation(self, context: dict, language: str) -> dict:
        """Return a deterministic template-based explanation."""
        crop    = context.get("crop_lot", {})
        rec     = context.get("recommendation", {})
        factors = context.get("reasoning_factors", [])

        explanation = self.FALLBACK_TEMPLATE.format(
            commodity=crop.get("commodity", "crop"),
            quantity=crop.get("quantity", ""),
            unit=crop.get("unit", "quintal"),
            action=rec.get("action", "SELL_NOW").replace("_", " ").title(),
            current_net_value=float(rec.get("current_net_value", 0)),
            expected_future_net_value=float(rec.get("expected_future_net_value", 0)),
            factors=", ".join(factors) if factors else "market analysis",
        )
        return {"explanation": explanation, "source": "fallback", "language": language}


# Singleton instance
granite_client = GraniteClient()
