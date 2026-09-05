"""
tests/test_financial_tools.py — Unit tests for deterministic financial tools.
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.financial_tools import (
    calculate_market_revenue,
    calculate_transport_cost,
    calculate_net_value,
    calculate_storage_cost,
    calculate_capital_cost,
    calculate_expected_future_value,
    recommend_sell_or_hold,
    calculate_partial_sell_strategy,
)


class TestCalculateMarketRevenue:
    def test_basic(self):
        result = calculate_market_revenue(modal_price=5800, quantity_quintal=40)
        assert result["gross_revenue"] == 232000.0

    def test_negative_price_raises(self):
        with pytest.raises(ValueError):
            calculate_market_revenue(modal_price=-100, quantity_quintal=40)

    def test_zero_quantity_raises(self):
        with pytest.raises(ValueError):
            calculate_market_revenue(modal_price=5800, quantity_quintal=0)


class TestCalculateTransportCost:
    def test_basic(self):
        result = calculate_transport_cost(distance_km=30, quantity_quintal=40)
        assert result["total_transport_cost"] == pytest.approx(800.0)

    def test_zero_distance(self):
        result = calculate_transport_cost(distance_km=0, quantity_quintal=40)
        assert result["total_transport_cost"] == 200.0

    def test_negative_distance_raises(self):
        with pytest.raises(ValueError):
            calculate_transport_cost(distance_km=-5, quantity_quintal=40)


class TestCalculateNetValue:
    def test_basic(self):
        result = calculate_net_value(gross_revenue=232000, transport_cost=800)
        assert result["net_value"] == 231200.0


class TestCalculateStorageCost:
    def test_farm_storage(self):
        result = calculate_storage_cost("farm", days=14, quantity_quintal=40)
        assert result["total_storage_cost"] == pytest.approx(56.0)

    def test_warehouse_storage(self):
        result = calculate_storage_cost("warehouse", days=14, quantity_quintal=40)
        assert result["total_storage_cost"] == pytest.approx(336.0)

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            calculate_storage_cost("refrigerator", days=14, quantity_quintal=40)


class TestRecommendSellOrHold:
    def test_hold_when_future_much_better(self):
        result = recommend_sell_or_hold(100000, 115000, threshold_pct=5.0)
        assert result["recommendation"] == "HOLD"

    def test_sell_when_future_much_worse(self):
        result = recommend_sell_or_hold(100000, 85000, threshold_pct=5.0)
        assert result["recommendation"] == "SELL_NOW"

    def test_partial_sell_in_middle(self):
        result = recommend_sell_or_hold(100000, 102000, threshold_pct=5.0)
        assert result["recommendation"] == "PARTIAL_SELL"

    def test_same_inputs_same_output(self):
        r1 = recommend_sell_or_hold(100000, 108000, 5.0)
        r2 = recommend_sell_or_hold(100000, 108000, 5.0)
        assert r1 == r2

    def test_zero_current_value_raises(self):
        with pytest.raises(ValueError):
            recommend_sell_or_hold(0, 100000)


class TestCalculatePartialSellStrategy:
    def test_basic(self):
        result = calculate_partial_sell_strategy(40, 200000, 220000, sell_fraction=0.5)
        assert result["sell_now_quantity_quintal"] == 20.0
        assert result["hold_quantity_quintal"] == 20.0

    def test_invalid_fraction_raises(self):
        with pytest.raises(ValueError):
            calculate_partial_sell_strategy(40, 200000, 220000, sell_fraction=1.0)
