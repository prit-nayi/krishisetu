"""
Development settings — extends base.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Email backend — print to console in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
