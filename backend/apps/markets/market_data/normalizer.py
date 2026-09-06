"""
market_data/normalizer.py

Normalises commodity names and market names so that external API data
can be matched reliably to local database records.

Rules
-----
* Commodity normalisation is deterministic: a known-alias map maps
  external names to canonical uppercase keys (GROUNDNUT, COTTON).
* Market normalisation strips common suffixes and whitespace then
  attempts an exact (case-insensitive) match.  It never auto-creates
  records; unmatched markets are logged and reported.

All logic here is pure (no DB access) so it is straightforwardly testable.
"""
import logging
import re
from typing import Dict, Optional

logger = logging.getLogger("krishilink")

# ---------------------------------------------------------------------------
# Supported MVP commodities
# ---------------------------------------------------------------------------
MVP_COMMODITIES = {"GROUNDNUT", "COTTON"}

# ---------------------------------------------------------------------------
# Commodity alias table
# The keys are lowercased external names (after stripping punctuation).
# The values are canonical uppercase names stored in the local DB.
# ---------------------------------------------------------------------------
_COMMODITY_ALIASES: Dict[str, str] = {
    # ── Groundnut variants ─────────────────────────────────────────────
    "groundnut":                   "GROUNDNUT",
    "ground nut":                  "GROUNDNUT",
    "groundnut (without shell)":   "GROUNDNUT",
    "groundnut (with shell)":      "GROUNDNUT",
    "groundnut pods (fresh)":      "GROUNDNUT",
    "peanut":                      "GROUNDNUT",
    "pea nut":                     "GROUNDNUT",
    "moongfali":                   "GROUNDNUT",
    "mungfali":                    "GROUNDNUT",
    "ground-nut":                  "GROUNDNUT",

    # ── Cotton variants ────────────────────────────────────────────────
    "cotton":                      "COTTON",
    "cotton (raw)":                "COTTON",
    "cotton seed":                 "COTTON",
    "cotton(raw)":                 "COTTON",
    "kapas":                       "COTTON",
    "kapas":                       "COTTON",
    "cotton bales":                "COTTON",
}


def normalize_commodity(raw_name: str) -> Optional[str]:
    """
    Return the canonical commodity name (e.g. 'GROUNDNUT') for *raw_name*,
    or None if the commodity is not in the MVP list.

    Matching is case-insensitive; leading/trailing whitespace is stripped.
    """
    if not raw_name:
        return None
    key = raw_name.strip().lower()
    canonical = _COMMODITY_ALIASES.get(key)
    if canonical is None:
        # Attempt prefix/substring match for slight variations
        for alias, canon in _COMMODITY_ALIASES.items():
            if key.startswith(alias) or alias.startswith(key):
                canonical = canon
                break
    if canonical not in MVP_COMMODITIES:
        return None
    return canonical


# ---------------------------------------------------------------------------
# Market name normalisation
# ---------------------------------------------------------------------------

# Common suffixes to strip before matching
_MARKET_SUFFIXES = re.compile(
    r"\s*(apmc|market|mandi|yard|veg\.?\s*yard|veg\.?\s*market|agri\s*market)\s*$",
    re.IGNORECASE,
)


def normalize_market_name(raw_name: str) -> str:
    """
    Return a normalised market name suitable for fuzzy comparison.

    Steps:
    1. Strip whitespace.
    2. Remove common suffixes (APMC, Market, Mandi, …).
    3. Collapse internal whitespace.
    4. Lowercase.

    This is NOT used for DB matching directly; use match_market() instead.
    """
    if not raw_name:
        return ""
    name = raw_name.strip()
    name = _MARKET_SUFFIXES.sub("", name)
    name = re.sub(r"\s+", " ", name).strip().lower()
    return name


def match_market(raw_name: str, market_lookup: Dict[str, int]) -> Optional[int]:
    """
    Given an external market name and a lookup dict of
    ``{normalised_name: market_id}``, return the matching market ID or None.

    *market_lookup* is built once per sync run by the management command
    so that this function remains pure and fast.

    Strategy (deterministic, no fuzzy matching):
    1. Exact match on the normalised form.
    2. No match → return None; the caller logs the unmatched record.
    """
    if not raw_name:
        return None
    key = normalize_market_name(raw_name)
    match_id = market_lookup.get(key)
    if match_id is None:
        # Try without any normalization (just lowercase + strip)
        simple_key = raw_name.strip().lower()
        match_id = market_lookup.get(simple_key)
    return match_id
