"""
markets/urls.py
"""
from django.urls import path

from .views import (
    MarketListView,
    MarketPriceListView,
    MarketPriceHistoryView,
    NearbyMarketsView,
)

urlpatterns = [
    path("", MarketListView.as_view(), name="market-list"),
    path("prices/", MarketPriceListView.as_view(), name="market-price-list"),
    path("<int:market_id>/history/", MarketPriceHistoryView.as_view(), name="market-price-history"),
    path("nearby/", NearbyMarketsView.as_view(), name="market-nearby"),
]
