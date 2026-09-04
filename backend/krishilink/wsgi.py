"""
WSGI config for KrishiLink AI.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "krishilink.settings.production")
application = get_wsgi_application()
