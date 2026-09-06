"""
marketplace/serializers.py — Serializers for CropListing and BuyerInquiry.
"""
from rest_framework import serializers
from .models import CropListing, BuyerInquiry
from apps.accounts.serializers import UserSerializer


class CropListingSerializer(serializers.ModelSerializer):
    """Full read serializer for crop marketplace listings."""

    farmer = UserSerializer(read_only=True)
    inquiry_count = serializers.SerializerMethodField()
    total_expected_value = serializers.SerializerMethodField()

    class Meta:
        model = CropListing
        fields = (
            "id",
            "crop_lot",
            "farmer",
            "title",
            "commodity",
            "quantity_quintal",
            "expected_price_per_quintal",
            "total_expected_value",
            "location_district",
            "location_state",
            "quality_grade",
            "harvest_date",
            "description",
            "status",
            "is_active",
            "inquiry_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "farmer", "inquiry_count", "total_expected_value", "created_at", "updated_at")

    def get_inquiry_count(self, obj):
        return obj.inquiries.count()

    def get_total_expected_value(self, obj):
        try:
            return float(obj.quantity_quintal * obj.expected_price_per_quintal)
        except Exception:
            return 0.0


class CropListingCreateSerializer(serializers.ModelSerializer):
    """Write serializer for creating/updating crop listings."""

    class Meta:
        model = CropListing
        fields = (
            "crop_lot",
            "title",
            "commodity",
            "quantity_quintal",
            "expected_price_per_quintal",
            "location_district",
            "location_state",
            "quality_grade",
            "harvest_date",
            "description",
            "status",
            "is_active",
        )


class BuyerInquirySerializer(serializers.ModelSerializer):
    """Full read serializer for buyer purchase inquiries."""

    buyer = UserSerializer(read_only=True)
    listing_title = serializers.CharField(source="listing.title", read_only=True)
    commodity = serializers.CharField(source="listing.commodity", read_only=True)
    farmer_email = serializers.CharField(source="listing.farmer.email", read_only=True)
    farmer_district = serializers.CharField(source="listing.location_district", read_only=True)
    total_offered_value = serializers.SerializerMethodField()

    class Meta:
        model = BuyerInquiry
        fields = (
            "id",
            "listing",
            "listing_title",
            "commodity",
            "buyer",
            "farmer_email",
            "farmer_district",
            "offered_price_per_quintal",
            "requested_quantity_quintal",
            "total_offered_value",
            "message",
            "contact_phone",
            "status",
            "farmer_notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "buyer",
            "listing_title",
            "commodity",
            "farmer_email",
            "farmer_district",
            "total_offered_value",
            "created_at",
            "updated_at",
        )

    def get_total_offered_value(self, obj):
        try:
            return float(obj.offered_price_per_quintal * obj.requested_quantity_quintal)
        except Exception:
            return 0.0


class BuyerInquiryCreateSerializer(serializers.ModelSerializer):
    """Write serializer for buyers creating an inquiry."""

    class Meta:
        model = BuyerInquiry
        fields = (
            "listing",
            "offered_price_per_quintal",
            "requested_quantity_quintal",
            "message",
            "contact_phone",
        )


class BuyerInquiryRespondSerializer(serializers.ModelSerializer):
    """Write serializer for farmers accepting/rejecting an inquiry."""

    class Meta:
        model = BuyerInquiry
        fields = ("status", "farmer_notes")
