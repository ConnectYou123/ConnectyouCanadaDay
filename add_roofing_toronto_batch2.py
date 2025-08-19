#!/usr/bin/env python3
"""
Batch script to add/update additional Roofing Specialist providers for Toronto.
This script focuses on the 10 providers the user listed on 2025-07-11.
It will create or update each provider in the `service_provider` table with
status='active'.

Run via:  python add_roofing_toronto_batch2.py
"""
from datetime import datetime
import re
from app import app, db
from models import ServiceProvider


def clean_phone(raw: str) -> str:
    """Convert a phone string to +1XXXXXXXXXX format if possible."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"+1{digits}"
    if digits.startswith("1"):
        return f"+{digits}"
    return raw  # fallback

PROVIDERS = [
    {
        "name": "T DOT Roofers Inc",
        "phone": "+1 416-451-9293",
        "business_address": "51 Sutherland Ave, Brampton, ON L6V 2H6",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "L6V 2H6",
        "star_rating": 5.0,
        "review_count": 41,
        "description": "Roof Repair · Leak Diagnosis · Free Quotes",
        "specialties": "Roof Repair, Leak Diagnosis, Free Quotes",
    },
    {
        "name": "Luso Roofing & Contracting Inc. (Toronto)",
        "phone": "+1 416-877-2020",
        "business_address": "684 St Clarens Ave, Toronto, ON M6H 3X1",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "M6H 3X1",
        "star_rating": 5.0,
        "review_count": 39,
        "description": "Residential Roofing · Roof Repair · Eavestrough Cleaning",
        "specialties": "Residential Roofing, Roof Repair, Eavestrough Cleaning",
    },
    {
        "name": "Professional Roofers Toronto",
        "phone": "+1 416-860-5976",
        "business_address": "Serves Ontario",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "",
        "star_rating": 5.0,
        "review_count": 30,
        "description": "Roof Install & Repair · Roof Leak Repair",
        "specialties": "Roof Install & Repair, Roof Leak Repair",
    },
    {
        "name": "High Skillz Roofing Inc.",
        "phone": "+1 647-704-3529",
        "business_address": "62 Alness St Unit 2-B, Toronto, ON M3J 2H1",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "M3J 2H1",
        "star_rating": 4.9,
        "review_count": 156,
        "description": "Residential Roofing · Preventative Maintenance",
        "specialties": "Residential Roofing, Preventative Maintenance",
    },
    {
        "name": "Luso Roofing & Contracting Inc. (North York)",
        "phone": "+1 647-866-6213",
        "business_address": "684 St Clarens Ave, Toronto, ON M6H 3X1",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "M6H 3X1",
        "star_rating": 4.9,
        "review_count": 186,
        "description": "Roof Repair · Replacement · Maintenance · Leak Repair",
        "specialties": "Roof Repair, Replacement, Maintenance, Leak Repair",
    },
    {
        "name": "Jimmy’s Roofing",
        "phone": "+1 647-854-3540",
        "business_address": "90 Bowie Ave, York, ON M6E 2P5",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "M6E 2P5",
        "star_rating": 4.9,
        "review_count": 79,
        "description": "Roof Repair · Storm Damage Repair",
        "specialties": "Roof Repair, Storm Damage Repair",
    },
    {
        "name": "All Roofing Toronto",
        "phone": "+1 647-560-2688",
        "business_address": "19 Sabrina Dr, Etobicoke, ON M9R 2J4",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "M9R 2J4",
        "star_rating": 4.9,
        "review_count": 65,
        "description": "Flat Roofing · Emergency Repairs · Skylights",
        "specialties": "Flat Roofing, Emergency Repairs, Skylights",
    },
    {
        "name": "Nailed It Roofing & Construction Ltd.",
        "phone": "+1 905-997-3667",
        "business_address": "4141 Sladeview Crescent Unit 16, Mississauga, ON L5L 5T1",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "L5L 5T1",
        "star_rating": 4.8,
        "review_count": 227,
        "description": "Residential Roofing · We Don’t Use Sub-Contractors",
        "specialties": "Residential Roofing, No Sub-Contractors",
    },
    {
        "name": "Three Bro Squirrels Roofing Ltd.",
        "phone": "+1 647-284-9557",
        "business_address": "130 Gowan Ave #1015, East York, ON M4K 2E3",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "M4K 2E3",
        "star_rating": 4.8,
        "review_count": 119,
        "description": "Roof Repair · Leak Detection / Fixing",
        "specialties": "Roof Repair, Leak Detection & Fixing",
    },
    {
        "name": "TORONTO HD.ROOFING",
        "phone": "+1 647-766-8414",
        "business_address": "21 Arthur Griffith Dr, Toronto, ON M3L 2J9",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "M3L 2J9",
        "star_rating": 4.8,
        "review_count": 53,
        "description": "Residential Roofing · Roof Replacement",
        "specialties": "Residential Roofing, Roof Replacement",
    },
]

CATEGORY = "Roofing Specialist"


def upsert_provider(data: dict):
    phone_clean = clean_phone(data["phone"])
    provider = ServiceProvider.query.filter_by(name=data["name"], city="Toronto").first()

    if provider:
        # Update existing
        provider.phone = phone_clean
        provider.business_address = data["business_address"]
        provider.postal_code = data["postal_code"]
        provider.star_rating = data["star_rating"]
        provider.review_count = data["review_count"]
        provider.description = data["description"]
        provider.specialties = data["specialties"]
        provider.status = "active"
        provider.updated_at = datetime.utcnow()
        print(f"Updated: {provider.name}")
    else:
        # Create new
        new_provider = ServiceProvider(
            name=data["name"],
            phone=phone_clean,
            business_address=data["business_address"],
            city="Toronto",
            province=data["province"],
            postal_code=data["postal_code"],
            service_category=CATEGORY,
            star_rating=data["star_rating"],
            review_count=data["review_count"],
            description=data["description"],
            specialties=data["specialties"],
            status="active",
            insurance_verified=True,
            background_checked=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(new_provider)
        print(f"Added: {new_provider.name}")


def main():
    with app.app_context():
        for pdata in PROVIDERS:
            upsert_provider(pdata)

        try:
            db.session.commit()
            print("✅ Additional roofing providers inserted/updated successfully.")
        except Exception as exc:
            db.session.rollback()
            print(f"❌ Database commit failed: {exc}")


if __name__ == "__main__":
    main() 