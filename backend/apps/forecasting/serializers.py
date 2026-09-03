"""forecasting/serializers.py"""
from rest_framework import serializers
from .models import Forecast


class ForecastSerializer(serializers.ModelSerializer):
    market_name = serializers.CharField(source="market.name", read_only=True)

    class Meta:
        model = Forecast
        fields = (
            "id", "commodity", "market", "market_name",
            "forecast_date", "predicted_price", "lower_bound", "upper_bound",
            "confidence_score", "model_name", "model_version",
            "horizon_days", "generated_at", "is_mock",
        )
