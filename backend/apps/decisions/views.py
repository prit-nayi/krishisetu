"""
decisions/views.py — Decision analysis stub (full implementation in Phase 6).
"""
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.crops.models import CropLot
from .models import Recommendation
from .serializers import RecommendationSerializer


class RecommendationListView(generics.ListAPIView):
    """GET /api/v1/decisions/ — list recommendations for the authenticated farmer."""

    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            farmer_profile = self.request.user.farmer_profile
        except Exception:
            return Recommendation.objects.none()
        return Recommendation.objects.filter(
            crop_lot__farmer=farmer_profile
        ).select_related("best_market", "crop_lot")


class AnalyzeView(APIView):
    """
    POST /api/v1/decisions/analyze/{crop_lot_id}/
    Full analysis pipeline — stub for Phase 8 orchestrator integration.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, crop_lot_id):
        try:
            farmer_profile = request.user.farmer_profile
            crop_lot = CropLot.objects.get(
                id=crop_lot_id, farmer=farmer_profile, is_active=True
            )
        except CropLot.DoesNotExist:
            return Response({"error": "Crop lot not found."}, status=404)
        except Exception:
            return Response({"error": "Farmer profile not found."}, status=400)

        # Placeholder — orchestrator will be wired in Phase 8
        return Response(
            {
                "message": "Analysis pipeline not yet implemented. Coming in Phase 8.",
                "crop_lot_id": crop_lot.id,
            },
            status=202,
        )
