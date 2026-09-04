"""
markets/views.py — Market and MarketPrice API views.
"""
import math
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import Market, MarketPrice
from .serializers import MarketSerializer, MarketPriceSerializer


class MarketListView(generics.ListAPIView):
    """GET /api/v1/markets/ — list all active markets."""
    queryset           = Market.objects.filter(is_active=True)
    serializer_class   = MarketSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ["district", "market_type"]


class MarketPriceListView(generics.ListAPIView):
    """GET /api/v1/markets/prices/?commodity=groundnut&market=1"""
    serializer_class   = MarketPriceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = MarketPrice.objects.select_related("market")
        commodity = self.request.query_params.get("commodity")
        market_id = self.request.query_params.get("market")
        if commodity:
            qs = qs.filter(commodity__iexact=commodity)
        if market_id:
            qs = qs.filter(market_id=market_id)
        return qs.order_by("-price_date")[:100]


class MarketPriceHistoryView(generics.ListAPIView):
    """GET /api/v1/markets/history/?commodity=groundnut&market=1&days=90"""
    serializer_class   = MarketPriceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from django.utils import timezone
        from datetime import timedelta
        commodity = self.request.query_params.get("commodity", "groundnut")
        market_id = self.request.query_params.get("market")
        days      = int(self.request.query_params.get("days", 90))
        since     = timezone.now().date() - timedelta(days=days)
        qs = MarketPrice.objects.filter(commodity__iexact=commodity, price_date__gte=since)
        if market_id:
            qs = qs.filter(market_id=market_id)
        return qs.order_by("price_date")


class NearbyMarketsView(APIView):
    """GET /api/v1/markets/nearby/?lat=22.16&lon=70.79&radius_km=50&commodity=groundnut"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            lat       = float(request.query_params.get("lat", 0))
            lon       = float(request.query_params.get("lon", 0))
            radius_km = float(request.query_params.get("radius_km", 100))
            commodity = request.query_params.get("commodity", "")
        except ValueError:
            return Response({"error": "Invalid parameters."}, status=400)

        markets = Market.objects.filter(is_active=True)
        results = []
        for m in markets:
            if m.latitude is None or m.longitude is None:
                continue
            dist = _haversine(lat, lon, float(m.latitude), float(m.longitude))
            if dist <= radius_km:
                data = MarketSerializer(m).data
                data["distance_km"] = round(dist, 1)
                results.append(data)

        results.sort(key=lambda x: x["distance_km"])
        return Response(results)


def _haversine(lat1, lon1, lat2, lon2):
    """Return distance in km between two lat/lon points."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
