
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import ServiceProviderReport

def add_hvac_to_waiting_list():
    """Adds a list of HVAC providers to the waiting list for Toronto."""
    providers = [
        {
            "name": "4Seasons HVAC", "rating": "4.8", "reviews": "2300", "phone": "+1 647-887-0099",
            "address": "750 Oakdale Rd #26, North York, ON M3N 2Z4", "email": "info@4sdc.ca",
            "years": "3+ years"
        },
        {
            "name": "Climax Heating & Air Conditioning", "rating": "4.9", "reviews": "504", "phone": "+1 416-499-8039",
            "address": "588 Gordon Baker Rd #586, North York, ON M2H 3B4", "email": "info@climaxair.ca",
            "years": "10+ years"
        },
        {
            "name": "Tempasure Heating and Air Conditioning", "rating": "4.9", "reviews": "465", "phone": "+1 416-806-6111",
            "address": "877 Alness St Suite 25, North York, ON M3J 2X4", "email": "web: https://tempasure.com/contact-us/",
            "years": "20+ years"
        },
        {
            "name": "DeMark Home Ontario", "rating": "4.9", "reviews": "206", "phone": "+1 647-847-2998",
            "address": "4255 Weston Rd unit-B, Toronto, ON M9L 1W8", "email": "Web: https://www.dhontario.com/contact/",
            "years": "20+ years"
        },
        {
            "name": "AccuServ Heating and Air Conditioning", "rating": "4.9", "reviews": "395", "phone": "+1 416-269-2228",
            "address": "1167 Woodbine Ave, East York, ON M4C 4C6", "email": "info@accuservheating.com",
            "years": "10+ years"
        },
        {
            "name": "Laird & Son Heating & Air Conditioning", "rating": "4.8", "reviews": "905", "phone": "+1 416-421-2121",
            "address": "120 Dynamic Dr #22, Toronto, ON M1V 5C8", "email": "web: https://www.lairdandson.com/contact/",
            "years": "75+ years"
        },
        {
            "name": "City Home Comfort", "rating": "4.8", "reviews": "611", "phone": "+1 416-556-8368",
            "address": "710 Kingston Rd, Toronto, ON M4E 1R7", "email": "info@cityhomecomfort.com",
            "years": "40+ years"
        },
        {
            "name": "Aire Max Heating & Cooling Inc.", "rating": "4.8", "reviews": "326", "phone": "+1 416-843-1321",
            "address": "647 Sheppard Ave W, North York, ON M3H 2S4", "email": "info@airemax.ca",
            "years": "15+ years"
        },
        {
            "name": "Green Heating and Air Inc.", "rating": "4.8", "reviews": "143", "phone": "+1 416-627-7724",
            "address": "1373 Bathurst St, Toronto, ON M5R 3H8", "email": None,
            "years": "15+ years"
        }
    ]

    with app.app_context():
        for provider in providers:
            entry = ServiceProviderReport(
                provider_name=provider['name'],
                provider_phone=provider['phone'],
                business_address=provider['address'],
                user_email=provider['email'],
                rating=provider['rating'],
                review_count=provider['reviews'],
                message=f"Years in Business: {provider['years']}",
                report_reason='waiting_list',
                service='HVAC',
                city='Toronto',
                timestamp=datetime.utcnow(),
                status='pending',
                is_hidden=False
            )
            db.session.add(entry)
        
        db.session.commit()
        print(f"Successfully added {len(providers)} HVAC providers to the Toronto waiting list.")

if __name__ == '__main__':
    add_hvac_to_waiting_list() 