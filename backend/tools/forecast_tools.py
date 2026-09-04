"""
tools/forecast_tools.py — Deterministic price forecasting tools (baseline linear model).

Phase 5 will upgrade to SARIMAX. This baseline uses simple linear regression.
"""
import statistics


def calculate_price_trend(price_history: list) -> dict:
    """
    Fit a simple linear trend to historical modal prices.

    Args:
        price_history: List of dicts with "modal_price". Ordered oldest → newest.

    Returns:
        {"trend_direction": "up"|"down"|"flat", "slope": float,
         "r_squared": float, "data_points": int}
    """
    prices = [float(p["modal_price"]) for p in price_history if p.get("modal_price") is not None]
    n = len(prices)
    if n < 3:
        return {"trend_direction": "flat", "slope": 0.0, "r_squared": 0.0, "data_points": n}

    x_vals   = list(range(n))
    x_mean   = statistics.mean(x_vals)
    y_mean   = statistics.mean(prices)
    ss_xy    = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, prices))
    ss_xx    = sum((x - x_mean) ** 2 for x in x_vals)

    slope = ss_xy / ss_xx if ss_xx != 0 else 0.0

    # R²
    y_pred  = [y_mean + slope * (x - x_mean) for x in x_vals]
    ss_res  = sum((y - yp) ** 2 for y, yp in zip(prices, y_pred))
    ss_tot  = sum((y - y_mean) ** 2 for y in prices)
    r2      = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

    direction = "up" if slope > 5 else ("down" if slope < -5 else "flat")
    return {
        "trend_direction": direction,
        "slope": round(slope, 2),
        "r_squared": round(r2, 4),
        "data_points": n,
    }


def generate_price_forecast(
    price_history: list,
    horizon_days: int = 14,
    model_name: str = "linear_regression",
) -> dict:
    """
    Generate a simple linear extrapolation forecast.

    Args:
        price_history: List of dicts with "modal_price". Ordered oldest → newest.
        horizon_days: Number of days to forecast ahead.
        model_name: Label for the model used.

    Returns:
        {"predictions": [float], "confidence_band": {"lower": [float], "upper": [float]},
         "model": str, "model_version": str, "is_mock": bool}
    """
    prices = [float(p["modal_price"]) for p in price_history if p.get("modal_price") is not None]
    n = len(prices)

    if n < 3:
        # Not enough data — return flat forecast from last known price
        last  = prices[-1] if prices else 0.0
        preds = [last] * horizon_days
        return {
            "predictions": preds,
            "confidence_band": {"lower": [last * 0.95] * horizon_days, "upper": [last * 1.05] * horizon_days},
            "model": model_name,
            "model_version": "1.0.0-baseline",
            "is_mock": False,
            "warning": "Insufficient data — flat forecast used.",
        }

    # Fit linear trend
    trend = calculate_price_trend(price_history)
    slope = trend["slope"]
    last  = prices[-1]

    # Extrapolate
    preds  = [max(0.0, last + slope * (i + 1)) for i in range(horizon_days)]
    margin = statistics.stdev(prices) if n > 1 else last * 0.05
    lower  = [max(0.0, p - 1.96 * margin) for p in preds]
    upper  = [p + 1.96 * margin for p in preds]

    return {
        "predictions": [round(p, 2) for p in preds],
        "confidence_band": {
            "lower": [round(p, 2) for p in lower],
            "upper": [round(p, 2) for p in upper],
        },
        "model": model_name,
        "model_version": "1.0.0-baseline",
        "is_mock": False,
    }
