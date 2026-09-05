from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Recommendation
from .serializers import RecommendationSerializer


class RecommendationListView(generics.ListAPIView):
    """GET /api/v1/decisions/ — list farmer's recommendations."""
    serializer_class   = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Recommendation.objects.filter(
            crop_lot__farmer__user=self.request.user
        ).order_by("-generated_at")


class AnalyzeView(APIView):
    """POST /api/v1/decisions/analyze/{crop_lot_id}/ — trigger full analysis pipeline."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, crop_lot_id):
        # Full orchestrator wired in Phase 8
        return Response(
            {"message": "Analysis pipeline not yet implemented. Coming in Phase 8."},
            status=501,
        )
