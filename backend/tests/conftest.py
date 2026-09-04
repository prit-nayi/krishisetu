"""
tests/conftest.py — Shared pytest fixtures for Phase 1+ integration tests.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.accounts.models import FarmerProfile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(farmer_user, tokens):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    return client


@pytest.fixture
def farmer_user(db):
    return User.objects.create_user(
        email="farmer@krishilink.test",
        username="testfarmer",
        password="StrongPass123!",
        role="farmer",
    )


@pytest.fixture
def farmer_user_2(db):
    return User.objects.create_user(
        email="farmer2@krishilink.test",
        username="testfarmer2",
        password="StrongPass123!",
        role="farmer",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@krishilink.test",
        username="testadmin",
        password="StrongPass123!",
        role="admin",
        is_staff=True,
    )


@pytest.fixture
def tokens(api_client, farmer_user):
    response = api_client.post(
        "/api/v1/auth/login/",
        {"email": "farmer@krishilink.test", "password": "StrongPass123!"},
        format="json",
    )
    assert response.status_code == 200, f"Login failed in fixture: {response.data}"
    return {"access": response.data["access"], "refresh": response.data["refresh"]}


@pytest.fixture
def farmer_profile(farmer_user):
    return FarmerProfile.objects.create(
        user=farmer_user,
        district="Rajkot",
        taluka="Gondal",
        village="Gondal",
        latitude="22.1631",
        longitude="70.7934",
        pincode="360311",
    )


@pytest.fixture
def farmer_profile_2(farmer_user_2):
    return FarmerProfile.objects.create(
        user=farmer_user_2,
        district="Amreli",
        taluka="Amreli",
        village="Amreli",
        latitude="21.6010",
        longitude="71.2214",
        pincode="365601",
    )
