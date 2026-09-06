"""
marketplace/views.py — ViewSets and APIs for Crop Listings, Buyer Inquiries, and Marketplace Stats.
"""
from django.db.models import Avg, Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CropListing, BuyerInquiry
from .serializers import (
    CropListingSerializer,
    CropListingCreateSerializer,
    BuyerInquirySerializer,
    BuyerInquiryCreateSerializer,
    BuyerInquiryRespondSerializer,
)
from apps.common.permissions import IsFarmer, IsBuyer, IsAdminUser, IsOwnerOrAdmin


class CropListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Crop Listings.
    - Public / All Authenticated: browse active listings with filters
    - Farmers: create, update, delete own listings, view my_listings
    - Admins: full CRUD
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["commodity", "location_district", "location_state", "status", "quality_grade"]
    search_fields = ["title", "commodity", "location_district", "description", "quality_grade"]
    ordering_fields = ["created_at", "expected_price_per_quintal", "quantity_quintal"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ["create"]:
            return [permissions.IsAuthenticated(), (IsFarmer | IsAdminUser)()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CropListingCreateSerializer
        return CropListingSerializer

    def get_queryset(self):
        user = self.request.user
        # Admins see everything
        if user.is_authenticated and (user.role == "admin" or user.is_staff):
            return CropListing.objects.all().select_related("farmer", "crop_lot")

        # By default in list view, return active listings
        if self.action == "list":
            return CropListing.objects.filter(is_active=True, status=CropListing.Status.ACTIVE).select_related("farmer", "crop_lot")

        return CropListing.objects.all().select_related("farmer", "crop_lot")

    def perform_create(self, serializer):
        serializer.save(farmer=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def my_listings(self, request):
        """Returns listings created by the authenticated farmer."""
        listings = CropListing.objects.filter(farmer=request.user).order_by("-created_at")
        page = self.paginate_queryset(listings)
        if page is not None:
            serializer = CropListingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = CropListingSerializer(listings, many=True)
        return Response(serializer.data)


class BuyerInquiryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Buyer Inquiries.
    - Buyers: submit inquiries, view sent inquiries
    - Farmers: view received inquiries on their listings, respond (accept/reject)
    - Admins: view and manage all inquiries
    """

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "listing"]
    ordering_fields = ["created_at", "offered_price_per_quintal"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ["create"]:
            return [permissions.IsAuthenticated(), (IsBuyer | IsAdminUser)()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ["create"]:
            return BuyerInquiryCreateSerializer
        if self.action in ["respond"]:
            return BuyerInquiryRespondSerializer
        return BuyerInquirySerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return BuyerInquiry.objects.none()

        if user.role == "admin" or user.is_staff:
            return BuyerInquiry.objects.all().select_related("buyer", "listing", "listing__farmer")

        if user.role == "buyer":
            return BuyerInquiry.objects.filter(buyer=user).select_related("buyer", "listing", "listing__farmer")

        # If farmer, return inquiries on this farmer's listings
        return BuyerInquiry.objects.filter(listing__farmer=user).select_related("buyer", "listing", "listing__farmer")

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def sent(self, request):
        """Inquiries initiated by the authenticated user."""
        inquiries = BuyerInquiry.objects.filter(buyer=request.user).order_by("-created_at")
        page = self.paginate_queryset(inquiries)
        if page is not None:
            serializer = BuyerInquirySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BuyerInquirySerializer(inquiries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def received(self, request):
        """Inquiries received for the authenticated farmer's listings."""
        inquiries = BuyerInquiry.objects.filter(listing__farmer=request.user).order_by("-created_at")
        page = self.paginate_queryset(inquiries)
        if page is not None:
            serializer = BuyerInquirySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BuyerInquirySerializer(inquiries, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def respond(self, request, pk=None):
        """Farmer accepts or rejects an inquiry."""
        inquiry = self.get_object()

        # Permission check: must be farmer owning the listing or admin
        if inquiry.listing.farmer != request.user and request.user.role != "admin" and not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to respond to this inquiry."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_status = request.data.get("status")
        if new_status not in [BuyerInquiry.Status.ACCEPTED, BuyerInquiry.Status.REJECTED, BuyerInquiry.Status.CLOSED]:
            return Response(
                {"error": f"Invalid status '{new_status}'. Must be ACCEPTED, REJECTED, or CLOSED."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inquiry.status = new_status
        inquiry.farmer_notes = request.data.get("farmer_notes", inquiry.farmer_notes)
        inquiry.save()

        # If accepted, mark listing status as PENDING_DEAL
        if new_status == BuyerInquiry.Status.ACCEPTED:
            inquiry.listing.status = CropListing.Status.PENDING_DEAL
            inquiry.listing.save(update_fields=["status", "updated_at"])

        return Response(BuyerInquirySerializer(inquiry).data, status=status.HTTP_200_OK)


class MarketplaceStatsView(APIView):
    """
    GET /api/v1/marketplace/stats/
    Returns high-level summary metrics of the active marketplace.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        active_listings = CropListing.objects.filter(is_active=True, status=CropListing.Status.ACTIVE)
        total_listings = active_listings.count()
        total_quantity = active_listings.aggregate(total_q=Sum("quantity_quintal"))["total_q"] or 0
        total_inquiries = BuyerInquiry.objects.count()

        cotton_avg = (
            active_listings.filter(commodity__icontains="cotton").aggregate(
                avg_p=Avg("expected_price_per_quintal")
            )["avg_p"]
            or 0
        )
        groundnut_avg = (
            active_listings.filter(commodity__icontains="groundnut").aggregate(
                avg_p=Avg("expected_price_per_quintal")
            )["avg_p"]
            or 0
        )

        districts_count = active_listings.values("location_district").distinct().count()

        return Response({
            "total_active_listings": total_listings,
            "total_listed_quantity_quintal": float(total_quantity),
            "total_inquiries": total_inquiries,
            "districts_covered": districts_count,
            "average_prices": {
                "cotton_per_quintal": round(float(cotton_avg), 2),
                "groundnut_per_quintal": round(float(groundnut_avg), 2),
            },
        }, status=status.HTTP_200_OK)
