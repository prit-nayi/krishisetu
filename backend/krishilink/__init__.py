"""Make Celery app available when package is imported."""
from .celery import app as celery_app

__all__ = ("celery_app",)
