"""
tools/forecast_tools.py
Deterministic forecasting tools for KrishiLink AI.
Uses linear regression as baseline; SARIMAX added in Phase 5.
"""
import math
from typing import Optional


def calculate_price_trend(prices: list) -> dict:
    """
    Fit a simple linear regression on historical prices to determine trend.

    Args:
        prices: List of dicts with 'modal_price' (float), sorted chronologically.

    Returns:
        dict with slope, trend_direction, r_squared, data_points.
    """
    n = len(prices)
    if n < 3:
        return {
            "slope": 0.0,
            "trend_direction": "insufficient_data",
            "r_squared": 0.0,
            "data_points": n,
        }

    x = list(range(n))
    y = [float(p["modal_price"]) for p in prices]

    x_mean = sum(x) / n
    y_mean = sum(y) / n

    ss_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    ss_xx = sum((xi - x_mean) ** 2 for xi in x)
    ss_yy = sum((yi - y_mean) ** 2 for yi in y)

    slope = ss_xy / ss_xx if ss_xx > 0 else 0.0
    r_squared = (ss_xy ** 2 / (ss_xx * ss_yy)) if (ss_xx > 0 and ss_yy > 0) else 0.0

    if slope > 5:
        trend_direction = "upward"
    elif slope < -5:
        trend_direction = "downward"
    else:
        trend_direction = "stable"

    return {
        "slope": round(slope, 4),
        "slope_per_day": round(slope, 2),
        "trend_direction": trend_direction,
        "r_squared": round(r_squared, 4),
        "data_points": n,
        "latest_price": round(y[-1], 2),
        "mean_price": round(y_mean, 2),
    }


def generate_linear_forecast(
    prices: list,
    horizon_days: int = 14,
) -> dict:
    """
    Generate a simple linear extrapolation forecast.

    Args:
        prices: List of dicts with 'modal_price', sorted chronologically.
        horizon_days: Number of days ahead to forecast.

    Returns:
        dict with predicted_price, lower_bound, upper_bound, confidence_score,
        model_name, and daily forecast series.
    """
    trend = calculate_price_trend(prices)

    if trend["trend_direction"] == "insufficient_data":
        return {
            "error": "Insufficient price history for forecasting (need at least 3 records).",
            "model_name": "linear_trend",
            "model_version": "1.0",
            "is_mock": True,
        }

    n = len(prices)
    last_price = float(prices[-1]["modal_price"])
    slope = trend["slope"]

    # Project forward
    predicted_price = last_price + slope * horizon_days

    # Simple uncertainty band: grows with horizon and inverse R²
    uncertainty = last_price * 0.03 * (1 + horizon_days / 30) * (1 - trend["r_squared"] * 0.5)
    lower_bound = max(0, predicted_price - uncertainty)
    upper_bound = predicted_price + uncertainty

    # Confidence: higher with more data and better R²
    raw_confidence = min(0.85, 0.3 + (n / 90) * 0.4 + trend["r_squared"] * 0.15)
    confidence_score = round(raw_confidence, 2)

    # Daily series
    series = []
    for day in range(1, horizon_days + 1):
        price = last_price + slope * day
        series.append({
            "day": day,
            "predicted_price": round(max(0, price), 2),
        })

    return {
        "horizon_days": horizon_days,
        "predicted_price": round(max(0, predicted_price), 2),
        "lower_bound": round(lower_bound, 2),
        "upper_bound": round(upper_bound, 2),
        "confidence_score": confidence_score,
        "trend_direction": trend["trend_direction"],
        "slope_per_day": trend["slope_per_day"],
        "r_squared": trend["r_squared"],
        "data_points": n,
        "model_name": "linear_trend",
        "model_version": "1.0",
        "daily_series": series,
    }
