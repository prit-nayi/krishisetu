"""
crops/admin.py
"""
from django.contrib import admin

from .models import CropLot


@admin.register(CropLot)
class CropLotAdmin(admin.ModelAdmin):
    list_display = ("farmer", "commodity", "quantity", "unit", "quality_grade", "is_active", "created_at")
    list_filter = ("commodity", "quality_grade", "storage_status", "is_active")
    search_fields = ("farmer__user__email", "farmer__village")
    ordering = ("-created_at",)
