"""
agents/granite_client.py — IBM Granite (watsonx.ai) client stub.
Full implementation in Phase 7.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class GraniteClient:
    """
    Thin wrapper around IBM watsonx.ai Granite model.
    Provides a single generate() method.
    Falls back to a template explanation when the API is unavailable.
    """

    def __init__(self):
        self.api_key = settings.IBM_WATSONX_API_KEY
        self.url = settings.IBM_WATSONX_URL
        self.project_id = settings.IBM_WATSONX_PROJECT_ID
        self.model_id = settings.IBM_GRANITE_MODEL_ID
        self._client = None

    def _get_client(self):
        """Lazily initialise the watsonx.ai client."""
        if not self._client:
            if not self.api_key or not self.url:
                return None
            try:
                from ibm_watsonx_ai import APIClient, Credentials
                credentials = Credentials(url=self.url, api_key=self.api_key)
                self._client = APIClient(credentials)
            except Exception as exc:
                logger.warning("Could not initialise Granite client: %s", exc)
                return None
        return self._client

    def generate(self, prompt: str, language: str = "english") -> str:
        """
        Generate a farmer-friendly explanation from a structured prompt.
        Returns a fallback message if Granite is unavailable.
        """
        client = self._get_client()
        if not client:
            return self._fallback_explanation(language)

        try:
            from ibm_watsonx_ai.foundation_models import ModelInference
            model = ModelInference(
                model_id=self.model_id,
                project_id=self.project_id,
                api_client=client,
            )
            response = model.generate_text(prompt=prompt)
            return response
        except Exception as exc:
            logger.error("Granite generation failed: %s", exc)
            return self._fallback_explanation(language)

    def _fallback_explanation(self, language: str) -> str:
        messages = {
            "gujarati": "AI સ્પષ્ટીકરણ હાલ ઉપલબ્ધ નથી. કૃપા કરીને ભલામણ કાર્ડ જુઓ.",
            "hindi": "AI स्पष्टीकरण अभी उपलब्ध नहीं है। कृपया अनुशंसा कार्ड देखें।",
            "english": (
                "AI explanation is temporarily unavailable. "
                "Please refer to the recommendation card for details."
            ),
        }
        return messages.get(language, messages["english"])
