"""
Development settings — extends base.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# ── Development database (SQLite for quick local dev without Docker) ───────────
# Override with DATABASE_URL in .env to use PostgreSQL
# e.g. DATABASE_URL=postgres://krishilink:krishilink@localhost:5432/krishilink_dev

# ── Email backend ─────────────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ── Debug toolbar (optional, uncomment if needed) ────────────────────────────
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
# INTERNAL_IPS = ["127.0.0.1"]
