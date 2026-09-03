"""
tools/financial_tools.py
Deterministic financial calculation tools for KrishiLink AI.
All calculations use plain Python arithmetic — never LLM-generated code.
"""
from decimal import Decimal
from typing import Optional


def calculate_market_revenue(modal_price: float, quantity_quintal: float) -> dict:
    """
    Calculate gross revenue for selling a crop lot at a given market.

    Args:
        modal_price: Modal price in Rs/quintal.
        quantity_quintal: Quantity in quintals.

    Returns:
        dict with gross_revenue (Rs).
    """
    if modal_price < 0:
        raise ValueError("modal_price cannot be negative.")
    if quantity_quintal <= 0:
        raise ValueError("quantity_quintal must be greater than zero.")

    gross = modal_price * quantity_quintal
    return {
        "modal_price_per_quintal": round(modal_price, 2),
        "quantity_quintal": round(quantity_quintal, 2),
        "gross_revenue": round(gross, 2),
    }


def calculate_transport_cost(
    distance_km: float,
    quantity_quintal: float,
    rate_per_quintal_per_km: float = 0.5,
    fixed_cost: float = 200.0,
) -> dict:
    """
    Estimate transport cost from farm to market.

    Args:
        distance_km: Distance to market in km.
        quantity_quintal: Quantity in quintals.
        rate_per_quintal_per_km: Variable rate (default ₹0.50/quintal/km).
        fixed_cost: Fixed loading/unloading cost (default ₹200).

    Returns:
        dict with cost breakdown.
    """
    if distance_km < 0:
        raise ValueError("distance_km cannot be negative.")
    if quantity_quintal <= 0:
        raise ValueError("quantity_quintal must be greater than zero.")

    variable_cost = distance_km * quantity_quintal * rate_per_quintal_per_km
    total_cost = variable_cost + fixed_cost
    cost_per_quintal = total_cost / quantity_quintal

    return {
        "distance_km": round(distance_km, 1),
        "quantity_quintal": round(quantity_quintal, 2),
        "variable_cost": round(variable_cost, 2),
        "fixed_cost": round(fixed_cost, 2),
        "total_transport_cost": round(total_cost, 2),
        "cost_per_quintal": round(cost_per_quintal, 2),
    }


def calculate_net_value(gross_revenue: float, transport_cost: float) -> dict:
    """
    Calculate net selling value after transport costs.

    Args:
        gross_revenue: Gross revenue (Rs).
        transport_cost: Total transport cost (Rs).

    Returns:
        dict with net_value.
    """
    net = gross_revenue - transport_cost
    return {
        "gross_revenue": round(gross_revenue, 2),
        "transport_cost": round(transport_cost, 2),
        "net_value": round(net, 2),
    }


def calculate_storage_cost(
    storage_type: str,
    days: int,
    quantity_quintal: float,
) -> dict:
    """
    Calculate storage cost for holding a crop lot.

    Rates (Rs/quintal/day):
        farm: 0.10  (minimal — farmer's own premises)
        warehouse: 0.60
        cold_storage: 1.20

    Args:
        storage_type: 'farm' | 'warehouse' | 'cold_storage'
        days: Number of days to store.
        quantity_quintal: Quantity in quintals.

    Returns:
        dict with total_storage_cost.
    """
    RATES = {
        "farm": 0.10,
        "warehouse": 0.60,
        "cold_storage": 1.20,
    }
    if storage_type not in RATES:
        raise ValueError(f"Invalid storage_type '{storage_type}'. Choose from {list(RATES)}.")
    if days < 0:
        raise ValueError("days cannot be negative.")
    if quantity_quintal <= 0:
        raise ValueError("quantity_quintal must be greater than zero.")

    rate = RATES[storage_type]
    total_cost = rate * days * quantity_quintal

    return {
        "storage_type": storage_type,
        "days": days,
        "quantity_quintal": round(quantity_quintal, 2),
        "rate_per_quintal_per_day": rate,
        "total_storage_cost": round(total_cost, 2),
    }


def calculate_capital_cost(
    current_net_value: float,
    holding_days: int,
    annual_interest_rate: float = 0.12,
) -> dict:
    """
    Calculate opportunity/capital cost of holding the crop.

    Args:
        current_net_value: Current selling value (Rs).
        holding_days: Days of intended holding.
        annual_interest_rate: Annual rate (default 12%).

    Returns:
        dict with capital_cost.
    """
    if holding_days < 0:
        raise ValueError("holding_days cannot be negative.")
    daily_rate = annual_interest_rate / 365
    capital_cost = current_net_value * daily_rate * holding_days

    return {
        "current_net_value": round(current_net_value, 2),
        "holding_days": holding_days,
        "annual_interest_rate_pct": round(annual_interest_rate * 100, 2),
        "capital_cost": round(capital_cost, 2),
    }


