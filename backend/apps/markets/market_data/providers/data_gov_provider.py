"""
market_data/providers/data_gov_provider.py

Fetches agricultural market price data from the Government of India
Open Government Data platform (data.gov.in).

Dataset: Current Daily Price of Various Commodities in Various Markets (Mandi)
Resource ID: 35985678-0d79-46b4-9ed6-6f13308a1d24
API URL:    https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24

Confirmed field names (probed live 2026-09-06):
    State, District, Market, Commodity, Variety, Grade,
    Arrival_Date, Min_Price, Max_Price, Modal_Price

Confirmed working filter params:
    filters[State]     — e.g. Gujarat  (5.4 M records)
    filters[Commodity] — e.g. Groundnut

Authentication: api-key query parameter.
                Store in environment variable DATA_GOV_API_KEY.

Root-cause of earlier ReadTimeout:
    The data.gov.in API server closes the connection after the response body
    but does NOT send a Content-Length header; requests' urllib3 waits
    indefinitely for more bytes.  Fix: send "Connection: close" so the server
    signals EOF immediately.

This provider never raises — all errors are returned in ProviderResult.errors
so the rest of the application can continue serving cached/stored data.
"""
import logging
import time
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional

import requests

from .base import BaseMarketDataProvider, ProviderResult, RawPriceRecord

logger = logging.getLogger("krishilink")

# Official resource endpoint
_BASE_URL = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"

# Page size — data.gov.in accepts up to 100 per page
_PAGE_SIZE = 100

# Default request timeout in seconds
_TIMEOUT = 60

# "Connection: close" forces the server to close the TCP connection after the
# response, which unblocks urllib3's read loop immediately.
_HEADERS = {
    "Connection": "close",
    "User-Agent": "KrishiLink/1.0",
}


