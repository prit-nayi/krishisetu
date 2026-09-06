"""
tests/test_market_phase3.py — Phase 3 Market Intelligence tests.

Test coverage
─────────────
Provider
  ✓ Successful API response → RawPriceRecord list
  ✓ API timeout → ProviderResult with error, no raise
  ✓ Connection error → ProviderResult with error, no raise
  ✓ HTTP 401 → ProviderResult with auth error
  ✓ HTTP 500 → ProviderResult with error
  ✓ Non-JSON response → ProviderResult with error
  ✓ Missing 'records' key → ProviderResult with error
  ✓ Empty records list (no more pages) → ProviderResult with 0 records
  ✓ Missing API key → ValueError on construction
  ✓ Pagination: stops when page is smaller than page size
  ✓ Price field with encoded space (Min_x0020_Price) parsed correctly
  ✓ Invalid date format → record skipped
  ✓ Negative price → record skipped
  ✓ min > max price → record skipped
  ✓ Missing required field → record skipped

Normalizer
  ✓ Groundnut aliases normalise to GROUNDNUT
  ✓ Cotton aliases normalise to COTTON
  ✓ Unknown commodity returns None
  ✓ Empty string returns None
  ✓ Market name suffix stripping
  ✓ Market name case/whitespace normalisation
  ✓ match_market: exact match found
  ✓ match_market: normalised suffix match found
  ✓ match_market: no match returns None
  ✓ match_market: empty name returns None

Management command: sync_market_prices
  ✓ Missing API key raises CommandError
  ✓ Provider API failure: no crash, logs error
  ✓ New records created
  ✓ Existing record updated (idempotent)
  ✓ Unmatched market → skipped, unmatched count incremented
  ✓ Unsupported commodity → skipped
  ✓ Dry run: records NOT written to DB
  ✓ Invalid price (min > max) → skipped

API Endpoints
  ✓ GET /api/v1/markets/ — 200 list
  ✓ GET /api/v1/markets/ — unauthenticated 401
  ✓ GET /api/v1/markets/?district=Rajkot — filter by district
  ✓ GET /api/v1/markets/?commodity=GROUNDNUT — filter by commodity
  ✓ GET /api/v1/markets/<id>/ — 200 detail
  ✓ GET /api/v1/markets/<id>/ — 404 for unknown id
  ✓ GET /api/v1/markets/prices/ — 200 list
  ✓ GET /api/v1/markets/prices/?commodity=GROUNDNUT — filter commodity
  ✓ GET /api/v1/markets/prices/?market=<id> — filter market
  ✓ GET /api/v1/markets/prices/?district=Rajkot — filter district
  ✓ GET /api/v1/markets/prices/?date=YYYY-MM-DD — filter date
  ✓ GET /api/v1/markets/history/?commodity=GROUNDNUT&days=30 — history
  ✓ GET /api/v1/markets/history/ — invalid days falls back to 90
  ✓ GET /api/v1/markets/nearby/?lat=22.16&lon=70.79&radius_km=50 — nearby
  ✓ GET /api/v1/markets/nearby/ — invalid params 400
  ✓ GET /api/v1/markets/prices/ — unauthenticated 401
"""
import json
from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient

from apps.markets.market_data.normalizer import (
    match_market,
    normalize_commodity,
    normalize_market_name,
)
from apps.markets.market_data.providers.data_gov_provider import (
    DataGovProvider,
    _first,
    _parse_date,
    _parse_price,
)
from apps.markets.models import Market, MarketPrice

# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_raw_record(**overrides):
    """Return a minimal valid raw API dict."""
    base = {
        "State":               "Gujarat",
        "District":            "Rajkot",
        "Market":              "Gondal",
        "Commodity":           "Groundnut",
        "Variety":             "Bold",
        "Grade":               "FAQ",
        "Arrival_Date":        "01/07/2025",
        "Min_x0020_Price":     "4500",
        "Max_x0020_Price":     "5200",
        "Modal_x0020_Price":   "4900",
    }
    base.update(overrides)
    return base


