"""
decisions/urls.py
"""
from django.urls import path
from .views import RecommendationListView, AnalyzeView, MarketAnalysisView

urlpatterns = [
    path("",                          RecommendationListView.as_view(), name="recommendation-list"),
    path("analyze/<int:crop_lot_id>/", AnalyzeView.as_view(),           name="analyze"),
    path("market-analysis/",          MarketAnalysisView.as_view(),     name="market-analysis"),
]
