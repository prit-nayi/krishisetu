"""
accounts/serializers.py — User registration, login, and FarmerProfile serializers.
"""
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, FarmerProfile, BuyerProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration across roles (Farmer, Buyer)."""

    password         = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    role             = serializers.ChoiceField(choices=User.Role.choices, default=User.Role.FARMER)

    class Meta:
        model  = User
        fields = ("email", "username", "phone", "password", "password_confirm", "role")

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password": "Password fields did not match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        # Create corresponding profile shell
        if user.role == User.Role.BUYER:
            BuyerProfile.objects.create(user=user)
        elif user.role == User.Role.FARMER:
            FarmerProfile.objects.create(user=user, district="", village="")
        return user


class UserSerializer(serializers.ModelSerializer):
    """Read-only user info serializer with profile summary."""

    farmer_profile = serializers.SerializerMethodField()
    buyer_profile  = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ("id", "email", "username", "phone", "role", "date_joined", "farmer_profile", "buyer_profile")
        read_only_fields = fields

    def get_farmer_profile(self, obj):
        if hasattr(obj, "farmer_profile"):
            fp = obj.farmer_profile
            return {
                "id": fp.id,
                "district": fp.district,
                "taluka": fp.taluka,
                "village": fp.village,
                "latitude": float(fp.latitude) if fp.latitude else None,
                "longitude": float(fp.longitude) if fp.longitude else None,
                "pincode": fp.pincode,
            }
        return None

    def get_buyer_profile(self, obj):
        if hasattr(obj, "buyer_profile"):
            bp = obj.buyer_profile
            return {
                "id": bp.id,
                "company_name": bp.company_name,
                "business_type": bp.business_type,
                "district": bp.district,
                "state": bp.state,
                "phone": bp.phone,
                "is_verified": bp.is_verified,
            }
        return None


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


class BuyerProfileSerializer(serializers.ModelSerializer):
    """Serializer for BuyerProfile reads."""

    user = UserSerializer(read_only=True)

    class Meta:
        model  = BuyerProfile
        fields = ("id", "user", "company_name", "business_type", "district", "state", "phone", "gst_number", "is_verified", "created_at", "updated_at")
        read_only_fields = ("id", "user", "is_verified", "created_at", "updated_at")


class BuyerProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for updating a buyer profile."""

    class Meta:
        model  = BuyerProfile
        fields = ("company_name", "business_type", "district", "state", "phone", "gst_number")

