"""
crops/views.py — CropLot CRUD ViewSet.
"""
from rest_framework import viewsets, permissions

from apps.accounts.models import FarmerProfile
from .models import CropLot
from .serializers import CropLotSerializer, CropLotCreateUpdateSerializer


class CropLotViewSet(viewsets.ModelViewSet):
    """
    CRUD for a farmer's crop lots.
    Farmers can only access their own lots.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only crop lots belonging to the authenticated farmer."""
        try:
            farmer_profile = self.request.user.farmer_profile
        except FarmerProfile.DoesNotExist:
            return CropLot.objects.none()
        return CropLot.objects.filter(
            farmer=farmer_profile, is_active=True
        ).order_by("-created_at")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CropLotCreateUpdateSerializer
        return CropLotSerializer

    def perform_create(self, serializer):
        farmer_profile, _ = FarmerProfile.objects.get_or_create(
            user=self.request.user
        )
        serializer.save(farmer=farmer_profile)
