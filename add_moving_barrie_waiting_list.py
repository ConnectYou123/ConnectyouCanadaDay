#!/usr/bin/env python3
"""
Insert Moving Services providers into the Barrie waiting list (ServiceProviderReport).
All entries will be given status = "approved" and report_reason = "waiting_list" so
that they appear in the admin waiting-list view but are already approved.

Run:  python3 add_moving_barrie_waiting_list.py
"""

import sys
import os
from datetime import datetime

# Ensure project root is in path so that `app` and `models` can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, db  # noqa: E402
from models import ServiceProviderReport  # noqa: E402


CATEGORY = "Moving Services"
CITY = "Barrie"
PROVINCE = "ON"

# Providers supplied by the user (2025-07-12)
PROVIDERS = [
    {
        "name": "Proactive Movers Inc.",
        "rating": "4.9",
        "reviews": "367",
        "phone": "Not listed",
        "address": "Serves Barrie",
        "email": None,
        "years": "1 year"
    },
    {
        "name": "Best Way To Move Ltd",
        "rating": "4.9",
        "reviews": "210",
        "phone": "Not listed",
        "address": "Serves Barrie",
        "email": None,
        "years": "24+ years"
    },
    {
        "name": "Zeus Moving Services LTD",
        "rating": "4.9",
        "reviews": "152",
        "phone": "(647) 735-8207",
        "address": "28 College Crescent, Barrie, ON L4N 2W3",
        "email": None,
        "years": "8+ years"
    },
    {
        "name": "More Than Moving",
        "rating": "4.9",
        "reviews": "137",
        "phone": "Not listed",
        "address": "Serves Barrie",
        "email": None,
        "years": "3+ years"
    },
    {
        "name": "Let's Get Moving – Barrie Movers",
        "rating": "4.9",
        "reviews": "77",
        "phone": "Not listed",
        "address": "Serves Barrie",
        "email": None,
        "years": "2+ years"
    },
    {
        "name": "Velocity Movers",
        "rating": "4.9",
        "reviews": "47",
        "phone": "Not listed",
        "address": "Serves Barrie",
        "email": None,
        "years": "12+ years"
    },
    {
        "name": "Kratos Moving Inc.",
        "rating": "4.8",
        "reviews": "643",
        "phone": "Not listed",
        "address": "Serves Barrie",
        "email": None,
        "years": "15+ years"
    },
    {
        "name": "TouchWood Movers",
        "rating": "4.8",
        "reviews": "661",
        "phone": "(905) 917-1670",
        "address": "Serves Barrie",
        "email": None,
        "years": "6+ years"
    },
    {
        "name": "Superior Mover in Barrie",
        "rating": "4.8",
        "reviews": "49",
        "phone": "Not listed",
        "address": "30 Quarry Ridge Rd, Barrie, ON L4M 7G1",
        "email": None,
        "years": "32+ years"
    },
]


def add_waiting_list_providers():
    """Add each provider to ServiceProviderReport with status approved."""
    with app.app_context():
        for p in PROVIDERS:
            entry = ServiceProviderReport(
                provider_name=p["name"],
                provider_phone=p["phone"],
                business_address=p["address"],
                user_email=p["email"],
                rating=p["rating"],
                review_count=p["reviews"],
                message=f"Years in Business: {p['years']}",
                report_reason="waiting_list",
                service=CATEGORY,
                city=CITY,
                province=PROVINCE,
                timestamp=datetime.utcnow(),
                status="approved",
                is_hidden=False,
            )
            db.session.add(entry)
        db.session.commit()
        print(f"Successfully added {len(PROVIDERS)} Moving Services providers to the {CITY} waiting list.")


if __name__ == "__main__":
    add_waiting_list_providers() 