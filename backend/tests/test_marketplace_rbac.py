"""
tests/test_marketplace_rbac.py — Tests for multi-role accounts, RBAC permissions, and marketplace workflows.
"""
import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User, FarmerProfile, BuyerProfile
from apps.crops.models import CropLot
from apps.marketplace.models import CropListing, BuyerInquiry


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def farmer_user(db):
    user = User.objects.create_user(
        username="farmer_test",
        email="farmer_test@krishilink.in",
        password="ValidPassword123!",
        role="farmer",
        phone="9876543210",
    )
    FarmerProfile.objects.create(
        user=user,
        district="Rajkot",
        taluka="Gondal",
        village="Gondal",
        latitude=Decimal("21.9619"),
        longitude=Decimal("70.7937"),
    )
    return user


@pytest.fixture
def buyer_user(db):
    user = User.objects.create_user(
        username="buyer_test",
        email="buyer_test@krishilink.in",
        password="ValidPassword123!",
        role="buyer",
        phone="9876543211",
    )
    BuyerProfile.objects.create(
        user=user,
        company_name="Gujarat Agro Traders",
        business_type="Wholesaler",
        district="Rajkot",
        state="Gujarat",
        phone="9876543211",
        is_verified=True,
    )
    return user


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin_test",
        email="admin_test@krishilink.in",
        password="ValidPassword123!",
        role="admin",
    )


@pytest.fixture
def crop_listing(farmer_user):
    crop_lot = CropLot.objects.create(
        farmer=farmer_user.farmer_profile,
        commodity="cotton",
        quantity=Decimal("50.00"),
        unit="quintal",
        harvest_date="2026-09-01",
    )
    return CropListing.objects.create(
        crop_lot=crop_lot,
        farmer=farmer_user,
        title="High Grade Shankar-6 Cotton",
        commodity="Cotton",
        quantity_quintal=Decimal("50.00"),
        expected_price_per_quintal=Decimal("7200.00"),
        location_district="Rajkot",
        location_state="Gujarat",
        quality_grade="Grade A",
        status=CropListing.Status.ACTIVE,
        is_active=True,
    )


# ── 1. Auth & Registration Multi-Role Tests ───────────────────────────────────

