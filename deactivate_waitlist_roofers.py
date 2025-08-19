#!/usr/bin/env python3
"""
Deactivate specific waiting-list roofing providers so they no longer appear in
frontend listings (status -> inactive).
Run: python deactivate_waitlist_roofers.py
"""
from app import app, db
from models import ServiceProvider

PROVIDER_NAMES = [
    "T DOT Roofers Inc",
    "Luso Roofing & Contracting Inc. (Toronto)",
    "Professional Roofers Toronto",
    "High Skillz Roofing Inc.",
    "Luso Roofing & Contracting Inc. (North York)",
    "Jimmy’s Roofing",
    "All Roofing Toronto",
    "Nailed It Roofing & Construction Ltd.",
    "Three Bro Squirrels Roofing Ltd.",
    "TORONTO HD.ROOFING",
]

CATEGORY = "Roofing Specialist"


def main():
    with app.app_context():
        changed = 0
        for name in PROVIDER_NAMES:
            providers = ServiceProvider.query.filter_by(name=name, service_category=CATEGORY).all()
            for p in providers:
                if p.status != "inactive":
                    p.status = "inactive"
                    changed += 1
                    print(f"Set inactive: {p.name}")
        if changed:
            db.session.commit()
            print(f"✅ Updated {changed} provider records to inactive.")
        else:
            print("No matching active providers found.")


if __name__ == "__main__":
    main() 