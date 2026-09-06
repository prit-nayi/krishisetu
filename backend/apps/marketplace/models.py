"""
marketplace/models.py — CropListing and BuyerInquiry models for Farmer-Buyer marketplace.
"""
from django.db import models
from apps.accounts.models import User
from apps.crops.models import CropLot


class CropListing(models.Model):
    """
    Direct farmer crop listing visible to registered buyers across Gujarat.
    """

    class Status(models.TextChoices):
        ACTIVE       = "ACTIVE",       "Active"
        PENDING_DEAL = "PENDING_DEAL", "Pending Deal"
        SOLD         = "SOLD",         "Sold"
        DELISTED     = "DELISTED",     "Delisted"

    crop_lot = models.ForeignKey(
        CropLot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marketplace_listings",
        help_text="Optional link to farmer's registered crop lot",
    )
    farmer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="crop_listings",
        limit_choices_to={"role": "farmer"},
    )
    title = models.CharField(max_length=200, help_text="e.g. Shankar-6 Cotton Lot 50 Qtl")
    commodity = models.CharField(max_length=100, default="Cotton")
    quantity_quintal = models.DecimalField(max_digits=10, decimal_places=2)
    expected_price_per_quintal = models.DecimalField(max_digits=10, decimal_places=2)
    location_district = models.CharField(max_length=100)
    location_state = models.CharField(max_length=100, default="Gujarat")
    quality_grade = models.CharField(max_length=50, default="Grade A")
    harvest_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Crop Listing"
        verbose_name_plural = "Crop Listings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.quantity_quintal} Qtl @ ₹{self.expected_price_per_quintal}"


class BuyerInquiry(models.Model):
    """
    Purchase inquiry submitted by a buyer for a farmer's crop listing.
    """

    class Status(models.TextChoices):
        PENDING  = "PENDING",  "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        CLOSED   = "CLOSED",   "Closed"

    listing = models.ForeignKey(
        CropListing,
        on_delete=models.CASCADE,
        related_name="inquiries",
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="buyer_inquiries",
        limit_choices_to={"role": "buyer"},
    )
    offered_price_per_quintal = models.DecimalField(max_digits=10, decimal_places=2)
    requested_quantity_quintal = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True, default="")
    contact_phone = models.CharField(max_length=20, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    farmer_notes = models.TextField(blank=True, default="", help_text="Farmer's response note")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Buyer Inquiry"
        verbose_name_plural = "Buyer Inquiries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Inquiry #{self.pk} by {self.buyer.email} on {self.listing.title} ({self.status})"
