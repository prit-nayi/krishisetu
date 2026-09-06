"""
management/commands/sync_market_prices.py

Fetches official agricultural market price data from data.gov.in (AGMARKNET),
normalises it, matches markets to the local database, and saves valid
MarketPrice records.

Usage
-----
    python manage.py sync_market_prices
    python manage.py sync_market_prices --commodity groundnut
    python manage.py sync_market_prices --commodity cotton
    python manage.py sync_market_prices --dry-run

The command is idempotent: existing records (matched by market+commodity+
variety+price_date unique_together) are updated rather than duplicated.
Historical records are never deleted during normal synchronisation.

Architecture
------------
    data.gov.in
         ↓
    DataGovProvider (HTTP + auth + pagination + error handling)
         ↓
    ProviderResult  (list of RawPriceRecord)
         ↓
    sync_market_prices command
         ↓  (commodity normalisation via normalizer.py)
         ↓  (market matching via normalizer.py + local DB lookup)
         ↓  (price validation)
    PostgreSQL  (MarketPrice table)
"""
import logging
from datetime import timezone as dt_tz
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.markets.models import Market, MarketPrice
from apps.markets.market_data.providers.data_gov_provider import DataGovProvider
from apps.markets.market_data.normalizer import (
    normalize_commodity,
    normalize_market_name,
    match_market,
    MVP_COMMODITIES,
)

logger = logging.getLogger("krishilink")

# Commodities to sync when no --commodity flag is given
_DEFAULT_COMMODITIES = ["Groundnut", "Cotton"]


class Command(BaseCommand):
    help = (
        "Fetch Gujarat market prices from data.gov.in (AGMARKNET) and store "
        "them in the local MarketPrice table."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--commodity",
            type=str,
            default=None,
            help="Sync only this commodity (e.g. 'groundnut'). "
                 "Defaults to Cotton and Groundnut.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch and validate records but do not write to the database.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=5000,
            help="Maximum number of raw records to fetch per commodity (default: 5000).",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=60,
            help="HTTP request timeout in seconds for each API call (default: 60).",
        )

    def handle(self, *args, **options):
        api_key = getattr(settings, "DATA_GOV_API_KEY", "")
        if not api_key:
            raise CommandError(
                "DATA_GOV_API_KEY is not set. "
                "Add it to your .env file and ensure it is loaded into settings."
            )

        dry_run = options["dry_run"]
        limit   = options["limit"]
        timeout = options["timeout"]

        commodities_to_sync = (
            [options["commodity"]]
            if options["commodity"]
            else _DEFAULT_COMMODITIES
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no records will be written."))

        try:
            provider = DataGovProvider(api_key=api_key, timeout=timeout)
        except ValueError as exc:
            raise CommandError(str(exc))

        # Build a lookup dict: normalised_market_name → market_id
        # This is done once here so normalizer functions stay pure.
        market_lookup = self._build_market_lookup()
        self.stdout.write(
            f"Market lookup built: {len(market_lookup)} normalised market names."
        )

        total_fetched   = 0
        total_accepted  = 0
        total_skipped   = 0
        total_unmatched = 0
        total_errors    = 0

        for commodity_query in commodities_to_sync:
            self.stdout.write(f"\nSyncing commodity: {commodity_query}")
            result = provider.fetch_prices(
                state="Gujarat",
                commodity=commodity_query,
                limit=limit,
            )

            if result.errors:
                for err in result.errors:
                    self.stderr.write(self.style.ERROR(f"  Provider error: {err}"))
                total_errors += len(result.errors)
                if not result.records:
                    self.stdout.write(
                        self.style.WARNING("  No records returned — skipping commodity.")
                    )
                    continue

            self.stdout.write(
                f"  Fetched {result.total_fetched} raw records, "
                f"parsed {len(result.records)} valid records."
            )
            total_fetched += result.total_fetched

            retrieved_at = timezone.now()

            for rec in result.records:
                # 1. Commodity normalisation
                canonical_commodity = normalize_commodity(rec.commodity)
                if canonical_commodity is None:
                    total_skipped += 1
                    logger.debug("Skipped unsupported commodity '%s'", rec.commodity)
                    continue

                # 2. Filter Gujarat only (provider already filters, but validate)
                if rec.state.strip().lower() not in ("gujarat", "gujrat"):
                    total_skipped += 1
                    logger.debug("Skipped non-Gujarat record: state='%s'", rec.state)
                    continue

                # 3. Market matching
                market_id = match_market(rec.market, market_lookup)
                if market_id is None:
                    total_unmatched += 1
                    logger.info(
                        "Unmatched market: '%s' (district: %s) — skipped.",
                        rec.market, rec.district,
                    )
                    continue

                # 4. Price validation (already done in provider, but double-check)
                if rec.min_price < 0 or rec.max_price < 0 or rec.modal_price < 0:
                    total_skipped += 1
                    continue
                if rec.min_price > rec.max_price:
                    total_skipped += 1
                    continue

                # 5. Persist (or update) the record
                if not dry_run:
                    variety = (rec.variety or "").strip()
                    _, was_created = MarketPrice.objects.update_or_create(
                        market_id=market_id,
                        commodity=canonical_commodity,
                        variety=variety,
                        price_date=rec.arrival_date,
                        defaults={
                            "grade":            (rec.grade or "").strip(),
                            "min_price":        rec.min_price,
                            "max_price":        rec.max_price,
                            "modal_price":      rec.modal_price,
                            "arrival_quantity": rec.arrival_quantity,
                            "source":           MarketPrice.Source.AGMARKNET,
                            "source_timestamp": retrieved_at,
                            "is_verified":      True,
                        },
                    )
                    action = "created" if was_created else "updated"
                    logger.debug(
                        "%s price: market_id=%s commodity=%s date=%s",
                        action, market_id, canonical_commodity, rec.arrival_date,
                    )

                total_accepted += 1

        # ── Summary ──────────────────────────────────────────────────────────
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"sync_market_prices complete.\n"
                f"  Fetched    : {total_fetched}\n"
                f"  Accepted   : {total_accepted}\n"
                f"  Skipped    : {total_skipped}\n"
                f"  Unmatched  : {total_unmatched}\n"
                f"  Errors     : {total_errors}\n"
                f"  Dry run    : {dry_run}"
            )
        )
        logger.info(
            "sync_market_prices done — fetched=%d accepted=%d skipped=%d "
            "unmatched=%d errors=%d dry_run=%s",
            total_fetched, total_accepted, total_skipped,
            total_unmatched, total_errors, dry_run,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_market_lookup() -> dict:
        """
        Return {normalised_name: market_id} for every active Market in the DB.

        Two keys are added per market:
        1. The fully normalised form (lower, strip, remove APMC suffix).
        2. The plain lowercase+strip form (no suffix removal).

        This maximises matches without requiring fuzzy logic.
        """
        lookup: dict = {}
        for market in Market.objects.filter(is_active=True, state="Gujarat"):
            norm  = normalize_market_name(market.name)
            plain = market.name.strip().lower()
            if norm:
                lookup[norm] = market.id
            if plain and plain not in lookup:
                lookup[plain] = market.id
            # Also add district-prefixed key for disambiguation
            district_key = f"{market.district.strip().lower()} {norm}".strip()
            if district_key and district_key not in lookup:
                lookup[district_key] = market.id
        return lookup
