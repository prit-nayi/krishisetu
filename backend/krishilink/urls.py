"""
KrishiLink AI — Root URL configuration.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # API v1
    path("api/v1/auth/",      include("apps.accounts.urls.auth_urls")),
    path("api/v1/farmer/",    include("apps.accounts.urls.farmer_urls")),
    path("api/v1/markets/",   include("apps.markets.urls")),
    path("api/v1/crops/",     include("apps.crops.urls")),
    path("api/v1/forecast/",  include("apps.forecasting.urls")),
    path("api/v1/decisions/", include("apps.decisions.urls")),

    # API schema / docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/",   SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/",  SpectacularRedocView.as_view(url_name="schema"),  name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