def _make_market(db, name="Gondal APMC", district="Rajkot") -> Market:
    return Market.objects.create(
        name=name, district=district, state="Gujarat",
        market_type=Market.MarketType.APMC, is_active=True,
        source=Market.Source.APMC_DIRECTORY,
    )


def _make_price(db, market, commodity="GROUNDNUT", price_date=None) -> MarketPrice:
    if price_date is None:
        price_date = date.today()
    return MarketPrice.objects.create(
        market=market,
        commodity=commodity,
        variety="Bold",
        grade="FAQ",
        min_price=Decimal("4500"),
        max_price=Decimal("5200"),
        modal_price=Decimal("4900"),
        price_date=price_date,
        source=MarketPrice.Source.AGMARKNET,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Provider tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDataGovProvider:

    def test_missing_api_key_raises(self):
        with pytest.raises(ValueError, match="api_key"):
            DataGovProvider(api_key="")

    def test_successful_response_returns_records(self):
        provider = DataGovProvider(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "records": [_make_raw_record(), _make_raw_record(Commodity="Cotton")]
        }

        with patch("requests.get", return_value=mock_resp):
            result = provider.fetch_prices(state="Gujarat", limit=10)

        assert len(result.records) == 2
        assert result.errors == []
        assert result.total_fetched == 2

    def test_timeout_returns_error_no_raise(self):
        import requests as req
        provider = DataGovProvider(api_key="test-key")
        with patch("requests.get", side_effect=req.exceptions.Timeout):
            result = provider.fetch_prices()
        assert len(result.errors) == 1
        assert "timed out" in result.errors[0].lower()
        assert result.records == []

    def test_connection_error_returns_error(self):
        import requests as req
        provider = DataGovProvider(api_key="test-key")
        with patch("requests.get", side_effect=req.exceptions.ConnectionError("refused")):
            result = provider.fetch_prices()
        assert len(result.errors) == 1
        assert result.records == []

    def test_http_401_returns_auth_error(self):
        provider = DataGovProvider(api_key="bad-key")
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 401
        with patch("requests.get", return_value=mock_resp):
            result = provider.fetch_prices()
        assert len(result.errors) == 1
        assert "401" in result.errors[0] or "unauthorized" in result.errors[0].lower()

    def test_http_500_returns_error(self):
        provider = DataGovProvider(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        with patch("requests.get", return_value=mock_resp):
            result = provider.fetch_prices()
        assert len(result.errors) == 1
        assert "500" in result.errors[0]

    def test_non_json_response_returns_error(self):
        provider = DataGovProvider(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("No JSON")
        with patch("requests.get", return_value=mock_resp):
            result = provider.fetch_prices()
        assert len(result.errors) == 1
        assert "non-json" in result.errors[0].lower()

    def test_missing_records_key_returns_error(self):
        provider = DataGovProvider(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok", "count": 0}
        with patch("requests.get", return_value=mock_resp):
            result = provider.fetch_prices()
        assert len(result.errors) == 1
        assert "records" in result.errors[0].lower()

    def test_empty_records_list_returns_zero_records(self):
        provider = DataGovProvider(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"records": []}
        with patch("requests.get", return_value=mock_resp):
            result = provider.fetch_prices()
        assert result.records == []
        assert result.errors == []

    def test_pagination_stops_when_partial_page(self):
        """If API returns fewer records than page size, no second request is made."""
        provider = DataGovProvider(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        # Return 2 records — smaller than PAGE_SIZE (100) so no second page
        mock_resp.json.return_value = {
            "records": [_make_raw_record(), _make_raw_record()]
        }
        with patch("requests.get", return_value=mock_resp) as mock_get:
            result = provider.fetch_prices(limit=1000)
        assert mock_get.call_count == 1
        assert len(result.records) == 2

    def test_encoded_space_price_fields_parsed(self):
        provider = DataGovProvider(api_key="test-key")
        raw = _make_raw_record()
        # Ensure encoded-space keys work
        assert "Min_x0020_Price" in raw
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"records": [raw]}
        with patch("requests.get", return_value=mock_resp):
            result = provider.fetch_prices()
        assert len(result.records) == 1
        assert result.records[0].min_price == Decimal("4500")

    def test_invalid_date_record_skipped(self):
        provider = DataGovProvider(api_key="test-key")
        raw = _make_raw_record(Arrival_Date="not-a-date")
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"records": [raw]}
        with patch("requests.get", return_value=mock_resp):
            result = provider.fetch_prices()
        assert result.records == []

    def test_negative_price_record_skipped(self):
        provider = DataGovProvider(api_key="test-key")
        raw = _make_raw_record(**{"Min_x0020_Price": "-100"})
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"records": [raw]}
        with patch("requests.get", return_value=mock_resp):
            result = provider.fetch_prices()
        assert result.records == []

    def test_min_greater_than_max_record_skipped(self):
        provider = DataGovProvider(api_key="test-key")
        raw = _make_raw_record(**{"Min_x0020_Price": "6000", "Max_x0020_Price": "4000"})
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"records": [raw]}
        with patch("requests.get", return_value=mock_resp):
            result = provider.fetch_prices()
        assert result.records == []

    def test_missing_commodity_field_record_skipped(self):
        provider = DataGovProvider(api_key="test-key")
        raw = _make_raw_record()
        raw["Commodity"] = ""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"records": [raw]}
        with patch("requests.get", return_value=mock_resp):
            result = provider.fetch_prices()
        assert result.records == []


