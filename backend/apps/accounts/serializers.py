"""
accounts/serializers.py — User registration, login, and FarmerProfile serializers.
"""
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, FarmerProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for new farmer registration."""

    password         = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model  = User
        fields = ("email", "username", "phone", "password", "password_confirm", "role")
        extra_kwargs = {"role": {"default": User.Role.FARMER}}

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password": "Password fields did not match."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Read-only user info serializer."""

    class Meta:
        model  = User
        fields = ("id", "email", "username", "phone", "role", "date_joined")
        read_only_fields = fields


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT token serializer — adds user role and email to token payload."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"]  = user.role
        token["email"] = user.email
        return token


class FarmerProfileSerializer(serializers.ModelSerializer):
    """Serializer for FarmerProfile reads (includes nested user)."""

    user = UserSerializer(read_only=True)

    class Meta:
        model  = FarmerProfile
        fields = ("id", "user", "district", "taluka", "village", "latitude", "longitude", "pincode", "created_at", "updated_at")
        read_only_fields = ("id", "user", "created_at", "updated_at")


class FarmerProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating a farmer profile."""

    class Meta:
        model  = FarmerProfile
        fields = ("district", "taluka", "village", "latitude", "longitude", "pincode")
