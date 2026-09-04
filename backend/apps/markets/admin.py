from django.contrib import admin
from .models import Market, MarketPrice

@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display  = ("name", "district", "market_type", "is_active")
    search_fields = ("name", "district")

@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    list_display  = ("market", "commodity", "modal_price", "price_date", "source")
    list_filter   = ("commodity", "source")
    search_fields = ("market__name",)
