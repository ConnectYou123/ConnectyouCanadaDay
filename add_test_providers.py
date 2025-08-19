#!/usr/bin/env python3
"""
Simple script to add test providers to the database
Run this with: python3 add_test_providers.py
"""

import os
import sys
import sqlite3
from datetime import datetime

from app import app, db
from models import ServiceProviderReport

def add_test_providers():
    """Add test providers directly to the SQLite database"""
    
    # Database path
    db_path = 'instance/contacts.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("Please make sure the Flask app has been run at least once to create the database.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if providers already exist
        cursor.execute("SELECT COUNT(*) FROM service_provider")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"Found {existing_count} existing providers in database")
            # Show existing providers
            cursor.execute("SELECT name, service_category, city FROM service_provider LIMIT 5")
            existing = cursor.fetchall()
            print("Existing providers:")
            for provider in existing:
                print(f"  - {provider[0]} ({provider[1]}) in {provider[2]}")
            return True
        
        print("Adding test providers to database...")
        
        # Test providers data
        test_providers = [
            # Electricians
            ('Toronto Electric Pro', '+14165551234', 'info@torontoelectric.ca', None, 
             '123 King St W', 'Toronto', None, 'ON', 'M5H 1A1', 'Electrician', 
             4.8, 156, 'Professional electrical services for Toronto', 
             'Electrical systems, wiring, outlets, lighting', 12, 'ELEC-001', 1, 1, 'active'),
            
            ('GTA Electrical Services', '+14165551235', 'contact@gtaelectric.ca', None,
             '456 Queen St E', 'Toronto', None, 'ON', 'M5A 1S2', 'Electrician',
             4.7, 203, 'Expert electrical repairs and installations', 
             'Residential and commercial electrical work', 10, 'ELEC-002', 1, 1, 'active'),
            
            # Plumbers  
            ('Toronto Plumbing Experts', '+14165555678', 'service@torontoplumbing.ca', None,
             '789 Bloor St W', 'Toronto', None, 'ON', 'M6G 1L5', 'Plumber',
             4.6, 178, 'Expert plumbing repairs and installations',
             'Pipe repairs, drain cleaning, water heaters', 8, 'PLUMB-001', 1, 1, 'active'),
             
            ('GTA Plumbing Solutions', '+14165555679', 'info@gtaplumbing.ca', None,
             '321 Dundas St W', 'Toronto', None, 'ON', 'M5T 1G5', 'Plumber',
             4.5, 145, 'Reliable plumbing services for Toronto',
             'Emergency repairs, installations, maintenance', 15, 'PLUMB-002', 1, 1, 'active'),
            
            # HVAC Technicians
            ('Toronto HVAC Experts', '+14165559876', 'service@torontohvac.ca', None,
             '654 College St', 'Toronto', None, 'ON', 'M6G 1B5', 'HVAC Technician',
             4.7, 234, 'Heating and cooling system specialists',
             'HVAC installation, repair, maintenance', 12, 'HVAC-001', 1, 1, 'active'),
             
            # General Handyman
            ('Toronto Handyman Services', '+14165557890', 'help@torontohandyman.ca', None,
             '987 Bathurst St', 'Toronto', None, 'ON', 'M5R 1Y8', 'General Handyman', 
             4.4, 167, 'Professional handyman services for all your needs',
             'Small repairs, installations, maintenance', 6, 'HAND-001', 1, 1, 'active'),
             
            # Carpenters
            ('Toronto Custom Carpentry', '+14165558901', 'info@torontocarpentry.ca', None,
             '147 Spadina Ave', 'Toronto', None, 'ON', 'M5V 2L1', 'Carpenter',
             4.6, 189, 'Custom carpentry and woodwork specialists', 
             'Custom cabinets, furniture, trim work', 14, 'CARP-001', 1, 1, 'active')
        ]
        
        # Insert providers
        insert_query = """
        INSERT INTO service_provider 
        (name, phone, email, website, business_address, city, sub_city, province, postal_code, 
         service_category, star_rating, review_count, description, specialties, years_experience, 
         license_number, insurance_verified, background_checked, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        current_time = datetime.utcnow().isoformat()
        
        for provider_data in test_providers:
            # Add timestamps to the data
            provider_with_timestamps = provider_data + (current_time, current_time)
            cursor.execute(insert_query, provider_with_timestamps)
        
        # Commit changes
        conn.commit()
        
        # Verify insertion
        cursor.execute("SELECT COUNT(*) FROM service_provider")
        new_count = cursor.fetchone()[0]
        
        print(f"✅ Successfully added {len(test_providers)} test providers!")
        print(f"Total providers in database: {new_count}")
        
        # Show added providers by category
        cursor.execute("""
        SELECT service_category, COUNT(*) as count 
        FROM service_provider 
        GROUP BY service_category 
        ORDER BY service_category
        """)
        categories = cursor.fetchall()
        
        print("\nProviders by category:")
        for category, count in categories:
            print(f"  - {category}: {count} provider(s)")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def add_handyman_waiting_list_entries():
    with app.app_context():
        # X-Engineer Handyman Services
        handyman1 = ServiceProviderReport(
            provider_name="X-Engineer Handyman Services",
            service="General Handyman",
            city="Toronto",
            province="Ontario",
            postal_code="M4P 0C2",
            rating="4.9",
            review_count="77",
            google_reviews_link="",
            provider_phone="+1 647-749-5888",
            business_address="15 Roehampton Ave, Toronto, ON M4P 0C2",
            report_reason="waiting_list",
            other_reason="""Service Provider Application:
