"""
accounts/urls/farmer_urls.py — Farmer profile endpoints.
"""
from django.urls import path

from apps.accounts.views import FarmerProfileView

urlpatterns = [
    path("profile/", FarmerProfileView.as_view(), name="farmer-profile"),
]
