#!/usr/bin/env python3
"""
Normalize Toronto house-cleaning waiting-list entries: set service field to
"House Cleaning" and update other_reason to match, so they appear under the
same category as existing entries in the admin Waiting List dashboard.

Run: python update_housecleaning_category.py
"""
from app import app, db
from models import ServiceProviderReport

CITY = "Toronto"
OLD = "House Cleaner"
NEW = "House Cleaning"


def main():
    updated = 0
    with app.app_context():
        entries = ServiceProviderReport.query.filter_by(city=CITY, service=OLD).all()
        for e in entries:
            e.service = NEW
            if e.other_reason and OLD in e.other_reason:
                e.other_reason = e.other_reason.replace(OLD, NEW)
            updated += 1
        if updated:
            db.session.commit()
        print(f"Updated {updated} house-cleaning waiting list entries to service '{NEW}'.")


if __name__ == "__main__":
    main() 