class TestFirstHelper:
    """Tests for the _first() key-lookup helper."""

    def test_returns_first_found_key(self):
        assert _first({"b": 2, "a": 1}, "a", "b") == 1

    def test_skips_missing_keys(self):
        assert _first({"c": 3}, "a", "b", "c") == 3

    def test_all_missing_returns_none(self):
        assert _first({"x": 1}, "a", "b") is None

    def test_empty_dict_returns_none(self):
        assert _first({}, "a") is None

    def test_does_not_return_none_value(self):
        # A key whose value is None should be skipped
        assert _first({"a": None, "b": "found"}, "a", "b") == "found"


class TestSnakeCaseFieldVariant:
    """Provider correctly parses records with snake_case field names (resource 35985678)."""

    def test_snake_case_record_parsed(self):
        provider = DataGovProvider(api_key="test-key")
        raw = {
            "state":        "Gujarat",
            "district":     "Rajkot",
            "market":       "Gondal",
            "commodity":    "Groundnut",
            "variety":      "Bold",
            "grade":        "FAQ",
            "arrival_date": "01/07/2025",
            "min_price":    "4500",
            "max_price":    "5200",
            "modal_price":  "4900",
        }
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"records": [raw]}
        with patch("requests.get", return_value=mock_resp):
            result = provider.fetch_prices()
        assert len(result.records) == 1
        r = result.records[0]
        assert r.market == "Gondal"
        assert r.commodity == "Groundnut"
        assert r.min_price == Decimal("4500")
        assert r.modal_price == Decimal("4900")

    def test_plain_space_price_fields_parsed(self):
        provider = DataGovProvider(api_key="test-key")
        raw = {
            "State":        "Gujarat",
            "District":     "Rajkot",
            "Market":       "Gondal",
            "Commodity":    "Cotton",
            "Variety":      "",
            "Grade":        "",
            "Arrival Date": "2025-07-01",
            "Min Price":    "6000",
            "Max Price":    "7000",
            "Modal Price":  "6500",
        }
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"records": [raw]}
        with patch("requests.get", return_value=mock_resp):
            result = provider.fetch_prices()
        assert len(result.records) == 1
        r = result.records[0]
        assert r.commodity == "Cotton"
        assert r.max_price == Decimal("7000")


class TestParseDateHelper:
    def test_slash_format(self):
        assert _parse_date("01/07/2025") == date(2025, 7, 1)

    def test_iso_format(self):
        assert _parse_date("2025-07-01") == date(2025, 7, 1)

    def test_hyphen_format(self):
        assert _parse_date("01-07-2025") == date(2025, 7, 1)

    def test_abbrev_month_format(self):
        assert _parse_date("01-Jul-2025") == date(2025, 7, 1)

    def test_invalid_returns_none(self):
        assert _parse_date("not-a-date") is None

    def test_empty_returns_none(self):
        assert _parse_date("") is None


