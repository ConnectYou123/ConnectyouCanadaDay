import re
from datetime import datetime
from app import app, db
from models import ServiceProvider

CATEGORY = "Moving Services"
CITY = "Toronto"
PROVINCE = "ON"

PROVIDERS = [
    {
        "name": "Professional Movers Toronto",
        "phone": "(647) 255-9978",
        "address": "2737 Keele St #1015, North York, ON M3M 2E9",
        "star": 5.0,
        "reviews": 485,
        "description": "Family owned · Free estimate · 7+ years in business · Open until 11:45 PM",
        "years": 7,
    },
    {
        "name": "Mr Relokate",
        "phone": "(437) 236-5027",
        "address": "Serves Toronto",
        "star": 5.0,
        "reviews": 290,
        "description": "Free estimate · Local business · 5+ years in business · Open 24 hours",
        "years": 5,
    },
    {
        "name": "West Atlantic Moving",
        "phone": "(647) 874-2858",
        "address": "475 Unwin Ave, Toronto, ON M4M 3M2",
        "star": 5.0,
        "reviews": 296,
        "description": "Family owned · Free estimate · 4+ years in business · Open until 9 PM",
        "years": 4,
    },
    {
        "name": "Shark Moving Services",
        "phone": "(647) 404-9610",
        "address": "8 York St, Toronto, ON M5J 2Y2",
        "star": 5.0,
        "reviews": 512,
        "description": "Background checked · 6+ years in business · Open until 7 PM",
        "years": 6,
    },
    {
        "name": "Like Father Like Son Movers",
        "phone": "(647) 993-4555",
        "address": "19 Pear Blossom Wy, Holland Landing, ON L9N 0T3",
        "star": 5.0,
        "reviews": 196,
        "description": "Background checked · 6+ years in business · Open until 8 PM",
        "years": 6,
    },
    {
        "name": "Top Rated Movers",
        "phone": "(249) 733-3777",
        "address": "111 Citrine Dr, Bradford, ON L3Z 0V2",
        "star": 5.0,
        "reviews": 178,
        "description": "Background checked · 4+ years in business · Open until 10:30 PM",
        "years": 4,
    },
]

def clean_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"+1{digits}"
    if digits.startswith("1"):
        return f"+{digits}"
    return raw

def upsert_provider(p: dict):
    phone_clean = clean_phone(p["phone"])
    provider = ServiceProvider.query.filter_by(name=p["name"], city=CITY).first()
    if provider:
        provider.phone = phone_clean
        provider.business_address = p["address"]
        provider.star_rating = p["star"]
        provider.review_count = p["reviews"]
        provider.description = p["description"]
        provider.service_category = CATEGORY
        provider.years_experience = p["years"]
        provider.status = "active"
        provider.updated_at = datetime.utcnow()
        print(f"Updated provider: {p['name']}")
    else:
        provider = ServiceProvider(
            name=p["name"],
            phone=phone_clean,
            business_address=p["address"],
            city=CITY,
            province=PROVINCE,
            postal_code="",
            service_category=CATEGORY,
            star_rating=p["star"],
            review_count=p["reviews"],
            description=p["description"],
            years_experience=p["years"],
            status="active",
            insurance_verified=True,
            background_checked=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(provider)
        print(f"Added provider: {p['name']}")

def deactivate_others(active_names: set):
    others = (
        ServiceProvider.query.filter_by(city=CITY, service_category=CATEGORY, status="active")
        .filter(~ServiceProvider.name.in_(active_names))
        .all()
    )
    for p in others:
        p.status = "inactive"
        print(f"Deactivated: {p.name}")
    return len(others)

def main():
    with app.app_context():
        for p in PROVIDERS:
            upsert_provider(p)
        deactivated_count = deactivate_others({p["name"] for p in PROVIDERS})
        try:
            db.session.commit()
            print(f"✅ Providers upserted. {deactivated_count} other provider(s) set to inactive.")
        except Exception as exc:
            db.session.rollback()
            print(f"❌ Commit failed: {exc}")

if __name__ == "__main__":
    main() 