"""
tools/market_tools.py — Deterministic market data tools.
"""
import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in km between two lat/lon coordinate pairs."""
    R = 6371
    phi1, phi2   = math.radians(lat1), math.radians(lat2)
    dphi         = math.radians(lat2 - lat1)
    dlambda      = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearest_markets(farmer_lat: float, farmer_lon: float, markets: list, radius_km: float = 100) -> list:
    """
    Filter and sort markets by distance from farmer location.

    Args:
        farmer_lat: Farmer latitude.
        farmer_lon: Farmer longitude.
        markets: List of dicts with keys: id, name, latitude, longitude.
        radius_km: Maximum radius to include.

    Returns:
        List of markets within radius, sorted by distance, each with added "distance_km".
    """
    results = []
    for m in markets:
        if m.get("latitude") is None or m.get("longitude") is None:
            continue
        dist = haversine_distance(farmer_lat, farmer_lon, float(m["latitude"]), float(m["longitude"]))
        if dist <= radius_km:
            entry = dict(m)
            entry["distance_km"] = round(dist, 1)
            results.append(entry)
    results.sort(key=lambda x: x["distance_km"])
    return results


def compare_market_prices(prices: list) -> list:
    """
    Rank markets by modal_price descending.

    Args:
        prices: List of dicts with keys: market_id, market_name, modal_price, distance_km (optional).

    Returns:
        Ranked list with added "rank" field.
    """
    if not prices:
        return []
    ranked = sorted(prices, key=lambda x: float(x.get("modal_price", 0)), reverse=True)
    for i, item in enumerate(ranked, start=1):
        item["rank"] = i
    return ranked


def calculate_price_change(price_history: list) -> dict:
    """
    Calculate percentage price change over the given price history.

    Args:
        price_history: List of dicts with "modal_price" field, ordered oldest → newest.

    Returns:
        {"change_pct": float, "trend": "up" | "down" | "flat",
         "first_price": float, "last_price": float}
    """
    if len(price_history) < 2:
        return {"change_pct": 0.0, "trend": "flat", "first_price": None, "last_price": None}

    first = float(price_history[0]["modal_price"])
    last  = float(price_history[-1]["modal_price"])
    if first == 0:
        return {"change_pct": 0.0, "trend": "flat", "first_price": first, "last_price": last}

    change_pct = ((last - first) / first) * 100
    trend = "up" if change_pct > 1 else ("down" if change_pct < -1 else "flat")
    return {"change_pct": round(change_pct, 2), "trend": trend, "first_price": first, "last_price": last}
