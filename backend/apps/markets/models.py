"""
markets/models.py — Market and MarketPrice models.
"""
from django.db import models
from django.core.validators import MinValueValidator


class Market(models.Model):
    """Represents an APMC or private market/mandi."""

    class MarketType(models.TextChoices):
        APMC = "APMC", "APMC (Government)"
        PRIVATE = "private", "Private Market"

    name = models.CharField(max_length=200)
    district = models.CharField(max_length=100)
    taluka = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, default="Gujarat")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    market_type = models.CharField(
        max_length=20, choices=MarketType.choices, default=MarketType.APMC
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Market"
        verbose_name_plural = "Markets"
        ordering = ["district", "name"]
        unique_together = [("name", "district", "state")]

    def __str__(self):
        return f"{self.name}, {self.district} ({self.market_type})"


class MarketPrice(models.Model):
    """Stores daily price records for a commodity at a market."""

    class Commodity(models.TextChoices):
        COTTON = "cotton", "Cotton"
        GROUNDNUT = "groundnut", "Groundnut"

    class Source(models.TextChoices):
        AGMARKNET = "agmarknet", "Agmarknet"
        MANUAL = "manual", "Manual Entry"
        MOCK = "mock", "Mock / Demo Data"

    market = models.ForeignKey(
        Market, on_delete=models.CASCADE, related_name="prices"
    )
    commodity = models.CharField(max_length=20, choices=Commodity.choices)
    variety = models.CharField(max_length=100, blank=True, null=True)
    min_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Minimum price (Rs/quintal)",
    )
    max_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Maximum price (Rs/quintal)",
    )
    modal_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Modal (most common) price (Rs/quintal)",
    )
    arrival_quantity = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Arrival quantity (quintals)",
    )
    price_date = models.DateField(help_text="Date of the price record")
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.MOCK
    )
    source_timestamp = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Market Price"
        verbose_name_plural = "Market Prices"
        ordering = ["-price_date"]
        indexes = [
            models.Index(fields=["commodity", "market", "price_date"]),
            models.Index(fields=["price_date"]),
        ]

    def __str__(self):
        return (
            f"{self.market.name} — {self.commodity} "
            f"@ ₹{self.modal_price}/q on {self.price_date}"
        )

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.min_price > self.modal_price:
            raise ValidationError(
                "min_price cannot be greater than modal_price."
            )
        if self.modal_price > self.max_price:
            raise ValidationError(
                "modal_price cannot be greater than max_price."
            )
