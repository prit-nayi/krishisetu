"""
marketplace/urls.py — Routing for marketplace listings, inquiries, and stats.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CropListingViewSet, BuyerInquiryViewSet, MarketplaceStatsView

router = DefaultRouter()
router.register(r"listings", CropListingViewSet, basename="crop-listing")
router.register(r"inquiries", BuyerInquiryViewSet, basename="buyer-inquiry")

urlpatterns = [
    path("stats/", MarketplaceStatsView.as_view(), name="marketplace-stats"),
    path("", include(router.urls)),
]
