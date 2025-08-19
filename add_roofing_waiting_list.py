#!/usr/bin/env python3
"""
Add roofing providers to the waiting list (ServiceProviderReport) and mark
those entries as *approved* so they appear in the admin list/history.
Run: python add_roofing_waiting_list.py
"""
from datetime import datetime

from app import app, db
from models import ServiceProviderReport

PROVIDERS = [
    {
        "name": "T DOT Roofers Inc",
        "phone": "+1 416-451-9293",
        "address": "51 Sutherland Ave, Brampton, ON L6V 2H6",
        "rating": "5.0",
        "reviews": "41",
        "email": "",
    },
    {
        "name": "Luso Roofing & Contracting Inc. (Toronto)",
        "phone": "+1 416-877-2020",
        "address": "684 St Clarens Ave, Toronto, ON M6H 3X1",
        "rating": "5.0",
        "reviews": "39",
        "email": "info@lusoroofing.com",
    },
    {
        "name": "Professional Roofers Toronto",
        "phone": "+1 416-860-5976",
        "address": "Serves Ontario",
        "rating": "5.0",
        "reviews": "30",
        "email": "",
    },
    {
        "name": "High Skillz Roofing Inc.",
        "phone": "+1 647-704-3529",
        "address": "62 Alness St Unit 2-B, Toronto, ON M3J 2H1",
        "rating": "4.9",
        "reviews": "156",
        "email": "info@highskillzroofing.ca",
    },
    {
        "name": "Luso Roofing & Contracting Inc. (North York)",
        "phone": "+1 647-866-6213",
        "address": "684 St Clarens Ave, Toronto, ON M6H 3X1",
        "rating": "4.9",
        "reviews": "186",
        "email": "info@lusoroofing.com",
    },
    {
        "name": "Jimmy’s Roofing",
        "phone": "+1 647-854-3540",
        "address": "90 Bowie Ave, York, ON M6E 2P5",
        "rating": "4.9",
        "reviews": "79",
        "email": "jimmysroofing.ca@gmail.com",
    },
    {
        "name": "All Roofing Toronto",
        "phone": "+1 647-560-2688",
        "address": "19 Sabrina Dr, Etobicoke, ON M9R 2J4",
        "rating": "4.9",
        "reviews": "65",
        "email": "info@allroofingtoronto.ca",
    },
    {
        "name": "Nailed It Roofing & Construction Ltd.",
        "phone": "+1 905-997-3667",
        "address": "4141 Sladeview Crescent Unit 16, Mississauga, ON L5L 5T1",
        "rating": "4.8",
        "reviews": "227",
        "email": "info@naileditroofing.ca",
    },
    {
        "name": "Three Bro Squirrels Roofing Ltd.",
        "phone": "+1 647-284-9557",
        "address": "130 Gowan Ave #1015, East York, ON M4K 2E3",
        "rating": "4.8",
        "reviews": "119",
        "email": "info@3bsroofing.ca",
    },
    {
        "name": "TORONTO HD.ROOFING",
        "phone": "+1 647-766-8414",
        "address": "21 Arthur Griffith Dr, Toronto, ON M3L 2J9",
        "rating": "4.8",
        "reviews": "53",
        "email": "",
    },
]

SERVICE = "Roofing Specialist"


def main():
    with app.app_context():
        for p in PROVIDERS:
            # Skip if an entry already exists
            existing = ServiceProviderReport.query.filter_by(
                provider_name=p["name"], service=SERVICE, city="Toronto"
            ).first()
            if existing:
                print(f"Already exists: {p['name']}")
                continue

            application_details = f"""Service Provider Application:\nBusiness Name: {p['name']}\nService Category: {SERVICE}\nBusiness Phone: {p['phone']}\nBusiness Address: {p['address']}\nPrimary Email: {p['email']}\nRating: {p['rating']}\nNumber of Reviews: {p['reviews']}"""

            report = ServiceProviderReport(
                provider_name=p["name"],
                provider_phone=p["phone"],
                business_address=p["address"],
                service=SERVICE,
                city="Toronto",
                province="ON",
                rating=p["rating"],
                review_count=p["reviews"],
                report_reason="service_provider_application",
                other_reason=application_details,
                user_email=p["email"],
                message=p["description"] if (desc := p.get("description")) else "",
                status="approved",
                timestamp=datetime.utcnow(),
                is_hidden=False,
            )
            db.session.add(report)
            print(f"Waiting list entry added: {p['name']}")

        try:
            db.session.commit()
            print("✅ Waiting list entries created (approved).")
        except Exception as exc:
            db.session.rollback()
            print(f"❌ Failed to commit waiting list entries: {exc}")


if __name__ == "__main__":
    main() 