"""
crops/models.py — CropLot model.
"""
from django.db import models
from apps.accounts.models import FarmerProfile


class CropLot(models.Model):
    """Represents a batch of crop a farmer wants to sell."""

    class Commodity(models.TextChoices):
        COTTON    = "cotton",    "Cotton"
        GROUNDNUT = "groundnut", "Groundnut"

    class Unit(models.TextChoices):
        QUINTAL = "quintal", "Quintal"
        KG      = "kg",      "Kilogram"
        TONNE   = "tonne",   "Tonne"

    class QualityGrade(models.TextChoices):
        A = "A", "Grade A (Premium)"
        B = "B", "Grade B (Standard)"
        C = "C", "Grade C (Below Standard)"

    class StorageStatus(models.TextChoices):
        FARM         = "farm",         "At Farm"
        WAREHOUSE    = "warehouse",    "In Warehouse"
        COLD_STORAGE = "cold_storage", "Cold Storage"

    farmer   = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name="crop_lots")
    commodity     = models.CharField(max_length=20,  choices=Commodity.choices)
    variety       = models.CharField(max_length=100, blank=True, null=True)
    quantity      = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quantity in the specified unit")
    unit          = models.CharField(max_length=10, choices=Unit.choices, default=Unit.QUINTAL)
    moisture_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    quality_grade = models.CharField(max_length=5, choices=QualityGrade.choices, null=True, blank=True)
    harvest_date  = models.DateField()
    storage_status     = models.CharField(max_length=20, choices=StorageStatus.choices, default=StorageStatus.FARM)
    storage_start_date = models.DateField(null=True, blank=True)
    notes     = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Crop Lot"
        verbose_name_plural = "Crop Lots"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.farmer.user.email} — {self.get_commodity_display()} {self.quantity}{self.unit}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.moisture_percent is not None and not (0 <= self.moisture_percent <= 100):
            raise ValidationError({"moisture_percent": "Moisture percent must be between 0 and 100."})
