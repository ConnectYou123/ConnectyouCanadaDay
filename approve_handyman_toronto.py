
import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import ServiceProvider, ServiceProviderReport

def approve_handyman_providers():
    """Move approved General Handyman waiting-list entries for Toronto into main providers table."""
    with app.app_context():
        entries = ServiceProviderReport.query.filter_by(
            city='Toronto',
            service='General Handyman',
            report_reason='waiting_list',
            status='approved'
        ).all()

        if not entries:
            print("No approved General Handyman waiting-list entries found for Toronto.")
            return

        added_count = 0
        for e in entries:
            # Skip if provider with same name already exists
            existing = ServiceProvider.query.filter_by(name=e.provider_name, city='Toronto', service_category='General Handyman').first()
            if existing:
                # Mark report as processed and continue
                e.status = 'processed'
                continue

            try:
                rating = float(e.rating) if e.rating else 4.5
            except ValueError:
                rating = 4.5
            try:
                reviews = int(e.review_count) if e.review_count else 0
            except ValueError:
                reviews = 0

            provider = ServiceProvider(
                name=e.provider_name,
                phone=e.provider_phone,
                email=e.user_email,
                business_address=e.business_address or '',
                city='Toronto',
                sub_city=None,
                province=e.province or 'ON',
                postal_code=e.postal_code,
                service_category='General Handyman',
                star_rating=rating,
                review_count=reviews,
                description=e.message,
                years_experience=None,
                status='active',
                created_at=datetime.utcnow(),
            )
            db.session.add(provider)
            e.status = 'processed'
            added_count += 1

        db.session.commit()
        print(f"Added {added_count} providers and updated {len(entries)} waiting-list entries to processed.")

if __name__ == '__main__':
    approve_handyman_providers() 