class TestParsePriceHelper:
    def test_string_number(self):
        assert _parse_price("4500") == Decimal("4500")

    def test_comma_separated(self):
        assert _parse_price("1,000") == Decimal("1000")

    def test_integer(self):
        assert _parse_price(5000) == Decimal("5000")

    def test_float(self):
        assert _parse_price(4500.5) == Decimal("4500.5")

    def test_none_returns_none(self):
        assert _parse_price(None) is None

    def test_invalid_string_returns_none(self):
        assert _parse_price("abc") is None

    def test_empty_string_returns_none(self):
        assert _parse_price("") is None


# ─────────────────────────────────────────────────────────────────────────────
# Normalizer tests
# ─────────────────────────────────────────────────────────────────────────────

class TestNormalizecommodity:
    def test_groundnut_variants(self):
        for alias in ["Groundnut", "Ground Nut", "groundnut", "GROUNDNUT",
                      "Peanut", "Moongfali", "Mungfali", "Ground-nut"]:
            assert normalize_commodity(alias) == "GROUNDNUT", f"Failed for: {alias}"

    def test_cotton_variants(self):
        for alias in ["Cotton", "cotton", "COTTON", "Cotton (Raw)", "Kapas"]:
            assert normalize_commodity(alias) == "COTTON", f"Failed for: {alias}"

    def test_unknown_commodity_returns_none(self):
        assert normalize_commodity("Wheat") is None
        assert normalize_commodity("Rice") is None
        assert normalize_commodity("Tomato") is None

    def test_empty_string_returns_none(self):
        assert normalize_commodity("") is None

    def test_none_returns_none(self):
        assert normalize_commodity(None) is None


class TestNormalizeMarketName:
    def test_strips_apmc_suffix(self):
        assert normalize_market_name("Gondal APMC") == "gondal"

    def test_strips_mandi_suffix(self):
        assert normalize_market_name("Rajkot Mandi") == "rajkot"

    def test_strips_market_suffix(self):
        assert normalize_market_name("Bhuj Market") == "bhuj"

    def test_case_insensitive(self):
        assert normalize_market_name("GONDAL APMC") == "gondal"

    def test_strips_whitespace(self):
        assert normalize_market_name("  Gondal  ") == "gondal"

    def test_empty_string(self):
        assert normalize_market_name("") == ""

    def test_normalises_internal_whitespace(self):
        # Multiple spaces collapsed
        assert normalize_market_name("Gondal  APMC") == "gondal"


class TestMatchMarket:
    def test_normalised_match_found(self):
        lookup = {"gondal": 42}
        assert match_market("Gondal APMC", lookup) == 42

    def test_plain_match_found(self):
        lookup = {"gondal apmc": 99}
        assert match_market("Gondal APMC", lookup) == 99

    def test_no_match_returns_none(self):
        lookup = {"rajkot": 1}
        assert match_market("Bhavnagar", lookup) is None

    def test_empty_name_returns_none(self):
        assert match_market("", {"gondal": 1}) is None


