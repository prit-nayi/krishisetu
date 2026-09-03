"""
crops/serializers.py
"""
from rest_framework import serializers

from .models import CropLot


class CropLotSerializer(serializers.ModelSerializer):
    """Full read serializer for a CropLot."""

    commodity_display = serializers.CharField(
        source="get_commodity_display", read_only=True
    )
    unit_display = serializers.CharField(source="get_unit_display", read_only=True)
    quality_grade_display = serializers.CharField(
        source="get_quality_grade_display", read_only=True
    )
    storage_status_display = serializers.CharField(
        source="get_storage_status_display", read_only=True
    )

    class Meta:
        model = CropLot
        fields = (
            "id", "commodity", "commodity_display",
            "variety", "quantity", "unit", "unit_display",
            "moisture_percent", "quality_grade", "quality_grade_display",
            "harvest_date", "storage_status", "storage_status_display",
            "storage_start_date", "notes", "is_active",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class CropLotCreateUpdateSerializer(serializers.ModelSerializer):
    """Write serializer for creating/updating a CropLot."""

    class Meta:
        model = CropLot
        fields = (
            "commodity", "variety", "quantity", "unit",
            "moisture_percent", "quality_grade",
            "harvest_date", "storage_status", "storage_start_date", "notes",
        )

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_moisture_percent(self, value):
        if value is not None and not (0 <= value <= 100):
            raise serializers.ValidationError(
                "Moisture percent must be between 0 and 100."
            )
        return value
