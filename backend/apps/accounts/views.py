"""
accounts/views.py — Auth and FarmerProfile views.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User, FarmerProfile, BuyerProfile
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    FarmerProfileSerializer,
    FarmerProfileCreateSerializer,
    BuyerProfileSerializer,
    BuyerProfileCreateSerializer,
)
from apps.common.permissions import IsAdminUser


class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ — create a new user (farmer or buyer)."""

    serializer_class   = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"message": "Registration successful.", "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """POST /api/v1/auth/login/ — obtain JWT pair."""
    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    """GET /api/v1/auth/me/ — return the authenticated user's info."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class FarmerProfileView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/farmer/profile/ — retrieve or update own farmer profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return FarmerProfileCreateSerializer
        return FarmerProfileSerializer

    def get_object(self):
        profile, _ = FarmerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"district": "", "village": ""},
        )
        return profile

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class BuyerProfileView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/buyer/profile/ — retrieve or update own buyer profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return BuyerProfileCreateSerializer
        return BuyerProfileSerializer

    def get_object(self):
        profile, _ = BuyerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"company_name": "", "district": ""},
        )
        return profile

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class AdminUserListView(generics.ListAPIView):
    """GET /api/v1/admin/users/ — list all registered users (Admin only)."""

    permission_classes = [IsAdminUser]
    serializer_class   = UserSerializer
    queryset           = User.objects.all().order_by("-date_joined")

