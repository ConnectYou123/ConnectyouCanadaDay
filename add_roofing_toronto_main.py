#!/usr/bin/env python3
"""
Script to repopulate Toronto's main Roofing Specialist providers.
Adds or updates the six specified 5-star roofing companies and
sets any other existing Toronto roofing providers to inactive.

Run with: python add_roofing_toronto_main.py
"""

from datetime import datetime
import re

from app import app, db
from models import ServiceProvider

# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------

def clean_phone(raw: str) -> str:
    """Convert human-friendly phone to canonical +1XXXXXXXXXX format."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"+1{digits}"
    return f"+{digits}" if digits.startswith("1") else f"+1{digits}"

# ----------------------------------------------------------------------------
# Provider data
# ----------------------------------------------------------------------------

PROVIDERS = [
    {
        "name": "Coverall Roofing – Toronto",
        "phone": "+1 647-470-4076",
        "business_address": "1620A Dupont St, Toronto, ON M6P 3S7",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "M6P 3S7",
        "description": "Onsite services · Residential & Commercial Roofing · Free Estimates",
        "specialties": "Residential & Commercial Roofing, Free Estimates",
        "review_count": 154,
    },
    {
        "name": "Prime Roof Repairs",
        "phone": "+1 647-633-1917",
        "business_address": "151 Beecroft Rd, North York, ON M2N 7C4",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "M2N 7C4",
        "description": "Onsite services · Roof Repair · Pipe Boots & Flashing · Leak Diagnoses",
        "specialties": "Roof Repair, Pipe Boots & Flashing, Leak Diagnoses",
        "review_count": 141,
    },
    {
        "name": "Universal Roofs – Flat Roofing Services",
        "phone": "+1 416-732-2421",
        "business_address": "30 Braddock Rd, Etobicoke, ON M9W 5H8",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "M9W 5H8",
        "description": "Flat Roofing · Emergency Roof Repair · Skylight Installation",
        "specialties": "Flat Roofing, Emergency Roof Repair, Skylight Installation",
        "review_count": 97,
    },
    {
        "name": "The Roof Technician Toronto",
        "phone": "+1 416-826-0040",
        "business_address": "Serves Ontario",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "",
        "description": "Residential Roofing · Roof Replacement · Free Inspections",
        "specialties": "Residential Roofing, Roof Replacement, Free Inspections",
        "review_count": 69,
    },
    {
        "name": "Unique Roofing Limited",
        "phone": "+1 416-522-3063",
        "business_address": "266 Valleymede Dr, Richmond Hill, ON L4B 2C4",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "L4B 2C4",
        "description": "Asphalt Shingles · Leak Repair · Gutter & Eavestrough Services",
        "specialties": "Asphalt Shingles, Leak Repair, Gutter & Eavestrough Services",
        "review_count": 61,
    },
    {
        "name": "Apple Roofing Toronto",
        "phone": "+1 416-618-5846",
        "business_address": "Serves Toronto, ON",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "",
        "description": "Residential & Commercial Roofing · Roof Maintenance",
        "specialties": "Residential & Commercial Roofing, Roof Maintenance",
        "review_count": 44,
    },
]

CATEGORY = "Roofing Specialist"
STAR_RATING = 5.0

# ----------------------------------------------------------------------------
# Main logic
# ----------------------------------------------------------------------------

def repopulate_roofing():
    with app.app_context():
        # Step 1: Deactivate existing Toronto roofing providers not in the new list
        provider_names = {p["name"] for p in PROVIDERS}

        existing_roofers = ServiceProvider.query.filter_by(city="Toronto", service_category=CATEGORY).all()
        for roofer in existing_roofers:
            if roofer.name not in provider_names:
                if roofer.status != "inactive":
                    roofer.status = "inactive"
                    print(f"Set inactive: {roofer.name}")

        # Step 2: Add or update each provider from the list
        for data in PROVIDERS:
            phone_clean = clean_phone(data["phone"])

            provider = ServiceProvider.query.filter_by(name=data["name"], city="Toronto").first()
            if provider:
                # Update fields
                provider.phone = phone_clean
                provider.business_address = data["business_address"]
                provider.province = data["province"]
                provider.postal_code = data["postal_code"]
                provider.service_category = CATEGORY
                provider.star_rating = STAR_RATING
                provider.review_count = data["review_count"]
                provider.description = data["description"]
                provider.specialties = data["specialties"]
                provider.status = "active"
                provider.updated_at = datetime.utcnow()
                print(f"Updated: {provider.name}")
            else:
                # Create new provider
                new_provider = ServiceProvider(
                    name=data["name"],
                    phone=phone_clean,
                    email=data.get("email"),
                    business_address=data["business_address"],
                    city="Toronto",
                    province=data["province"],
                    postal_code=data["postal_code"],
                    service_category=CATEGORY,
                    star_rating=STAR_RATING,
                    review_count=data["review_count"],
                    description=data["description"],
                    specialties=data["specialties"],
                    years_experience=None,
                    insurance_verified=True,
                    background_checked=True,
                    status="active",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.session.add(new_provider)
                print(f"Added: {new_provider.name}")

        # Commit all changes
        try:
            db.session.commit()
            print("✅ Toronto Roofing Specialist providers repopulated successfully.")
        except Exception as exc:
            db.session.rollback()
            print(f"❌ Error committing changes: {exc}")


if __name__ == "__main__":
    repopulate_roofing() 