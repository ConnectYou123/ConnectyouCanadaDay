#!/usr/bin/env python3
"""
Populate the main Moving Services providers list for Barrie with the six
providers supplied by the user on 2025-07-12. The script will:

1. Add or update each listed provider, setting status="active".
2. Deactivate (status="inactive") any **other** Barrie Moving Services
   providers so only these six appear on the public site.

Run:  python add_moving_barrie_main.py
"""
import re
from datetime import datetime

from app import app, db
from models import ServiceProvider

CATEGORY = "Moving Services"
CITY = "Barrie"
PROVINCE = "ON"

PROVIDERS = [
    {
        "name": "Fast Track Move",
        "phone": "(647) 931-2328",
        "address": "14 Carluke Crescent, North York, ON M2L 2H8 (Serves Barrie)",
        "star": 5.0,
        "reviews": 867,
        "years": 9,
        "description": "Free estimate · Beat or match price · 9+ years in business",
    },
    {
        "name": "Shark Moving",
        "phone": "",  # Not listed
        "address": "Serves Barrie",
        "star": 5.0,
        "reviews": 237,
        "years": 6,
        "description": "6+ years in business",
    },
    {
        "name": "Top Rated Movers",
        "phone": "(705) 417-8882",
        "address": "Serves Barrie",
        "star": 5.0,
        "reviews": 207,
        "years": 4,
        "description": "Background checked · 4+ years in business",
    },
    {
        "name": "Like Father Like Son Movers",
        "phone": "(647) 993-4555",
        "address": "19 Pear Blossom Way, Holland Landing, ON L9N 0T3 (Serves Barrie)",
        "star": 5.0,
        "reviews": 199,
        "years": 6,
        "description": "Background checked · 6+ years in business",
        "email": "lflsmovers@gmail.com",
        "website": "http://lflsmovers.ca",
    },
    {
        "name": "Zagros Movers",
        "phone": "",  # Not listed
        "address": "Serves Barrie",
        "star": 5.0,
        "reviews": 190,
        "years": 6,
        "description": "6+ years in business",
    },
    {
        "name": "Kratos Moving Inc.",
        "phone": "",  # Not listed
        "address": "Serves Barrie",
        "star": 5.0,
        "reviews": 49,
        "years": 6,
        "description": "Accepts urgent jobs · Free estimate · 6+ years in business",
    },
]

def clean_phone(raw: str) -> str:
    """Normalize phone numbers to +1XXXXXXXXXX format when possible."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"+1{digits}"
    if digits.startswith("1"):
        return f"+{digits}"
    return raw.strip()

def upsert_provider(p: dict):
    phone_clean = clean_phone(p["phone"])
    provider = ServiceProvider.query.filter_by(name=p["name"], city=CITY).first()

    if provider:
        provider.phone = phone_clean
        provider.business_address = p["address"]
        provider.star_rating = p["star"]
        provider.review_count = p["reviews"]
        provider.description = p["description"]
        provider.service_category = CATEGORY
        provider.years_experience = p["years"]
        provider.email = p.get("email")
        provider.website = p.get("website")
        provider.status = "active"
        provider.updated_at = datetime.utcnow()
        print(f"Updated provider: {p['name']}")
    else:
        provider = ServiceProvider(
            name=p["name"],
            phone=phone_clean,
            email=p.get("email"),
            website=p.get("website"),
            business_address=p["address"],
            city=CITY,
            province=PROVINCE,
            postal_code="",
            service_category=CATEGORY,
            star_rating=p["star"],
            review_count=p["reviews"],
            description=p["description"],
            years_experience=p["years"],
            status="active",
            insurance_verified=True,
            background_checked=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(provider)
        print(f"Added provider: {p['name']}")

def deactivate_others(active_names: set):
    """Deactivate any Barrie Moving Services providers not in active_names."""
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
            print(f"✅ Barrie providers upserted. {deactivated_count} other provider(s) set to inactive.")
        except Exception as exc:
            db.session.rollback()
            print(f"❌ Commit failed: {exc}")

if __name__ == "__main__":
    main() 