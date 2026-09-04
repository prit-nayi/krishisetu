"""
common/exceptions.py — Standardised DRF exception handler.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response

logger = logging.getLogger("krishilink")


def krishilink_exception_handler(exc, context):
    """
    Custom DRF exception handler that wraps all errors in a consistent shape:
    {
        "error": true,
        "detail": "...",
        "errors": { field: [messages] }   # optional, for validation errors
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        data = {"error": True}

        if isinstance(response.data, dict):
            if "detail" in response.data:
                data["detail"] = str(response.data["detail"])
            else:
                data["detail"] = "Validation error."
                data["errors"] = response.data
        elif isinstance(response.data, list):
            data["detail"] = "Validation error."
            data["errors"] = response.data
        else:
            data["detail"] = str(response.data)

        response.data = data

    return response