class DataGovProvider(BaseMarketDataProvider):
    """
    Fetches AGMARKNET commodity prices via the data.gov.in REST API.

    Constructor params
    ------------------
    api_key : str
        data.gov.in API key.  Read from settings by the caller.
    timeout : int
        Per-request HTTP timeout in seconds (default: 60).
    """

    def __init__(self, api_key: str, timeout: int = _TIMEOUT):
        if not api_key:
            raise ValueError("DataGovProvider requires a non-empty api_key.")
        self._api_key = api_key
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fetch_prices(
        self,
        state: str = "Gujarat",
        commodity: Optional[str] = None,
        limit: int = 5000,
    ) -> ProviderResult:
        """
        Fetch price records from data.gov.in, filtered by state and optionally
        commodity.  Paginates automatically until *limit* records are retrieved.

        Returns a ProviderResult; never raises.
        """
        result = ProviderResult()

        try:
            all_records = self._paginate(state=state, commodity=commodity, limit=limit)
            result.total_fetched = len(all_records)
            for raw in all_records:
                parsed = self._parse_record(raw)
                if parsed is not None:
                    result.records.append(parsed)
        except _ProviderError as exc:
            logger.error("DataGovProvider fetch failed: %s", exc)
            result.errors.append(str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception("DataGovProvider unexpected error: %s", exc)
            result.errors.append(f"Unexpected error: {exc}")

        logger.info(
            "DataGovProvider: fetched %d raw records, parsed %d valid records, %d errors",
            result.total_fetched,
            len(result.records),
            len(result.errors),
        )
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _paginate(
        self,
        state: str,
        commodity: Optional[str],
        limit: int,
    ) -> List[dict]:
        """
        Page through the API and collect raw dict records up to *limit*.
        Raises _ProviderError on HTTP / auth / format problems.

        Filter param confirmed to work: filters[State] and filters[Commodity]
        (without the .keyword suffix — that syntax returns 0 results for this resource).
        """
        collected: List[dict] = []
        offset = 0

        while len(collected) < limit:
            batch_size = min(_PAGE_SIZE, limit - len(collected))
            params = {
                "api-key":         self._api_key,
                "format":          "json",
                "offset":          offset,
                "limit":           batch_size,
                "filters[State]":  state,
            }
            if commodity:
                params["filters[Commodity]"] = commodity

            try:
                resp = requests.get(
                    _BASE_URL,
                    params=params,
                    headers=_HEADERS,
                    timeout=self._timeout,
                )
            except requests.exceptions.Timeout:
                raise _ProviderError(
                    f"Request to data.gov.in timed out after {self._timeout}s."
                )
            except requests.exceptions.ConnectionError as exc:
                raise _ProviderError(f"Connection error: {exc}")
            except requests.exceptions.RequestException as exc:
                raise _ProviderError(f"HTTP request failed: {exc}")

            if resp.status_code == 401:
                raise _ProviderError(
                    "data.gov.in returned 401 Unauthorized — check DATA_GOV_API_KEY."
                )
            if resp.status_code == 403:
                raise _ProviderError(
                    "data.gov.in returned 403 Forbidden — API key may be invalid or revoked."
                )
            if not resp.ok:
                raise _ProviderError(
                    f"data.gov.in returned HTTP {resp.status_code}: {resp.text[:200]}"
                )

            try:
                payload = resp.json()
            except ValueError as exc:
                raise _ProviderError(
                    f"data.gov.in returned non-JSON response: {exc}"
                )

            if not isinstance(payload, dict):
                raise _ProviderError("data.gov.in response is not a JSON object.")

            records = payload.get("records")
            if records is None:
                raise _ProviderError(
                    "data.gov.in response missing 'records' key. "
                    f"Keys found: {list(payload.keys())}"
                )
            if not isinstance(records, list):
                raise _ProviderError(
                    "'records' in data.gov.in response is not a list."
                )

            if not records:
                break  # No more pages

            collected.extend(records)
            offset += len(records)

            if len(records) < batch_size:
                break  # Last page

            time.sleep(0.15)  # Polite delay between pages

        return collected

    def _parse_record(self, raw: dict) -> Optional[RawPriceRecord]:
        """
        Convert a single raw API dict into a RawPriceRecord.
        Returns None (and logs) if any required field is missing or invalid.

        Confirmed field names for resource 35985678 (probed live):
            State, District, Market, Commodity, Variety, Grade,
            Arrival_Date, Min_Price, Max_Price, Modal_Price

        Additional fallback variants are kept for forward-compatibility.
        """
        try:
            state     = _safe_str(_first(raw, "State",     "state"))
            district  = _safe_str(_first(raw, "District",  "district"))
            market    = _safe_str(_first(raw, "Market",    "market"))
            commodity = _safe_str(_first(raw, "Commodity", "commodity"))
            variety   = _safe_str(_first(raw, "Variety",   "variety"))
            grade     = _safe_str(_first(raw, "Grade",     "grade"))

            arrival_date_raw = _safe_str(
                _first(raw, "Arrival_Date", "arrival_date", "ArrivalDate",
                           "Arrival Date", "arrivaldate")
            )

            # Confirmed primary names: Min_Price, Max_Price, Modal_Price
            # Fallbacks kept for other resource variants
            min_price_raw   = _first(raw,
                "Min_Price",       "Min_x0020_Price", "Min Price",
                "min_price",       "minimum_price",   "MinPrice")
            max_price_raw   = _first(raw,
                "Max_Price",       "Max_x0020_Price", "Max Price",
                "max_price",       "maximum_price",   "MaxPrice")
            modal_price_raw = _first(raw,
                "Modal_Price",     "Modal_x0020_Price", "Modal Price",
                "modal_price",     "modalPrice",        "ModalPrice")

            if not all([state, district, market, commodity]):
                logger.debug("Skipping record with missing required fields: %s", raw)
                return None

            arrival_date = _parse_date(arrival_date_raw)
            if arrival_date is None:
                logger.debug("Skipping record with unparseable date '%s': %s", arrival_date_raw, raw)
                return None

            min_price   = _parse_price(min_price_raw)
            max_price   = _parse_price(max_price_raw)
            modal_price = _parse_price(modal_price_raw)

            if min_price is None or max_price is None or modal_price is None:
                logger.debug("Skipping record with missing/invalid price: %s", raw)
                return None

            if min_price < 0 or max_price < 0 or modal_price < 0:
                logger.debug("Skipping record with negative price: %s", raw)
                return None

            if min_price > max_price:
                logger.debug(
                    "Skipping record where min_price (%s) > max_price (%s): %s",
                    min_price, max_price, raw,
                )
                return None

            return RawPriceRecord(
                state=state,
                district=district,
                market=market,
                commodity=commodity,
                variety=variety,
                grade=grade,
                arrival_date=arrival_date,
                min_price=min_price,
                max_price=max_price,
                modal_price=modal_price,
                source="agmarknet",
                raw_commodity_name=commodity,
            )

        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to parse record %s: %s", raw, exc)
            return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _first(record: dict, *keys):
    """Return the value of the first key found in *record*, or None."""
    for key in keys:
        val = record.get(key)
        if val is not None:
            return val
    return None


def _safe_str(value) -> str:
    """Return a stripped string, empty string for None/falsy."""
    return str(value).strip() if value is not None else ""


def _parse_date(raw: str) -> Optional[date]:
    """
    Try several date formats commonly returned by data.gov.in AGMARKNET.
    Returns a date object or None.
    """
    if not raw:
        return None
    formats = [
        "%d/%m/%Y",  # 27/04/2010  ← confirmed format in this resource
        "%Y-%m-%d",  # 2025-07-01
        "%d-%m-%Y",  # 01-07-2025
        "%d-%b-%Y",  # 01-Jul-2025
        "%d %b %Y",  # 01 Jul 2025
        "%Y/%m/%d",  # 2025/07/01
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_price(raw) -> Optional[Decimal]:
    """Convert a price value (string or number) to Decimal, or return None."""
    if raw is None:
        return None
    try:
        cleaned = str(raw).replace(",", "").strip()
        if not cleaned:
            return None
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


class _ProviderError(Exception):
    """Internal exception raised during _paginate(); caught in fetch_prices()."""
