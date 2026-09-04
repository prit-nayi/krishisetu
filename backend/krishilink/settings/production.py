"""
Production settings — extends base.
Override SECRET_KEY, DATABASES, ALLOWED_HOSTS via environment variables.
"""
from .base import *  # noqa: F401, F403
import os

DEBUG = False

SECRET_KEY = os.environ.get("SECRET_KEY", "INSECURE-CHANGE-ME")

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

# Production database — set DATABASE_URL env var
if os.environ.get("DATABASE_URL"):
    import dj_database_url
    DATABASES = {"default": dj_database_url.config(default=os.environ["DATABASE_URL"])}

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
