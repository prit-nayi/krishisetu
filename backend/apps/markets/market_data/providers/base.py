"""
market_data/providers/base.py — Abstract base class for market data providers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional


@dataclass
class RawPriceRecord:
    """Normalised price record returned by any provider before DB storage."""
    state: str
    district: str
    market: str
    commodity: str
    variety: str
    grade: str
    arrival_date: date
    min_price: Decimal
    max_price: Decimal
    modal_price: Decimal
    source: str
    # Optional fields
    arrival_quantity: Optional[Decimal] = None
    raw_commodity_name: str = ""   # original external name, for traceability


@dataclass
class ProviderResult:
    """Container returned by a provider fetch operation."""
    records: List[RawPriceRecord] = field(default_factory=list)
    total_fetched: int = 0
    errors: List[str] = field(default_factory=list)


class BaseMarketDataProvider(ABC):
    """
    Contract that every market data provider must implement.

    Concrete providers (DataGovProvider, …) call their respective
    external APIs and return a ProviderResult with RawPriceRecord objects.
    The rest of the application must not depend on raw external responses.
    """

    @abstractmethod
    def fetch_prices(
        self,
        state: str = "Gujarat",
        commodity: Optional[str] = None,
        limit: int = 1000,
    ) -> ProviderResult:
        """
        Fetch price records and return them as RawPriceRecord objects.
        Must handle timeouts, auth errors, and invalid responses gracefully.
        All errors are collected in ProviderResult.errors — never raised.
        """
        ...
