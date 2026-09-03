"""
tools/market_tools.py
Deterministic market data tools for KrishiLink AI.
"""
import math
from datetime import date, timedelta
from typing import Optional


def get_nearest_markets_by_distance(
    farmer_lat: float,
    farmer_lon: float,
    markets: list,
    radius_km: float = 100.0,
    top_n: int = 5,
) -> list:
    """
    Return the nearest markets sorted by Haversine distance.

    Args:
        farmer_lat: Farmer latitude.
        farmer_lon: Farmer longitude.
        markets: List of dicts with keys: id, name, district, latitude, longitude.
        radius_km: Maximum search radius.
        top_n: Maximum number of results.

    Returns:
        List of market dicts with 'distance_km' added, sorted ascending.
    """
    results = []
    for market in markets:
        if not market.get("latitude") or not market.get("longitude"):
            continue
        dist = _haversine(
            farmer_lat, farmer_lon,
            float(market["latitude"]), float(market["longitude"])
        )
        if dist <= radius_km:
            entry = dict(market)
            entry["distance_km"] = round(dist, 1)
            results.append(entry)

    results.sort(key=lambda x: x["distance_km"])
    return results[:top_n]


def compare_market_prices(
    markets_with_prices: list,
    quantity_quintal: float,
    farmer_lat: float,
    farmer_lon: float,
) -> list:
    """
    Compare markets by net value (after transport cost).

    Args:
        markets_with_prices: List of dicts:
            {id, name, district, latitude, longitude, modal_price, distance_km}
        quantity_quintal: Quantity to sell in quintals.
        farmer_lat, farmer_lon: Farmer's coordinates.

    Returns:
        List sorted by net_value descending, with transport_cost and net_value added.
    """
    from tools.financial_tools import (
        calculate_transport_cost,
        calculate_market_revenue,
        calculate_net_value,
    )

    results = []
    for market in markets_with_prices:
        distance_km = market.get("distance_km", 0)
        modal_price = float(market.get("modal_price", 0))

        transport = calculate_transport_cost(distance_km, quantity_quintal)
        revenue = calculate_market_revenue(modal_price, quantity_quintal)
        net = calculate_net_value(revenue["gross_revenue"], transport["total_transport_cost"])

        entry = dict(market)
        entry["transport_cost"] = transport["total_transport_cost"]
        entry["gross_revenue"] = revenue["gross_revenue"]
        entry["net_value"] = net["net_value"]
        entry["net_per_quintal"] = round(net["net_value"] / quantity_quintal, 2)
        results.append(entry)

    results.sort(key=lambda x: x["net_value"], reverse=True)
    return results


def calculate_price_change(prices: list) -> dict:
    """
    Calculate price change over a price history list.

    Args:
        prices: List of dicts with 'modal_price' and 'price_date', sorted ascending.

    Returns:
        dict with change_pct and trend_direction.
    """
    if len(prices) < 2:
        return {
            "change_pct": 0.0,
            "trend_direction": "insufficient_data",
            "oldest_price": None,
            "latest_price": None,
        }

    oldest = float(prices[0]["modal_price"])
    latest = float(prices[-1]["modal_price"])

    change_pct = ((latest - oldest) / oldest) * 100 if oldest > 0 else 0.0

    if change_pct > 2:
        trend = "upward"
    elif change_pct < -2:
        trend = "downward"
    else:
        trend = "stable"

    return {
        "change_pct": round(change_pct, 2),
        "trend_direction": trend,
        "oldest_price": round(oldest, 2),
        "latest_price": round(latest, 2),
    }


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
