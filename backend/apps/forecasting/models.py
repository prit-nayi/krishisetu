"""
forecasting/models.py — Forecast model.
"""
from django.db import models
from apps.markets.models import Market


class Forecast(models.Model):
    """ML price forecast for a commodity at a market."""

    commodity       = models.CharField(max_length=50)
    market          = models.ForeignKey(Market, on_delete=models.SET_NULL, null=True, blank=True, related_name="forecasts")
    forecast_date   = models.DateField()
    predicted_price = models.DecimalField(max_digits=10, decimal_places=2)
    lower_bound     = models.DecimalField(max_digits=10, decimal_places=2)
    upper_bound     = models.DecimalField(max_digits=10, decimal_places=2)
    confidence_score = models.DecimalField(max_digits=4, decimal_places=3, help_text="0.0 – 1.0")
    model_name      = models.CharField(max_length=100)
    model_version   = models.CharField(max_length=50)
    horizon_days    = models.IntegerField(default=14)
    generated_at    = models.DateTimeField(auto_now_add=True)
    is_mock         = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Forecast"
        verbose_name_plural = "Forecasts"
        ordering = ["-forecast_date"]

    def __str__(self):
        return f"{self.commodity} forecast for {self.forecast_date} (model: {self.model_name})"
