"""
forecasting/views.py — Forecast API stub (full implementation in Phase 5).
"""
from rest_framework import generics, permissions

from .models import Forecast
from .serializers import ForecastSerializer


class ForecastListView(generics.ListAPIView):
    """GET /api/v1/forecast/?commodity=groundnut&market=1"""

    serializer_class = ForecastSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["commodity", "market"]
    ordering = ["-forecast_date"]

    def get_queryset(self):
        return Forecast.objects.select_related("market").all()
