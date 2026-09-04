"""
markets/models.py — Market and MarketPrice models.
"""
from django.db import models


class Market(models.Model):
    """Represents an APMC or private market."""

    class MarketType(models.TextChoices):
        APMC    = "APMC",    "APMC"
        PRIVATE = "private", "Private"

    name        = models.CharField(max_length=200)
    district    = models.CharField(max_length=100)
    taluka      = models.CharField(max_length=100, blank=True, null=True)
    latitude    = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude   = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    market_type = models.CharField(max_length=20, choices=MarketType.choices, default=MarketType.APMC)
    state       = models.CharField(max_length=50, default="Gujarat")
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Market"
        verbose_name_plural = "Markets"
        ordering = ["district", "name"]

    def __str__(self):
        return f"{self.name} ({self.district})"


class MarketPrice(models.Model):
    """Daily price record for a commodity at a market."""

    class Source(models.TextChoices):
        AGMARKNET = "agmarknet", "Agmarknet"
        MANUAL    = "manual",    "Manual"
        MOCK      = "mock",      "Mock/Demo"

    market           = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="prices")
    commodity        = models.CharField(max_length=50)
    variety          = models.CharField(max_length=100, blank=True, null=True)
    min_price        = models.DecimalField(max_digits=10, decimal_places=2)
    max_price        = models.DecimalField(max_digits=10, decimal_places=2)
    modal_price      = models.DecimalField(max_digits=10, decimal_places=2)
    arrival_quantity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_date       = models.DateField()
    source           = models.CharField(max_length=20, choices=Source.choices, default=Source.MOCK)
    source_timestamp = models.DateTimeField(null=True, blank=True)
    is_verified      = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Market Price"
        verbose_name_plural = "Market Prices"
        ordering = ["-price_date"]
        unique_together = [("market", "commodity", "price_date")]

    def __str__(self):
        return f"{self.market.name} — {self.commodity} — {self.price_date}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.min_price > self.modal_price or self.modal_price > self.max_price:
            raise ValidationError("min_price <= modal_price <= max_price must hold.")
