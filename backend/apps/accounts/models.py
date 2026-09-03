"""
accounts/models.py — Custom User and FarmerProfile models.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended User model with role-based access control."""

    class Role(models.TextChoices):
        FARMER = "farmer", "Farmer"
        ADMIN = "admin", "Admin"
        BUYER = "buyer", "Buyer"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.FARMER,
    )
    phone = models.CharField(max_length=15, blank=True, null=True, unique=True)
    email = models.EmailField(unique=True)

    # Use email as login field
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_farmer(self):
        return self.role == self.Role.FARMER

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN


class FarmerProfile(models.Model):
    """Extended profile for farmer users with location data."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="farmer_profile",
    )
    district = models.CharField(max_length=100)
    taluka = models.CharField(max_length=100, blank=True, null=True)
    village = models.CharField(max_length=100)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    pincode = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Farmer Profile"
        verbose_name_plural = "Farmer Profiles"

    def __str__(self):
        return f"{self.user.email} — {self.village}, {self.district}"
