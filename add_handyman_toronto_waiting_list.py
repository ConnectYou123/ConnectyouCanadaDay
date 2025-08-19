
import sys
import os
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import ServiceProviderReport

def add_handyman_to_waiting_list():
    """Adds General Handyman providers to Toronto waiting list (status = approved)."""
    providers = [
        {
            "name": "X-Engineer Handyman Services",
            "rating": "4.9",
            "reviews": "77",
            "phone": "+1 647-749-5888",
            "address": "15 Roehampton Ave, Toronto, ON M4P 0C2",
            "email": "hello@xengineer.ca",
            "years": "Not listed"
        },
        {
            "name": "Mike the Downtown Handyman",
            "rating": "4.9",
            "reviews": "57",
            "phone": "+1 647-989-7217",
            "address": "1163 Lansdowne Ave, Toronto, ON M6H 3Z7",
            "email": "mikethedowntownhandyman@gmail.com",
            "years": "10+ years"
        },
        {
            "name": "Konrad Handyman Home Repairs",
            "rating": "4.9",
            "reviews": "57",
            "phone": "(647) 720-4548",
            "address": "707 Finch Ave W, North York, ON M3H 4X6",
            "email": None,
            "years": "3+ years"
        },
        {
            "name": "TheFixitGuys General Contracting and Construction",
            "rating": "4.9",
            "reviews": "46",
            "phone": "(289) 266-3967",
            "address": "3300 Hwy 7 #600, Vaughan, ON L4K 0G2",
            "email": "Info@thefixitguys.ca",
            "years": "Not listed"
        }
    ]

    with app.app_context():
        for provider in providers:
            entry = ServiceProviderReport(
                provider_name=provider["name"],
                provider_phone=provider["phone"],
                business_address=provider["address"],
                user_email=provider["email"],
                rating=provider["rating"],
                review_count=provider["reviews"],
                message=f"Years in Business: {provider['years']}",
                report_reason='waiting_list',
                service='General Handyman',
                city='Toronto',
                timestamp=datetime.utcnow(),
                status='approved',
                is_hidden=False
            )
            db.session.add(entry)

        db.session.commit()
        print(f"Successfully added {len(providers)} General Handyman providers to the Toronto waiting list.")

if __name__ == '__main__':
    add_handyman_to_waiting_list() 