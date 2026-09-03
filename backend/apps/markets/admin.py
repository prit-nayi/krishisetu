from django.contrib import admin
from .models import Market, MarketPrice


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "market_type", "is_active")
    list_filter = ("district", "market_type", "is_active")
    search_fields = ("name", "district")


@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    list_display = ("market", "commodity", "modal_price", "price_date", "source", "is_verified")
    list_filter = ("commodity", "source", "is_verified", "price_date")
    search_fields = ("market__name", "market__district")
    ordering = ("-price_date",)
