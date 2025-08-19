
import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import ServiceProviderReport

def add_more_providers():
    providers = [
        {
            "name": "MANOS Handyman",
            "rating": "4.9",
            "reviews": "40",
            "phone": "(647) 339-6313",
            "address": "2170 Dufferin St, York, ON M6E 3R8",
            "email": None,
            "years": "15+ years"
        },
        {
            "name": "Seaton Village Handyman",
            "rating": "4.9",
            "reviews": "35",
            "phone": "(416) 838-3980",
            "address": None,
            "email": None,
            "years": "3+ years"
        },
        {
            "name": "Fix-It Friend",
            "rating": "4.8",
            "reviews": "275",
            "phone": "(416) 910-2003",
            "address": "208 Gerrard St E Unit 1, Toronto, ON M5A 2E6",
            "email": None,
            "years": "7+ years"
        }
    ]

    with app.app_context():
        for p in providers:
            entry = ServiceProviderReport(
                provider_name=p["name"],
                provider_phone=p["phone"],
                business_address=p["address"],
                user_email=p["email"],
                rating=p["rating"],
                review_count=p["reviews"],
                message=f"Years in Business: {p['years']}",
                report_reason='waiting_list',
                service='General Handyman',
                city='Toronto',
                timestamp=datetime.utcnow(),
                status='approved',
                is_hidden=False
            )
            db.session.add(entry)
        db.session.commit()
        print(f"Successfully added {len(providers)} more handyman providers to waiting list.")

if __name__ == '__main__':
    add_more_providers() 