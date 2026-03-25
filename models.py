from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='employee')  # 'admin', 'manager', 'employee'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    contact_lists = db.relationship('ContactList', backref='owner', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def can_manage_lists(self):
        return self.role in ['admin', 'manager']
    
    def can_view_all_lists(self):
        return self.role == 'admin'

class ContactList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contacts = db.relationship('Contact', backref='contact_list', lazy=True, cascade='all, delete-orphan')
    
    @property
    def contact_count(self):
        return len(self.contacts)
    
    @property
    def can_add_contact(self):
        return self.contact_count < 6

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    position = db.Column(db.String(100))
    department = db.Column(db.String(100))
    notes = db.Column(db.Text)
    list_id = db.Column(db.Integer, db.ForeignKey('contact_list.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def formatted_phone(self):
        """Format phone number for display"""
        phone = self.phone_number.replace('+1', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
        if len(phone) == 10:
            return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
        return self.phone_number


class CommunicationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_name = db.Column(db.String(200), nullable=False)
    provider_phone = db.Column(db.String(20), nullable=False)
    service_category = db.Column(db.String(100), nullable=False)
    communication_type = db.Column(db.String(10), nullable=False)  # 'call' or 'text'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_ip = db.Column(db.String(45))  # For tracking unique users
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
  
    
    def __repr__(self):
        return f'<CommunicationLog {self.communication_type} to {self.provider_name}>'

class ServiceProvider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=True)
    password=db.Column(db.String(150), nullable=True)
    email1=db.Column(db.String(120),nullable=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    website = db.Column(db.String(300))
    business_address = db.Column(db.String(300), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    sub_city = db.Column(db.String(100), nullable=True)
    province = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(10))
    service_category = db.Column(db.String(100), nullable=False)
    star_rating = db.Column(db.Float, default=4.5)  # Out of 5
    review_count = db.Column(db.Integer, default=100)
    # Optional Google mapping for accurate ratings sync
    google_place_id = db.Column(db.String(128), nullable=True, index=True)
    description = db.Column(db.Text)
    specialties = db.Column(db.Text)  # JSON string of specialties
    years_experience = db.Column(db.Integer)
    license_number = db.Column(db.String(50))
    insurance_verified = db.Column(db.Boolean, default=True)
    background_checked = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='active')  # active, inactive, suspended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def formatted_phone(self):
        """Format phone number for display"""
        phone = self.phone.replace('+1', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
        if len(phone) == 10:
            return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
        return self.phone
    
    def full_address(self):
        """Get full formatted address"""
        location = self.sub_city if self.sub_city else self.city
        address_parts = [self.business_address, location, self.province]
        if self.postal_code:
                address_parts.append(self.postal_code)
        return ', '.join(filter(None, address_parts))
    
    def __repr__(self):
        return f'<ServiceProvider {self.name} - {self.service_category}>'

class ServiceProviderReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_name = db.Column(db.String(200), nullable=False)
    service=db.Column(db.String(200),nullable=True)
    city=db.Column(db.String(200),nullable=True)
    province=db.Column(db.String(200),nullable=True)
    postal_code=db.Column(db.String(200),nullable=True)
    rating=db.Column(db.String(200),nullable=True)
    review_count=db.Column(db.String(200),nullable=True)
    google_reviews_link=db.Column(db.String(200),nullable=True)
    provider_phone = db.Column(db.String(120), nullable=False)  # Increased to accommodate email addresses
    business_address = db.Column(db.String(300))  # Business address field
    report_reason = db.Column(db.String(50), nullable=False)
    other_reason = db.Column(db.Text)
    user_ip = db.Column(db.String(45))
    user_email = db.Column(db.String(120))  # User's email address
    message=db.Column(db.String(200),nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved
    is_hidden = db.Column(db.Boolean, default=False, nullable=False)


    def __repr__(self):
        
        return f'<ServiceProviderReport {self.provider_name} - {self.report_reason}>'

class AppDownloadTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True)  # Added name field
    source = db.Column(db.String(20), nullable=False)  # 'call', 'text', 'apple_app_store', 'google_play_store'
    user_ip = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    email = db.Column(db.String(120), nullable=True)
    
    def __repr__(self):
        return f'<AppDownloadTracking {self.source} - {self.timestamp}>'
class NotificationChange(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    rating_change = db.Column(db.Float, default=4.5)
    review_change = db.Column(db.Integer, default=100)
    p_name=db.Column(db.String(120),nullable=False)   
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<NotificationChange {self.user_email}"
    

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    country = db.Column(db.String(100), nullable=False)
    flag_emoji = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - using primaryjoin since ServiceProvider.city is a string field
    service_providers = db.relationship('ServiceProvider', 
                                       primaryjoin="City.name == foreign(ServiceProvider.city)",
                                       backref='city_ref', lazy=True)
    
    categories = db.relationship('Category', backref='city', lazy=True)
    def __repr__(self):
        return f'<City {self.name}, {self.country}>'
    
    @property
    def provider_count(self):
        """Get count of active service providers in this city"""
        return ServiceProvider.query.filter_by(city=self.name, status='active').count()
    
    @property
    def category_count(self):
        """Get count of unique service categories in this city"""
        return db.session.query(ServiceProvider.service_category).filter_by(
            city=self.name, status='active'
        ).distinct().count()

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), nullable=False, default='fas fa-tools')
    status = db.Column(db.String(20), nullable=False, default='active')  # active, inactive, pending
    city_name = db.Column(db.String(100), db.ForeignKey('city.name'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship back to City is created via `backref='categories'` in the City model

    def __repr__(self):
        return f'<Category {self.name} in {self.city_name}>'

# Import chat models to ensure they're created in database
from chat_models import ChatConversation, ChatMessage,ChatIcon

class Advertisement(db.Model):
    """Model for storing advertisements that appear between service providers"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=False)  # Path to uploaded image
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(300), nullable=True)
    
    # Targeting options
    city_name = db.Column(db.String(100), db.ForeignKey('city.name'), nullable=False)
    category_name = db.Column(db.String(100), nullable=False)  # Which service category to show in
    
    # Position control
    position = db.Column(db.Integer, default=3)  # Show after which provider (e.g., after provider #3)
    
    # Rating and reviews (optional)
    star_rating = db.Column(db.Float, nullable=True)  # 1.0 to 5.0 rating
    review_count = db.Column(db.Integer, default=0)  # Number of reviews
    review_text = db.Column(db.Text, nullable=True)  # Featured review or testimonial
    
    # Status and metadata
    status = db.Column(db.String(20), default='active')  # active, inactive, pending
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    city = db.relationship('City', backref='advertisements')
    
    def formatted_phone(self):
        """Format phone number for display"""
        phone = self.phone_number.replace('+1', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
        if len(phone) == 10:
            return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
        return self.phone_number
    
    def __repr__(self):
        return f'<Advertisement {self.title} in {self.city_name} - {self.category_name}>'


# ---------------------------------------------
# Customer interaction logging
# ---------------------------------------------
class InteractionLog(db.Model):
    """Represents a single customer interaction note/log.

    Stores high-level details about the interaction and links to any
    uploaded attachments such as images or documents.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    author_name = db.Column(db.String(120), nullable=True)
    client_address = db.Column(db.String(300), nullable=True)
    service_needed = db.Column(db.String(150), nullable=True)
    client_phone = db.Column(db.String(50), nullable=True)
    client_email = db.Column(db.String(120), nullable=True)
    service_city = db.Column(db.String(100), nullable=True)
    referral_source = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='incomplete')  # complete, incomplete
    status_note = db.Column(db.Text, nullable=True)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    attachments = db.relationship(
        'InteractionAttachment',
        backref='log',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<InteractionLog {self.id} - {self.title}>'


class InteractionAttachment(db.Model):
    """File uploaded and attached to an interaction log."""
    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.Integer, db.ForeignKey('interaction_log.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<InteractionAttachment {self.id} -> log {self.log_id}>'


class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=True)
    recipients = db.Column(db.Text, nullable=False)  # comma separated
    attachments = db.Column(db.Text, nullable=True)  # comma separated filenames
    status = db.Column(db.String(20), nullable=False, default='sent')  # sent, failed
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)