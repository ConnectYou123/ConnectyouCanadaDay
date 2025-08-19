#!/usr/bin/env python3
"""Restore waiting_list tag for Barrie moving service reports (status already approved)."""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from models import ServiceProviderReport

with app.app_context():
    reports = ServiceProviderReport.query.filter_by(city='Barrie', service='Moving Services', status='approved').all()
    count=0
    for r in reports:
        if r.report_reason!='waiting_list':
            r.report_reason='waiting_list'
            count+=1
    db.session.commit()
    print(f'Restored waiting_list for {count} records.') 