"""
tests/test_auth.py — Phase 1 Authentication Integration Tests.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestRegister:
    URL = "/api/v1/auth/register/"

    def test_register_farmer_success(self, api_client):
        payload = {"email": "newfarmer@test.com", "username": "newfarmer",
                   "password": "StrongPass123!", "password_confirm": "StrongPass123!", "role": "farmer"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["message"] == "Registration successful."
        assert response.data["user"]["email"] == "newfarmer@test.com"
        assert "password" not in response.data["user"]

    def test_register_creates_user_in_db(self, api_client):
        payload = {"email": "dbcheck@test.com", "username": "dbcheckuser",
                   "password": "StrongPass123!", "password_confirm": "StrongPass123!"}
        api_client.post(self.URL, payload, format="json")
        assert User.objects.filter(email="dbcheck@test.com").exists()

    def test_register_default_role_is_farmer(self, api_client):
        payload = {"email": "defaultrole@test.com", "username": "defaultrole",
                   "password": "StrongPass123!", "password_confirm": "StrongPass123!"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"]["role"] == "farmer"

    def test_register_duplicate_email_returns_400(self, api_client, farmer_user):
        payload = {"email": farmer_user.email, "username": "dup",
                   "password": "StrongPass123!", "password_confirm": "StrongPass123!"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_username_returns_400(self, api_client, farmer_user):
        payload = {"email": "brand_new@test.com", "username": farmer_user.username,
                   "password": "StrongPass123!", "password_confirm": "StrongPass123!"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch_returns_400(self, api_client):
        payload = {"email": "mismatch@test.com", "username": "mismatchuser",
                   "password": "StrongPass123!", "password_confirm": "DifferentPass456!"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password_returns_400(self, api_client):
        payload = {"email": "weakpass@test.com", "username": "weakpassuser",
                   "password": "123", "password_confirm": "123"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_email_returns_400(self, api_client):
        payload = {"username": "noemail", "password": "StrongPass123!", "password_confirm": "StrongPass123!"}
        response = api_client.post(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    URL = "/api/v1/auth/login/"

    def test_login_success_returns_tokens(self, api_client, farmer_user):
        response = api_client.post(self.URL, {"email": farmer_user.email, "password": "StrongPass123!"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password_returns_401(self, api_client, farmer_user):
        response = api_client.post(self.URL, {"email": farmer_user.email, "password": "Wrong!"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_unknown_email_returns_401(self, api_client):
        response = api_client.post(self.URL, {"email": "nobody@test.com", "password": "StrongPass123!"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_inactive_user_returns_401(self, api_client, farmer_user):
        farmer_user.is_active = False
        farmer_user.save()
        response = api_client.post(self.URL, {"email": farmer_user.email, "password": "StrongPass123!"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_fields_returns_400(self, api_client):
        response = api_client.post(self.URL, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTokenRefresh:
    URL = "/api/v1/auth/refresh/"

    def test_refresh_returns_new_access_token(self, api_client, tokens):
        response = api_client.post(self.URL, {"refresh": tokens["refresh"]}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_invalid_token_returns_401(self, api_client):
        response = api_client.post(self.URL, {"refresh": "not.a.valid.token"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_missing_token_returns_400(self, api_client):
        response = api_client.post(self.URL, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestMeEndpoint:
    URL = "/api/v1/auth/me/"

    def test_me_authenticated_returns_user_data(self, auth_client, farmer_user):
        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == farmer_user.email
        assert response.data["role"] == "farmer"
        assert "password" not in response.data

    def test_me_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_returns_correct_role(self, api_client, farmer_user, tokens):
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == farmer_user.role


@pytest.mark.django_db
class TestFarmerProfile:
    URL = "/api/v1/farmer/profile/"

    def test_get_profile_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_profile_creates_empty_profile_if_missing(self, auth_client):
        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert "user" in response.data

    def test_get_profile_returns_existing_profile(self, auth_client, farmer_profile):
        response = auth_client.get(self.URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["district"] == "Rajkot"
        assert response.data["village"] == "Gondal"

    def test_patch_profile_updates_fields(self, auth_client, farmer_profile):
        payload = {"district": "Amreli", "village": "Dhari", "latitude": "21.7200", "longitude": "71.5300"}
        response = auth_client.patch(self.URL, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        farmer_profile.refresh_from_db()
        assert farmer_profile.district == "Amreli"
        assert farmer_profile.village == "Dhari"

    def test_patch_profile_partial_update(self, auth_client, farmer_profile):
        original_district = farmer_profile.district
        response = auth_client.patch(self.URL, {"village": "Upleta"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        farmer_profile.refresh_from_db()
        assert farmer_profile.village == "Upleta"
        assert farmer_profile.district == original_district

    def test_patch_profile_unauthenticated_returns_401(self, api_client, farmer_profile):
        response = api_client.patch(self.URL, {"village": "Gondal"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestRoleBasedAccess:
    def test_farmer_cannot_access_django_admin(self, auth_client):
        response = auth_client.get("/admin/", follow=False)
        assert response.status_code in (status.HTTP_302_FOUND, status.HTTP_403_FORBIDDEN)

    def test_invalid_bearer_token_returns_401(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.here")
        response = api_client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestOwnershipIsolation:
    def test_farmer_a_gets_own_profile_not_farmer_b(
        self, api_client, farmer_user, farmer_profile, farmer_user_2, farmer_profile_2
    ):
        login_resp = api_client.post("/api/v1/auth/login/",
            {"email": farmer_user.email, "password": "StrongPass123!"}, format="json")
        assert login_resp.status_code == status.HTTP_200_OK
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_resp.data['access']}")
        response = api_client.get("/api/v1/farmer/profile/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["district"] == "Rajkot"
        assert response.data["district"] != farmer_profile_2.district

    def test_farmer_b_gets_own_profile_not_farmer_a(
        self, api_client, farmer_user, farmer_profile, farmer_user_2, farmer_profile_2
    ):
        login_resp = api_client.post("/api/v1/auth/login/",
            {"email": farmer_user_2.email, "password": "StrongPass123!"}, format="json")
        assert login_resp.status_code == status.HTTP_200_OK
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_resp.data['access']}")
        response = api_client.get("/api/v1/farmer/profile/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["district"] == "Amreli"
        assert response.data["district"] != farmer_profile.district
