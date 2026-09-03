"""ASGI config for KrishiLink AI."""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "krishilink.settings.development")
application = get_asgi_application()
