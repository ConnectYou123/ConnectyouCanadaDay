#!/usr/bin/env python3
"""
Add 10 painting companies to Toronto's waiting list (ServiceProviderReport)
with status="approved". These entries will appear in Admin → Waiting List and
in the approved waiting list API but will NOT be shown on the main provider
cards because no ServiceProvider records are created.

Run: python add_painting_waiting_list.py
"""
from datetime import datetime

from app import app, db
from models import ServiceProviderReport

CITY = "Toronto"
PROVINCE = "ON"
CATEGORY = "Painter"

PROVIDERS = [
    {
        "name": "Paint My Condo | Toronto Condo Painters",
        "phone": "+1 877-720-6999",
        "address": "21 Vulcan St, Toronto ON M9W 1L3",
        "rating": "4.9",
        "reviews": "325",
        "email": "sales@paintmycondo.com",
        "description": "Onsite services · Online estimates · 10+ years in business",
    },
    {
        "name": "Encore Painting Ltd.",
        "phone": "+1 416-670-6589",
        "address": "43 McFarland Ave, Toronto, ON M6H 3N1",
        "rating": "4.9",
        "reviews": "249",
        "email": "info@encorepaintingltd.com",
        "description": "Online estimates · 15+ years in business",
    },
    {
        "name": "Five Star Painting of Midtown Toronto",
        "phone": "+1 437-291-5341",
        "address": "55 Peterborough Ave, Toronto, ON M6H 2K9",
        "rating": "4.9",
        "reviews": "95",
        "email": "",
        "description": "Online estimates · 3+ years in business",
    },
    {
        "name": "CertaPro Painters of Toronto, ON",
        "phone": "+1 416-620-4600",
        "address": "Toronto, ON",
        "rating": "4.9",
        "reviews": "85",
        "email": "CustomersForLife@certapro.com",
        "description": "10+ years in business",
    },
    {
        "name": "Bright Painting | Toronto Painting Company",
        "phone": "+1 647-723-9892",
        "address": "Toronto, ON",
        "rating": "4.9",
        "reviews": "82",
        "email": "frotan@bright-painting.ca",
        "description": "Onsite services · Online estimates · 15+ years in business",
    },
    {
        "name": "Condo Painters Pro",
        "phone": "+1 416-896-1071",
        "address": "18 Clubhouse Ct, Toronto, ON M3L 2K5",
        "rating": "4.9",
        "reviews": "79",
        "email": "condopainterspro@gmail.com",
        "description": "Onsite services · Online estimates · 20+ years in business",
    },
    {
        "name": "Home Painters Toronto",
        "phone": "+1 416-494-9095",
        "address": "3 Whitehorse Rd, Unit #8, North York, ON M3J 3G8",
        "rating": "4.9",
        "reviews": "37",
        "email": "Brian@HomePainterstoronto.com",
        "description": "Onsite services · Online estimates · 30+ years in business",
    },
    {
        "name": "Prestige Painting & Contracting Ltd.",
        "phone": "+1 905-264-6222",
        "address": "724 Caledonia Rd Unit 11, North York, ON M6B 4B3",
        "rating": "4.9",
        "reviews": "51",
        "email": "info@prestigepaintinggta.ca",
        "description": "Onsite services · Online estimates · 7+ years in business",
    },
    {
        "name": "Royal Home Painters",
        "phone": "+1 647-492-3993",
        "address": "44 Jackes Ave, Toronto, ON M4T 1E5",
        "rating": "4.8",
        "reviews": "109",
        "email": "Admin@RoyalHomePainters.ca",
        "description": "Onsite services · Online estimates · 10+ years in business",
    },
    {
        "name": "Dependable Painting",
        "phone": "+1 416-829-0006",
        "address": "Toronto ON M1L 4S1",
        "rating": "4.8",
        "reviews": "54",
        "email": "",
        "description": "Online estimates · 25+ years in business",
    },
]


def upsert_waiting_entry(p):
    existing = ServiceProviderReport.query.filter_by(
        provider_name=p["name"], service=CATEGORY, city=CITY
    ).first()
    if existing:
        existing.status = "approved"
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
        for p in PROVIDERS:
            upsert_waiting_entry(p)
        try:
            db.session.commit()
            print("✅ Painting providers added to waiting list and approved.")
        except Exception as exc:
            db.session.rollback()
            print(f"❌ Commit failed: {exc}")


if __name__ == "__main__":
    main() 