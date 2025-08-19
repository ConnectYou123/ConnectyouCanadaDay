#!/usr/bin/env python3
"""
Ensure only the TOP 6 Toronto HVAC Technician providers remain active. All
other active Toronto HVAC providers will be switched to status="inactive" so
that the public list shows just six.

Run: python deactivate_extra_hvac.py
"""
from app import app, db
from models import ServiceProvider

CATEGORY = "HVAC"
CITY = "Toronto"
KEEP_LIMIT = 6

# Some providers may be stored with category "HVAC Technician" per earlier data
ALT_CATEGORY = "HVAC Technician"


def main():
    with app.app_context():
        providers = (
            ServiceProvider.query.filter(
                ServiceProvider.city == CITY,
                ServiceProvider.status == "active",
                ServiceProvider.service_category.in_([CATEGORY, ALT_CATEGORY]),
            )
            .order_by(ServiceProvider.star_rating.desc(), ServiceProvider.review_count.desc())
            .all()
        )

        if len(providers) <= KEEP_LIMIT:
            print(f"Only {len(providers)} active HVAC providers; nothing to deactivate.")
            return

        deactivate_providers = providers[KEEP_LIMIT:]
        for p in deactivate_providers:
            p.status = "inactive"
            print(f"Deactivated: {p.name} (rating {p.star_rating}, reviews {p.review_count})")

        try:
            db.session.commit()
            print(f"✅ Deactivated {len(deactivate_providers)} provider(s). {KEEP_LIMIT} remain active.")
        except Exception as exc:
            db.session.rollback()
            print(f"❌ Commit failed: {exc}")


if __name__ == "__main__":
    main() 