Business Name: X-Engineer Handyman Services
Service Category: General Handyman
Business Phone: +1 647-749-5888
Business Address: 15 Roehampton Ave, Toronto, ON M4P 0C2
Primary Email: hello@xengineer.ca
Contact Email: hello@xengineer.ca
Preferred City: Toronto
Province: Ontario
Postal Code: M4P 0C2
Star Rating: 4.9
Number of Reviews: 77
Hours: 9 AM–8 PM daily
Additional Information: Professional handyman services""",
            user_ip="127.0.0.1",
            user_email="hello@xengineer.ca",
            message="Professional handyman services, operating 9 AM–8 PM daily",
            status="pending",
            timestamp=datetime.utcnow()
        )

        # Mike the Downtown Handyman
        handyman2 = ServiceProviderReport(
            provider_name="Mike the Downtown Handyman",
            service="General Handyman",
            city="Toronto",
            province="Ontario",
            postal_code="M6H 3Z7",
            rating="4.9",
            review_count="57",
            google_reviews_link="",
            provider_phone="+1 647-989-7217",
            business_address="1163 m Lansdowne Ave, Toronto, ON M6H 3Z7",
            report_reason="waiting_list",
            other_reason="""Service Provider Application:
Business Name: Mike the Downtown Handyman
Service Category: General Handyman
Business Phone: +1 647-989-7217
Business Address: 1163 m Lansdowne Ave, Toronto, ON M6H 3Z7
Primary Email: mikethedowntownhandyman@gmail.com
Contact Email: mikethedowntownhandyman@gmail.com
Preferred City: Toronto
Province: Ontario
Postal Code: M6H 3Z7
Star Rating: 4.9
Number of Reviews: 57
Years in Business: 10+ years
Hours: 8 AM–8 PM daily
Additional Information: 10+ years experience in handyman services""",
            user_ip="127.0.0.1",
            user_email="mikethedowntownhandyman@gmail.com",
            message="10+ years experience in handyman services, operating 8 AM–8 PM daily",
            status="pending",
            timestamp=datetime.utcnow()
        )

        # Konrad Handyman Home Repairs
        handyman3 = ServiceProviderReport(
            provider_name="Konrad Handyman Home Repairs",
            service="General Handyman",
            city="Toronto",
            province="Ontario",
            postal_code="M3H 4X6",
            rating="4.9",
            review_count="57",
            google_reviews_link="",
            provider_phone="(647) 720-4548",
            business_address="707 Finch Ave W, North York, ON M3H 4X6",
            report_reason="waiting_list",
            other_reason="""Service Provider Application:
Business Name: Konrad Handyman Home Repairs
Service Category: General Handyman
Business Phone: (647) 720-4548
Business Address: 707 Finch Ave W, North York, ON M3H 4X6
Primary Email: N/a
Contact Email: N/a
Preferred City: Toronto
Province: Ontario
Postal Code: M3H 4X6
Star Rating: 4.9
Number of Reviews: 57
Years in Business: 3+ years
Hours: Open until 8 PM
Additional Information: 3+ years experience in home repairs""",
            user_ip="127.0.0.1",
            user_email="",
            message="3+ years experience in home repairs, serving North York area",
            status="pending",
            timestamp=datetime.utcnow()
        )

        # TheFixitGuys General Contracting
        handyman4 = ServiceProviderReport(
            provider_name="TheFixitGuys General Contracting and Construction",
            service="General Handyman",
            city="Toronto",
            province="Ontario",
            postal_code="L4K 0G2",
            rating="4.9",
            review_count="46",
            google_reviews_link="",
            provider_phone="(289) 266-3967",
            business_address="3300 Hwy 7 #600, Vaughan, ON L4K 0G2",
            report_reason="waiting_list",
            other_reason="""Service Provider Application:
Business Name: TheFixitGuys General Contracting and Construction
Service Category: General Handyman
Business Phone: (289) 266-3967
Business Address: 3300 Hwy 7 #600, Vaughan, ON L4K 0G2
Primary Email: Info@thefixitguys.ca
Contact Email: Info@thefixitguys.ca
Preferred City: Toronto
Province: Ontario
Postal Code: L4K 0G2
Star Rating: 4.9
Number of Reviews: 46
Hours: Opens 8 AM
Additional Information: General Contractor serving Toronto area""",
            user_ip="127.0.0.1",
            user_email="Info@thefixitguys.ca",
            message="General Contractor serving Toronto area",
            status="pending",
            timestamp=datetime.utcnow()
        )

        try:
            db.session.add(handyman1)
            db.session.add(handyman2)
            db.session.add(handyman3)
            db.session.add(handyman4)
            db.session.commit()
            print("Successfully added handyman waiting list entries for Toronto")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding handyman entries: {str(e)}")

if __name__ == "__main__":
    print("🔧 ConnectYou Provider Database Setup")
    print("=" * 40)
    
    success = add_test_providers()
    
    if success:
        print("\n🎉 Setup complete!")
        print("\n📋 Next steps:")
        print("1. Start your Flask application:")
        print("   python3 main.py")
        print("2. Open your browser to http://localhost:5000")
        print("3. Select 'Toronto' as your city")
        print("4. Click on any service category to see providers!")
        print("\n💡 The frontend has been updated to properly load and display providers.")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        
    print("=" * 40) 