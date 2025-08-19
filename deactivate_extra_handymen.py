#!/usr/bin/env python3
"""
Limit Toronto's General Handyman category to the TOP 6 providers (by star
rating then review count). Any other active Toronto General Handyman providers
will be set to status="inactive" so they no longer appear on the public list.

Run: python deactivate_extra_handymen.py
"""
from app import app, db
from models import ServiceProvider

CATEGORY = "General Handyman"
CITY = "Toronto"
KEEP_LIMIT = 6


def main():
    with app.app_context():
        # Fetch all active Toronto handymen
        providers = (
            ServiceProvider.query.filter_by(city=CITY, service_category=CATEGORY, status="active")
            .order_by(ServiceProvider.star_rating.desc(), ServiceProvider.review_count.desc())
            .all()
        )

        if len(providers) <= KEEP_LIMIT:
            print(f"Only {len(providers)} active providers, nothing to deactivate.")
            return

        keep_providers = providers[:KEEP_LIMIT]
        deactivate_providers = providers[KEEP_LIMIT:]

        for p in deactivate_providers:
            p.status = "inactive"
            print(f"Deactivated: {p.name} (rating {p.star_rating}, reviews {p.review_count})")

        try:
            db.session.commit()
            print(f"✅ Deactivated {len(deactivate_providers)} provider(s). {KEEP_LIMIT} top providers remain active.")
        except Exception as exc:
            db.session.rollback()
            print(f"❌ Commit failed: {exc}")


if __name__ == "__main__":
    main() 