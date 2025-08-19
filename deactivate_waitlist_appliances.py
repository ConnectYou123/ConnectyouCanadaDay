#!/usr/bin/env python3
"""
Deactivate specific appliance-repair waiting-list providers so they no longer
appear in public provider listings (status → inactive).

Run: python deactivate_waitlist_appliances.py
"""
from app import app, db
from models import ServiceProvider

PROVIDER_NAMES = [
    "TRC Experts Appliance Repair",
    "Modern Appliance",
    "Kampen Appliance Service",
    "Promaster Appliance Repair",
    "Canada Appliance Repair",
    "Appliance Heroes",
    "Toronto Appliance Repairs",
    "Fast Appliance Repair Pro",
    "CN Appliance Repair Inc.",
    "Fix It Right Appliance Repair",
    "East Liberty Appliance Repair",
    "Appliance Doc",
]

CATEGORY = "Appliance Repair Technician"


def main():
    with app.app_context():
        changed = 0
        for name in PROVIDER_NAMES:
            # We scope by both name and category to avoid accidental matches.
            providers = ServiceProvider.query.filter_by(name=name, service_category=CATEGORY).all()
            for p in providers:
                if p.status != "inactive":
                    p.status = "inactive"
                    changed += 1
                    print(f"Set inactive: {p.name}")
        if changed:
            db.session.commit()
            print(f"✅ Updated {changed} provider record(s) to inactive.")
        else:
            print("No matching active providers found.")


if __name__ == "__main__":
    main() 