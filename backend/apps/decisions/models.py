"""
decisions/models.py — Recommendation model.
"""
from django.db import models
from apps.crops.models import CropLot
from apps.markets.models import Market


class Recommendation(models.Model):
    """SELL/HOLD/PARTIAL_SELL recommendation for a crop lot."""

    class Action(models.TextChoices):
        SELL_NOW     = "SELL_NOW",     "Sell Now"
        HOLD         = "HOLD",         "Hold"
        PARTIAL_SELL = "PARTIAL_SELL", "Partial Sell"

    crop_lot                  = models.ForeignKey(CropLot, on_delete=models.CASCADE, related_name="recommendations")
    best_market               = models.ForeignKey(Market, on_delete=models.SET_NULL, null=True, blank=True)
    recommendation            = models.CharField(max_length=20, choices=Action.choices)
    current_net_value         = models.DecimalField(max_digits=14, decimal_places=2)
    expected_future_net_value = models.DecimalField(max_digits=14, decimal_places=2)
    sell_quantity_suggestion  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    confidence                = models.DecimalField(max_digits=4, decimal_places=3, help_text="0.0 – 1.0")
    reasoning_factors         = models.JSONField(default=dict)
    rule_version              = models.CharField(max_length=50, default="1.0.0")
    generated_at              = models.DateTimeField(auto_now_add=True)
    granite_explanation       = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Recommendation"
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.crop_lot} → {self.recommendation}"
