"""
Make Celery app available when package is imported.
Guarded so Django can start without Celery being installed (e.g. during tests).
"""
try:
    from .celery import app as celery_app  # noqa: F401
    __all__ = ("celery_app",)
except ImportError:
    __all__ = ()