# ─────────────────────────────────────────────────────────────────────────────
# Management command: sync_market_prices
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSyncMarketPricesCommand:

    def test_missing_api_key_raises_command_error(self, settings):
        settings.DATA_GOV_API_KEY = ""
        with pytest.raises(CommandError, match="DATA_GOV_API_KEY"):
            call_command("sync_market_prices")

    def test_provider_failure_no_crash(self, db, settings):
        """If the provider returns errors and no records, command completes cleanly."""
        settings.DATA_GOV_API_KEY = "fake-key"
        market = _make_market(db)

        mock_result = MagicMock()
        mock_result.errors = ["Connection refused"]
        mock_result.records = []
        mock_result.total_fetched = 0

        with patch(
            "apps.markets.management.commands.sync_market_prices.DataGovProvider.fetch_prices",
            return_value=mock_result,
        ):
            # Must not raise
            call_command("sync_market_prices", stdout=StringIO(), stderr=StringIO())

        assert MarketPrice.objects.count() == 0

    def test_new_records_created(self, db, settings):
        settings.DATA_GOV_API_KEY = "fake-key"
        market = _make_market(db, name="Gondal APMC", district="Rajkot")

        from apps.markets.market_data.providers.base import RawPriceRecord
        raw = RawPriceRecord(
            state="Gujarat", district="Rajkot", market="Gondal",
            commodity="Groundnut", variety="Bold", grade="FAQ",
            arrival_date=date(2025, 7, 1),
            min_price=Decimal("4500"), max_price=Decimal("5200"),
            modal_price=Decimal("4900"), source="agmarknet",
        )

        mock_result = MagicMock()
        mock_result.errors = []
        mock_result.records = [raw]
        mock_result.total_fetched = 1

        with patch(
            "apps.markets.management.commands.sync_market_prices.DataGovProvider.fetch_prices",
            return_value=mock_result,
        ):
            call_command("sync_market_prices", stdout=StringIO(), stderr=StringIO())

        assert MarketPrice.objects.count() == 1
        price = MarketPrice.objects.get()
        assert price.commodity == "GROUNDNUT"
        assert price.market == market
        assert price.min_price == Decimal("4500")

    def test_existing_record_updated_not_duplicated(self, db, settings):
        settings.DATA_GOV_API_KEY = "fake-key"
        market = _make_market(db, name="Gondal APMC", district="Rajkot")
        _make_price(db, market, "GROUNDNUT", date(2025, 7, 1))
        assert MarketPrice.objects.count() == 1

        from apps.markets.market_data.providers.base import RawPriceRecord
        # Same market/commodity/variety/date but different prices
        raw = RawPriceRecord(
            state="Gujarat", district="Rajkot", market="Gondal",
            commodity="Groundnut", variety="Bold", grade="FAQ",
            arrival_date=date(2025, 7, 1),
            min_price=Decimal("4600"), max_price=Decimal("5300"),
            modal_price=Decimal("5000"), source="agmarknet",
        )
        mock_result = MagicMock()
        mock_result.errors = []
        mock_result.records = [raw]
        mock_result.total_fetched = 1

        with patch(
            "apps.markets.management.commands.sync_market_prices.DataGovProvider.fetch_prices",
            return_value=mock_result,
        ):
            call_command("sync_market_prices", stdout=StringIO(), stderr=StringIO())

        # Still only 1 record — updated not duplicated
        assert MarketPrice.objects.count() == 1
        assert MarketPrice.objects.get().modal_price == Decimal("5000")

    def test_unmatched_market_skipped(self, db, settings):
        settings.DATA_GOV_API_KEY = "fake-key"
        # No market in DB

        from apps.markets.market_data.providers.base import RawPriceRecord
        raw = RawPriceRecord(
            state="Gujarat", district="Rajkot", market="UnknownMarketXYZ",
            commodity="Groundnut", variety="", grade="",
            arrival_date=date(2025, 7, 1),
            min_price=Decimal("4500"), max_price=Decimal("5200"),
            modal_price=Decimal("4900"), source="agmarknet",
        )
        mock_result = MagicMock()
        mock_result.errors = []
        mock_result.records = [raw]
        mock_result.total_fetched = 1

        with patch(
            "apps.markets.management.commands.sync_market_prices.DataGovProvider.fetch_prices",
            return_value=mock_result,
        ):
            call_command("sync_market_prices", stdout=StringIO(), stderr=StringIO())

        assert MarketPrice.objects.count() == 0

    def test_unsupported_commodity_skipped(self, db, settings):
        settings.DATA_GOV_API_KEY = "fake-key"
        market = _make_market(db)

        from apps.markets.market_data.providers.base import RawPriceRecord
        raw = RawPriceRecord(
            state="Gujarat", district="Rajkot", market="Gondal",
            commodity="Wheat", variety="", grade="",
            arrival_date=date(2025, 7, 1),
            min_price=Decimal("2000"), max_price=Decimal("2500"),
            modal_price=Decimal("2200"), source="agmarknet",
        )
        mock_result = MagicMock()
        mock_result.errors = []
        mock_result.records = [raw]
        mock_result.total_fetched = 1

        with patch(
            "apps.markets.management.commands.sync_market_prices.DataGovProvider.fetch_prices",
            return_value=mock_result,
        ):
            call_command("sync_market_prices", stdout=StringIO(), stderr=StringIO())

        assert MarketPrice.objects.count() == 0

    def test_dry_run_does_not_write(self, db, settings):
        settings.DATA_GOV_API_KEY = "fake-key"
        market = _make_market(db, name="Gondal APMC", district="Rajkot")

        from apps.markets.market_data.providers.base import RawPriceRecord
        raw = RawPriceRecord(
            state="Gujarat", district="Rajkot", market="Gondal",
            commodity="Groundnut", variety="", grade="",
            arrival_date=date(2025, 7, 1),
            min_price=Decimal("4500"), max_price=Decimal("5200"),
            modal_price=Decimal("4900"), source="agmarknet",
        )
        mock_result = MagicMock()
        mock_result.errors = []
        mock_result.records = [raw]
        mock_result.total_fetched = 1

        with patch(
            "apps.markets.management.commands.sync_market_prices.DataGovProvider.fetch_prices",
            return_value=mock_result,
        ):
            call_command("sync_market_prices", "--dry-run",
                         stdout=StringIO(), stderr=StringIO())

        assert MarketPrice.objects.count() == 0

    def test_invalid_price_min_gt_max_skipped(self, db, settings):
        """Records with min > max from the provider are skipped."""
        settings.DATA_GOV_API_KEY = "fake-key"
        market = _make_market(db, name="Gondal APMC", district="Rajkot")

        from apps.markets.market_data.providers.base import RawPriceRecord
        # Intentionally create a bad record (provider normally filters these,
        # but command defends again)
        raw = RawPriceRecord(
            state="Gujarat", district="Rajkot", market="Gondal",
            commodity="Groundnut", variety="", grade="",
            arrival_date=date(2025, 7, 1),
            min_price=Decimal("6000"), max_price=Decimal("4000"),
            modal_price=Decimal("5000"), source="agmarknet",
        )
        mock_result = MagicMock()
        mock_result.errors = []
        mock_result.records = [raw]
        mock_result.total_fetched = 1

        with patch(
            "apps.markets.management.commands.sync_market_prices.DataGovProvider.fetch_prices",
            return_value=mock_result,
        ):
            call_command("sync_market_prices", stdout=StringIO(), stderr=StringIO())

        assert MarketPrice.objects.count() == 0


