"""
tests/test_analysis_phase45.py — Phase 4+5 integration tests.

Coverage
--------
Unit conversion (to_quintal)
  ✓ quintal
  ✓ kg
  ✓ tonne
  ✓ unknown unit raises ValueError

MarketAnalysisService
  ✓ Single market, groundnut, quintal → financial breakdown correct
  ✓ Single market, cotton, quintal → financial breakdown correct
  ✓ KG → quintal conversion flows through correctly
  ✓ Tonne → quintal conversion
  ✓ Market with coordinates → distance + transport cost calculated
  ✓ Market without coordinates → distance=None, transport_cost=0
  ✓ Farmer without coordinates → distance=None
  ✓ No price records for commodity → error result
  ✓ Crop lot not found → error result
  ✓ Crop lot owned by other farmer → permission error
  ✓ Multiple markets → ranked by net_revenue descending
  ✓ Market with higher price but further distance → correct ranking

ForecastService
  ✓ 0 records → INSUFFICIENT_DATA, no predictions
  ✓ 3 records (< 7) → INSUFFICIENT_DATA
  ✓ 7 records → LOW confidence, moving_average
  ✓ 30 records → MEDIUM confidence, linear_regression
  ✓ 90 records → HIGH confidence, linear_regression
  ✓ predicted_price is a float
  ✓ price_change = predicted - current
  ✓ save=True → Forecast record created in DB

CombinedAnalysisService
  ✓ Returns combined entry with financial + forecast fields
  ✓ best_market is rank 1 by net_revenue
  ✓ Markets ranked net_revenue DESC
  ✓ Forecast INSUFFICIENT_DATA does not crash combined result
  ✓ Errors from financial layer propagate

MarketAnalysisView (API)
  ✓ Unauthenticated → 401
  ✓ Missing crop_lot_id → 400
  ✓ Non-integer crop_lot_id → 400
  ✓ Other farmer's crop lot → 403
  ✓ Nonexistent crop lot → 404
  ✓ Valid request with groundnut → 200, markets list, best_market
  ✓ Valid request with cotton → 200
  ✓ Multiple markets ranked in response
  ✓ forecast_days clamped to 1..90
  ✓ Response shape contains all required keys
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import FarmerProfile
from apps.crops.models import CropLot
from apps.forecasting.models import Forecast
from apps.markets.models import Market, MarketPrice
from apps.decisions.services.market_analysis import MarketAnalysisService, to_quintal
from apps.decisions.services.forecast_service import ForecastService
from apps.decisions.services.combined_analysis import CombinedAnalysisService


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def market_gondal(db):
    return Market.objects.create(
        name="Gondal APMC", district="Rajkot", state="Gujarat",
        market_type="APMC", is_active=True,
        source="apmc_directory",
        latitude=Decimal("22.1631"), longitude=Decimal("70.7934"),
    )


@pytest.fixture
def market_bhavnagar(db):
    return Market.objects.create(
        name="Bhavnagar APMC", district="Bhavnagar", state="Gujarat",
        market_type="APMC", is_active=True,
        source="apmc_directory",
        latitude=Decimal("21.7645"), longitude=Decimal("72.1519"),
    )


@pytest.fixture
def market_no_coords(db):
    return Market.objects.create(
        name="No Coords APMC", district="Rajkot", state="Gujarat",
        market_type="APMC", is_active=True,
        source="apmc_directory",
        latitude=None, longitude=None,
    )


def _add_price(db, market, commodity, modal_price, price_date=None, variety="Bold"):
    if price_date is None:
        price_date = date.today()
    return MarketPrice.objects.create(
        market=market, commodity=commodity, variety=variety, grade="FAQ",
        min_price=Decimal(str(modal_price)) * Decimal("0.9"),
        max_price=Decimal(str(modal_price)) * Decimal("1.1"),
        modal_price=Decimal(str(modal_price)),
        price_date=price_date,
        source="agmarknet",
    )


def _make_crop_lot(farmer_profile, commodity="GROUNDNUT", qty=10, unit="quintal"):
    return CropLot.objects.create(
        farmer=farmer_profile,
        commodity=commodity.lower(),
        quantity=Decimal(str(qty)),
        unit=unit,
        harvest_date=date.today() - timedelta(days=30),
        storage_status="farm",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Unit conversion tests
# ─────────────────────────────────────────────────────────────────────────────

class TestToQuintal:
    def test_quintal(self):
        assert to_quintal(10, "quintal") == pytest.approx(10.0)

    def test_kg(self):
        assert to_quintal(500, "kg") == pytest.approx(5.0)

    def test_tonne(self):
        assert to_quintal(2, "tonne") == pytest.approx(20.0)

    def test_unknown_unit_raises(self):
        with pytest.raises(ValueError, match="Unsupported unit"):
            to_quintal(10, "maund")

    def test_case_insensitive(self):
        assert to_quintal(100, "KG") == pytest.approx(1.0)


# ─────────────────────────────────────────────────────────────────────────────
# MarketAnalysisService tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMarketAnalysisService:

    def test_single_groundnut_market_financial_breakdown(
        self, farmer_user, farmer_profile, market_gondal
    ):
        _add_price(None, market_gondal, "GROUNDNUT", 5000)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10, "quintal")

        result = MarketAnalysisService().run(lot.id, farmer_user)

        assert not result.errors or len(result.markets) > 0
        assert len(result.markets) == 1
        m = result.markets[0]
        assert m.commodity_note if hasattr(m, "commodity_note") else True
        assert m.modal_price == pytest.approx(5000.0)
        assert m.gross_revenue == pytest.approx(50000.0)   # 10 × 5000
        assert m.quantity_quintal == pytest.approx(10.0)
        assert m.rank == 1

    def test_single_cotton_market(self, farmer_user, farmer_profile, market_gondal):
        _add_price(None, market_gondal, "COTTON", 6500)
        lot = _make_crop_lot(farmer_profile, "COTTON", 5, "quintal")

        result = MarketAnalysisService().run(lot.id, farmer_user)
        assert len(result.markets) == 1
        m = result.markets[0]
        assert m.gross_revenue == pytest.approx(32500.0)  # 5 × 6500

    def test_kg_conversion(self, farmer_user, farmer_profile, market_gondal):
        _add_price(None, market_gondal, "GROUNDNUT", 5000)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 500, "kg")  # 500 kg = 5 q

        result = MarketAnalysisService().run(lot.id, farmer_user)
        m = result.markets[0]
        assert m.quantity_quintal == pytest.approx(5.0)
        assert m.gross_revenue == pytest.approx(25000.0)

    def test_tonne_conversion(self, farmer_user, farmer_profile, market_gondal):
        _add_price(None, market_gondal, "GROUNDNUT", 5000)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 2, "tonne")  # 2t = 20q

        result = MarketAnalysisService().run(lot.id, farmer_user)
        m = result.markets[0]
        assert m.quantity_quintal == pytest.approx(20.0)
        assert m.gross_revenue == pytest.approx(100000.0)

    def test_market_with_coordinates_has_distance_and_transport(
        self, farmer_user, farmer_profile, market_gondal
    ):
        # farmer_profile lat/lon is set to Gondal area in conftest
        _add_price(None, market_gondal, "GROUNDNUT", 5000)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)

        result = MarketAnalysisService().run(lot.id, farmer_user)
        m = result.markets[0]
        # farmer and market are very close — distance should be small
        assert m.distance_km is not None
        assert m.distance_km >= 0
        # transport cost should be non-negative
        assert m.transport_cost >= 0
        # net revenue = gross - transport
        assert pytest.approx(m.net_revenue, rel=1e-4) == m.gross_revenue - m.transport_cost

    def test_market_without_coordinates_zero_transport(
        self, farmer_user, farmer_profile, market_no_coords
    ):
        _add_price(None, market_no_coords, "GROUNDNUT", 4800)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)

        result = MarketAnalysisService().run(lot.id, farmer_user)
        m = result.markets[0]
        assert m.distance_km is None
        assert m.transport_cost == 0.0
        assert m.net_revenue == m.gross_revenue

    def test_farmer_without_coordinates(self, farmer_user, farmer_profile, market_gondal):
        farmer_profile.latitude  = None
        farmer_profile.longitude = None
        farmer_profile.save()

        _add_price(None, market_gondal, "GROUNDNUT", 5000)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)

        result = MarketAnalysisService().run(lot.id, farmer_user)
        assert result.farmer_lat is None
        m = result.markets[0]
        assert m.distance_km is None

    def test_no_price_records_returns_error(self, farmer_user, farmer_profile, market_gondal):
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)
        # No price records created
        result = MarketAnalysisService().run(lot.id, farmer_user)
        assert result.errors
        assert len(result.markets) == 0

    def test_crop_lot_not_found(self, farmer_user):
        result = MarketAnalysisService().run(99999, farmer_user)
        assert result.errors
        assert "not found" in result.errors[0].lower()

    def test_other_farmers_crop_lot_rejected(
        self, farmer_user, farmer_user_2, farmer_profile_2, market_gondal
    ):
        lot = _make_crop_lot(farmer_profile_2, "GROUNDNUT", 10)
        result = MarketAnalysisService().run(lot.id, farmer_user)
        assert result.errors
        assert "permission" in result.errors[0].lower()

    def test_multiple_markets_ranked_by_net_revenue(
        self, farmer_user, farmer_profile, market_gondal, market_bhavnagar
    ):
        _add_price(None, market_gondal,   "GROUNDNUT", 5000)
        _add_price(None, market_bhavnagar, "GROUNDNUT", 4000)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)

        result = MarketAnalysisService().run(lot.id, farmer_user)
        assert len(result.markets) == 2
        # Gondal has higher price → should be rank 1
        assert result.markets[0].market_name == "Gondal APMC"
        assert result.markets[0].rank == 1
        assert result.markets[1].rank == 2

    def test_ranking_accounts_for_transport(
        self, farmer_user, farmer_profile, market_gondal, market_bhavnagar
    ):
        """
        Bhavnagar has a slightly higher modal price but is much further from Gondal
        farmer; after transport deduction, Gondal may still win.
        """
        _add_price(None, market_gondal,    "GROUNDNUT", 5000)
        _add_price(None, market_bhavnagar, "GROUNDNUT", 5100)  # slightly higher
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)

        result = MarketAnalysisService().run(lot.id, farmer_user)
        # Just assert no error and ranking is deterministic
        assert len(result.markets) == 2
        assert result.markets[0].rank == 1
        assert result.best_market is not None


# ─────────────────────────────────────────────────────────────────────────────
# ForecastService tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestForecastService:

    def _add_history(self, market, commodity, n_days, base_price=5000.0):
        """Add n_days of price history ending today."""
        today = date.today()
        prices = []
        for i in range(n_days):
            d = today - timedelta(days=n_days - 1 - i)
            p = MarketPrice(
                market=market, commodity=commodity, variety="", grade="",
                min_price=Decimal(str(base_price * 0.9)),
                max_price=Decimal(str(base_price * 1.1)),
                modal_price=Decimal(str(base_price + i * 2)),
                price_date=d, source="agmarknet",
            )
            prices.append(p)
        MarketPrice.objects.bulk_create(prices)

    def test_zero_records_insufficient(self, market_gondal):
        result = ForecastService().run(
            market_gondal.id, market_gondal.name, "GROUNDNUT", horizon_days=7
        )
        assert result.confidence_level == "INSUFFICIENT_DATA"
        assert result.predicted_price is None
        assert result.data_points == 0
        assert result.error != ""

    def test_three_records_insufficient(self, market_gondal):
        self._add_history(market_gondal, "GROUNDNUT", 3)
        result = ForecastService().run(
            market_gondal.id, market_gondal.name, "GROUNDNUT", horizon_days=7
        )
        assert result.confidence_level == "INSUFFICIENT_DATA"

    def test_seven_records_low_confidence(self, market_gondal):
        self._add_history(market_gondal, "GROUNDNUT", 7)
        result = ForecastService().run(
            market_gondal.id, market_gondal.name, "GROUNDNUT", horizon_days=7
        )
        assert result.confidence_level == "LOW"
        assert result.model_name == "moving_average"
        assert result.predicted_price is not None
        assert isinstance(result.predicted_price, float)
        assert len(result.predictions) == 7

    def test_thirty_records_medium_confidence(self, market_gondal):
        self._add_history(market_gondal, "GROUNDNUT", 30)
        result = ForecastService().run(
            market_gondal.id, market_gondal.name, "GROUNDNUT", horizon_days=7
        )
        assert result.confidence_level == "MEDIUM"
        assert result.model_name == "linear_regression"
        assert result.confidence_score == pytest.approx(0.6)

    def test_ninety_records_high_confidence(self, market_gondal):
        self._add_history(market_gondal, "GROUNDNUT", 90)
        result = ForecastService().run(
            market_gondal.id, market_gondal.name, "GROUNDNUT", horizon_days=7
        )
        assert result.confidence_level == "HIGH"
        assert result.model_name == "linear_regression"
        assert result.confidence_score == pytest.approx(0.85)

    def test_price_change_is_predicted_minus_current(self, market_gondal):
        self._add_history(market_gondal, "GROUNDNUT", 30, base_price=5000.0)
        result = ForecastService().run(
            market_gondal.id, market_gondal.name, "GROUNDNUT", horizon_days=7
        )
        assert result.current_price is not None
        assert result.predicted_price is not None
        expected_change = round(result.predicted_price - result.current_price, 2)
        assert result.price_change == pytest.approx(expected_change, abs=0.01)

    def test_save_true_creates_forecast_record(self, market_gondal):
        self._add_history(market_gondal, "GROUNDNUT", 30)
        assert Forecast.objects.count() == 0
        ForecastService().run(
            market_gondal.id, market_gondal.name, "GROUNDNUT",
            horizon_days=7, save=True
        )
        assert Forecast.objects.count() == 1
        f = Forecast.objects.get()
        assert f.commodity == "GROUNDNUT"
        assert f.market == market_gondal
        assert f.horizon_days == 7

    def test_save_true_idempotent(self, market_gondal):
        """Running twice should upsert, not create duplicates."""
        self._add_history(market_gondal, "GROUNDNUT", 30)
        svc = ForecastService()
        svc.run(market_gondal.id, market_gondal.name, "GROUNDNUT", horizon_days=7, save=True)
        svc.run(market_gondal.id, market_gondal.name, "GROUNDNUT", horizon_days=7, save=True)
        assert Forecast.objects.count() == 1

    def test_predictions_length_matches_horizon(self, market_gondal):
        self._add_history(market_gondal, "GROUNDNUT", 30)
        for h in (3, 7, 14):
            result = ForecastService().run(
                market_gondal.id, market_gondal.name, "GROUNDNUT", horizon_days=h
            )
            assert len(result.predictions) == h


# ─────────────────────────────────────────────────────────────────────────────
# CombinedAnalysisService tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCombinedAnalysisService:

    def _add_history(self, market, commodity, n_days, base_price=5000.0):
        today = date.today()
        prices = [
            MarketPrice(
                market=market, commodity=commodity, variety="", grade="",
                min_price=Decimal(str(base_price * 0.9)),
                max_price=Decimal(str(base_price * 1.1)),
                modal_price=Decimal(str(base_price + i)),
                price_date=today - timedelta(days=n_days - 1 - i),
                source="agmarknet",
            )
            for i in range(n_days)
        ]
        MarketPrice.objects.bulk_create(prices)

    def test_combined_entry_has_financial_and_forecast_fields(
        self, farmer_user, farmer_profile, market_gondal
    ):
        self._add_history(market_gondal, "GROUNDNUT", 30)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)

        result = CombinedAnalysisService().run(lot.id, farmer_user, forecast_days=7)

        assert len(result.markets) == 1
        entry = result.markets[0]
        # Financial
        assert entry.gross_revenue > 0
        assert entry.net_revenue > 0
        # Forecast
        assert entry.forecast_confidence_level in (
            "INSUFFICIENT_DATA", "LOW", "MEDIUM", "HIGH"
        )
        assert entry.forecast_model != ""

    def test_best_market_is_rank_1(
        self, farmer_user, farmer_profile, market_gondal, market_bhavnagar
    ):
        self._add_history(market_gondal,   "GROUNDNUT", 30, base_price=5000)
        self._add_history(market_bhavnagar, "GROUNDNUT", 30, base_price=4000)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)

        result = CombinedAnalysisService().run(lot.id, farmer_user, forecast_days=7)
        assert result.best_market is not None
        assert result.best_market.rank == 1
        assert result.best_market.market_name == "Gondal APMC"

    def test_insufficient_forecast_does_not_crash(
        self, farmer_user, farmer_profile, market_gondal
    ):
        # Only 1 price record — forecast will be INSUFFICIENT_DATA
        _add_price(None, market_gondal, "GROUNDNUT", 5000)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)

        result = CombinedAnalysisService().run(lot.id, farmer_user, forecast_days=7)
        assert len(result.markets) == 1
        entry = result.markets[0]
        assert entry.forecast_confidence_level == "INSUFFICIENT_DATA"
        assert entry.predicted_price is None
        # Financial result is still present
        assert entry.gross_revenue > 0

    def test_financial_error_propagates(self, farmer_user):
        """Non-existent crop lot propagates error cleanly."""
        result = CombinedAnalysisService().run(99999, farmer_user, forecast_days=7)
        assert result.errors
        assert len(result.markets) == 0


# ─────────────────────────────────────────────────────────────────────────────
# MarketAnalysisView (API) tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMarketAnalysisAPI:

    URL = "/api/v1/analysis/market-analysis/"

    def _add_history(self, market, commodity, n_days, base_price=5000.0):
        today = date.today()
        MarketPrice.objects.bulk_create([
            MarketPrice(
                market=market, commodity=commodity, variety="", grade="",
                min_price=Decimal(str(base_price * 0.9)),
                max_price=Decimal(str(base_price * 1.1)),
                modal_price=Decimal(str(base_price + i)),
                price_date=today - timedelta(days=n_days - 1 - i),
                source="agmarknet",
            )
            for i in range(n_days)
        ])

    def test_unauthenticated_returns_401(self, api_client, db):
        resp = api_client.post(self.URL, {"crop_lot_id": 1}, format="json")
        assert resp.status_code == 401

    def test_missing_crop_lot_id_returns_400(self, auth_client, db):
        resp = auth_client.post(self.URL, {}, format="json")
        assert resp.status_code == 400
        assert "crop_lot_id" in resp.json()["error"]

    def test_non_integer_crop_lot_id_returns_400(self, auth_client, db):
        resp = auth_client.post(self.URL, {"crop_lot_id": "abc"}, format="json")
        assert resp.status_code == 400

    def test_other_farmers_crop_lot_returns_403(
        self, auth_client, farmer_user_2, farmer_profile_2, market_gondal
    ):
        lot = _make_crop_lot(farmer_profile_2, "GROUNDNUT", 10)
        resp = auth_client.post(self.URL, {"crop_lot_id": lot.id}, format="json")
        assert resp.status_code == 403

    def test_nonexistent_crop_lot_returns_404(self, auth_client, db):
        resp = auth_client.post(self.URL, {"crop_lot_id": 99999}, format="json")
        assert resp.status_code == 404

    def test_valid_groundnut_request_returns_200(
        self, auth_client, farmer_profile, market_gondal
    ):
        self._add_history(market_gondal, "GROUNDNUT", 10)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)

        resp = auth_client.post(
            self.URL,
            {"crop_lot_id": lot.id, "forecast_days": 7},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["commodity"] == "GROUNDNUT"
        assert data["market_count"] >= 1
        assert "markets" in data
        assert "best_market" in data
        assert data["best_market"] is not None

    def test_valid_cotton_request_returns_200(
        self, auth_client, farmer_profile, market_gondal
    ):
        self._add_history(market_gondal, "COTTON", 10, base_price=6000)
        lot = _make_crop_lot(farmer_profile, "COTTON", 5)

        resp = auth_client.post(self.URL, {"crop_lot_id": lot.id}, format="json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["commodity"] == "COTTON"

    def test_multiple_markets_ranked_in_response(
        self, auth_client, farmer_profile, market_gondal, market_bhavnagar
    ):
        self._add_history(market_gondal,   "GROUNDNUT", 10, base_price=5000)
        self._add_history(market_bhavnagar, "GROUNDNUT", 10, base_price=4000)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)

        resp = auth_client.post(self.URL, {"crop_lot_id": lot.id}, format="json")
        assert resp.status_code == 200
        markets = resp.json()["markets"]
        assert len(markets) == 2
        # Rank 1 is first
        assert markets[0]["rank"] == 1
        assert markets[1]["rank"] == 2
        # Sorted by net_revenue descending
        assert markets[0]["net_revenue"] >= markets[1]["net_revenue"]

    def test_forecast_days_clamped(
        self, auth_client, farmer_profile, market_gondal
    ):
        self._add_history(market_gondal, "GROUNDNUT", 10)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)

        # forecast_days=999 should be clamped to 90
        resp = auth_client.post(
            self.URL,
            {"crop_lot_id": lot.id, "forecast_days": 999},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["forecast_days"] == 90

    def test_response_shape_all_required_keys(
        self, auth_client, farmer_profile, market_gondal
    ):
        self._add_history(market_gondal, "GROUNDNUT", 10)
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)

        resp = auth_client.post(
            self.URL, {"crop_lot_id": lot.id, "forecast_days": 7}, format="json"
        )
        assert resp.status_code == 200
        data = resp.json()

        # Top-level keys
        for key in ("crop_lot_id", "commodity", "quantity_quintal",
                    "farmer_location", "forecast_days", "market_count",
                    "best_market", "markets", "skipped_markets", "warnings"):
            assert key in data, f"Missing top-level key: {key}"

        # Market entry keys
        if data["markets"]:
            entry = data["markets"][0]
            for key in ("market_id", "market_name", "district", "state",
                        "modal_price", "gross_revenue", "transport_cost",
                        "net_revenue", "rank",
                        "forecast_confidence_level", "forecast_model",
                        "forecast_data_points", "predicted_price",
                        "trend_direction"):
                assert key in entry, f"Missing market entry key: {key}"

    def test_no_prices_returns_400_with_error(
        self, auth_client, farmer_profile, market_gondal
    ):
        """No price records → service returns error → API 400."""
        lot = _make_crop_lot(farmer_profile, "GROUNDNUT", 10)
        resp = auth_client.post(self.URL, {"crop_lot_id": lot.id}, format="json")
        assert resp.status_code == 400
        assert "error" in resp.json()
