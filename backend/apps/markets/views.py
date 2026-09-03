"""
markets/views.py — Market and MarketPrice API views.
"""
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Market, MarketPrice
from .serializers import MarketSerializer, MarketPriceSerializer


class MarketListView(generics.ListAPIView):
    """GET /api/v1/markets/ — list all active markets."""

    serializer_class = MarketSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Market.objects.filter(is_active=True)
    filterset_fields = ["district", "market_type"]
    search_fields = ["name", "district"]


class MarketPriceListView(generics.ListAPIView):
    """GET /api/v1/markets/prices/ — list market prices with filters."""

    serializer_class = MarketPriceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["commodity", "market", "price_date"]
    ordering_fields = ["price_date", "modal_price"]
    ordering = ["-price_date"]

    def get_queryset(self):
        return MarketPrice.objects.select_related("market").all()


class MarketPriceHistoryView(generics.ListAPIView):
    """
    GET /api/v1/markets/{market_id}/history/?commodity=cotton&days=90
    Returns price history for a specific market and commodity.
    """

    serializer_class = MarketPriceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from datetime import date, timedelta

        market_id = self.kwargs["market_id"]
        commodity = self.request.query_params.get("commodity", "cotton")
        days = int(self.request.query_params.get("days", 90))
        since = date.today() - timedelta(days=days)

        return MarketPrice.objects.filter(
            market_id=market_id,
            commodity=commodity,
            price_date__gte=since,
        ).order_by("price_date")


class NearbyMarketsView(APIView):
    """
    GET /api/v1/markets/nearby/?lat=22.5&lon=70.8&radius_km=100&commodity=groundnut
    Returns active markets sorted by distance from the given coordinates.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        import math

        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        radius_km = float(request.query_params.get("radius_km", 100))
        commodity = request.query_params.get("commodity", "")

        if not lat or not lon:
            return Response(
                {"error": "lat and lon query parameters are required."},
                status=400,
            )

        lat, lon = float(lat), float(lon)

        markets = Market.objects.filter(
            is_active=True,
            latitude__isnull=False,
            longitude__isnull=False,
        )

        results = []
        for market in markets:
            distance = _haversine(lat, lon, float(market.latitude), float(market.longitude))
            if distance <= radius_km:
                data = MarketSerializer(market).data
                data["distance_km"] = round(distance, 1)
                results.append(data)

        results.sort(key=lambda x: x["distance_km"])
        return Response(results)


def _haversine(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance in km between two lat/lon points."""
    import math

    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