@pytest.mark.django_db
class TestMultiRoleAuth:
    def test_register_farmer(self, api_client):
        payload = {
            "email": "new_farmer@krishilink.in",
            "username": "new_farmer",
            "phone": "9998887771",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "role": "farmer",
        }
        res = api_client.post("/api/v1/auth/register/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email="new_farmer@krishilink.in")
        assert user.role == "farmer"
        assert hasattr(user, "farmer_profile")

    def test_register_buyer(self, api_client):
        payload = {
            "email": "new_buyer@krishilink.in",
            "username": "new_buyer",
            "phone": "9998887772",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "role": "buyer",
        }
        res = api_client.post("/api/v1/auth/register/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email="new_buyer@krishilink.in")
        assert user.role == "buyer"
        assert hasattr(user, "buyer_profile")

    def test_me_returns_profile_data(self, api_client, buyer_user):
        api_client.force_authenticate(user=buyer_user)
        res = api_client.get("/api/v1/auth/me/")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["role"] == "buyer"
        assert data["buyer_profile"]["company_name"] == "Gujarat Agro Traders"

    def test_buyer_profile_update(self, api_client, buyer_user):
        api_client.force_authenticate(user=buyer_user)
        res = api_client.patch("/api/v1/buyer/profile/", {"company_name": "Updated Agro Ltd"}, format="json")
        assert res.status_code == status.HTTP_200_OK
        buyer_user.buyer_profile.refresh_from_db()
        assert buyer_user.buyer_profile.company_name == "Updated Agro Ltd"


# ── 2. Marketplace Listings Tests ─────────────────────────────────────────────

@pytest.mark.django_db
class TestMarketplaceListings:
    def test_list_active_listings(self, api_client, farmer_user, crop_listing):
        api_client.force_authenticate(user=farmer_user)
        res = api_client.get("/api/v1/marketplace/listings/")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        results = data.get("results", data)
        assert len(results) >= 1
        assert results[0]["title"] == "High Grade Shankar-6 Cotton"
        assert results[0]["expected_price_per_quintal"] == "7200.00"

    def test_farmer_create_listing(self, api_client, farmer_user):
        api_client.force_authenticate(user=farmer_user)
        payload = {
            "title": "Fresh Groundnut Lot",
            "commodity": "Groundnut",
            "quantity_quintal": "80.00",
            "expected_price_per_quintal": "6500.00",
            "location_district": "Junagadh",
            "location_state": "Gujarat",
            "quality_grade": "Grade A",
        }
        res = api_client.post("/api/v1/marketplace/listings/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        listing = CropListing.objects.get(title="Fresh Groundnut Lot")
        assert listing.farmer == farmer_user
        assert listing.status == CropListing.Status.ACTIVE

    def test_buyer_cannot_create_crop_listing(self, api_client, buyer_user):
        api_client.force_authenticate(user=buyer_user)
        payload = {
            "title": "Unauthorized Listing",
            "commodity": "Cotton",
            "quantity_quintal": "20.00",
            "expected_price_per_quintal": "7000.00",
            "location_district": "Rajkot",
        }
        res = api_client.post("/api/v1/marketplace/listings/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_farmer_my_listings(self, api_client, farmer_user, crop_listing):
        api_client.force_authenticate(user=farmer_user)
        res = api_client.get("/api/v1/marketplace/listings/my_listings/")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        results = data.get("results", data)
        assert len(results) >= 1
        assert results[0]["id"] == crop_listing.id


# ── 3. Marketplace Buyer Inquiry Flow Tests ───────────────────────────────────

@pytest.mark.django_db
class TestMarketplaceInquiries:
    def test_buyer_create_inquiry(self, api_client, buyer_user, crop_listing):
        api_client.force_authenticate(user=buyer_user)
        payload = {
            "listing": crop_listing.id,
            "offered_price_per_quintal": "7150.00",
            "requested_quantity_quintal": "50.00",
            "message": "Ready for prompt payment and pickup.",
            "contact_phone": "9876543211",
        }
        res = api_client.post("/api/v1/marketplace/inquiries/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        inquiry = BuyerInquiry.objects.get(listing=crop_listing)
        assert inquiry.buyer == buyer_user
        assert inquiry.status == BuyerInquiry.Status.PENDING

    def test_farmer_accepts_inquiry(self, api_client, farmer_user, buyer_user, crop_listing):
        inquiry = BuyerInquiry.objects.create(
            listing=crop_listing,
            buyer=buyer_user,
            offered_price_per_quintal=Decimal("7150.00"),
            requested_quantity_quintal=Decimal("50.00"),
            message="Interested in full lot.",
        )
        api_client.force_authenticate(user=farmer_user)
        res = api_client.post(
            f"/api/v1/marketplace/inquiries/{inquiry.id}/respond/",
            {"status": "ACCEPTED", "farmer_notes": "Deal agreed. Pickup on Monday."},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        inquiry.refresh_from_db()
        crop_listing.refresh_from_db()
        assert inquiry.status == BuyerInquiry.Status.ACCEPTED
        assert crop_listing.status == CropListing.Status.PENDING_DEAL

    def test_other_farmer_cannot_respond_to_inquiry(self, api_client, buyer_user, crop_listing):
        other_farmer = User.objects.create_user(
            username="other_farmer",
            email="other_farmer@krishilink.in",
            password="ValidPassword123!",
            role="farmer",
        )
        inquiry = BuyerInquiry.objects.create(
            listing=crop_listing,
            buyer=buyer_user,
            offered_price_per_quintal=Decimal("7150.00"),
            requested_quantity_quintal=Decimal("50.00"),
        )
        api_client.force_authenticate(user=other_farmer)
        res = api_client.post(
            f"/api/v1/marketplace/inquiries/{inquiry.id}/respond/",
            {"status": "ACCEPTED"},
            format="json",
        )
        assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

    def test_marketplace_stats_endpoint(self, api_client, crop_listing):
        res = api_client.get("/api/v1/marketplace/stats/")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["total_active_listings"] >= 1
        assert "average_prices" in data