def calculate_expected_future_value(
    forecasted_price: float,
    quantity_quintal: float,
    transport_cost: float,
    storage_cost: float,
    capital_cost: float,
    quality_loss_pct: float = 0.0,
) -> dict:
    """
    Calculate expected net value if the farmer holds and sells later.

    Args:
        forecasted_price: Predicted modal price (Rs/quintal).
        quantity_quintal: Quantity in quintals.
        transport_cost: Transport cost at future sale (Rs).
        storage_cost: Storage cost during holding period (Rs).
        capital_cost: Opportunity/capital cost (Rs).
        quality_loss_pct: Expected quality degradation (0–1, default 0).

    Returns:
        dict with expected_future_net_value and breakdown.
    """
    if quality_loss_pct < 0 or quality_loss_pct > 1:
        raise ValueError("quality_loss_pct must be between 0 and 1.")

    effective_quantity = quantity_quintal * (1 - quality_loss_pct)
    gross_future = forecasted_price * effective_quantity
    total_holding_cost = transport_cost + storage_cost + capital_cost
    expected_net = gross_future - total_holding_cost

    return {
        "forecasted_price_per_quintal": round(forecasted_price, 2),
        "effective_quantity_quintal": round(effective_quantity, 2),
        "gross_future_revenue": round(gross_future, 2),
        "transport_cost": round(transport_cost, 2),
        "storage_cost": round(storage_cost, 2),
        "capital_cost": round(capital_cost, 2),
        "total_holding_cost": round(total_holding_cost, 2),
        "expected_future_net_value": round(expected_net, 2),
    }


def recommend_sell_or_hold(
    current_net_value: float,
    expected_future_net_value: float,
    threshold_pct: float = 5.0,
    risk_factor: float = 0.0,
) -> dict:
    """
    Produce a deterministic SELL_NOW / HOLD / PARTIAL_SELL recommendation.

    Decision logic:
        - If expected_future > current * (1 + threshold_pct/100): HOLD
        - If expected_future < current * (1 - threshold_pct/100): SELL_NOW
        - Otherwise: PARTIAL_SELL

    Args:
        current_net_value: Current net selling value (Rs).
        expected_future_net_value: Expected future net value (Rs).
        threshold_pct: Minimum gain % to recommend HOLD (default 5%).
        risk_factor: Additive risk adjustment (reduces expected future value).

    Returns:
        dict with recommendation, margin, and reasoning.
    """
    if current_net_value <= 0:
        raise ValueError("current_net_value must be positive.")

    adjusted_future = expected_future_net_value - risk_factor
    gain = adjusted_future - current_net_value
    gain_pct = (gain / current_net_value) * 100

    upper_threshold = current_net_value * (1 + threshold_pct / 100)
    lower_threshold = current_net_value * (1 - threshold_pct / 100)

    if adjusted_future >= upper_threshold:
        action = "HOLD"
    elif adjusted_future <= lower_threshold:
        action = "SELL_NOW"
    else:
        action = "PARTIAL_SELL"

    return {
        "recommendation": action,
        "current_net_value": round(current_net_value, 2),
        "expected_future_net_value": round(expected_future_net_value, 2),
        "adjusted_future_net_value": round(adjusted_future, 2),
        "gain_rs": round(gain, 2),
        "gain_pct": round(gain_pct, 2),
        "threshold_pct": threshold_pct,
        "risk_factor": round(risk_factor, 2),
        "reasoning": (
            f"Expected future net value ({adjusted_future:.0f}) is "
            f"{gain_pct:+.1f}% vs current net value ({current_net_value:.0f}). "
            f"Threshold: ±{threshold_pct}%."
        ),
    }


def calculate_partial_sell_strategy(
    quantity_quintal: float,
    current_net_value: float,
    expected_future_net_value: float,
    sell_fraction: float = 0.5,
) -> dict:
    """
    Calculate how much to sell now vs hold.

    Args:
        quantity_quintal: Total lot quantity in quintals.
        current_net_value: Current net selling value for full lot (Rs).
        expected_future_net_value: Expected net value for full lot if held (Rs).
        sell_fraction: Fraction to sell now (default 0.5 = 50%).

    Returns:
        dict with sell/hold quantities and projected values.
    """
    if not (0 < sell_fraction < 1):
        raise ValueError("sell_fraction must be between 0 and 1 (exclusive).")

    sell_qty = quantity_quintal * sell_fraction
    hold_qty = quantity_quintal * (1 - sell_fraction)

    sell_value = current_net_value * sell_fraction
    hold_value = expected_future_net_value * (1 - sell_fraction)
    total_projected = sell_value + hold_value

    return {
        "total_quantity_quintal": round(quantity_quintal, 2),
        "sell_now_quantity_quintal": round(sell_qty, 2),
        "hold_quantity_quintal": round(hold_qty, 2),
        "sell_fraction_pct": round(sell_fraction * 100, 1),
        "sell_now_value": round(sell_value, 2),
        "projected_hold_value": round(hold_value, 2),
        "total_projected_value": round(total_projected, 2),
        "vs_sell_all_now": round(total_projected - current_net_value, 2),
    }
