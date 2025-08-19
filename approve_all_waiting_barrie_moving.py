#!/usr/bin/env python3
"""Approve all waiting-list Moving Services entries for Barrie.
Run: python approve_all_waiting_barrie_moving.py
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from models import ServiceProviderReport, ServiceProvider

# Map report entries into main ServiceProvider table
def upsert_provider(report: ServiceProviderReport):
    if not report.provider_name:
        return
    exists = ServiceProvider.query.filter_by(name=report.provider_name, city=report.city).first()
    if exists:
        return
    new = ServiceProvider(
        name=report.provider_name,
        phone=report.provider_phone or '',
        business_address=report.business_address or '',
        city=report.city or 'Barrie',
        province=report.province or 'ON',
        postal_code=report.postal_code or '',
        service_category='Moving Services',
        star_rating=float(report.rating) if report.rating else 4.5,
        review_count=int(report.review_count) if report.review_count else 0,
        email=report.user_email or None,
        status='active',
    )
    db.session.add(new)

with app.app_context():
    reports = ServiceProviderReport.query.filter_by(report_reason='waiting_list', city='Barrie', service='Moving Services').all()
    for r in reports:
        # Move to approved application and create active provider
        r.status = 'approved'
        r.report_reason = 'service_provider_application'
        upsert_provider(r)
    db.session.commit()
    print(f"Converted {len(reports)} waiting-list entries to active providers for Barrie Moving Services.") 