"""
common/management/commands/seed_demo_data.py — Seed instant demo data for KrishiLink AI.
Creates:
- Demo Farmer: farmer_demo@krishilink.in / Password123!
- Demo Buyer: buyer_demo@krishilink.in / Password123!
- Demo Admin: admin_demo@krishilink.in / Password123!
- Realistic CropLots for Cotton and Groundnut
- Active marketplace listings across Gujarat districts
- Buyer purchase inquiries in various states
"""
from decimal import Decimal
from datetime import date
from django.core.management.base import BaseCommand
from apps.accounts.models import User, FarmerProfile, BuyerProfile
from apps.crops.models import CropLot
from apps.marketplace.models import CropListing, BuyerInquiry


class Command(BaseCommand):
    help = "Seed mock data and demo accounts for hackathon evaluation."

    def handle(self, *args, **options):
        self.stdout.write("Seeding KrishiLink AI demo data...")

        # 1. Demo Farmer
        farmer_user, _ = User.objects.get_or_create(
            email="farmer_demo@krishilink.in",
            defaults={
                "username": "ramesh_patel",
                "phone": "9876543210",
                "role": User.Role.FARMER,
            },
        )
        farmer_user.set_password("Password123!")
        farmer_user.save()

        farmer_profile, _ = FarmerProfile.objects.get_or_create(
            user=farmer_user,
            defaults={
                "district": "Rajkot",
                "taluka": "Gondal",
                "village": "Gondal",
                "latitude": Decimal("21.9619"),
                "longitude": Decimal("70.7937"),
                "pincode": "360311",
            },
        )

        # 2. Demo Buyer
        buyer_user, _ = User.objects.get_or_create(
            email="buyer_demo@krishilink.in",
            defaults={
                "username": "saurashtra_agro_traders",
                "phone": "9876543211",
                "role": User.Role.BUYER,
            },
        )
        buyer_user.set_password("Password123!")
        buyer_user.save()

        BuyerProfile.objects.get_or_create(
            user=buyer_user,
            defaults={
                "company_name": "Saurashtra Agro Exports Ltd",
                "business_type": "Wholesaler",
                "district": "Rajkot",
                "state": "Gujarat",
                "phone": "9876543211",
                "gst_number": "24AAAAA1234A1Z5",
                "is_verified": True,
            },
        )

        # 3. Demo Admin
        admin_user, _ = User.objects.get_or_create(
            email="admin_demo@krishilink.in",
            defaults={
                "username": "krishilink_admin",
                "phone": "9876543212",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.set_password("Password123!")
        admin_user.save()

        # 4. Crop Lots for Farmer
        lot_cotton, _ = CropLot.objects.get_or_create(
            farmer=farmer_profile,
            commodity="cotton",
            defaults={
                "variety": "Shankar-6",
                "quantity": Decimal("65.00"),
                "unit": "quintal",
                "moisture_percent": Decimal("7.50"),
                "quality_grade": "A",
                "harvest_date": date(2026, 8, 20),
                "storage_status": "farm",
                "notes": "Premium Shankar-6 cotton, low moisture, warehouse stored.",
                "is_active": True,
            },
        )

        lot_groundnut, _ = CropLot.objects.get_or_create(
            farmer=farmer_profile,
            commodity="groundnut",
            defaults={
                "variety": "GG-20",
                "quantity": Decimal("40.00"),
                "unit": "quintal",
                "moisture_percent": Decimal("6.20"),
                "quality_grade": "A",
                "harvest_date": date(2026, 8, 25),
                "storage_status": "warehouse",
                "notes": "High oil content GG-20 groundnut.",
                "is_active": True,
            },
        )

        # 5. Crop Marketplace Listings
        listing_1, _ = CropListing.objects.get_or_create(
            title="Premium Shankar-6 Cotton Lot (65 Qtl)",
            farmer=farmer_user,
            defaults={
                "crop_lot": lot_cotton,
                "commodity": "Cotton",
                "quantity_quintal": Decimal("65.00"),
                "expected_price_per_quintal": Decimal("7250.00"),
                "location_district": "Rajkot",
                "location_state": "Gujarat",
                "quality_grade": "Grade A",
                "description": "High staple length Shankar-6 cotton. Stored in dry shed in Gondal, ready for prompt pickup.",
                "status": CropListing.Status.ACTIVE,
                "is_active": True,
            },
        )

        listing_2, _ = CropListing.objects.get_or_create(
            title="High Oil GG-20 Groundnut Lot (40 Qtl)",
            farmer=farmer_user,
            defaults={
                "crop_lot": lot_groundnut,
                "commodity": "Groundnut",
                "quantity_quintal": Decimal("40.00"),
                "expected_price_per_quintal": Decimal("6600.00"),
                "location_district": "Junagadh",
                "location_state": "Gujarat",
                "quality_grade": "Grade A",
                "description": "Double filtered GG-20 groundnut with 48% oil content.",
                "status": CropListing.Status.ACTIVE,
                "is_active": True,
            },
        )

        # 6. Sample Buyer Inquiries
        BuyerInquiry.objects.get_or_create(
            listing=listing_1,
            buyer=buyer_user,
            defaults={
                "offered_price_per_quintal": Decimal("7200.00"),
                "requested_quantity_quintal": Decimal("65.00"),
                "message": "Ready to purchase entire 65 quintal lot with prompt RTGS payment.",
                "contact_phone": "9876543211",
                "status": BuyerInquiry.Status.PENDING,
            },
        )

        self.stdout.write(self.style.SUCCESS("[OK] Successfully seeded KrishiLink AI demo data!"))
        self.stdout.write("Demo accounts created:")
        self.stdout.write(" - Farmer: farmer_demo@krishilink.in / Password123!")
        self.stdout.write(" - Buyer:  buyer_demo@krishilink.in  / Password123!")
        self.stdout.write(" - Admin:  admin_demo@krishilink.in  / Password123!")