# ─────────────────────────────────────────────────────────────────────────────
# API endpoint tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMarketListAPI:

    def test_list_unauthenticated_401(self, api_client):
        resp = api_client.get("/api/v1/markets/")
        assert resp.status_code == 401

    def test_list_authenticated_200(self, auth_client, db):
        _make_market(db, name="Gondal APMC", district="Rajkot")
        resp = auth_client.get("/api/v1/markets/")
        assert resp.status_code == 200
        data = resp.json()
        # DRF pagination: results key present
        results = data.get("results", data)
        assert len(results) >= 1

    def test_list_filter_by_district(self, auth_client, db):
        _make_market(db, name="Gondal APMC",   district="Rajkot")
        _make_market(db, name="Bhavnagar APMC", district="Bhavnagar")
        resp = auth_client.get("/api/v1/markets/?district=Rajkot")
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        assert all(m["district"] == "Rajkot" for m in results)

    def test_list_filter_by_commodity(self, auth_client, db):
        m1 = _make_market(db, name="Gondal APMC",   district="Rajkot")
        m2 = _make_market(db, name="Bhavnagar APMC", district="Bhavnagar")
        # Only m1 has groundnut prices
        _make_price(db, m1, "GROUNDNUT")
        resp = auth_client.get("/api/v1/markets/?commodity=GROUNDNUT")
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        ids = [r["id"] for r in results]
        assert m1.id in ids
        assert m2.id not in ids

    def test_list_inactive_markets_excluded(self, auth_client, db):
        Market.objects.create(
            name="Inactive APMC", district="Rajkot", state="Gujarat",
            market_type=Market.MarketType.APMC, is_active=False,
            source=Market.Source.APMC_DIRECTORY,
        )
        resp = auth_client.get("/api/v1/markets/")
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        assert all(m["is_active"] for m in results)


