#!/usr/bin/env python3
"""
Add 8 house-cleaning companies to Toronto's waiting list (ServiceProviderReport)
with status="approved". These records will appear in Admin → Waiting List and
via the waiting-list API, but they will NOT be shown on the main provider
cards because no ServiceProvider entries are created.

Run:  python add_housecleaning_waiting_list.py
"""
from datetime import datetime

from app import app, db
from models import ServiceProviderReport

CITY = "Toronto"
PROVINCE = "ON"
CATEGORY = "House Cleaner"

PROVIDERS = [
    {
        "name": "King Quality Cleaning Services",
        "phone": "+1 437-770-8080",
        "address": "17 Desert View Crescent, Richmond Hill, Ontario",
        "rating": "4.9",
        "reviews": "167",
        "email": "contact@kingquality.ca",
        "description": "Free in-home estimate · Flat rate pricing · 4+ years in business",
    },
    {
        "name": "Clean Proper",
        "phone": "+1 647-695-6878",
        "address": "872 Sheppard Ave W, North York, ON M3H 5V5",
        "rating": "4.9",
        "reviews": "98",
        "email": "",
        "description": "Professional cleaning service · Opens 8 a.m.",
    },
    {
        "name": "MOLLY MAID Toronto North",
        "phone": "+1 416-342-5476",
        "address": "821 Eglinton Ave W Suite 202, Toronto, ON M5N 1E6",
        "rating": "4.9",
        "reviews": "80",
        "email": "info@mollymaid.ca",
        "description": "3+ years in business · Opens 7:30 a.m.",
    },
    {
        "name": "Toronto Shine Cleaning",
        "phone": "+1 647-424-0355",
        "address": "140 Yonge St Suite 285, Toronto, ON M5C 1X6",
        "rating": "4.8",
        "reviews": "348",
        "email": "support@torontoshinecleaning.ca",
        "description": "5+ years in business · Opens 9 a.m.",
    },
    {
        "name": "Enjoy House Cleaning",
        "phone": "+1 416-909-1590",
        "address": "705 Lawrence Ave W #201, North York, ON M6A 1B4",
        "rating": "4.8",
        "reviews": "291",
        "email": "enjoyhousecleaning@hotmail.com",
        "description": "7+ years in business · Opens 8 a.m.",
    },
    {
        "name": "Master maid",
        "phone": "+1 647-888-8441",
        "address": "275 Shuter St Unit 707, Toronto, ON M5A 1W4",
        "rating": "4.8",
        "reviews": "285",
        "email": "info@mastermaid.ca",
        "description": "10+ years in business · Opens 9 a.m.",
    },
    {
        "name": "Dhyana Cleaning",
        "phone": "+1 647-642-7487",
        "address": "554 Palmerston Ave, Toronto, ON M6G 2P7",
        "rating": "4.8",
        "reviews": "174",
        "email": "info@dhyanacleaning.com",
        "description": "10+ years in business · Closes 9 p.m.",
    },
    {
        "name": "Elite Housekeeping",
        "phone": "+1 416-540-8205",
        "address": "111 Queen St E Suite #450, Toronto, ON M5C 1S2",
        "rating": "4.8",
        "reviews": "165",
        "email": "info@elitehousekeeping.ca",
        "description": "7+ years in business · Opens 8:30 a.m.",
    },
]


def upsert_waiting_entry(p):
    """Insert or update a waiting-list entry for a provider."""
    existing = ServiceProviderReport.query.filter_by(
        provider_name=p["name"], service=CATEGORY, city=CITY
    ).first()
    if existing:
        existing.status = "approved"
        existing.other_reason = p.get("description", "")
        print(f"Updated waiting entry: {p['name']}")
        return

    details = (
        f"Service Provider Application:\nBusiness Name: {p['name']}\n"
        f"Service Category: {CATEGORY}\nBusiness Phone: {p['phone']}\n"
        f"Business Address: {p['address']}\nPrimary Email: {p['email']}\n"
        f"Star Rating: {p['rating']}\nNumber of Reviews: {p['reviews']}"
    )

    report = ServiceProviderReport(
        provider_name=p["name"],
        provider_phone=p["phone"],
        business_address=p["address"],
        service=CATEGORY,
        city=CITY,
        province=PROVINCE,
        rating=p["rating"],
        review_count=p["reviews"],
        report_reason="service_provider_application",
        other_reason=details,
        user_email=p["email"],
        message=p["description"],
        status="approved",
        timestamp=datetime.utcnow(),
        is_hidden=False,
    )
    db.session.add(report)
    print(f"Added waiting entry: {p['name']}")


def main():
    with app.app_context():
        for prov in PROVIDERS:
            upsert_waiting_entry(prov)
        try:
            db.session.commit()
            print("✅ House-cleaning providers added to waiting list and approved.")
        except Exception as exc:
            db.session.rollback()
            print(f"❌ Commit failed: {exc}")


if __name__ == "__main__":
    main() 