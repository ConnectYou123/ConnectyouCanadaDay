
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import ServiceProvider, ServiceProviderReport

def approve_hvac_in_toronto():
    """
    Approves all HVAC providers on the waiting list for Toronto by creating
    ServiceProvider entries and updating their report status.
    """
    with app.app_context():
        # Find all pending HVAC waiting list entries for Toronto
        waiting_list_entries = ServiceProviderReport.query.filter_by(
            city='Toronto',
            service='HVAC',
            report_reason='waiting_list',
            status='pending'
        ).all()

        if not waiting_list_entries:
            print("No pending HVAC providers found in the Toronto waiting list.")
            return

        approved_count = 0
        for report in waiting_list_entries:
            # Check if a provider with the same name and phone already exists
            existing_provider = ServiceProvider.query.filter_by(
                name=report.provider_name,
                phone=report.provider_phone
            ).first()

            if existing_provider:
                print(f"Provider '{report.provider_name}' already exists. Skipping.")
                # Optionally update the report status to 'approved' anyway
                report.status = 'approved'
                continue
            
            # Create a new ServiceProvider from the report
            new_provider = ServiceProvider(
                name=report.provider_name,
                phone=report.provider_phone,
                email=report.user_email,
                business_address=report.business_address,
                city=report.city,
                province="ON",  # Assuming all are in Ontario
                service_category=report.service,
                star_rating=float(report.rating) if report.rating else 4.5,
                review_count=int(report.review_count) if report.review_count else 0,
                description=report.message,
                status='active',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(new_provider)
            
            # Update the report's status to 'approved'
            report.status = 'approved'
            approved_count += 1
            print(f"Approving and creating provider: {report.provider_name}")

        try:
            db.session.commit()
            print(f"\nSuccessfully approved and created {approved_count} new HVAC providers in Toronto.")
        except Exception as e:
            db.session.rollback()
            print(f"\nAn error occurred: {e}")
            print("Transaction rolled back. No changes were made to the database.")

if __name__ == '__main__':
    approve_hvac_in_toronto() 