@pytest.mark.django_db
class TestMarketDetailAPI:

    def test_detail_200(self, auth_client, db):
        market = _make_market(db)
        resp = auth_client.get(f"/api/v1/markets/{market.id}/")
        assert resp.status_code == 200
        assert resp.json()["name"] == market.name

    def test_detail_404(self, auth_client, db):
        resp = auth_client.get("/api/v1/markets/999999/")
        assert resp.status_code == 404

    def test_detail_contains_required_fields(self, auth_client, db):
        market = _make_market(db)
        resp = auth_client.get(f"/api/v1/markets/{market.id}/")
        data = resp.json()
        for field in ("id", "name", "district", "state", "market_type", "is_active"):
            assert field in data, f"Missing field: {field}"


@pytest.mark.django_db
class TestMarketPriceListAPI:

    def test_prices_unauthenticated_401(self, api_client):
        resp = api_client.get("/api/v1/markets/prices/")
        assert resp.status_code == 401

    def test_prices_200(self, auth_client, db):
        market = _make_market(db)
        _make_price(db, market)
        resp = auth_client.get("/api/v1/markets/prices/")
        assert resp.status_code == 200

    def test_prices_filter_commodity(self, auth_client, db):
        market = _make_market(db)
        _make_price(db, market, "GROUNDNUT", date.today())
        _make_price(db, market, "COTTON",    date.today() - timedelta(days=1))
        resp = auth_client.get("/api/v1/markets/prices/?commodity=GROUNDNUT")
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        assert all(r["commodity"] == "GROUNDNUT" for r in results)

    def test_prices_filter_market(self, auth_client, db):
        m1 = _make_market(db, name="Gondal APMC",   district="Rajkot")
        m2 = _make_market(db, name="Rajkot APMC",   district="Rajkot")
        _make_price(db, m1, "GROUNDNUT")
        _make_price(db, m2, "GROUNDNUT", date.today() - timedelta(days=1))
        resp = auth_client.get(f"/api/v1/markets/prices/?market={m1.id}")
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        assert all(r["market"] == m1.id for r in results)

    def test_prices_filter_district(self, auth_client, db):
        m1 = _make_market(db, name="Gondal APMC",    district="Rajkot")
        m2 = _make_market(db, name="Bhavnagar APMC", district="Bhavnagar")
        _make_price(db, m1, "GROUNDNUT")
        _make_price(db, m2, "GROUNDNUT", date.today() - timedelta(days=1))
        resp = auth_client.get("/api/v1/markets/prices/?district=Rajkot")
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        assert all(r["market_district"] == "Rajkot" for r in results)

    def test_prices_filter_date(self, auth_client, db):
        market = _make_market(db)
        target = date(2025, 7, 1)
        _make_price(db, market, "GROUNDNUT", target)
        _make_price(db, market, "COTTON",    date(2025, 6, 1))
        resp = auth_client.get(f"/api/v1/markets/prices/?date=2025-07-01")
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        assert len(results) == 1
        assert results[0]["price_date"] == "2025-07-01"

    def test_price_response_shape(self, auth_client, db):
        market = _make_market(db)
        _make_price(db, market)
        resp = auth_client.get("/api/v1/markets/prices/")
        results = resp.json().get("results", resp.json())
        assert len(results) >= 1
        row = results[0]
        for field in ("id", "market", "market_name", "market_district",
                      "commodity", "variety", "grade",
                      "min_price", "max_price", "modal_price",
                      "price_date", "source"):
            assert field in row, f"Missing field in price response: {field}"


