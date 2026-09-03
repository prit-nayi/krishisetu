"""
forecasting/models.py — Forecast storage model.
"""
from django.db import models
from django.core.validators import MinValueValidator

from apps.markets.models import Market


class Forecast(models.Model):
    """Stores a price forecast for a commodity at a market."""

    class Commodity(models.TextChoices):
        COTTON = "cotton", "Cotton"
        GROUNDNUT = "groundnut", "Groundnut"

    commodity = models.CharField(max_length=20, choices=Commodity.choices)
    market = models.ForeignKey(
        Market, on_delete=models.SET_NULL, null=True, blank=True, related_name="forecasts"
    )
    forecast_date = models.DateField(help_text="Date for which the price is predicted")
    predicted_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Predicted modal price (Rs/quintal)",
    )
    lower_bound = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True, blank=True,
    )
    upper_bound = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True, blank=True,
    )
    confidence_score = models.FloatField(
        null=True, blank=True,
        help_text="Confidence score 0–1",
    )
    model_name = models.CharField(max_length=100, default="linear_trend")
    model_version = models.CharField(max_length=50, default="1.0")
    horizon_days = models.IntegerField(default=14)
    generated_at = models.DateTimeField(auto_now_add=True)
    is_mock = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Forecast"
        verbose_name_plural = "Forecasts"
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["commodity", "market", "forecast_date"]),
        ]

    def __str__(self):
        market_name = self.market.name if self.market else "State-wide"
        return (
            f"{self.commodity} @ {market_name} → "
            f"₹{self.predicted_price} on {self.forecast_date}"
        )
