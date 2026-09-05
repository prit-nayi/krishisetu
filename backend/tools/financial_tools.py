"""
tools/financial_tools.py — Deterministic financial calculation tools.

All functions are pure Python — no Django ORM, no LLM calls.
Inputs are validated; errors are raised as ValueError.
Every function returns a plain dict for easy JSON serialisation.
"""


# ── Revenue ───────────────────────────────────────────────────────────────────

def calculate_market_revenue(modal_price: float, quantity_quintal: float) -> dict:
    """
    Calculate gross revenue from selling at a given modal price.

    Args:
        modal_price: Price per quintal in Rs.
        quantity_quintal: Quantity in quintals.

    Returns:
        {"gross_revenue": float, "modal_price": float, "quantity_quintal": float}
    """
    if modal_price < 0:
        raise ValueError("modal_price must be non-negative.")
    if quantity_quintal <= 0:
        raise ValueError("quantity_quintal must be greater than zero.")
    gross = float(modal_price) * float(quantity_quintal)
    return {"gross_revenue": gross, "modal_price": float(modal_price), "quantity_quintal": float(quantity_quintal)}


# ── Transport ─────────────────────────────────────────────────────────────────

def calculate_transport_cost(
    distance_km: float,
    quantity_quintal: float,
    rate_per_quintal_per_km: float = 0.5,
    fixed_cost: float = 200.0,
) -> dict:
    """
    Estimate transport cost using a simple linear model.

    Args:
        distance_km: Distance to market in km.
        quantity_quintal: Quantity in quintals.
        rate_per_quintal_per_km: Variable cost rate (Rs per quintal per km).
        fixed_cost: Fixed loading/unloading cost in Rs.

    Returns:
        {"total_transport_cost": float, "distance_km": float,
         "variable_cost": float, "fixed_cost": float, "cost_per_quintal": float}
    """
    if distance_km < 0:
        raise ValueError("distance_km must be non-negative.")
    if quantity_quintal <= 0:
        raise ValueError("quantity_quintal must be greater than zero.")
    variable = float(distance_km) * float(quantity_quintal) * float(rate_per_quintal_per_km)
    total    = variable + float(fixed_cost)
    return {
        "total_transport_cost": total,
        "distance_km": float(distance_km),
        "variable_cost": variable,
        "fixed_cost": float(fixed_cost),
        "cost_per_quintal": total / float(quantity_quintal),
    }


# ── Net value ─────────────────────────────────────────────────────────────────

def calculate_net_value(gross_revenue: float, transport_cost: float) -> dict:
    """
    Calculate net selling value after transport costs.

    Returns:
        {"net_value": float, "gross_revenue": float, "transport_cost": float}
    """
    net = float(gross_revenue) - float(transport_cost)
    return {"net_value": net, "gross_revenue": float(gross_revenue), "transport_cost": float(transport_cost)}


# ── Storage ───────────────────────────────────────────────────────────────────

STORAGE_RATES = {
    "farm":         0.10,  # Rs per quintal per day
    "warehouse":    0.60,
    "cold_storage": 1.20,
}


def calculate_storage_cost(storage_type: str, days: int, quantity_quintal: float) -> dict:
    """
    Calculate storage cost.

    Args:
        storage_type: "farm" | "warehouse" | "cold_storage"
        days: Number of days stored.
        quantity_quintal: Quantity in quintals.

    Returns:
        {"total_storage_cost": float, "daily_rate_per_quintal": float,
         "days": int, "quantity_quintal": float}
    """
    if storage_type not in STORAGE_RATES:
        raise ValueError(f"Unknown storage_type '{storage_type}'. Choose from: {list(STORAGE_RATES)}")
    if days < 0:
        raise ValueError("days must be non-negative.")
    if quantity_quintal <= 0:
        raise ValueError("quantity_quintal must be greater than zero.")
    rate  = STORAGE_RATES[storage_type]
    total = rate * int(days) * float(quantity_quintal)
    return {
        "total_storage_cost": total,
        "daily_rate_per_quintal": rate,
        "days": int(days),
        "quantity_quintal": float(quantity_quintal),
    }


# ── Capital / opportunity cost ────────────────────────────────────────────────

def calculate_capital_cost(
    current_net_value: float,
    holding_days: int,
    annual_interest_rate: float = 0.12,
) -> dict:
    """
    Calculate opportunity cost of holding crop (interest forgone).

    Returns:
        {"capital_cost": float, "annual_rate": float, "holding_days": int}
    """
    daily_rate   = annual_interest_rate / 365
    capital_cost = float(current_net_value) * daily_rate * int(holding_days)
    return {"capital_cost": capital_cost, "annual_rate": annual_interest_rate, "holding_days": holding_days}


