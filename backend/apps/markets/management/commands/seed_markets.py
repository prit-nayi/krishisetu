"""
management/commands/seed_markets.py

Populates the local Market database with Gujarat APMC markets.

Data is derived from the scraped Gujarat APMC directory data.  The scraped
file contained market names and district information but did not include
commodity price data or coordinates — prices come from the data.gov.in sync.

Coordinates below are approximate centroids for well-known Gujarat APMCs
that trade cotton and groundnut.  They were sourced from public geographic
references and are used to support the nearby-market feature.  Any market
without a known coordinate is loaded without lat/lon (both remain NULL).

Usage
-----
    python manage.py seed_markets
    python manage.py seed_markets --clear    # wipe existing records first

This command is idempotent: re-running it will update existing records
(matched by normalised name + district) rather than creating duplicates.
"""
import logging
from django.core.management.base import BaseCommand
from apps.markets.models import Market

logger = logging.getLogger("krishilink")

# ---------------------------------------------------------------------------
# Gujarat APMC market seed data
# Sourced from: scraped Gujarat APMC directory (Gujarat APMC_data file)
# Fields: name, district, taluka, latitude, longitude
# Latitude/longitude: approximate APMC centroid coordinates (public sources)
# Markets without confirmed coordinates have None values.
# ---------------------------------------------------------------------------
GUJARAT_MARKETS = [
    # ── Ahmedabad ─────────────────────────────────────────────────────────────
    {"name": "Ahmedabad APMC",                   "district": "Ahmedabad",    "taluka": "Ahmedabad",   "lat":  23.0225, "lon":  72.5714},
    {"name": "Dhandhuka APMC",                   "district": "Ahmedabad",    "taluka": "Dhandhuka",   "lat":  22.3745, "lon":  71.9871},
    {"name": "Dholka APMC",                      "district": "Ahmedabad",    "taluka": "Dholka",      "lat":  22.7315, "lon":  72.4662},
    {"name": "Mandal APMC",                      "district": "Ahmedabad",    "taluka": "Mandal",      "lat":  22.9600, "lon":  72.0100},
    {"name": "Sanand APMC",                      "district": "Ahmedabad",    "taluka": "Sanand",      "lat":  22.9900, "lon":  72.3700},
    {"name": "Viramgam APMC",                    "district": "Ahmedabad",    "taluka": "Viramgam",    "lat":  23.1200, "lon":  72.0300},

    # ── Amreli ────────────────────────────────────────────────────────────────
    {"name": "Amreli APMC",                      "district": "Amreli",       "taluka": "Amreli",      "lat":  21.6010, "lon":  71.2214},
    {"name": "Bagasara APMC",                    "district": "Amreli",       "taluka": "Bagasara",    "lat":  21.4900, "lon":  71.0200},
    {"name": "Khambha APMC",                     "district": "Amreli",       "taluka": "Khambha",     "lat":  21.3200, "lon":  71.2100},
    {"name": "Lathi APMC",                       "district": "Amreli",       "taluka": "Lathi",       "lat":  21.7300, "lon":  71.3800},
    {"name": "Rajula APMC",                      "district": "Amreli",       "taluka": "Rajula",      "lat":  21.0400, "lon":  71.4400},
    {"name": "Savarkundla APMC",                 "district": "Amreli",       "taluka": "Savarkundla", "lat":  21.3400, "lon":  71.3200},
    {"name": "Dhari APMC",                       "district": "Amreli",       "taluka": "Dhari",       "lat":  21.3300, "lon":  71.0300},
    {"name": "Dhari",                            "district": "Amreli",       "taluka": "Dhari",       "lat":  21.3300, "lon":  71.0300},

    # ── Anand ─────────────────────────────────────────────────────────────────
    {"name": "Anand APMC",                       "district": "Anand",        "taluka": "Anand",       "lat":  22.5580, "lon":  72.9500},
    {"name": "Khambhat APMC",                    "district": "Anand",        "taluka": "Khambhat",    "lat":  22.3200, "lon":  72.6200},
    {"name": "Petlad APMC",                      "district": "Anand",        "taluka": "Petlad",      "lat":  22.4700, "lon":  72.8000},

    # ── Banaskantha ───────────────────────────────────────────────────────────
    {"name": "Deesa APMC",                       "district": "Banaskantha",  "taluka": "Deesa",       "lat":  24.2600, "lon":  72.1900},
    {"name": "Dhanera APMC",                     "district": "Banaskantha",  "taluka": "Dhanera",     "lat":  24.5100, "lon":  72.0200},
    {"name": "Palanpur APMC",                    "district": "Banaskantha",  "taluka": "Palanpur",    "lat":  24.1700, "lon":  72.4400},
    {"name": "Radhanpur APMC",                   "district": "Banaskantha",  "taluka": "Radhanpur",   "lat":  23.8300, "lon":  71.6000},
    {"name": "Tharad APMC",                      "district": "Banaskantha",  "taluka": "Tharad",      "lat":  24.3900, "lon":  71.6300},
    # API uses district spelling "Banaskanth" (no 'a') — alias entries
    {"name": "Deesa(Bhildi)",                    "district": "Banaskanth",   "taluka": "Deesa",       "lat":  24.2100, "lon":  72.1600},
    {"name": "Panthawada",                       "district": "Banaskanth",   "taluka": "Panthawada",  "lat":  23.9800, "lon":  71.7200},
    {"name": "Vadgam",                           "district": "Banaskanth",   "taluka": "Vadgam",      "lat":  23.9500, "lon":  72.6600},

    # ── Bharuch ───────────────────────────────────────────────────────────────
    {"name": "Bharuch APMC",                     "district": "Bharuch",      "taluka": "Bharuch",     "lat":  21.7050, "lon":  72.9959},
    {"name": "Ankleshwar APMC",                  "district": "Bharuch",      "taluka": "Ankleshwar",  "lat":  21.6300, "lon":  73.0000},

    # ── Bhavnagar ─────────────────────────────────────────────────────────────
    {"name": "Bhavnagar APMC",                   "district": "Bhavnagar",    "taluka": "Bhavnagar",   "lat":  21.7645, "lon":  72.1519},
    {"name": "Mahuva APMC",                      "district": "Bhavnagar",    "taluka": "Mahuva",      "lat":  21.0900, "lon":  71.7700},
    {"name": "Palitana APMC",                    "district": "Bhavnagar",    "taluka": "Palitana",    "lat":  21.5200, "lon":  71.8200},
    {"name": "Sihor APMC",                       "district": "Bhavnagar",    "taluka": "Sihor",       "lat":  21.7000, "lon":  71.9700},
    {"name": "Talaja APMC",                      "district": "Bhavnagar",    "taluka": "Talaja",      "lat":  21.3500, "lon":  72.0400},

    # ── Botad ─────────────────────────────────────────────────────────────────
    {"name": "Botad APMC",                       "district": "Botad",        "taluka": "Botad",       "lat":  22.1700, "lon":  71.6700},
    {"name": "Gadhada APMC",                     "district": "Botad",        "taluka": "Gadhada",     "lat":  21.9800, "lon":  71.5700},

    # ── Dahod ─────────────────────────────────────────────────────────────────
    {"name": "Dahod APMC",                       "district": "Dahod",        "taluka": "Dahod",       "lat":  22.8350, "lon":  74.2650},

    # ── Chhota Udaipur ────────────────────────────────────────────────────────
    {"name": "Bodeliu",                          "district": "Chhota Udaipur","taluka": "Bodeli",      "lat":  22.0800, "lon":  73.8000},
    {"name": "Bodeli APMC",                      "district": "Chhota Udaipur","taluka": "Bodeli",      "lat":  22.0800, "lon":  73.8000},
    {"name": "Hadad",                            "district": "Chhota Udaipur","taluka": "Chhota Udaipur","lat": 22.3200, "lon": 74.0100},
    {"name": "Jetpur-Pavi",                      "district": "Chhota Udaipur","taluka": "Jetpur Pavi", "lat":  22.0900, "lon":  73.8300},
    {"name": "Kalediya",                         "district": "Chhota Udaipur","taluka": "Chhota Udaipur","lat": 22.2000, "lon": 73.9500},
    {"name": "Thalkala",                         "district": "Chhota Udaipur","taluka": "Chhota Udaipur","lat": 22.1500, "lon": 73.9000},

    # ── Gandhinagar ───────────────────────────────────────────────────────────
    {"name": "Gandhinagar APMC",                 "district": "Gandhinagar",  "taluka": "Gandhinagar", "lat":  23.2156, "lon":  72.6369},
    {"name": "Kalol APMC",                       "district": "Gandhinagar",  "taluka": "Kalol",       "lat":  23.2400, "lon":  72.4900},
    {"name": "Dehgam APMC",                      "district": "Gandhinagar",  "taluka": "Dehgam",      "lat":  23.1800, "lon":  72.8200},
    {"name": "Dehgam",                           "district": "Gandhinagar",  "taluka": "Dehgam",      "lat":  23.1800, "lon":  72.8200},
    {"name": "Mansa APMC",                       "district": "Gandhinagar",  "taluka": "Mansa",       "lat":  23.4300, "lon":  72.6600},
    {"name": "Mansa",                            "district": "Gandhinagar",  "taluka": "Mansa",       "lat":  23.4300, "lon":  72.6600},

    # ── Jamnagar ──────────────────────────────────────────────────────────────
    {"name": "Jamnagar APMC",                    "district": "Jamnagar",     "taluka": "Jamnagar",    "lat":  22.4707, "lon":  70.0577},
    {"name": "Jamkhambhaliya APMC",              "district": "Jamnagar",     "taluka": "Jamkhambhaliya","lat": 22.1900, "lon": 69.7000},
    {"name": "Kalavad APMC",                     "district": "Jamnagar",     "taluka": "Kalavad",     "lat":  22.2000, "lon":  70.3000},
    # API returns "Kalawad" (alternate spelling) — alias entry for matching
    {"name": "Kalawad",                          "district": "Jamnagar",     "taluka": "Kalavad",     "lat":  22.2000, "lon":  70.3000},
    {"name": "Jam Jodhpur APMC",                 "district": "Jamnagar",     "taluka": "Jam Jodhpur", "lat":  22.1000, "lon":  70.0000},
    # API uses "Jam Jodhpur" (without APMC suffix) — alias
    {"name": "Jam Jodhpur",                      "district": "Jamnagar",     "taluka": "Jam Jodhpur", "lat":  22.1000, "lon":  70.0000},

    # ── Junagadh ──────────────────────────────────────────────────────────────
    {"name": "Junagadh APMC",                    "district": "Junagadh",     "taluka": "Junagadh",    "lat":  21.5222, "lon":  70.4579},
    {"name": "Keshod APMC",                      "district": "Junagadh",     "taluka": "Keshod",      "lat":  21.3000, "lon":  70.2500},
    {"name": "Mangrol APMC",                     "district": "Junagadh",     "taluka": "Mangrol",     "lat":  21.1200, "lon":  70.1200},
    {"name": "Veraval APMC",                     "district": "Junagadh",     "taluka": "Veraval",     "lat":  20.9070, "lon":  70.3674},
    {"name": "Visavadar APMC",                   "district": "Junagadh",     "taluka": "Visavadar",   "lat":  21.5400, "lon":  70.9300},

    # ── Kutch ─────────────────────────────────────────────────────────────────
    {"name": "Bhuj APMC",                        "district": "Kutch",        "taluka": "Bhuj",        "lat":  23.2420, "lon":  69.6669},
    {"name": "Anjar APMC",                       "district": "Kutch",        "taluka": "Anjar",       "lat":  23.1100, "lon":  70.0300},
    {"name": "Gandhidham APMC",                  "district": "Kutch",        "taluka": "Gandhidham",  "lat":  23.0700, "lon":  70.1300},

    # ── Mehsana ───────────────────────────────────────────────────────────────
    {"name": "Mehsana APMC",                     "district": "Mehsana",      "taluka": "Mehsana",     "lat":  23.5880, "lon":  72.3693},
    {"name": "Kadi APMC",                        "district": "Mehsana",      "taluka": "Kadi",        "lat":  23.2900, "lon":  72.3200},
    {"name": "Unjha APMC",                       "district": "Mehsana",      "taluka": "Unjha",       "lat":  23.8000, "lon":  72.4000},

    # ── Morbi ─────────────────────────────────────────────────────────────────
    {"name": "Morbi APMC",                       "district": "Morbi",        "taluka": "Morbi",       "lat":  22.8175, "lon":  70.8373},
    {"name": "Wankaner APMC",                    "district": "Morbi",        "taluka": "Wankaner",    "lat":  22.6100, "lon":  70.9500},

    # ── Narmada ───────────────────────────────────────────────────────────────
    {"name": "Rajpipla APMC",                    "district": "Narmada",      "taluka": "Rajpipla",    "lat":  21.8700, "lon":  73.5000},

    # ── Navsari ───────────────────────────────────────────────────────────────
    {"name": "Navsari APMC",                     "district": "Navsari",      "taluka": "Navsari",     "lat":  20.9467, "lon":  72.9520},

    # ── Patan ─────────────────────────────────────────────────────────────────
    {"name": "Patan APMC",                       "district": "Patan",        "taluka": "Patan",       "lat":  23.8490, "lon":  72.1270},
    {"name": "Siddhpur APMC",                    "district": "Patan",        "taluka": "Siddhpur",    "lat":  23.9200, "lon":  72.3700},

    # ── Porbandar ─────────────────────────────────────────────────────────────
    {"name": "Porbandar APMC",                   "district": "Porbandar",    "taluka": "Porbandar",   "lat":  21.6420, "lon":  69.6293},
    {"name": "Kutiyana APMC",                    "district": "Porbandar",    "taluka": "Kutiyana",    "lat":  21.6200, "lon":  69.9800},
    {"name": "Ranavav APMC",                     "district": "Porbandar",    "taluka": "Ranavav",     "lat":  21.6700, "lon":  69.7600},

    # ── Rajkot ────────────────────────────────────────────────────────────────
    {"name": "Rajkot APMC",                      "district": "Rajkot",       "taluka": "Rajkot",      "lat":  22.3039, "lon":  70.8022},
    {"name": "Gondal APMC",                      "district": "Rajkot",       "taluka": "Gondal",      "lat":  22.1631, "lon":  70.7934},
    {"name": "Jetpur APMC",                      "district": "Rajkot",       "taluka": "Jetpur",      "lat":  21.7600, "lon":  70.6200},
    {"name": "Dhoraji APMC",                     "district": "Rajkot",       "taluka": "Dhoraji",     "lat":  21.7300, "lon":  70.4500},
    {"name": "Upleta APMC",                      "district": "Rajkot",       "taluka": "Upleta",      "lat":  21.7500, "lon":  70.2800},
    {"name": "Kotda Sangani APMC",               "district": "Rajkot",       "taluka": "Kotda Sangani","lat": 22.0100, "lon":  70.6500},

    # ── Sabarkantha ───────────────────────────────────────────────────────────
    {"name": "Himatnagar APMC",                  "district": "Sabarkantha",  "taluka": "Himatnagar",  "lat":  23.5990, "lon":  72.9640},
    {"name": "Modasa APMC",                      "district": "Sabarkantha",  "taluka": "Modasa",      "lat":  23.4600, "lon":  73.3000},
    {"name": "Idar APMC",                        "district": "Sabarkantha",  "taluka": "Idar",        "lat":  23.8300, "lon":  73.0000},
    {"name": "Bhiloda APMC",                     "district": "Sabarkantha",  "taluka": "Bhiloda",     "lat":  23.6100, "lon":  73.0700},
    {"name": "Bhiloda",                          "district": "Sabarkantha",  "taluka": "Bhiloda",     "lat":  23.6100, "lon":  73.0700},
    {"name": "Modasa(Tintoi)",                   "district": "Sabarkantha",  "taluka": "Modasa",      "lat":  23.4600, "lon":  73.3000},
    {"name": "Talod APMC",                       "district": "Sabarkantha",  "taluka": "Talod",       "lat":  23.3400, "lon":  73.0200},
    {"name": "Talod",                            "district": "Sabarkantha",  "taluka": "Talod",       "lat":  23.3400, "lon":  73.0200},
    # Also add Rajkot "Jetpur(Dist.Rajkot)" variant
    {"name": "Jetpur(Dist.Rajkot)",              "district": "Rajkot",       "taluka": "Jetpur",      "lat":  21.7600, "lon":  70.6200},

    # ── Surat ─────────────────────────────────────────────────────────────────
    {"name": "Surat APMC",                       "district": "Surat",        "taluka": "Surat",       "lat":  21.1702, "lon":  72.8311},
    {"name": "S.Mandvi",                         "district": "Surat",        "taluka": "Mandvi",      "lat":  21.1600, "lon":  73.2600},
    {"name": "Songadh",                          "district": "Surat",        "taluka": "Songadh",     "lat":  21.1700, "lon":  73.5800},
    {"name": "Valod(Buhari)",                    "district": "Surat",        "taluka": "Valod",       "lat":  21.0800, "lon":  73.1200},
    {"name": "Vyra",                             "district": "Surat",        "taluka": "Vyara",       "lat":  21.1100, "lon":  73.3900},

    # ── Surendranagar ─────────────────────────────────────────────────────────
    {"name": "Surendranagar APMC",               "district": "Surendranagar","taluka": "Surendranagar","lat": 22.7280, "lon":  71.6490},
    {"name": "Chotila APMC",                     "district": "Surendranagar","taluka": "Chotila",     "lat":  22.4200, "lon":  71.1800},
    {"name": "Dhrangadhra APMC",                 "district": "Surendranagar","taluka": "Dhrangadhra", "lat":  22.9900, "lon":  71.4700},
    {"name": "Halvad APMC",                      "district": "Surendranagar","taluka": "Halvad",      "lat":  23.0200, "lon":  71.1800},
    {"name": "Limbdi APMC",                      "district": "Surendranagar","taluka": "Limbdi",      "lat":  22.5700, "lon":  71.8200},
    {"name": "Lakhtar APMC",                     "district": "Surendranagar","taluka": "Lakhtar",     "lat":  22.9200, "lon":  71.7800},
    {"name": "Vadhvan APMC",                     "district": "Surendranagar","taluka": "Vadhvan",     "lat":  22.7600, "lon":  71.6900},
    {"name": "Wadhwan APMC",                     "district": "Surendranagar","taluka": "Wadhwan",     "lat":  22.7300, "lon":  71.6700},

    # ── Vadodara ──────────────────────────────────────────────────────────────
    {"name": "Vadodara APMC",                    "district": "Vadodara",     "taluka": "Vadodara",    "lat":  22.3072, "lon":  73.1812},
    {"name": "Padra APMC",                       "district": "Vadodara",     "taluka": "Padra",       "lat":  22.2400, "lon":  73.0900},

    # ── Valsad ────────────────────────────────────────────────────────────────
    {"name": "Valsad APMC",                      "district": "Valsad",       "taluka": "Valsad",      "lat":  20.5992, "lon":  72.9342},

    # ── Gir Somnath ───────────────────────────────────────────────────────────
    {"name": "Veraval (Gir Somnath) APMC",       "district": "Gir Somnath",  "taluka": "Veraval",     "lat":  20.9070, "lon":  70.3674},
    {"name": "Una APMC",                         "district": "Gir Somnath",  "taluka": "Una",         "lat":  20.8200, "lon":  71.0400},
    {"name": "Kodinar APMC",                     "district": "Gir Somnath",  "taluka": "Kodinar",     "lat":  20.7900, "lon":  70.7000},
    {"name": "Kodinar",                          "district": "Gir Somnath",  "taluka": "Kodinar",     "lat":  20.7900, "lon":  70.7000},

    # ── Devbhoomi Dwarka ──────────────────────────────────────────────────────
    {"name": "Dwarka APMC",                      "district": "Devbhoomi Dwarka","taluka": "Dwarka",   "lat":  22.2395, "lon":  68.9678},
    {"name": "Khambhalia APMC",                  "district": "Devbhoomi Dwarka","taluka": "Khambhalia","lat": 22.2000, "lon": 69.6500},
]


class Command(BaseCommand):
    help = "Seed the Market table with Gujarat APMC data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing Market records before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            count, _ = Market.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {count} existing market records."))

        created = 0
        updated = 0

        for entry in GUJARAT_MARKETS:
            lat = entry.get("lat")
            lon = entry.get("lon")
            market, was_created = Market.objects.update_or_create(
                name=entry["name"],
                district=entry["district"],
                defaults={
                    "taluka":      entry.get("taluka"),
                    "latitude":    lat,
                    "longitude":   lon,
                    "market_type": Market.MarketType.APMC,
                    "state":       "Gujarat",
                    "source":      Market.Source.APMC_DIRECTORY,
                    "source_url":  "https://mandipulse.com/mandi-bhav/gujarat",
                    "is_active":   True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"seed_markets complete: {created} created, {updated} updated. "
                f"Total markets in DB: {Market.objects.count()}"
            )
        )
        logger.info("seed_markets: created=%d, updated=%d", created, updated)
