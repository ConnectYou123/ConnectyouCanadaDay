#!/usr/bin/env python3
"""
Add/Update Appliance Repair Technician providers for Toronto and create
corresponding approved waiting-list entries so they appear on both the
frontend and the admin waiting-list history.

Run: python add_appliance_toronto_batch.py
"""
from datetime import datetime
import re
from app import app, db
from models import ServiceProvider, ServiceProviderReport

CATEGORY = "Appliance Repair Technician"
CITY = "Toronto"
PROVINCE = "ON"


def clean_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"+1{digits}"
    if digits.startswith("1"):
        return f"+{digits}"
    return raw

PROVIDERS = [
    {
        "name": "TRC Experts Appliance Repair",
        "phone": "+1 437-837-0208",
        "address": "Serves all Ontario",
        "rating": 5.0,
        "reviews": 17,
        "email": "info@trcexperts.com",
        "description": "24-hour service covering all home appliances across Ontario, available day or night",
    },
    {
        "name": "Modern Appliance",
        "phone": "+1 416-457-2152",
        "address": "Toronto, ON (serves GTA)",
        "rating": 5.0,
        "reviews": 180,
        "email": "modernappliance@sympatico.ca",
        "description": "Repairs refrigerators, freezers, dryers, washers, dishwashers, ovens, gas appliances; insured technicians; 100% workmanship guarantee",
    },
    {
        "name": "Kampen Appliance Service",
        "phone": "+1 905-738-1687",
        "address": "141 Caster Ave, Woodbridge, ON L4L 5Y8",
        "rating": 4.9,
        "reviews": 1929,
        "email": "info@kampenappliance.com",
        "description": "Repairs for all major home appliances; in-home diagnostics, parts & warranty support",
    },
    {
        "name": "Promaster Appliance Repair",
        "phone": "+1 647-575-6835",
        "address": "30 Shore Breeze Dr unit 6208, Etobicoke, ON M8V 0J1",
        "rating": 4.9,
        "reviews": 476,
        "email": "info@promasterappliance.com",
        "description": "Repair services for refrigerators, ovens, dishwashers, washers & dryers; after-hours availability till 11 p.m.",
    },
    {
        "name": "Canada Appliance Repair",
        "phone": "+1 416-887-5839",
        "address": "325 Bogert Ave Unit L2, North York, ON M2N 1L8",
        "rating": 4.9,
        "reviews": 408,
        "email": "info@canadaappliancerepair.com",
        "description": "Repair services for fridges, ovens, washers, dryers, dishwashers; same-day service till 10 p.m.",
    },
    {
        "name": "Appliance Heroes",
        "phone": "+1 647-655-1003",
        "address": "1287 Caledonia Rd, North York, ON M6A 2X7",
        "rating": 4.9,
        "reviews": 266,
        "email": "support@applianceheroes.ca",
        "description": "Comprehensive appliance repairs; service includes washers, dryers, dishwashers, fridges & ovens; opens 9 a.m. Tue",
    },
    {
        "name": "Toronto Appliance Repairs",
        "phone": "+1 782-823-9813",
        "address": "43 Mammoth Hall Trail, Scarborough, ON M1B 1P5",
        "rating": 4.9,
        "reviews": 231,
        "email": "info@torontoappliancerepairs.ca",
        "description": "Repairs for home appliances province-wide, including emergency services; opens 9 a.m. Tue",
    },
    {
        "name": "Fast Appliance Repair Pro",
        "phone": "+1 416-900-3727",
        "address": "Ontario (province-wide)",
        "rating": 4.9,
        "reviews": 220,
        "email": "info@fastappliancerepairpro.ca",
        "description": "24-hour emergency repairs for all major appliances across Ontario",
    },
    {
        "name": "CN Appliance Repair Inc.",
        "phone": "+1 647-479-9711",
        "address": "33 Singer Ct #512, Toronto, ON M2K 0B4",
        "rating": 4.9,
        "reviews": 127,
        "email": "info@cnappliancerepair.ca",
        "description": "Repairs for fridges, washers & dryers, ovens, dishwashers; service hours till 11 p.m.",
    },
    {
        "name": "Fix It Right Appliance Repair",
        "phone": "+1 647-556-6228",
        "address": "7250 Keele St Unit 152, Concord, ON L4K 1Z8",
        "rating": 4.9,
        "reviews": 104,
        "email": "info@fixitrightappliances.ca",
        "description": "24-hour appliance repair for fridges, washers, dryers, ovens, dishwashers",
    },
    {
        "name": "East Liberty Appliance Repair",
        "phone": "+1 416-997-0494",
        "address": "Toronto, ON",
        "rating": 4.9,
        "reviews": 72,
        "email": "info@eastlibertyappliance.com",
        "description": "Repairs for all major home appliances; open until 10 p.m.",
    },
    {
        "name": "Appliance Doc",
        "phone": "+1 437-296-0384",
        "address": "970 Lawrence Ave W Suite 801, North York, ON M6A 3B6",
        "rating": 4.9,
        "reviews": 79,
        "email": "david@appliancedoc.ca",
        "description": "Repairs for fridges, washers, dryers, ovens & dishwashers; opens 8 a.m. Tue",
    },
]


def upsert_provider(p):
    phone_clean = clean_phone(p["phone"])
    provider = ServiceProvider.query.filter_by(name=p["name"], city=CITY).first()
    if provider:
        provider.phone = phone_clean
        provider.business_address = p["address"]
        provider.star_rating = p["rating"]
        provider.review_count = p["reviews"]
        provider.description = p["description"]
        provider.service_category = CATEGORY
        provider.status = "active"
        provider.updated_at = datetime.utcnow()
        print(f"Updated provider: {p['name']}")
    else:
        provider = ServiceProvider(
            name=p["name"],
            phone=phone_clean,
            email=p["email"],
            business_address=p["address"],
            city=CITY,
            province=PROVINCE,
            postal_code="",
            service_category=CATEGORY,
            star_rating=p["rating"],
            review_count=p["reviews"],
            description=p["description"],
            status="active",
            insurance_verified=True,
            background_checked=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(provider)
        print(f"Added provider: {p['name']}")


def upsert_waiting_entry(p):
    existing = ServiceProviderReport.query.filter_by(
        provider_name=p["name"], service=CATEGORY, city=CITY
    ).first()
    if existing:
        existing.status = "approved"
        print(f"Updated waiting entry: {p['name']}")
        return

    details = f"Service Provider Application:\nBusiness Name: {p['name']}\nService Category: {CATEGORY}\nBusiness Phone: {p['phone']}\nBusiness Address: {p['address']}\nPrimary Email: {p['email']}\nRating: {p['rating']}\nNumber of Reviews: {p['reviews']}"

    report = ServiceProviderReport(
        provider_name=p["name"],
        provider_phone=p["phone"],
        business_address=p["address"],
        service=CATEGORY,
        city=CITY,
        province=PROVINCE,
        rating=str(p["rating"]),
        review_count=str(p["reviews"]),
        report_reason="service_provider_application",
        other_reason=details,
        user_email=p["email"],
        message=p["description"],
        status="approved",
        timestamp=datetime.utcnow(),
        is_hidden=False,
    )
    db.session.add(report)
    print(f"Added waiting entry: {p['name']}")


def main():
    with app.app_context():
        for p in PROVIDERS:
            upsert_provider(p)
            upsert_waiting_entry(p)
        try:
            db.session.commit()
            print("✅ Appliance repair providers added/updated and waiting list entries approved.")
        except Exception as exc:
            db.session.rollback()
            print(f"❌ Commit failed: {exc}")


if __name__ == "__main__":
    main() 