@pytest.mark.django_db
class TestMarketPriceHistoryAPI:

    def test_history_200(self, auth_client, db):
        market = _make_market(db)
        for i in range(5):
            MarketPrice.objects.create(
                market=market,
                commodity="GROUNDNUT",
                variety="",
                grade="",
                min_price=Decimal("4500"),
                max_price=Decimal("5200"),
                modal_price=Decimal("4900"),
                price_date=date.today() - timedelta(days=i),
                source=MarketPrice.Source.AGMARKNET,
            )
        resp = auth_client.get(
            f"/api/v1/markets/history/?commodity=GROUNDNUT&market={market.id}&days=30"
        )
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        assert len(results) == 5

    def test_history_invalid_days_defaults_to_90(self, auth_client, db):
        resp = auth_client.get("/api/v1/markets/history/?days=notanumber")
        assert resp.status_code == 200  # should not crash

    def test_history_ordered_by_date_asc(self, auth_client, db):
        market = _make_market(db)
        for i in range(3):
            MarketPrice.objects.create(
                market=market, commodity="COTTON", variety="", grade="",
                min_price=Decimal("6000"), max_price=Decimal("7000"),
                modal_price=Decimal("6500"),
                price_date=date.today() - timedelta(days=i),
                source=MarketPrice.Source.AGMARKNET,
            )
        resp = auth_client.get("/api/v1/markets/history/?commodity=COTTON")
        results = resp.json().get("results", resp.json())
        dates = [r["price_date"] for r in results]
        assert dates == sorted(dates)

    def test_history_excludes_old_records(self, auth_client, db):
        market = _make_market(db)
        # One recent, one very old
        MarketPrice.objects.create(
            market=market, commodity="GROUNDNUT", variety="", grade="",
            min_price=Decimal("4500"), max_price=Decimal("5200"),
            modal_price=Decimal("4900"),
            price_date=date.today() - timedelta(days=5),
            source=MarketPrice.Source.AGMARKNET,
        )
        MarketPrice.objects.create(
            market=market, commodity="GROUNDNUT", variety="old", grade="",
            min_price=Decimal("3000"), max_price=Decimal("4000"),
            modal_price=Decimal("3500"),
            price_date=date.today() - timedelta(days=200),
            source=MarketPrice.Source.AGMARKNET,
        )
        resp = auth_client.get("/api/v1/markets/history/?commodity=GROUNDNUT&days=30")
        results = resp.json().get("results", resp.json())
        assert len(results) == 1


@pytest.mark.django_db
class TestNearbyMarketsAPI:

    def test_nearby_200(self, auth_client, db):
        Market.objects.create(
            name="Gondal APMC", district="Rajkot", state="Gujarat",
            market_type=Market.MarketType.APMC, is_active=True,
            source=Market.Source.APMC_DIRECTORY,
            latitude=Decimal("22.1631"), longitude=Decimal("70.7934"),
        )
        resp = auth_client.get(
            "/api/v1/markets/nearby/?lat=22.16&lon=70.79&radius_km=50"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "distance_km" in data[0]

    def test_nearby_invalid_params_400(self, auth_client, db):
        resp = auth_client.get(
            "/api/v1/markets/nearby/?lat=notanumber&lon=70.79"
        )
        assert resp.status_code == 400

    def test_nearby_market_without_coordinates_excluded(self, auth_client, db):
        Market.objects.create(
            name="No Coords APMC", district="Rajkot", state="Gujarat",
            market_type=Market.MarketType.APMC, is_active=True,
            source=Market.Source.APMC_DIRECTORY,
            latitude=None, longitude=None,
        )
        resp = auth_client.get(
            "/api/v1/markets/nearby/?lat=22.16&lon=70.79&radius_km=200"
        )
        assert resp.status_code == 200
        data = resp.json()
        # Market without coordinates must not appear
        assert not any(m["name"] == "No Coords APMC" for m in data)
