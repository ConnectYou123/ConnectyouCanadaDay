#!/usr/bin/env python3
"""
Promote all approved waiting-list entries for Toronto House Cleaners into the
main ServiceProvider table. Skips duplicates. Also converts their
report_reason to 'service_provider_application' (if still 'waiting_list') so
admin dashboards count them as approved applications.

Run: python promote_housecleaners_waiting_list.py
"""
from datetime import datetime

from app import app, db
from models import ServiceProvider, ServiceProviderReport

CITY = "Toronto"
CATEGORY = "House Cleaner"
ALT_CATEGORIES = {"House Cleaning", "House Cleaning Services", "Housecleaning"}
PROVINCE_DEFAULT = "ON"


def map_category(raw: str) -> str:
    """Map raw service string to canonical category name."""
    if not raw:
        return CATEGORY
    raw_lower = raw.lower()
    if raw_lower in {x.lower() for x in ALT_CATEGORIES}:
        return CATEGORY
    return raw.strip()


def promote():
    promoted = 0
    updated = 0
    # Get all approved waiting list entries for Toronto house cleaning
    entries = (
        ServiceProviderReport.query.filter(
            ServiceProviderReport.city == CITY,
            ServiceProviderReport.status == "approved",
            ServiceProviderReport.service.in_([CATEGORY, *ALT_CATEGORIES]),
        ).all()
    )

    for entry in entries:
        # Ensure dashboard treats it as approved application
        if entry.report_reason == "waiting_list":
            entry.report_reason = "service_provider_application"
            updated += 1

        # Skip if provider already exists (match by name and phone)
        existing = ServiceProvider.query.filter_by(
            name=entry.provider_name, phone=entry.provider_phone
        ).first()
        if existing:
            continue

        provider = ServiceProvider(
            name=entry.provider_name,
            phone=entry.provider_phone,
            business_address=entry.business_address or "",
            city=entry.city or CITY,
            province=entry.province or PROVINCE_DEFAULT,
            postal_code=entry.postal_code or "",
            service_category=map_category(entry.service),
            star_rating=float(entry.rating) if entry.rating else 4.5,
            review_count=int(entry.review_count) if entry.review_count else 0,
            website=entry.google_reviews_link or None,
            email=entry.user_email or None,
            status="active",
            created_at=datetime.utcnow(),
        )
        db.session.add(provider)
        promoted += 1
        print(f"Added ServiceProvider: {provider.name}")

    db.session.commit()
    print(f"✅ Promotion complete. Added {promoted} providers, updated {updated} reports.")


if __name__ == "__main__":
    with app.app_context():
        promote() 