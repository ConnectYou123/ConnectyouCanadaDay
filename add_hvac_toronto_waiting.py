from app import app, db
from models import ServiceProviderReport, City
from datetime import datetime

def add_hvac_providers():
    with app.app_context():
        providers = [
            {
                "name": "4Seasons HVAC",
                "phone": "+1 647-887-0099",
                "address": "750 Oakdale Rd #26, North York, ON M3N 2Z4",
                "email": "info@4sdc.ca",
                "years": "3+",
                "rating": "4.8",
                "reviews": "2300",
                "area": "North York & GTA",
                "description": "⭐ 4.8 (📌 2,300 reviews)\n📍 Serves North York & GTA\n✅ 3+ years in business"
            },
            {
                "name": "Climax Heating & Air Conditioning",
                "phone": "+1 416-499-8039",
                "address": "588 Gordon Baker Rd #586, North York, ON M2H 3B4",
                "email": "info@climaxair.ca",
                "years": "10+",
                "rating": "4.9",
                "reviews": "504",
                "area": "North York & GTA",
                "description": "⭐ 4.9 (📌 504 reviews)\n📍 Serves North York & GTA\n✅ 10+ years in business · Open 24 hours"
            },
            {
                "name": "Tempasure Heating and Air Conditioning",
                "phone": "+1 416-806-6111",
                "address": "877 Alness St Suite 25, North York, ON M3J 2X4",
                "email": "contact@tempasure.com",
                "years": "20+",
                "rating": "4.9",
                "reviews": "465",
                "area": "North York & GTA",
                "description": "⭐ 4.9 (📌 465 reviews)\n📍 Serves North York & GTA\n✅ 20+ years in business"
            },
            {
                "name": "DeMark Home Ontario",
                "phone": "+1 647-847-2998",
                "address": "4255 Weston Rd unit-B, Toronto, ON M9L 1W8",
                "email": "contact@dhontario.com",
                "years": "20+",
                "rating": "4.9",
                "reviews": "206",
                "area": "Toronto & GTA",
                "description": "⭐ 4.9 (📌 206 reviews)\n📍 Serves Toronto & GTA\n✅ 20+ years in business · Open 24 hours"
            },
            {
                "name": "AccuServ Heating and Air Conditioning",
                "phone": "+1 416-269-2228",
                "address": "1167 Woodbine Ave, East York, ON M4C 4C6",
                "email": "info@accuservheating.com",
                "years": "10+",
                "rating": "4.9",
                "reviews": "395",
                "area": "GTA",
                "description": "⭐ 4.9 (📌 395 reviews)\n📍 Serves GTA\n✅ 10+ years in business · Open 24 hours"
            },
            {
                "name": "Laird & Son Heating & Air Conditioning",
                "phone": "+1 416-421-2121",
                "address": "120 Dynamic Dr #22, Toronto, ON M1V 5C8",
                "email": "contact@lairdandson.com",
                "years": "75+",
                "rating": "4.8",
                "reviews": "905",
                "area": "Toronto",
                "description": "⭐ 4.8 (📌 905 reviews)\n📍 Serves Toronto\n✅ 75+ years in business"
            },
            {
                "name": "City Home Comfort",
                "phone": "+1 416-556-8368",
                "address": "710 Kingston Rd, Toronto, ON M4E 1R7",
                "email": "info@cityhomecomfort.com",
                "years": "40+",
                "rating": "4.8",
                "reviews": "611",
                "area": "Toronto",
                "description": "⭐ 4.8 (📌 611 reviews)\n📍 Serves Toronto\n✅ 40+ years in business · Open 24 hours"
            },
            {
                "name": "Aire Max Heating & Cooling Inc.",
                "phone": "+1 416-843-1321",
                "address": "647 Sheppard Ave W, North York, ON M3H 2S4",
                "email": "info@airemax.ca",
                "years": "15+",
                "rating": "4.8",
                "reviews": "326",
                "area": "North York & GTA",
                "description": "⭐ 4.8 (📌 326 reviews)\n📍 Serves North York & GTA\n✅ 15+ years in business"
            }
        ]

        for provider in providers:
            # Check if provider already exists
            existing = ServiceProviderReport.query.filter_by(
                provider_name=provider["name"],
                city='Toronto'
            ).first()

            if existing:
                print(f"Provider {provider['name']} already exists in waiting list")
                continue

            application_details = f"""Service Provider Application:
Business Name: {provider['name']}
Service Category: HVAC Technician
Business Phone: {provider['phone']}
Business Address: {provider['address']}
Primary Email: {provider['email']}
Contact Email: {provider['email']}
Preferred City: Toronto
Province: ON
Star Rating: {provider['rating']}
Number of Reviews: {provider['reviews']}
Years in Business: {provider['years']}
Service Area: {provider['area']}"""

            new_provider = ServiceProviderReport(
                provider_name=provider["name"],
                provider_phone=provider["phone"],
                business_address=provider["address"],
                user_email=provider["email"],
                service="HVAC Technician",
                city="Toronto",
                province="ON",
                rating=provider["rating"],
                review_count=provider["reviews"],
                report_reason="service_provider_application",
                other_reason=application_details,
                message=provider["description"],
                timestamp=datetime.utcnow(),
                status="pending",
                is_hidden=False
            )
            db.session.add(new_provider)
            print(f"Added {provider['name']} to waiting list")

        try:
            db.session.commit()
            print("Successfully added all providers to waiting list")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding providers: {str(e)}")

if __name__ == "__main__":
    add_hvac_providers() 