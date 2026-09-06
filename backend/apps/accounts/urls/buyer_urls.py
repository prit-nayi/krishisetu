"""
accounts/urls/buyer_urls.py — Buyer profile endpoints.
"""
from django.urls import path
from apps.accounts.views import BuyerProfileView

urlpatterns = [
    path("profile/", BuyerProfileView.as_view(), name="buyer-profile"),
]