# ── Expected future value ─────────────────────────────────────────────────────

def calculate_expected_future_value(
    forecast_price: float,
    quantity_quintal: float,
    transport_cost: float,
    storage_cost: float,
    capital_cost: float = 0.0,
    quality_adjustment: float = 0.0,
) -> dict:
    """
    Calculate expected net value if holding until forecast horizon.

    Returns:
        {"expected_net_value": float, "gross_future_revenue": float,
         "total_deductions": float, "breakdown": dict}
    """
    gross       = float(forecast_price) * float(quantity_quintal)
    deductions  = float(transport_cost) + float(storage_cost) + float(capital_cost) + float(quality_adjustment)
    net         = gross - deductions
    return {
        "expected_net_value": net,
        "gross_future_revenue": gross,
        "total_deductions": deductions,
        "breakdown": {
            "transport_cost":     float(transport_cost),
            "storage_cost":       float(storage_cost),
            "capital_cost":       float(capital_cost),
            "quality_adjustment": float(quality_adjustment),
        },
    }


# ── SELL / HOLD / PARTIAL SELL ────────────────────────────────────────────────

def recommend_sell_or_hold(
    current_net_value: float,
    expected_future_net_value: float,
    threshold_pct: float = 5.0,
) -> dict:
    """
    Deterministic SELL/HOLD/PARTIAL_SELL recommendation.

    Decision logic:
        future > current * (1 + threshold/100)  → HOLD
        future < current * (1 - threshold/100)  → SELL_NOW
        otherwise                                → PARTIAL_SELL

    Args:
        current_net_value: Net value if selling today.
        expected_future_net_value: Net value if holding until forecast horizon.
        threshold_pct: Minimum % improvement to recommend HOLD (default 5%).

    Returns:
        {"recommendation": str, "margin": float, "margin_pct": float,
         "current_net_value": float, "expected_future_net_value": float,
         "threshold_pct": float}
    """
    if current_net_value <= 0:
        raise ValueError("current_net_value must be positive.")
    current  = float(current_net_value)
    future   = float(expected_future_net_value)
    margin   = future - current
    margin_pct = (margin / current) * 100

    upper = current * (1 + threshold_pct / 100)
    lower = current * (1 - threshold_pct / 100)

    if future >= upper:
        action = "HOLD"
    elif future <= lower:
        action = "SELL_NOW"
    else:
        action = "PARTIAL_SELL"

    return {
        "recommendation": action,
        "margin": margin,
        "margin_pct": round(margin_pct, 2),
        "current_net_value": current,
        "expected_future_net_value": future,
        "threshold_pct": threshold_pct,
    }


# ── Partial sell strategy ────────────────────────────────────────────────────

def calculate_partial_sell_strategy(
    quantity_quintal: float,
    current_net_value: float,
    expected_future_net_value: float,
    sell_fraction: float = 0.5,
) -> dict:
    """
    Calculate a partial sell strategy.

    Args:
        quantity_quintal: Total quantity in quintals.
        current_net_value: Current net value for full lot.
        expected_future_net_value: Expected future net value for full lot.
        sell_fraction: Fraction to sell now (default 0.5 = 50%).

    Returns:
        {"sell_now_quantity_quintal": float, "hold_quantity_quintal": float,
         "sell_now_value": float, "hold_expected_value": float, "rationale": str}
    """
    if not (0 < sell_fraction < 1):
        raise ValueError("sell_fraction must be between 0 and 1 (exclusive).")
    if quantity_quintal <= 0:
        raise ValueError("quantity_quintal must be greater than zero.")

    sell_qty  = float(quantity_quintal) * sell_fraction
    hold_qty  = float(quantity_quintal) * (1 - sell_fraction)
    sell_val  = float(current_net_value)  * sell_fraction
    hold_val  = float(expected_future_net_value) * (1 - sell_fraction)

    return {
        "sell_now_quantity_quintal": sell_qty,
        "hold_quantity_quintal": hold_qty,
        "sell_now_value": sell_val,
        "hold_expected_value": hold_val,
        "rationale": (
            f"Sell {sell_fraction * 100:.0f}% now to secure ₹{sell_val:,.0f}, "
            f"hold {(1 - sell_fraction) * 100:.0f}% for expected ₹{hold_val:,.0f}."
        ),
    }
