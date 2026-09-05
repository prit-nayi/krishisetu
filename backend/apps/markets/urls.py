"""
markets/urls.py
"""
from django.urls import path
from .views import MarketListView, MarketPriceListView, MarketPriceHistoryView, NearbyMarketsView

urlpatterns = [
    path("",        MarketListView.as_view(),        name="market-list"),
    path("prices/", MarketPriceListView.as_view(),   name="market-prices"),
    path("history/",MarketPriceHistoryView.as_view(),name="market-history"),
    path("nearby/", NearbyMarketsView.as_view(),     name="market-nearby"),
]
