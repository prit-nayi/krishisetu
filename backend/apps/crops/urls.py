"""
crops/urls.py
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CropLotViewSet

router = DefaultRouter()
router.register(r"lots", CropLotViewSet, basename="crop-lot")

urlpatterns = [
    path("", include(router.urls)),
]
