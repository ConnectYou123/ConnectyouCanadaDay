
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import ServiceProviderReport

def approve_hvac_on_waiting_list():
    """
    Approves all HVAC providers on the waiting list for Toronto by updating
    their status to 'approved' without creating ServiceProvider entries.
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
            print("No pending HVAC providers found in the Toronto waiting list to approve.")
            return

        approved_count = 0
        for report in waiting_list_entries:
            report.status = 'approved'
            approved_count += 1
            print(f"Approving waiting list entry for: {report.provider_name}")

        try:
            db.session.commit()
            print(f"\nSuccessfully approved {approved_count} HVAC providers on the waiting list.")
        except Exception as e:
            db.session.rollback()
            print(f"\nAn error occurred: {e}")
            print("Transaction rolled back. No changes were made to the database.")

if __name__ == '__main__':
    approve_hvac_on_waiting_list() 