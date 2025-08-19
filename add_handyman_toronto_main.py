#!/usr/bin/env python3
"""
Populate Toronto's General Handyman providers so that ONLY the six specified
companies are active on the public site *and* visible in the Admin → Waiting
List.  Steps performed:

1. Upsert the six providers into `service_provider` with status="active" and
   updated rating / review counts.
2. Deactivate (`status='inactive'`) any other **active** Toronto General
   Handyman providers so they disappear from the public list.
3. Ensure `service_provider_report` has exactly those six entries for Toronto
   General Handyman with `status='approved'` and `is_hidden=False`.
   All other Toronto General Handyman reports are hidden (`is_hidden=True`).

Run:
    python add_handyman_toronto_main.py
"""
from datetime import datetime
import re

from app import app, db
from models import ServiceProvider, ServiceProviderReport

CATEGORY = "General Handyman"
CITY = "Toronto"
PROVINCE = "ON"

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def clean_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"+1{digits}"
    if digits.startswith("1"):
        return f"+{digits}"
    return raw

# ---------------------------------------------------------------------------
# Canonical provider list (must match exactly 6)
# ---------------------------------------------------------------------------
PROVIDERS = [
    {
        "name": "Handld - Handyman on Demand",
        "phone": "+1 647-206-3243",
        "address": "38 Joe Shuster Way, Toronto, ON M6K 0A5",
        "star": 5.0,
        "reviews": 74,
        "email": "Info@HANDLD.ca",
        "years": 5,
    },
    {
        "name": "Consider it Fixed",
        "phone": "+1 437-984-6012",
        "address": "55 Halton St, Toronto, ON M6J 1R5",
        "star": 5.0,
        "reviews": 47,
        "email": "info@consideritfixed.ca",
    },
    {
        "name": "416 Handyman Toronto",
        "phone": "+1 647-835-2071",
        "address": "215 Fort York Blvd, Toronto, ON M5V 4A2",
        "star": 5.0,
        "reviews": 27,
        "email": "ken@416handymantoronto.com",
        "years": 3,
    },
    {
        "name": "ThingsDone.ca - Handyman Services",
        "phone": "+1 647-914-1515",
        "address": "50B Reggae Ln Unit. 1, York, ON M6C 2B4",
        "star": 5.0,
        "reviews": 27,
        "email": "hello@thingsdone.ca",
        "years": 7,
    },
    {
        "name": "Odd Job Handyman Services Toronto",
        "phone": "+1 416-520-1161",
        "address": "46 Noble St, Toronto, ON M6K 2C9",
        "star": 4.9,
        "reviews": 200,
        "email": "help@oddjob.ca",
        "years": 15,
    },
    {
        "name": "Star Handyman",
        "phone": "+1 647-629-2148",
        "address": "75 St Nicholas St, Toronto, ON M4Y 0A5",
        "star": 4.9,
        "reviews": 179,
        "email": "inquiry@starhandyman.ca",
        "years": 3,
    },
]

# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def upsert_providers():
    """Insert or update the 6 canonical providers and deactivate the rest."""
    names_set = {p["name"] for p in PROVIDERS}
    changed = 0

    # Deactivate others first
    others = ServiceProvider.query.filter(
        ServiceProvider.city == CITY,
        ServiceProvider.service_category == CATEGORY,
        ServiceProvider.status == "active",
        ~ServiceProvider.name.in_(names_set),
    ).all()
    for sp in others:
        sp.status = "inactive"
        sp.updated_at = datetime.utcnow()
        changed += 1

    # Upsert the canonical 6
    for p in PROVIDERS:
        sp = ServiceProvider.query.filter_by(city=CITY, service_category=CATEGORY, name=p["name"]).first()
        if sp is None:
            sp = ServiceProvider(
                name=p["name"],
                city=CITY,
                province=PROVINCE,
                service_category=CATEGORY,
                status="active",
            )
            db.session.add(sp)
        # Update common fields
        sp.phone = clean_phone(p["phone"])
        sp.business_address = p["address"]
        sp.star_rating = p["star"]
        sp.review_count = p["reviews"]
        sp.email = p.get("email")
        sp.years_experience = p.get("years")
        sp.status = "active"
        sp.updated_at = datetime.utcnow()
        changed += 1

    return changed


def update_waiting_list():
    """Ensure waiting list shows only these six providers approved."""
    visible_names = {p["name"] for p in PROVIDERS}
    changed = 0

    # Hide any other handyman reports for Toronto
    others = ServiceProviderReport.query.filter(
        ServiceProviderReport.city == CITY,
        ServiceProviderReport.service == CATEGORY,
        ~ServiceProviderReport.provider_name.in_(visible_names),
        ServiceProviderReport.is_hidden == False,
    ).all()
    for r in others:
        r.is_hidden = True
        r.updated_at = datetime.utcnow() if hasattr(r, "updated_at") else datetime.utcnow()
        changed += 1

    # Upsert reports for the canonical 6
    for p in PROVIDERS:
        r = ServiceProviderReport.query.filter_by(
            city=CITY,
            service=CATEGORY,
            provider_name=p["name"],
        ).first()
        if r is None:
            r = ServiceProviderReport(
                provider_name=p["name"],
                provider_phone=clean_phone(p["phone"]),
                business_address=p["address"],
                service=CATEGORY,
                city=CITY,
                province=PROVINCE,
                rating=str(p["star"]),
                review_count=str(p["reviews"]),
                report_reason="service_provider_application",
                other_reason=f"Added via script on {datetime.utcnow().date()}",
                status="approved",
                is_hidden=False,
            )
            db.session.add(r)
        else:
            r.provider_phone = clean_phone(p["phone"])
            r.business_address = p["address"]
            r.rating = str(p["star"])
            r.review_count = str(p["reviews"])
            r.status = "approved"
            r.is_hidden = False
        changed += 1
    return changed


def main():
    with app.app_context():
        total_changes = upsert_providers()
        total_changes += update_waiting_list()
        db.session.commit()
        print(f"Applied {total_changes} changes for Toronto General Handyman.")


if __name__ == "__main__":
    main() 