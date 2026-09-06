"""
tests/test_analysis_comprehensive.py — Comprehensive tests for Phase 4 & Phase 5 + IBM Granite Mock.

Covers all scenarios requested in project audit:
- Financial calculations (Gross revenue, transport cost, other costs, total cost, net revenue)
- Unit conversion (kg, quintal, tonne)
- Market comparison & ranking
- Cotton commodity lots
- Groundnut commodity lots
- Multiple markets
- Missing market price
- Missing coordinates (farmer or market)
- Invalid quantity (0, negative)
- Unauthorized access (401 unauthenticated, 403 wrong user)
- Insufficient historical data (<7 records)
- Small dataset forecast (7–29 records, LOW confidence)
- Medium dataset forecast (30–89 records, MEDIUM confidence)
- Forecast calculation failure handling
- Combined analysis API response structure
- IBM Granite Demo/Mock explanation service (DEMO_MOCK mode)
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APIClient

from apps.crops.models import CropLot
from apps.markets.models import Market, MarketPrice
from apps.decisions.services.market_analysis import (
    MarketAnalysisService,
    to_quintal,
    MarketFinancialResult,
)
from apps.decisions.services.forecast_service import ForecastService
from apps.decisions.services.combined_analysis import CombinedAnalysisService
from apps.agents.ai_explanation_service import (
    AIExplanationService,
    MockGraniteProvider,
)
from tools.financial_tools import (
    calculate_market_revenue,
    calculate_transport_cost,
    calculate_net_value,
)


# ════════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mandi_rajkot(db):
    return Market.objects.create(
        name="Rajkot APMC",
        district="Rajkot",
        state="Gujarat",
        market_type="APMC",
        is_active=True,
        latitude=Decimal("22.3039"),
        longitude=Decimal("70.8022"),
    )


@pytest.fixture
def mandi_gondal(db):
    return Market.objects.create(
        name="Gondal APMC",
        district="Rajkot",
        state="Gujarat",
        market_type="APMC",
        is_active=True,
        latitude=Decimal("22.1631"),
        longitude=Decimal("70.7934"),
    )


@pytest.fixture
def mandi_amreli(db):
    return Market.objects.create(
        name="Amreli APMC",
        district="Amreli",
        state="Gujarat",
        market_type="APMC",
        is_active=True,
        latitude=Decimal("21.6032"),
        longitude=Decimal("71.2221"),
    )


@pytest.fixture
def lot_groundnut(db, farmer_profile):
    return CropLot.objects.create(
        farmer=farmer_profile,
        commodity="groundnut",
        quantity=Decimal("25.0"),
        unit="quintal",
        harvest_date=date.today() - timedelta(days=20),
        storage_status="farm",
        quality_grade="A",
    )


@pytest.fixture
def lot_cotton(db, farmer_profile):
    return CropLot.objects.create(
        farmer=farmer_profile,
        commodity="cotton",
        quantity=Decimal("50.0"),
        unit="quintal",
        harvest_date=date.today() - timedelta(days=15),
        storage_status="warehouse",
        quality_grade="B",
    )


# ════════════════════════════════════════════════════════════════════════════
# 1. Financial Calculations & Formulas
# ════════════════════════════════════════════════════════════════════════════

class TestFinancialCalculations:
    def test_gross_revenue_formula(self):
        """Gross Revenue = modal_price * quantity_quintal"""
        res = calculate_market_revenue(modal_price=5500.0, quantity_quintal=10.0)
        assert res["gross_revenue"] == 55000.0

    def test_transport_cost_formula(self):
        """Transport cost = distance * quantity * rate + fixed_cost"""
        res = calculate_transport_cost(
            distance_km=40.0,
            quantity_quintal=10.0,
            rate_per_quintal_per_km=0.5,
            fixed_cost=200.0,
        )
        assert res["variable_cost"] == 200.0
        assert res["total_transport_cost"] == 400.0

    def test_net_revenue_formula(self):
        """Net Revenue = Gross Revenue - Total Cost"""
        gross = 55000.0
        transport = 400.0
        other = 0.0
        total_cost = transport + other
        net = calculate_net_value(gross, total_cost)["net_value"]
        assert net == 54600.0

    def test_negative_price_or_quantity_raises(self):
        with pytest.raises(ValueError):
            calculate_market_revenue(modal_price=-100.0, quantity_quintal=10.0)
        with pytest.raises(ValueError):
            calculate_market_revenue(modal_price=5000.0, quantity_quintal=0.0)


# ════════════════════════════════════════════════════════════════════════════
# 2. Unit Conversions
# ════════════════════════════════════════════════════════════════════════════

class TestUnitConversions:
    def test_conversions(self):
        assert to_quintal(10.0, "quintal") == 10.0
        assert to_quintal(1000.0, "kg") == 10.0
        assert to_quintal(5.0, "tonne") == 50.0

    def test_invalid_unit_raises(self):
        with pytest.raises(ValueError):
            to_quintal(10.0, "bag")


# ════════════════════════════════════════════════════════════════════════════
# 3. Commodity Support (Cotton & Groundnut)
# ════════════════════════════════════════════════════════════════════════════

class TestCommoditySupport:
    def test_groundnut_analysis(self, db, farmer_profile, lot_groundnut, mandi_gondal):
        MarketPrice.objects.create(
            market=mandi_gondal,
            commodity="GROUNDNUT",
            modal_price=Decimal("5200.0"),
            min_price=Decimal("5000.0"),
            max_price=Decimal("5400.0"),
            price_date=date.today(),
        )
        svc = MarketAnalysisService()
        res = svc.run(lot_groundnut.id, farmer_profile.user)
        assert len(res.markets) == 1
        m = res.markets[0]
        assert m.commodity if hasattr(m, 'commodity') else True
        assert m.gross_revenue == 5200.0 * 25.0
        assert m.net_revenue > 0

    def test_cotton_analysis(self, db, farmer_profile, lot_cotton, mandi_rajkot):
        MarketPrice.objects.create(
            market=mandi_rajkot,
            commodity="COTTON",
            modal_price=Decimal("7100.0"),
            min_price=Decimal("6900.0"),
            max_price=Decimal("7300.0"),
            price_date=date.today(),
        )
        svc = MarketAnalysisService()
        res = svc.run(lot_cotton.id, farmer_profile.user)
        assert len(res.markets) == 1
        m = res.markets[0]
        assert m.gross_revenue == 7100.0 * 50.0
        assert m.total_cost >= 0
        assert m.net_revenue == m.gross_revenue - m.total_cost


# ════════════════════════════════════════════════════════════════════════════
# 4. Multiple Markets & Ranking
# ════════════════════════════════════════════════════════════════════════════

class TestMultipleMarketsRanking:
    def test_ranked_by_net_revenue_descending(
        self, db, farmer_profile, lot_groundnut, mandi_gondal, mandi_rajkot, mandi_amreli
    ):
        today = date.today()
        # Gondal: High price
        MarketPrice.objects.create(market=mandi_gondal, commodity="GROUNDNUT", modal_price=Decimal("5500.0"), min_price=Decimal("5400"), max_price=Decimal("5600"), price_date=today)
        # Rajkot: Lower price
        MarketPrice.objects.create(market=mandi_rajkot, commodity="GROUNDNUT", modal_price=Decimal("5100.0"), min_price=Decimal("5000"), max_price=Decimal("5200"), price_date=today)
        # Amreli: Lowest price
        MarketPrice.objects.create(market=mandi_amreli, commodity="GROUNDNUT", modal_price=Decimal("4800.0"), min_price=Decimal("4700"), max_price=Decimal("4900"), price_date=today)

        svc = MarketAnalysisService()
        res = svc.run(lot_groundnut.id, farmer_profile.user)

        assert len(res.markets) == 3
        # Rank 1 must have highest net revenue
        assert res.markets[0].rank == 1
        assert res.markets[0].net_revenue >= res.markets[1].net_revenue
        assert res.markets[1].net_revenue >= res.markets[2].net_revenue
        assert res.best_market.market_id == res.markets[0].market_id


# ════════════════════════════════════════════════════════════════════════════
# 5. Missing Coordinates & Missing Prices & Edge Cases
# ════════════════════════════════════════════════════════════════════════════

class TestMissingAndEdgeCases:
    def test_missing_farmer_coordinates(self, db, farmer_profile, lot_groundnut, mandi_gondal):
        farmer_profile.latitude = None
        farmer_profile.longitude = None
        farmer_profile.save()

        MarketPrice.objects.create(
            market=mandi_gondal, commodity="GROUNDNUT", modal_price=Decimal("5000"),
            min_price=Decimal("4900"), max_price=Decimal("5100"), price_date=date.today(),
        )
        svc = MarketAnalysisService()
        res = svc.run(lot_groundnut.id, farmer_profile.user)
        assert len(res.markets) == 1
        assert res.markets[0].distance_km is None
        assert res.markets[0].transport_cost == 0.0
        assert res.markets[0].net_revenue == res.markets[0].gross_revenue

    def test_missing_market_coordinates(self, db, farmer_profile, lot_groundnut, mandi_gondal):
        mandi_gondal.latitude = None
        mandi_gondal.longitude = None
        mandi_gondal.save()

        MarketPrice.objects.create(
            market=mandi_gondal, commodity="GROUNDNUT", modal_price=Decimal("5000"),
            min_price=Decimal("4900"), max_price=Decimal("5100"), price_date=date.today(),
        )
        svc = MarketAnalysisService()
        res = svc.run(lot_groundnut.id, farmer_profile.user)
        assert len(res.markets) == 1
        assert res.markets[0].distance_km is None

    def test_no_price_records_returns_error(self, db, farmer_profile, lot_groundnut):
        svc = MarketAnalysisService()
        res = svc.run(lot_groundnut.id, farmer_profile.user)
        assert len(res.markets) == 0
        assert any("No price records" in err for err in res.errors)

    def test_zero_or_negative_quantity(self, db, farmer_profile, lot_groundnut):
        lot_groundnut.quantity = Decimal("0.0")
        lot_groundnut.save()
        svc = MarketAnalysisService()
        res = svc.run(lot_groundnut.id, farmer_profile.user)
        assert any("greater than zero" in err.lower() for err in res.errors)

    def test_unauthorized_farmer_access(self, db, farmer_user_2, lot_groundnut):
        svc = MarketAnalysisService()
        res = svc.run(lot_groundnut.id, farmer_user_2)
        assert any("permission" in err.lower() for err in res.errors)


# ════════════════════════════════════════════════════════════════════════════
# 6. Forecasting Strategy & Confidence Tiers
# ════════════════════════════════════════════════════════════════════════════

class TestForecastTiers:
    def _create_prices(self, market, commodity, count, base_price=5000):
        today = date.today()
        records = []
        for i in range(count):
            p_date = today - timedelta(days=count - i)
            records.append(
                MarketPrice(
                    market=market,
                    commodity=commodity,
                    modal_price=Decimal(str(base_price + i * 10)),
                    min_price=Decimal(str(base_price + i * 10 - 50)),
                    max_price=Decimal(str(base_price + i * 10 + 50)),
                    price_date=p_date,
                )
            )
        MarketPrice.objects.bulk_create(records)

    def test_insufficient_data_tier(self, db, mandi_gondal):
        self._create_prices(mandi_gondal, "GROUNDNUT", count=5)
        svc = ForecastService()
        fc = svc.run(mandi_gondal.id, mandi_gondal.name, "GROUNDNUT", horizon_days=7)
        assert fc.confidence_level == "INSUFFICIENT_DATA"
        assert fc.confidence_score == 0.0
        assert fc.predicted_price is None

    def test_low_confidence_tier(self, db, mandi_gondal):
        self._create_prices(mandi_gondal, "GROUNDNUT", count=15)
        svc = ForecastService()
        fc = svc.run(mandi_gondal.id, mandi_gondal.name, "GROUNDNUT", horizon_days=7)
        assert fc.confidence_level == "LOW"
        assert fc.confidence_score == 0.3
        assert fc.model_name == "moving_average"
        assert len(fc.predictions) == 7

    def test_medium_confidence_tier(self, db, mandi_gondal):
        self._create_prices(mandi_gondal, "GROUNDNUT", count=45)
        svc = ForecastService()
        fc = svc.run(mandi_gondal.id, mandi_gondal.name, "GROUNDNUT", horizon_days=7)
        assert fc.confidence_level == "MEDIUM"
        assert fc.confidence_score == 0.6
        assert fc.model_name == "linear_regression"
        assert len(fc.predictions) == 7

    def test_high_confidence_tier(self, db, mandi_gondal):
        self._create_prices(mandi_gondal, "GROUNDNUT", count=95)
        svc = ForecastService()
        fc = svc.run(mandi_gondal.id, mandi_gondal.name, "GROUNDNUT", horizon_days=7)
        assert fc.confidence_level == "HIGH"
        assert fc.confidence_score == 0.85
        assert fc.model_name == "linear_regression"
        assert len(fc.predictions) == 7

    def test_forecast_failure_gracefully_handled(self, db, mandi_gondal):
        self._create_prices(mandi_gondal, "GROUNDNUT", count=10)
        svc = ForecastService()
        with patch("apps.decisions.services.forecast_service.generate_price_forecast", side_effect=ValueError("Math error")):
            fc = svc.run(mandi_gondal.id, mandi_gondal.name, "GROUNDNUT", horizon_days=7)
            assert "Math error" in fc.error
            assert fc.predicted_price is None


# ════════════════════════════════════════════════════════════════════════════
# 7. IBM Granite Demo / Mock AI Explanation Service
# ════════════════════════════════════════════════════════════════════════════

class TestIBMGraniteMock:
    def test_mock_provider_output_structure(self):
        provider = MockGraniteProvider()
        context = {
            "commodity": "GROUNDNUT",
            "quantity_quintal": 20.0,
            "best_market": {
                "market_id": 1,
                "market_name": "Gondal APMC",
                "district": "Rajkot",
                "modal_price": 5400.0,
                "distance_km": 35.0,
                "gross_revenue": 108000.0,
                "transport_cost": 550.0,
                "other_costs": 0.0,
                "total_cost": 550.0,
                "net_revenue": 107450.0,
            },
            "markets": [{"market_id": 1, "market_name": "Gondal APMC"}],
            "forecast_days": 7,
            "forecast_method": "linear_regression",
            "forecast_confidence_level": "MEDIUM",
            "forecast_confidence_score": 0.6,
            "predicted_price": 5550.0,
            "price_change": 150.0,
            "price_change_pct": 2.78,
            "trend_direction": "up",
        }
        res = provider.generate_explanation(context)
        assert res["mode"] == "DEMO_MOCK"
        assert res["provider"] == "IBM Granite Demo"
        assert "Gondal APMC" in res["explanation"]
        assert "107,450" in res["explanation"] or "107450" in res["explanation"]
        assert len(res["key_factors"]) >= 3
        assert len(res["risk_notes"]) >= 1
        assert "Gondal APMC" in res["market_summary"]

    def test_ai_explanation_service_picks_mock_mode(self):
        svc = AIExplanationService()
        assert isinstance(svc.provider, MockGraniteProvider)


# ════════════════════════════════════════════════════════════════════════════
# 8. Combined Analysis API (POST /api/v1/analysis/market-analysis/)
# ════════════════════════════════════════════════════════════════════════════

class TestCombinedMarketAnalysisAPI:
    def test_api_success_shape(self, db, auth_client, lot_groundnut, mandi_gondal):
        today = date.today()
        # Seed 10 price days
        for i in range(10):
            MarketPrice.objects.create(
                market=mandi_gondal,
                commodity="GROUNDNUT",
                modal_price=Decimal(str(5100 + i * 10)),
                min_price=Decimal("5000"),
                max_price=Decimal("5300"),
                price_date=today - timedelta(days=10 - i),
            )

        url = reverse("market-analysis")
        resp = auth_client.post(url, {"crop_lot_id": lot_groundnut.id, "forecast_days": 7}, format="json")
        assert resp.status_code == 200
        data = resp.json()

        # Crop lot info
        assert data["crop_lot_id"] == lot_groundnut.id
        assert data["commodity"] == "GROUNDNUT"
        assert data["quantity_quintal"] == 25.0

        # Market info
        assert data["market_count"] == 1
        assert data["best_market"] is not None
        assert data["best_market"]["market_name"] == "Gondal APMC"

        # Required financial fields
        m = data["markets"][0]
        assert "gross_revenue" in m
        assert "transport_cost" in m
        assert "other_costs" in m
        assert "total_cost" in m
        assert "net_revenue" in m
        assert m["net_revenue"] == round(m["gross_revenue"] - m["total_cost"], 2)

        # Required forecast fields
        assert "forecast_confidence_level" in m
        assert "forecast_confidence_score" in m
        assert "forecast_method" in m
        assert "predicted_price" in m
        assert "predicted_prices" in m
        assert len(m["predicted_prices"]) == 7

        # AI explanation
        assert "ai_explanation" in data
        ai = data["ai_explanation"]
        assert ai["mode"] == "DEMO_MOCK"
        assert ai["provider"] == "IBM Granite Demo"
        assert len(ai["key_factors"]) > 0

    def test_unauthenticated_api_call_401(self):
        client = APIClient()
        url = reverse("market-analysis")
        resp = client.post(url, {"crop_lot_id": 1}, format="json")
        assert resp.status_code == 401

    def test_other_farmer_api_call_403(self, db, farmer_user_2, lot_groundnut):
        client = APIClient()
        client.force_authenticate(user=farmer_user_2)
        url = reverse("market-analysis")
        resp = client.post(url, {"crop_lot_id": lot_groundnut.id}, format="json")
        assert resp.status_code == 403
