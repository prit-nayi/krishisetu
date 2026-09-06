"""
markets/serializers.py
"""
from rest_framework import serializers
from .models import Market, MarketPrice


class MarketSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Market
        fields = (
            "id", "name", "district", "taluka",
            "latitude", "longitude",
            "market_type", "state",
            "source", "source_url",
            "is_active",
        )


class MarketPriceSerializer(serializers.ModelSerializer):
    market_name     = serializers.CharField(source="market.name",     read_only=True)
    market_district = serializers.CharField(source="market.district", read_only=True)

    class Meta:
        model  = MarketPrice
        fields = (
            "id",
            "market", "market_name", "market_district",
            "commodity", "variety", "grade",
            "min_price", "max_price", "modal_price",
            "arrival_quantity",
            "price_date",
            "source", "source_timestamp",
            "is_verified",
        )
