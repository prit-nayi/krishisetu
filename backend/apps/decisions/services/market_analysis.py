"""
decisions/services/market_analysis.py — Phase 4: Financial & Market Analysis Service.

Connects CropLot → Market → MarketPrice → financial_tools to produce a
ranked list of markets with full financial breakdown per market.

All calculation logic is delegated to the existing deterministic tools in
tools/financial_tools.py and tools/market_tools.py.  This service only
orchestrates data retrieval and tool calls — it contains no calculation logic
of its own.
"""
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from apps.crops.models import CropLot
from apps.markets.models import Market, MarketPrice
from tools.financial_tools import (
    calculate_market_revenue,
    calculate_transport_cost,
    calculate_net_value,
)
from tools.market_tools import haversine_distance

logger = logging.getLogger("krishilink")

# ── Unit conversion to quintals ───────────────────────────────────────────────

_TO_QUINTAL = {
    "quintal": 1.0,
    "kg":      0.01,    # 1 quintal = 100 kg
    "tonne":   10.0,    # 1 tonne   = 10 quintals
}


def to_quintal(quantity: float, unit: str) -> float:
    """Convert crop lot quantity to quintals. Raises ValueError for unknown units."""
    factor = _TO_QUINTAL.get(unit.lower())
    if factor is None:
        raise ValueError(f"Unsupported unit '{unit}'. Supported: {list(_TO_QUINTAL)}")
    return float(quantity) * factor


# ── Result dataclasses ────────────────────────────────────────────────────────

@dataclass
class MarketFinancialResult:
    """Financial analysis for one market."""
    market_id:       int
    market_name:     str
    district:        str
    state:           str
    distance_km:     Optional[float]       # None if no farmer/market coordinates

    # Price
    modal_price:     float
    price_date:      Optional[str]         # ISO date string

    # Financials (all in INR)
    quantity_quintal: float
    gross_revenue:   float
    transport_cost:  float
    net_revenue:     float
    other_costs:     float = 0.0
    total_cost:      float = 0.0

    # Rank (filled in after sorting)
    rank:            int = 0

    # Optional error/skip reason
    skipped:         bool  = False
    skip_reason:     str   = ""


@dataclass
class MarketAnalysisResult:
    """Full result from MarketAnalysisService.run()."""
    crop_lot_id:          int
    commodity:            str
    quantity_quintal:     float
    farmer_lat:           Optional[float]
    farmer_lon:           Optional[float]
    markets:              List[MarketFinancialResult] = field(default_factory=list)
    skipped_markets:      List[MarketFinancialResult] = field(default_factory=list)
    best_market:          Optional[MarketFinancialResult] = None
    errors:               List[str]                   = field(default_factory=list)


# ── Service ───────────────────────────────────────────────────────────────────

