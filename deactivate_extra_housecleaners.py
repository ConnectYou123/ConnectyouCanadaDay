#!/usr/bin/env python3
"""
Keep only the TOP 6 Toronto House Cleaner providers visible to users and tidy
up category naming.

Actions:
1. Convert any active provider with service_category variants ('House Cleaning',
   'House Cleaning Specialist', etc.) to canonical 'House Cleaner'.
2. Among all active House Cleaner providers in Toronto, retain the six highest
   ranked (star rating, then review count) and set the rest to status='inactive'.

Run: python deactivate_extra_housecleaners.py
"""
from app import app, db
from models import ServiceProvider

CITY = "Toronto"
KEEP_LIMIT = 6
CANONICAL = "House Cleaner"
VARIANTS = {"House Cleaner", "House Cleaning", "House Cleaning Specialist", "House Cleaning Services"}


def main():
    with app.app_context():
        # Step 1: unify category names
        providers = ServiceProvider.query.filter(
            ServiceProvider.city == CITY,
            ServiceProvider.status == "active",
            ServiceProvider.service_category.in_(VARIANTS),
        ).all()
        for p in providers:
            if p.service_category != CANONICAL:
                p.service_category = CANONICAL
        db.session.commit()

        # Step 2: enforce top 6 limit
        unified = ServiceProvider.query.filter_by(
            city=CITY, status="active", service_category=CANONICAL
        ).order_by(
            ServiceProvider.star_rating.desc(),
            ServiceProvider.review_count.desc(),
        ).all()
        for idx, prov in enumerate(unified):
            if idx >= KEEP_LIMIT:
                prov.status = "inactive"
        db.session.commit()
        print(
            f"House Cleaner providers unified and trimmed. Active count now: {min(len(unified), KEEP_LIMIT)}")


if __name__ == "__main__":
    main() 