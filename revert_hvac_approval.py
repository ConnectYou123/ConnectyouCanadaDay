
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import ServiceProvider, ServiceProviderReport

def revert_hvac_approval():
    """
    Deletes the newly added HVAC providers from Toronto and resets their 
    corresponding waiting list reports back to 'pending'.
    """
    provider_names_to_delete = [
        "4Seasons HVAC",
        "Climax Heating & Air Conditioning",
        "Tempasure Heating and Air Conditioning",
        "DeMark Home Ontario",
        "AccuServ Heating and Air Conditioning",
        "Laird & Son Heating & Air Conditioning",
        "City Home Comfort",
        "Aire Max Heating & Cooling Inc.",
        "Green Heating and Air Inc."
    ]

    with app.app_context():
        # Find and delete the ServiceProvider entries
        providers_deleted_count = 0
        for name in provider_names_to_delete:
            provider = ServiceProvider.query.filter_by(name=name, city='Toronto', service_category='HVAC').first()
            if provider:
                db.session.delete(provider)
                providers_deleted_count += 1
                print(f"Deleting provider: {name}")

        # Find the corresponding reports and revert their status to 'pending'
        reports_reverted_count = 0
        reports = ServiceProviderReport.query.filter(
            ServiceProviderReport.provider_name.in_(provider_names_to_delete),
            ServiceProviderReport.city == 'Toronto',
            ServiceProviderReport.service == 'HVAC',
            ServiceProviderReport.status == 'approved'
        ).all()

        for report in reports:
            report.status = 'pending'
            reports_reverted_count += 1
            print(f"Reverting report status for: {report.provider_name}")

        try:
            db.session.commit()
            print(f"\nSuccessfully deleted {providers_deleted_count} providers.")
            print(f"Successfully reverted {reports_reverted_count} reports to 'pending'.")
        except Exception as e:
            db.session.rollback()
            print(f"\nAn error occurred: {e}")
            print("Transaction rolled back. No changes were made.")

if __name__ == '__main__':
    revert_hvac_approval() 