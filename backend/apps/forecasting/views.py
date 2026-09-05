from rest_framework import generics, permissions
from .models import Forecast
from .serializers import ForecastSerializer

class ForecastListView(generics.ListAPIView):
    """GET /api/v1/forecast/?commodity=groundnut"""
    serializer_class   = ForecastSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Forecast.objects.all()
        commodity = self.request.query_params.get("commodity")
        if commodity:
            qs = qs.filter(commodity__iexact=commodity)
        return qs.order_by("-forecast_date")[:50]
