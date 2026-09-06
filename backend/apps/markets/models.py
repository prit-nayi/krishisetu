"""
markets/models.py — Market and MarketPrice models.
"""
from django.db import models


class Market(models.Model):
    """Represents an APMC or private market."""

    class MarketType(models.TextChoices):
        APMC    = "APMC",    "APMC"
        PRIVATE = "private", "Private"

    class Source(models.TextChoices):
        APMC_DIRECTORY = "apmc_directory", "APMC Directory (Scraped)"
        DATA_GOV       = "data_gov",       "data.gov.in"
        MANUAL         = "manual",         "Manual"

    name        = models.CharField(max_length=200)
    district    = models.CharField(max_length=100)
    taluka      = models.CharField(max_length=100, blank=True, null=True)
    latitude    = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude   = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    market_type = models.CharField(max_length=20, choices=MarketType.choices, default=MarketType.APMC)
    state       = models.CharField(max_length=50, default="Gujarat")
    source      = models.CharField(
        max_length=30,
        choices=Source.choices,
        default=Source.APMC_DIRECTORY,
        help_text="How this market record was populated.",
    )
    source_url  = models.URLField(blank=True, null=True, help_text="Source page URL if available.")
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
        AGMARKNET = "agmarknet", "Agmarknet / data.gov.in"
        MANUAL    = "manual",    "Manual"
        MOCK      = "mock",      "Mock/Demo"

    market           = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="prices")
    commodity        = models.CharField(max_length=50)
    variety          = models.CharField(max_length=100, blank=True, default="")
    grade            = models.CharField(max_length=100, blank=True, default="",
                                        help_text="Grade as reported by the source (e.g. FAQ, Bold).")
    min_price        = models.DecimalField(max_digits=10, decimal_places=2)
    max_price        = models.DecimalField(max_digits=10, decimal_places=2)
    modal_price      = models.DecimalField(max_digits=10, decimal_places=2)
    arrival_quantity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_date       = models.DateField()
    source           = models.CharField(max_length=20, choices=Source.choices, default=Source.MOCK)
    source_timestamp = models.DateTimeField(null=True, blank=True,
                                            help_text="When this record was retrieved from the source.")
    is_verified      = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Market Price"
        verbose_name_plural = "Market Prices"
        ordering = ["-price_date"]
        # Include variety so that the same market/commodity/date can have
        # multiple variety-level records without collision.
        unique_together = [("market", "commodity", "variety", "price_date")]

    def __str__(self):
        return f"{self.market.name} — {self.commodity} — {self.price_date}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValidationError("min_price must be <= max_price.")
        if self.modal_price is not None and self.min_price is not None:
            if self.modal_price < self.min_price:
                raise ValidationError("modal_price must be >= min_price.")
        if self.modal_price is not None and self.max_price is not None:
            if self.modal_price > self.max_price:
                raise ValidationError("modal_price must be <= max_price.")
