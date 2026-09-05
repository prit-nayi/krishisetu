"""
accounts/admin.py
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, FarmerProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ("email", "username", "role", "is_active", "date_joined")
    list_filter   = ("role", "is_active", "is_staff")
    search_fields = ("email", "username")
    ordering      = ("-date_joined",)
    fieldsets     = BaseUserAdmin.fieldsets + (
        ("KrishiLink", {"fields": ("role", "phone")}),
    )


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display  = ("user", "district", "village", "created_at")
    search_fields = ("user__email", "district", "village")
