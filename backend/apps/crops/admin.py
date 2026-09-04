from django.contrib import admin
from .models import CropLot

@admin.register(CropLot)
class CropLotAdmin(admin.ModelAdmin):
    list_display  = ("farmer", "commodity", "quantity", "unit", "storage_status", "is_active", "created_at")
    list_filter   = ("commodity", "storage_status", "is_active")
    search_fields = ("farmer__user__email",)