class MarketAnalysisService:
    """
    Analyse all active Gujarat markets for a given CropLot.

    Usage::

        result = MarketAnalysisService().run(crop_lot_id=5, user=request.user)
    """

    def run(self, crop_lot_id: int, user) -> MarketAnalysisResult:
        """
        Execute the full financial analysis pipeline.

        Steps:
        1. Load CropLot and verify ownership.
        2. Normalise quantity to quintals.
        3. Load farmer coordinates.
        4. For each active market with a recent price:
           a. Get latest modal price.
           b. Calculate distance.
           c. Calculate gross revenue, transport cost, net revenue.
        5. Rank markets by net revenue descending.
        6. Return structured MarketAnalysisResult.
        """
        # ── 1. Load crop lot ──────────────────────────────────────────────────
        try:
            crop_lot = CropLot.objects.select_related(
                "farmer", "farmer__user"
            ).get(pk=crop_lot_id, is_active=True)
        except CropLot.DoesNotExist:
            return MarketAnalysisResult(
                crop_lot_id=crop_lot_id,
                commodity="",
                quantity_quintal=0,
                farmer_lat=None,
                farmer_lon=None,
                errors=["Crop lot not found or is inactive."],
            )

        if crop_lot.farmer.user != user:
            return MarketAnalysisResult(
                crop_lot_id=crop_lot_id,
                commodity="",
                quantity_quintal=0,
                farmer_lat=None,
                farmer_lon=None,
                errors=["You do not have permission to analyse this crop lot."],
            )

        # ── 2. Normalise quantity ─────────────────────────────────────────────
        try:
            qty_quintal = to_quintal(float(crop_lot.quantity), crop_lot.unit)
        except ValueError as exc:
            return MarketAnalysisResult(
                crop_lot_id=crop_lot_id,
                commodity=crop_lot.commodity,
                quantity_quintal=0,
                farmer_lat=None,
                farmer_lon=None,
                errors=[str(exc)],
            )

        if qty_quintal <= 0:
            return MarketAnalysisResult(
                crop_lot_id=crop_lot_id,
                commodity=crop_lot.commodity,
                quantity_quintal=0,
                farmer_lat=None,
                farmer_lon=None,
                errors=["Quantity must be greater than zero."],
            )

        # ── 3. Farmer coordinates ─────────────────────────────────────────────
        farmer    = crop_lot.farmer
        farmer_lat = float(farmer.latitude)  if farmer.latitude  else None
        farmer_lon = float(farmer.longitude) if farmer.longitude else None

        commodity_upper = crop_lot.commodity.upper()  # GROUNDNUT / COTTON

        # ── 4. Latest price per market for this commodity ─────────────────────
        # Get the most recent price date per market, then fetch those records.
        from django.db.models import Max
        latest_dates = (
            MarketPrice.objects
            .filter(commodity=commodity_upper, market__is_active=True)
            .values("market_id")
            .annotate(latest=Max("price_date"))
        )
        # Build {market_id: latest_date}
        market_latest = {row["market_id"]: row["latest"] for row in latest_dates}

        if not market_latest:
            return MarketAnalysisResult(
                crop_lot_id=crop_lot_id,
                commodity=commodity_upper,
                quantity_quintal=qty_quintal,
                farmer_lat=farmer_lat,
                farmer_lon=farmer_lon,
                errors=[f"No price records found for commodity '{commodity_upper}'."],
            )

        # Fetch all those latest price records in one query
        from django.db.models import Q
        price_filters = Q()
        for mid, latest in market_latest.items():
            price_filters |= Q(market_id=mid, commodity=commodity_upper, price_date=latest)

        prices_qs = (
            MarketPrice.objects
            .filter(price_filters)
            .select_related("market")
        )
        # If multiple variety records on the same date, take the highest modal price
        best_price_by_market: dict = {}
        for p in prices_qs:
            mid = p.market_id
            if mid not in best_price_by_market or float(p.modal_price) > float(best_price_by_market[mid].modal_price):
                best_price_by_market[mid] = p

        # ── 5. Financial analysis per market ──────────────────────────────────
        result = MarketAnalysisResult(
            crop_lot_id=crop_lot_id,
            commodity=commodity_upper,
            quantity_quintal=qty_quintal,
            farmer_lat=farmer_lat,
            farmer_lon=farmer_lon,
        )

        for market_id, price_rec in best_price_by_market.items():
            market = price_rec.market
            mfr = self._analyse_market(
                market=market,
                price_rec=price_rec,
                qty_quintal=qty_quintal,
                farmer_lat=farmer_lat,
                farmer_lon=farmer_lon,
            )
            if mfr.skipped:
                result.skipped_markets.append(mfr)
            else:
                result.markets.append(mfr)

        # ── 6. Rank by net revenue descending ────────────────────────────────
        result.markets.sort(key=lambda x: x.net_revenue, reverse=True)
        for i, mfr in enumerate(result.markets, start=1):
            mfr.rank = i

        if result.markets:
            result.best_market = result.markets[0]

        logger.info(
            "MarketAnalysisService: crop_lot=%d commodity=%s qty=%.2f q | "
            "%d markets analysed, %d skipped",
            crop_lot_id, commodity_upper, qty_quintal,
            len(result.markets), len(result.skipped_markets),
        )
        return result

    # ------------------------------------------------------------------

    @staticmethod
    def _analyse_market(
        market: Market,
        price_rec: MarketPrice,
        qty_quintal: float,
        farmer_lat: Optional[float],
        farmer_lon: Optional[float],
    ) -> MarketFinancialResult:
        """Compute financial metrics for a single market. Returns skipped on error."""

        modal_price = float(price_rec.modal_price)

        # Distance
        distance_km: Optional[float] = None
        if (
            farmer_lat is not None and farmer_lon is not None
            and market.latitude is not None and market.longitude is not None
        ):
            distance_km = round(
                haversine_distance(
                    farmer_lat, farmer_lon,
                    float(market.latitude), float(market.longitude),
                ),
                1,
            )

        # Gross revenue
        try:
            rev = calculate_market_revenue(modal_price, qty_quintal)
            gross_revenue = rev["gross_revenue"]
        except ValueError as exc:
            return MarketFinancialResult(
                market_id=market.id, market_name=market.name,
                district=market.district, state=market.state,
                distance_km=distance_km,
                modal_price=modal_price,
                price_date=str(price_rec.price_date),
                quantity_quintal=qty_quintal,
                gross_revenue=0, transport_cost=0, other_costs=0, total_cost=0, net_revenue=0,
                skipped=True, skip_reason=f"Revenue calculation failed: {exc}",
            )

        # Transport cost (if distance available, else 0)
        transport_cost = 0.0
        if distance_km is not None:
            try:
                tc = calculate_transport_cost(distance_km, qty_quintal)
                transport_cost = tc["total_transport_cost"]
            except ValueError:
                transport_cost = 0.0

        # Other applicable costs (mandi cess, loading/unloading if applicable, default 0.0)
        other_costs = 0.0

        # Total cost = Transport Cost + Other Applicable Costs
        total_cost = round(transport_cost + other_costs, 2)

        # Net revenue = Gross Revenue - Total Cost
        net_rev = calculate_net_value(gross_revenue, total_cost)
        net_revenue = net_rev["net_value"]

        return MarketFinancialResult(
            market_id=market.id,
            market_name=market.name,
            district=market.district,
            state=market.state,
            distance_km=distance_km,
            modal_price=modal_price,
            price_date=str(price_rec.price_date),
            quantity_quintal=qty_quintal,
            gross_revenue=round(gross_revenue, 2),
            transport_cost=round(transport_cost, 2),
            other_costs=round(other_costs, 2),
            total_cost=round(total_cost, 2),
            net_revenue=round(net_revenue, 2),
        )
