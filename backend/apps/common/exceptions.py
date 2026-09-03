"""
common/exceptions.py — Standardised DRF exception handler.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def krishilink_exception_handler(exc, context):
    """Custom exception handler that returns consistent JSON error envelopes."""
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "success": False,
            "error": {
                "status_code": response.status_code,
                "detail": response.data,
            },
        }
    else:
        logger.exception("Unhandled exception in view: %s", exc)
        response = Response(
            {
                "success": False,
                "error": {
                    "status_code": 500,
                    "detail": "An unexpected error occurred.",
                },
            },
            status=500,
        )

    return response
