"""decisions/urls.py"""
from django.urls import path
from .views import RecommendationListView, AnalyzeView

urlpatterns = [
    path("", RecommendationListView.as_view(), name="recommendation-list"),
    path("analyze/<int:crop_lot_id>/", AnalyzeView.as_view(), name="decision-analyze"),
]
