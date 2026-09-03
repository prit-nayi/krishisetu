"""decisions/serializers.py"""
from rest_framework import serializers
from .models import Recommendation


class RecommendationSerializer(serializers.ModelSerializer):
    best_market_name = serializers.CharField(
        source="best_market.name", read_only=True, allow_null=True
    )
    recommendation_display = serializers.CharField(
        source="get_recommendation_display", read_only=True
    )

    class Meta:
        model = Recommendation
        fields = (
            "id", "crop_lot",
            "best_market", "best_market_name",
            "recommendation", "recommendation_display",
            "current_net_value", "expected_future_net_value",
            "sell_quantity_suggestion", "confidence",
            "reasoning_factors", "rule_version",
            "granite_explanation", "generated_at",
        )
        read_only_fields = fields
