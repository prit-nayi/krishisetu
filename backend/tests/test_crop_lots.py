"""
tests/test_crop_lots.py — Phase 2 CropLot Integration Tests.

Covers:
  - Unauthenticated access (401)
  - List own lots
  - Create a lot (valid + invalid data)
  - Retrieve a single lot
  - Partial update (PATCH)
  - Full update (PUT)
  - Soft-delete (DELETE → is_active=False)
  - Ownership enforcement (farmer cannot see/modify another farmer's lots)
  - Commodity validation (only cotton / groundnut)
  - Quantity validation (must be > 0)
  - Moisture validation (0–100)
"""
import pytest
from rest_framework import status
from apps.crops.models import CropLot
import datetime


LIST_URL   = "/api/v1/crops/lots/"
DETAIL_URL = lambda pk: f"/api/v1/crops/lots/{pk}/"


# ── Helpers ────────────────────────────────────────────────────────────────────

def valid_payload(**overrides):
    base = {
        "commodity":    "groundnut",
        "quantity":     "40.00",
        "unit":         "quintal",
        "harvest_date": str(datetime.date.today()),
        "storage_status": "farm",
    }
    base.update(overrides)
    return base


def create_lot(auth_client, **overrides):
    """Helper: create a lot and assert success."""
    resp = auth_client.post(LIST_URL, valid_payload(**overrides), format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    return resp.data


# ══════════════════════════════════════════════════════════════════════════════
# 1. Authentication
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCropLotAuth:

    def test_list_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(LIST_URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_unauthenticated_returns_401(self, api_client):
        resp = api_client.post(LIST_URL, valid_payload(), format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_detail_unauthenticated_returns_401(self, api_client, auth_client, farmer_profile):
        lot = create_lot(auth_client)
        resp = api_client.get(DETAIL_URL(lot["id"]))
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_unauthenticated_returns_401(self, api_client, auth_client, farmer_profile):
        lot = create_lot(auth_client)
        resp = api_client.delete(DETAIL_URL(lot["id"]))
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ══════════════════════════════════════════════════════════════════════════════
# 2. List
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCropLotList:

    def test_list_empty_for_new_farmer(self, auth_client, farmer_profile):
        resp = auth_client.get(LIST_URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["results"] == []

    def test_list_returns_own_lots_only(self, auth_client, farmer_profile):
        create_lot(auth_client, commodity="cotton")
        create_lot(auth_client, commodity="groundnut")
        resp = auth_client.get(LIST_URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 2

    def test_list_excludes_deleted_lots(self, auth_client, farmer_profile):
        lot = create_lot(auth_client)
        auth_client.delete(DETAIL_URL(lot["id"]))
        resp = auth_client.get(LIST_URL)
        assert resp.data["count"] == 0

    def test_list_response_shape(self, auth_client, farmer_profile):
        create_lot(auth_client)
        resp = auth_client.get(LIST_URL)
        item = resp.data["results"][0]
        required_keys = {"id", "commodity", "commodity_display", "quantity",
                         "unit", "harvest_date", "storage_status", "is_active",
                         "created_at", "updated_at"}
        assert required_keys.issubset(set(item.keys()))


# ══════════════════════════════════════════════════════════════════════════════
# 3. Create
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCropLotCreate:

    def test_create_cotton_lot(self, auth_client, farmer_profile):
        resp = auth_client.post(LIST_URL, valid_payload(commodity="cotton"), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["commodity"] == "cotton"

    def test_create_groundnut_lot(self, auth_client, farmer_profile):
        resp = auth_client.post(LIST_URL, valid_payload(commodity="groundnut"), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["commodity"] == "groundnut"

    def test_create_saves_to_db(self, auth_client, farmer_profile):
        create_lot(auth_client)
        assert CropLot.objects.filter(farmer=farmer_profile).count() == 1

    def test_create_with_optional_fields(self, auth_client, farmer_profile):
        payload = valid_payload(
            variety="Bold",
            moisture_percent="8.50",
            quality_grade="A",
            notes="Premium lot",
        )
        resp = auth_client.post(LIST_URL, payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_create_invalid_commodity_returns_400(self, auth_client, farmer_profile):
        resp = auth_client.post(
            LIST_URL, valid_payload(commodity="wheat"), format="json"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_zero_quantity_returns_400(self, auth_client, farmer_profile):
        resp = auth_client.post(
            LIST_URL, valid_payload(quantity="0"), format="json"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_negative_quantity_returns_400(self, auth_client, farmer_profile):
        resp = auth_client.post(
            LIST_URL, valid_payload(quantity="-5"), format="json"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_invalid_moisture_over_100_returns_400(self, auth_client, farmer_profile):
        resp = auth_client.post(
            LIST_URL, valid_payload(moisture_percent="101"), format="json"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_missing_commodity_returns_400(self, auth_client, farmer_profile):
        payload = valid_payload()
        del payload["commodity"]
        resp = auth_client.post(LIST_URL, payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_missing_quantity_returns_400(self, auth_client, farmer_profile):
        payload = valid_payload()
        del payload["quantity"]
        resp = auth_client.post(LIST_URL, payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_missing_harvest_date_returns_400(self, auth_client, farmer_profile):
        payload = valid_payload()
        del payload["harvest_date"]
        resp = auth_client.post(LIST_URL, payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_invalid_unit_returns_400(self, auth_client, farmer_profile):
        resp = auth_client.post(
            LIST_URL, valid_payload(unit="sack"), format="json"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ══════════════════════════════════════════════════════════════════════════════
# 4. Retrieve
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCropLotRetrieve:

    def test_retrieve_own_lot(self, auth_client, farmer_profile):
        lot = create_lot(auth_client, commodity="cotton")
        resp = auth_client.get(DETAIL_URL(lot["id"]))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["id"] == lot["id"]
        assert resp.data["commodity"] == "cotton"

    def test_retrieve_includes_display_fields(self, auth_client, farmer_profile):
        lot = create_lot(auth_client)
        resp = auth_client.get(DETAIL_URL(lot["id"]))
        assert resp.data["commodity_display"] == "Groundnut"
        assert "unit_display" in resp.data

    def test_retrieve_nonexistent_returns_404(self, auth_client, farmer_profile):
        resp = auth_client.get(DETAIL_URL(99999))
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ══════════════════════════════════════════════════════════════════════════════
# 5. Update (PATCH + PUT)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCropLotUpdate:

    def test_patch_quantity(self, auth_client, farmer_profile):
        lot = create_lot(auth_client)
        resp = auth_client.patch(
            DETAIL_URL(lot["id"]), {"quantity": "55.00"}, format="json"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["quantity"] == "55.00"

    def test_patch_notes(self, auth_client, farmer_profile):
        lot = create_lot(auth_client)
        resp = auth_client.patch(
            DETAIL_URL(lot["id"]), {"notes": "Ready to sell"}, format="json"
        )
        assert resp.status_code == status.HTTP_200_OK

    def test_patch_storage_status(self, auth_client, farmer_profile):
        lot = create_lot(auth_client)
        resp = auth_client.patch(
            DETAIL_URL(lot["id"]),
            {"storage_status": "warehouse"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["storage_status"] == "warehouse"

    def test_patch_invalid_quantity_returns_400(self, auth_client, farmer_profile):
        lot = create_lot(auth_client)
        resp = auth_client.patch(
            DETAIL_URL(lot["id"]), {"quantity": "0"}, format="json"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_full_update(self, auth_client, farmer_profile):
        lot = create_lot(auth_client)
        full_payload = valid_payload(
            commodity="cotton",
            quantity="100.00",
            unit="quintal",
            storage_status="warehouse",
        )
        resp = auth_client.put(DETAIL_URL(lot["id"]), full_payload, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["commodity"] == "cotton"
        assert resp.data["quantity"] == "100.00"


# ══════════════════════════════════════════════════════════════════════════════
# 6. Delete (soft)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCropLotDelete:

    def test_delete_returns_204(self, auth_client, farmer_profile):
        lot = create_lot(auth_client)
        resp = auth_client.delete(DETAIL_URL(lot["id"]))
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_is_soft_only(self, auth_client, farmer_profile):
        """Record must still exist in DB with is_active=False."""
        lot = create_lot(auth_client)
        lot_id = lot["id"]
        auth_client.delete(DETAIL_URL(lot_id))
        db_lot = CropLot.objects.get(pk=lot_id)
        assert db_lot.is_active is False

    def test_delete_removes_from_list(self, auth_client, farmer_profile):
        lot = create_lot(auth_client)
        auth_client.delete(DETAIL_URL(lot["id"]))
        resp = auth_client.get(LIST_URL)
        assert resp.data["count"] == 0

    def test_deleted_lot_not_retrievable(self, auth_client, farmer_profile):
        lot = create_lot(auth_client)
        auth_client.delete(DETAIL_URL(lot["id"]))
        resp = auth_client.get(DETAIL_URL(lot["id"]))
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ══════════════════════════════════════════════════════════════════════════════
# 7. Ownership Enforcement
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCropLotOwnership:

    def _auth_client_2(self, api_client, farmer_user_2, tokens_2):
        from rest_framework.test import APIClient
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens_2['access']}")
        return client

    def test_farmer_cannot_see_other_farmers_lots(
        self, api_client, auth_client, farmer_profile, farmer_user_2, farmer_profile_2
    ):
        # Create a lot for farmer 1
        create_lot(auth_client)

        # Log in as farmer 2
        resp2 = api_client.post(
            "/api/v1/auth/login/",
            {"email": "farmer2@krishilink.test", "password": "StrongPass123!"},
            format="json",
        )
        assert resp2.status_code == 200
        client2 = api_client.__class__()
        client2.credentials(HTTP_AUTHORIZATION=f"Bearer {resp2.data['access']}")

        # Farmer 2 should see an empty list
        resp = client2.get(LIST_URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 0

    def test_farmer_cannot_retrieve_other_farmers_lot(
        self, api_client, auth_client, farmer_profile, farmer_user_2, farmer_profile_2
    ):
        lot = create_lot(auth_client)

        resp2 = api_client.post(
            "/api/v1/auth/login/",
            {"email": "farmer2@krishilink.test", "password": "StrongPass123!"},
            format="json",
        )
        client2 = api_client.__class__()
        client2.credentials(HTTP_AUTHORIZATION=f"Bearer {resp2.data['access']}")

        resp = client2.get(DETAIL_URL(lot["id"]))
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_farmer_cannot_patch_other_farmers_lot(
        self, api_client, auth_client, farmer_profile, farmer_user_2, farmer_profile_2
    ):
        lot = create_lot(auth_client)

        resp2 = api_client.post(
            "/api/v1/auth/login/",
            {"email": "farmer2@krishilink.test", "password": "StrongPass123!"},
            format="json",
        )
        client2 = api_client.__class__()
        client2.credentials(HTTP_AUTHORIZATION=f"Bearer {resp2.data['access']}")

        resp = client2.patch(DETAIL_URL(lot["id"]), {"notes": "hacked"}, format="json")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_farmer_cannot_delete_other_farmers_lot(
        self, api_client, auth_client, farmer_profile, farmer_user_2, farmer_profile_2
    ):
        lot = create_lot(auth_client)

        resp2 = api_client.post(
            "/api/v1/auth/login/",
            {"email": "farmer2@krishilink.test", "password": "StrongPass123!"},
            format="json",
        )
        client2 = api_client.__class__()
        client2.credentials(HTTP_AUTHORIZATION=f"Bearer {resp2.data['access']}")

        resp = client2.delete(DETAIL_URL(lot["id"]))
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        # Original lot must still be active
        assert CropLot.objects.get(pk=lot["id"]).is_active is True
