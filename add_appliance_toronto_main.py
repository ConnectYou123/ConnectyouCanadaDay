#!/usr/bin/env python3
"""
Populate the main Appliance Repair Technician providers list for Toronto with
exactly the six providers supplied by the user on 2025-07-11. The script will:

1. Add or update each listed provider, setting status="active".
2. Deactivate (status="inactive") any **other** Toronto Appliance Repair
   Technician providers so only these six appear on the public site.

Run:  python add_appliance_toronto_main.py
"""
from datetime import datetime
import re

from app import app, db
from models import ServiceProvider

CATEGORY = "Appliance Repair Technician"
CITY = "Toronto"
PROVINCE = "ON"

PROVIDERS = [
    {
        "name": "Total Care Appliance Repair",
        "phone": "+1 647-308-8103",
        "address": "70 Angelina Ave, Woodbridge, ON L4L 8N9",
        "rating": 5.0,
        "reviews": 196,
        "email": "support@totalcareappliance.com",
        "description": (
            "Repair of refrigerators, freezers, electric/gas ranges, dishwashers, "
            "washers & dryers; certified technicians and 30-day parts & labour warranty"
        ),
    },
    {
        "name": "Infinity Appliances Repair",
        "phone": "+1 416-565-6893",
        "address": "129 Gesher Crescent, Maple, ON L6A 0W9",
        "rating": 5.0,
        "reviews": 161,
        "email": "infinityappliancesrepair@gmail.com",
        "description": (
            "Repairs for fridges, ovens, dishwashers, washers & dryers; same-day "
            "diagnostics, call/text support, emergency service"
        ),
    },
    {
        "name": "Appliance Bureau Canada",
        "phone": "+1 647-575-6323",
        "address": "Unit 1, 1981 Boylen Rd, Mississauga, ON L5S 1R9",
        "rating": 5.0,
        "reviews": 88,
        "email": "appliancebureau@gmail.com",
        "description": (
            "In-store sales/pickup/delivery of washers, dryers, dishwashers, "
            "refrigerators, ranges, microwaves; appliance servicing"
        ),
    },
    {
        "name": "Canada Appliance Solution",
        "phone": "+1 647-454-7788",
        "address": "111 Micarta Ave, Brampton, ON L6P 3Z3",
        "rating": 5.0,
        "reviews": 56,
        "email": "info@canadaappliancesolution.com",
        "description": (
            "Repairs for refrigerators, ranges, dishwashers, washers & dryers; "
            "diagnostic visits and service warranty"
        ),
    },
    {
        "name": "247 Appliance Service",
        "phone": "+1 416-628-1090",
        "address": "425 Alness St Unit 201, North York, ON M3J 2T8",
        "rating": 5.0,
        "reviews": 40,
        "email": "contact@247applianceservice.ca",
        "description": (
            "Repairs for ovens, fridges, dishwashers, washers, dryers, stoves; "
            "emergency & after-hours service"
        ),
    },
    {
        "name": "Repair in Toronto",
        "phone": "+1 647-922-8244",
        "address": "Vaughan, ON (serves GTA)",
        "rating": 5.0,
        "reviews": 72,
        "email": "service@repairintoronto.ca",
        "description": (
            "Full appliance repair for fridges, freezers, ranges, dishwashers, "
            "washers & dryers; same-day and 24/7 emergency service"
        ),
    },
]


def clean_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"+1{digits}"
    if digits.startswith("1"):
        return f"+{digits}"
    return raw


def upsert_provider(p: dict):
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


def deactivate_others(active_names: set):
    """Set inactive any Toronto Appliance Repair Technician not in active_names."""
    others = (
        ServiceProvider.query.filter_by(city=CITY, service_category=CATEGORY, status="active")
        .filter(~ServiceProvider.name.in_(active_names))
        .all()
    )
    for p in others:
        p.status = "inactive"
        print(f"Deactivated: {p.name}")
    return len(others)


def main():
    with app.app_context():
        for p in PROVIDERS:
            upsert_provider(p)

        deactivated_count = deactivate_others({p["name"] for p in PROVIDERS})

        try:
            db.session.commit()
            print(
                f"✅ Providers upserted. {deactivated_count} other provider(s) set to inactive."
            )
        except Exception as exc:
            db.session.rollback()
            print(f"❌ Commit failed: {exc}")


if __name__ == "__main__":
    main() 