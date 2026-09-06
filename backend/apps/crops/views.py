"""
crops/views.py — CropLot CRUD ViewSet.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from apps.accounts.models import FarmerProfile
from .models import CropLot
from .serializers import CropLotSerializer, CropLotCreateUpdateSerializer


class CropLotViewSet(viewsets.ModelViewSet):
    """
    CRUD for a farmer's crop lots.
    Farmers can only access and modify their own lots.
    DELETE performs a soft-delete (sets is_active=False).
    Create/Update responses use the full read serializer so callers receive id.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only active crop lots belonging to the authenticated farmer."""
        try:
            farmer_profile = self.request.user.farmer_profile
        except FarmerProfile.DoesNotExist:
            return CropLot.objects.none()
        return (
            CropLot.objects.filter(farmer=farmer_profile, is_active=True)
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        """Write operations use the compact write serializer for input validation."""
        if self.action in ("create", "update", "partial_update"):
            return CropLotCreateUpdateSerializer
        return CropLotSerializer

    def _full_response(self, instance, status_code):
        """Return the full read serializer representation."""
        serializer = CropLotSerializer(instance, context=self.get_serializer_context())
        return Response(serializer.data, status=status_code)

    def create(self, request, *args, **kwargs):
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        self.perform_create(write_serializer)
        return self._full_response(write_serializer.instance, status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        write_serializer = self.get_serializer(instance, data=request.data, partial=partial)
        write_serializer.is_valid(raise_exception=True)
        self.perform_update(write_serializer)
        return self._full_response(write_serializer.instance, status.HTTP_200_OK)

    def perform_create(self, serializer):
        """Attach the authenticated farmer's profile to the new lot."""
        farmer_profile, _ = FarmerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"district": "", "village": ""},
        )
        serializer.save(farmer=farmer_profile)

    def destroy(self, request, *args, **kwargs):
        """Soft-delete: set is_active=False instead of removing the record."""
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
