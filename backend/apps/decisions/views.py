"""
decisions/views.py — Phase 4+5+6 combined market analysis + SELL/HOLD decision API.
"""
import logging
from dataclasses import asdict
from decimal import Decimal

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from .models import Recommendation
from .serializers import RecommendationSerializer
from .services.combined_analysis import CombinedAnalysisService

logger = logging.getLogger("krishilink")


# ── Existing views (unchanged) ────────────────────────────────────────────────

class RecommendationListView(generics.ListAPIView):
    """GET /api/v1/decisions/ — list farmer's recommendations."""
    serializer_class   = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Recommendation.objects.filter(
            crop_lot__farmer__user=self.request.user
        ).order_by("-generated_at")


# ── Phase 6: Full Analyze + Persist ──────────────────────────────────────────

class AnalyzeView(APIView):
    """
    POST /api/v1/decisions/analyze/{crop_lot_id}/

    Runs the full combined analysis pipeline (market financial + forecast + decision)
    and persists a Recommendation record to the database.

    Returns the full analysis result including the saved recommendation ID.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, crop_lot_id):
        # ── Parse forecast_days ───────────────────────────────────────────────
        try:
            forecast_days = int(request.data.get("forecast_days", 7))
            forecast_days = max(1, min(forecast_days, 90))
        except (TypeError, ValueError):
            forecast_days = 7

        # ── Run combined analysis ─────────────────────────────────────────────
        svc = CombinedAnalysisService()
        result = svc.run(
            crop_lot_id=crop_lot_id,
            user=request.user,
            forecast_days=forecast_days,
            save_forecasts=False,
        )

        # ── Permission / not-found check ──────────────────────────────────────
        if result.errors and not result.markets:
            first_error = result.errors[0]
            if "permission" in first_error.lower():
                return Response({"error": first_error}, status=status.HTTP_403_FORBIDDEN)
            if "not found" in first_error.lower() or "inactive" in first_error.lower():
                return Response({"error": first_error}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": first_error, "details": result.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        # ── Persist recommendation ────────────────────────────────────────────
        recommendation_id = None
        if result.decision and result.best_market:
            try:
                recommendation_id = _persist_recommendation(
                    crop_lot_id=crop_lot_id,
                    result=result,
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("AnalyzeView: failed to persist recommendation: %s", exc)
                # Non-fatal: still return the analysis result

        # ── Serialise ─────────────────────────────────────────────────────────
        markets_out  = [asdict(m) for m in result.markets]
        best_out     = asdict(result.best_market) if result.best_market else None
        decision_out = asdict(result.decision) if result.decision else None

        return Response({
            "crop_lot_id":          result.crop_lot_id,
            "commodity":            result.commodity,
            "quantity_quintal":     round(result.quantity_quintal, 4),
            "farmer_location": {
                "lat": result.farmer_lat,
                "lon": result.farmer_lon,
            },
            "forecast_days":        forecast_days,
            "market_count":         len(result.markets),
            "best_market":          best_out,
            "markets":              markets_out,
            "ai_explanation":       result.ai_explanation,
            "decision":             decision_out,
            "recommendation_id":    recommendation_id,
            "skipped_markets":      result.skipped_markets,
            "warnings":             result.errors,
        }, status=status.HTTP_200_OK)


# ── Phase 4+5: Combined Market Analysis (no persistence) ─────────────────────

class MarketAnalysisView(APIView):
    """
    POST /api/v1/analysis/market-analysis/

    Input:
        {
          "crop_lot_id": 12,
          "forecast_days": 7          (optional, default 7, max 90)
        }

    Returns a combined financial analysis + price forecast + SELL/HOLD decision
    for every active Gujarat market that has a recent price for the crop lot commodity.

    Markets are ranked by net_revenue descending.
    Does NOT persist the recommendation (use /decisions/analyze/<id>/ for that).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # ── Validate input ────────────────────────────────────────────────────
        crop_lot_id = request.data.get("crop_lot_id")
        if crop_lot_id is None:
            return Response(
                {"error": "crop_lot_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            crop_lot_id = int(crop_lot_id)
        except (TypeError, ValueError):
            return Response(
                {"error": "crop_lot_id must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            forecast_days = int(request.data.get("forecast_days", 7))
            forecast_days = max(1, min(forecast_days, 90))
        except (TypeError, ValueError):
            forecast_days = 7

        # ── Run combined analysis ─────────────────────────────────────────────
        svc = CombinedAnalysisService()
        result = svc.run(
            crop_lot_id=crop_lot_id,
            user=request.user,
            forecast_days=forecast_days,
            save_forecasts=False,
        )

        # ── Permission / not-found check ──────────────────────────────────────
        if result.errors and not result.markets:
            first_error = result.errors[0]
            if "permission" in first_error.lower():
                return Response({"error": first_error}, status=status.HTTP_403_FORBIDDEN)
            if "not found" in first_error.lower():
                return Response({"error": first_error}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": first_error, "details": result.errors},
                            status=status.HTTP_400_BAD_REQUEST)

        # ── Serialise ─────────────────────────────────────────────────────────
        markets_out  = [asdict(m) for m in result.markets]
        best_out     = asdict(result.best_market) if result.best_market else None
        decision_out = asdict(result.decision) if result.decision else None

        return Response({
            "crop_lot_id":       result.crop_lot_id,
            "commodity":         result.commodity,
            "quantity_quintal":  round(result.quantity_quintal, 4),
            "farmer_location": {
                "lat": result.farmer_lat,
                "lon": result.farmer_lon,
            },
            "forecast_days":     forecast_days,
            "market_count":      len(result.markets),
            "best_market":       best_out,
            "markets":           markets_out,
            "ai_explanation":    result.ai_explanation,
            "decision":          decision_out,
            "skipped_markets":   result.skipped_markets,
            "warnings":          result.errors,
        }, status=status.HTTP_200_OK)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _persist_recommendation(crop_lot_id: int, result) -> int:
    """
    Save (or update) today's Recommendation record for this crop lot.

    Strategy: fetch any existing recommendation created today for this crop lot
    and update it; otherwise create a new one.  This keeps the operation
    idempotent when the endpoint is called multiple times in the same day.

    Returns the pk of the saved Recommendation.
    """
    from django.utils import timezone
    from apps.crops.models import CropLot
    from apps.markets.models import Market

    decision = result.decision
    best_mkt = result.best_market
    today    = timezone.now().date()

    crop_lot = CropLot.objects.get(pk=crop_lot_id)

    best_market_obj = None
    if best_mkt:
        try:
            best_market_obj = Market.objects.get(pk=best_mkt.market_id)
        except Market.DoesNotExist:
            pass

    # Try to find today's recommendation for this crop lot
    existing = (
        Recommendation.objects
        .filter(crop_lot=crop_lot, generated_at__date=today)
        .order_by("-generated_at")
        .first()
    )

    fields = {
        "best_market":               best_market_obj,
        "recommendation":            decision.recommendation,
        "current_net_value":         Decimal(str(decision.current_net_value)),
        "expected_future_net_value": Decimal(str(decision.expected_future_net_value)),
        "sell_quantity_suggestion":  (
            Decimal(str(decision.sell_now_quantity_quintal))
            if decision.sell_now_quantity_quintal is not None else None
        ),
        "confidence":                Decimal(str(decision.confidence)),
        "reasoning_factors":         decision.reasoning_factors,
        "rule_version":              decision.rule_version,
        "granite_explanation":       (
            result.ai_explanation.get("explanation")
            if isinstance(result.ai_explanation, dict)
            else (result.ai_explanation if isinstance(result.ai_explanation, str) else None)
        ),
    }

    if existing:
        for attr, val in fields.items():
            setattr(existing, attr, val)
        existing.save()
        return existing.pk

    rec = Recommendation.objects.create(crop_lot=crop_lot, **fields)
    return rec.pk
