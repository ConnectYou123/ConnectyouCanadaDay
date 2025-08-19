import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, Blueprint, request, redirect, url_for, flash, session, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
from sqlalchemy import func, or_, desc

# App and database
from app import app, db

# Models
from models import (
    User, ContactList, Contact, CommunicationLog, ServiceProviderReport, ServiceProvider,
    AppDownloadTracking, NotificationChange, City, Category, ChatConversation, ChatMessage, Advertisement
)
from chat_models import ChatIcon

# Services
from twilio_service import send_sms, make_call
from email_service import send_report_email

# External packages
import requests
import json
import threading
import uuid

# --- Configuration ---

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Upload folder path
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'chat_icons')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Flask config
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# API Key for authentication (production tip: use env variable instead)
EXPECTED_API_KEY = os.getenv("EXPECTED_API_KEY", "your_default_key_here")

# Logging
logging.basicConfig(level=logging.DEBUG)

# Blueprints
import admin_chat_routes  # must be imported after `app` is defined
notifications_bp = Blueprint('notifications', __name__)

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    cities = City.query.all()
    return render_template('index.html', cities=cities)

@app.route('/api/categories', methods=['GET'])
def get_categories_by_city():
    city_name = request.args.get('city')

    if not city_name:
        return jsonify({"error": "City parameter is required"}), 400

    city = City.query.filter_by(name=city_name).first()
    if not city:
        return jsonify({"error": f"City '{city_name}' not found"}), 404

    categories = Category.query.filter_by(city_name=city_name, status='active').order_by(Category.name).all()

    category_list = []
    for category in categories:
        category_list.append({
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "icon": category.icon,
            "status": category.status,
            "city": category.city_name,
            "created_at": category.created_at.isoformat()
        })

    return jsonify(category_list)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash('Username or email already exists!', 'danger')
            return render_template('register.html')

        # Create new user
        new_user = User()
        new_user.username = username
        new_user.email = email
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/contact_list/<int:list_id>')
@login_required
def contact_list(list_id):
    current_user = get_current_user()
    contact_list = ContactList.query.get_or_404(list_id)

    # Check permissions
    if not current_user.can_view_all_lists() and contact_list.owner_id != current_user.id:
        flash('You do not have permission to view this contact list.', 'danger')
        return redirect(url_for('index'))

    return render_template('contact_list.html', contact_list=contact_list, current_user=current_user)

@app.route('/create_list', methods=['GET', 'POST'])
@login_required
def create_list():
    current_user = get_current_user()

    if not current_user.can_manage_lists():
        flash('You do not have permission to create contact lists.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if not name:
            flash('List name is required!', 'danger')
            return render_template('create_list.html')

        new_list = ContactList()
        new_list.name = name
        new_list.description = description
        new_list.owner_id = current_user.id

        db.session.add(new_list)
        db.session.commit()

        flash('Contact list created successfully!', 'success')
        return redirect(url_for('contact_list', list_id=new_list.id))

    return render_template('create_list.html')

@app.route('/add_contact/<int:list_id>', methods=['GET', 'POST'])
@login_required
def add_contact(list_id):
    current_user = get_current_user()
    contact_list = ContactList.query.get_or_404(list_id)

    # Check permissions
    if not current_user.can_manage_lists() and contact_list.owner_id != current_user.id:
        flash('You do not have permission to add contacts to this list.', 'danger')
        return redirect(url_for('contact_list', list_id=list_id))

    if not contact_list.can_add_contact:
        flash('This contact list is full. Maximum 6 contacts allowed.', 'danger')
        return redirect(url_for('contact_list', list_id=list_id))

    if request.method == 'POST':
        name = request.form.get('name')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        position = request.form.get('position')
        department = request.form.get('department')
        notes = request.form.get('notes')

        if not name or not phone_number:
            flash('Name and phone number are required!', 'danger')
            return render_template('add_contact.html', contact_list=contact_list)

        new_contact = Contact()
        new_contact.name = name
        new_contact.phone_number = phone_number
        new_contact.email = email
        new_contact.position = position
        new_contact.department = department
        new_contact.notes = notes
        new_contact.list_id = list_id

        db.session.add(new_contact)
        db.session.commit()

        flash('Contact added successfully!', 'success')
        return redirect(url_for('contact_list', list_id=list_id))

    return render_template('add_contact.html', contact_list=contact_list)

@app.route('/edit_contact/<int:contact_id>', methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    current_user = get_current_user()
    contact = Contact.query.get_or_404(contact_id)
    contact_list = contact.contact_list

    # Check permissions
    if not current_user.can_manage_lists() and contact_list.owner_id != current_user.id:
        flash('You do not have permission to edit this contact.', 'danger')
        return redirect(url_for('contact_list', list_id=contact_list.id))

    if request.method == 'POST':
        contact.name = request.form.get('name')
        contact.phone_number = request.form.get('phone_number')
        contact.email = request.form.get('email')
        contact.position = request.form.get('position')
        contact.department = request.form.get('department')
        contact.notes = request.form.get('notes')

        if not contact.name or not contact.phone_number:
            flash('Name and phone number are required!', 'danger')
            return render_template('edit_contact.html', contact=contact)

        db.session.commit()
        flash('Contact updated successfully!', 'success')
        return redirect(url_for('contact_list', list_id=contact_list.id))

    return render_template('edit_contact.html', contact=contact)

@app.route('/delete_contact/<int:contact_id>', methods=['POST'])
@login_required
def delete_contact(contact_id):
    current_user = get_current_user()
    contact = Contact.query.get_or_404(contact_id)
    contact_list = contact.contact_list

    # Check permissions
    if not current_user.can_manage_lists() and contact_list.owner_id != current_user.id:
        flash('You do not have permission to delete this contact.', 'danger')
        return redirect(url_for('contact_list', list_id=contact_list.id))

    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted successfully!', 'success')
    return redirect(url_for('contact_list', list_id=contact_list.id))

@app.route('/call_contact/<int:contact_id>')
@login_required
def call_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)

    # Use Twilio to make the call
    call_sid = make_call(contact.phone_number)

    if call_sid:
        flash(f'Call initiated to {contact.name}!', 'success')
    else:
        flash('Failed to initiate call. Please try again.', 'danger')

    return redirect(url_for('contact_list', list_id=contact.list_id))

@app.route('/send_message/<int:list_id>', methods=['POST'])
@login_required
def send_message(list_id):
    current_user = get_current_user()
    contact_list = ContactList.query.get_or_404(list_id)

    # Check permissions
    if not current_user.can_manage_lists() and contact_list.owner_id != current_user.id:
        flash('You do not have permission to send messages from this list.', 'danger')
        return redirect(url_for('contact_list', list_id=list_id))

    message_text = request.form.get('message')
    selected_contacts = request.form.getlist('selected_contacts')

    if not message_text or not selected_contacts:
        flash('Please select contacts and enter a message!', 'danger')
        return redirect(url_for('contact_list', list_id=list_id))

    success_count = 0
    for contact_id in selected_contacts:
        contact = Contact.query.get(contact_id)
        if contact and contact.list_id == list_id:
            message_sid = send_sms(contact.phone_number, message_text)
            if message_sid:
                success_count += 1

    flash(f'Message sent to {success_count} contact(s)!', 'success')
    return redirect(url_for('contact_list', list_id=list_id))

@app.route('/send_individual_message/<int:contact_id>', methods=['POST'])
@login_required
def send_individual_message(contact_id):
    current_user = get_current_user()
    contact = Contact.query.get_or_404(contact_id)
    contact_list = contact.contact_list

    # Check permissions
    if not current_user.can_manage_lists() and contact_list.owner_id != current_user.id:
        flash('You do not have permission to send messages to this contact.', 'danger')
        return redirect(url_for('contact_list', list_id=contact_list.id))

    message_text = request.form.get('message')

    if not message_text:
        flash('Please enter a message!', 'danger')
        return redirect(url_for('contact_list', list_id=contact_list.id))

    message_sid = send_sms(contact.phone_number, message_text)

    if message_sid:
        flash(f'Message sent to {contact.name}!', 'success')
    else:
        flash('Failed to send message. Please try again.', 'danger')

    return redirect(url_for('contact_list', list_id=contact_list.id))

@app.context_processor
def inject_user():
    return {'current_user': get_current_user()}

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/call_provider', methods=['POST'])
def call_provider():
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        print(f"The phone number is {phone_number}")
        if not phone_number:
            return jsonify({'success': False, 'error': 'Phone number is required'}), 400

        # Get user IP address for logging
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))

        # Log the communication attempt
        log_entry = CommunicationLog()
        log_entry.provider_name = data.get('provider_name', 'Unknown Provider')
        log_entry.provider_id=data.get('id')
        log_entry.provider_phone = phone_number
        log_entry.service_category = data.get('service_category', 'Unknown')
        log_entry.communication_type = 'call'
        log_entry.user_ip = user_ip

        # Attempt to make the call
        call_sid = make_call(phone_number)

        if call_sid:
            log_entry.success = True
            db.session.add(log_entry)
            db.session.commit()
            return jsonify({'success': True, 'call_sid': call_sid})
        else:
            log_entry.success = False
            log_entry.error_message = 'Failed to initiate call'
            db.session.add(log_entry)
            db.session.commit()
            return jsonify({'success': False, 'error': 'Failed to initiate call'}), 500

    except Exception as e:
        logging.error(f"Error in call_provider: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/text_provider', methods=['POST'])
def text_provider():
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        message = data.get('message')
        provider_id = data.get('id')

        if not phone_number or not message:
            return jsonify({'success': False, 'error': 'Phone number and message are required'}), 400

        # Get user IP address for logging
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))

        # Log the communication attempt
        log_entry = CommunicationLog()
        log_entry.provider_name = data.get('provider_name', 'Unknown Provider')
        log_entry.provider_phone = phone_number
        log_entry.provider_id=provider_id
        log_entry.service_category = data.get('service_category', 'Unknown')
        log_entry.communication_type = 'text'
        log_entry.user_ip = user_ip

        # Attempt to send the SMS
        message_sid = send_sms(phone_number, message)

        if message_sid:
            log_entry.success = True
            db.session.add(log_entry)
            db.session.commit()
            return jsonify({'success': True, 'message_sid': message_sid})
        else:
            log_entry.success = False
            log_entry.error_message = 'Failed to send SMS'
            db.session.add(log_entry)
            db.session.commit()
            return jsonify({'success': False, 'error': 'Failed to send SMS'}), 500

    except Exception as e:
        logging.error(f"Error in text_provider: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username, role='admin').first()

        print(f"Login attempt: username={username}, password={password}")

        if user and user.check_password(password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Admin login successful!', 'success')
            return redirect(url_for('reports_dashboard'))
        else:
            flash('Invalid admin credentials!', 'danger')

    return render_template('admin_login.html')



@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Admin logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/change-password', methods=['GET', 'POST'])
@admin_required
def admin_change_password():
    """Change admin password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        admin_user = User.query.filter_by(username='admin',role='admin').first()

        if not admin_user.check_password(current_password):
            flash('Current password is incorrect!', 'danger')
            return render_template('admin_change_password.html')

        if not new_password or len(new_password) < 8:
            flash('New password must be at least 8 characters long!', 'danger')
            return render_template('admin_change_password.html')

        if new_password != confirm_password:
            flash('New passwords do not match!', 'danger')
            return render_template('admin_change_password.html')

        # Save new hashed password in DB
        admin_user.set_password(new_password)
        db.session.commit()

        flash('Admin password changed successfully!', 'success')
        return redirect(url_for('reports_dashboard'))

    return render_template('admin_change_password.html')
    # if request.method == 'POST':
    #     current_password = request.form.get('current_password')
    #     new_password = request.form.get('new_password')
    #     confirm_password = request.form.get('confirm_password')

    #     # Verify current password (check against stored password or default)
    #     stored_password = session.get('admin_password', "Developer1!")
    #     if current_password != stored_password:
    #         flash('Current password is incorrect!', 'danger')
    #         return render_template('admin_change_password.html')

    #     # Validate new password
    #     if not new_password or len(new_password) < 8:
    #         flash('New password must be at least 8 characters long!', 'danger')
    #         return render_template('admin_change_password.html')

    #     if new_password != confirm_password:
    #         flash('New passwords do not match!', 'danger')
    #         return render_template('admin_change_password.html')

    #     # Store new password in environment variable for this session
    #     # Note: In production, this should be stored in a secure database
    #     session['admin_password'] = new_password
    #     flash('Admin password changed successfully!', 'success')
    #     return redirect(url_for('reports_dashboard'))

    # return render_template('admin_change_password.html')

@app.route("/reports")
@admin_required
def reports_dashboard():
    """Reports dashboard showing all submitted provider reports, feedback, and waiting list entries"""
    # Get all service provider reports

    all_reports = ServiceProviderReport.query.order_by(desc(ServiceProviderReport.timestamp)).all()

    # Separate different types of reports
    provider_reports = [r for r in all_reports if r.provider_name != 'App Feedback' and r.report_reason not in ['waiting_list', 'service_provider_application']]
    feedback_submissions = [r for r in all_reports if r.provider_name == 'App Feedback']
    waiting_list_entries = [r for r in all_reports if r.report_reason == 'waiting_list']

    # Separate applications by status for better organization
    pending_applications = [r for r in all_reports if r.report_reason == 'service_provider_application' and r.status == 'pending']
    approved_applications = [r for r in all_reports if r.report_reason == 'service_provider_applicawaition' and r.status == 'approved']
    rejected_applications = [r for r in all_reports if r.report_reason == 'service_provider_application' and r.status == 'rejected']

    # Calculate statistics
    stats = {
        'total_reports': len(provider_reports),
        'total_feedback': len(feedback_submissions),
        'total_waiting_list': len(waiting_list_entries),
        'pending_applications': len(pending_applications),
        'approved_applications': len(approved_applications),
        'rejected_applications': len(rejected_applications),
        'recent_reports': len([r for r in provider_reports if r.timestamp >= datetime.utcnow() - timedelta(days=7)]),
        'recent_feedback': len([r for r in feedback_submissions if r.timestamp >= datetime.utcnow() - timedelta(days=7)]),
        'recent_waiting_list': len([r for r in waiting_list_entries if r.timestamp >= datetime.utcnow() - timedelta(days=7)])
    }
    notifications = NotificationChange.query.order_by(NotificationChange.created_at.desc()).limit(2).all()
    
    for notif in notifications:
        flash(
            f"Notification for {notif.user_email}: Rating Change = {notif.rating_change}, Review Change = {notif.review_change}",
            "info"
        )
    from chat_models import ChatConversation, ChatMessage
    total_conversations = ChatConversation.query.count()
    open_conversations = ChatConversation.query.filter_by(status='open').count()
    unread_messages = ChatMessage.query.filter_by(is_from_admin=False, is_read=False).count()
    
    # Get recent chat messages for dashboard
    recent_messages = ChatMessage.query.filter_by(is_from_admin=False, is_read=False)\
        .order_by(desc(ChatMessage.created_at))\
        .limit(5)\
        .all()
    
    chat_stats = {
        'total': total_conversations,
        'open': open_conversations,
        'unread_messages': unread_messages,
        'recent_messages': recent_messages
    }
    return render_template('reports.html',
                         provider_reports=provider_reports,
                         feedback_submissions=feedback_submissions,
                         waiting_list_entries=waiting_list_entries,
                         pending_applications=pending_applications,
                         approved_applications=approved_applications,
                         rejected_applications=rejected_applications,
                         all_reports=all_reports,
                         stats=stats,
                         chat_stats=chat_stats)

@app.route('/admin/waiting_list')
@admin_required
def admin_waiting_list():
    """Dedicated waiting list page for service provider applications"""
    # Get all cities that have waiting list entries or applications
    cities_query = db.session.query(ServiceProviderReport.city).distinct().filter(
        ServiceProviderReport.city.isnot(None),
        ServiceProviderReport.city != ''
    ).order_by(ServiceProviderReport.city).all()
    cities = [city[0] for city in cities_query] if cities_query else []
    
    # Get selected city from query params
    selected_city = request.args.get('city', 'All Cities')
    
    # Get all waiting list entries and applications
    all_reports = ServiceProviderReport.query.order_by(desc(ServiceProviderReport.timestamp)).all()

    # Filter by city if a specific city is selected
    if selected_city != 'All Cities':
        all_reports = [r for r in all_reports if r.city == selected_city]

    # Filter for waiting list entries and applications
    waiting_list_entries = [r for r in all_reports if r.report_reason == 'waiting_list']
    pending_applications = [r for r in all_reports if r.report_reason == 'service_provider_application' and r.status == 'pending']
    approved_applications = [r for r in all_reports if r.report_reason == 'service_provider_application' and r.status == 'approved']
    rejected_applications = [r for r in all_reports if r.report_reason == 'service_provider_application' and r.status == 'rejected']

    # Helper function to extract category from report
    def get_category_from_report(report):
        if report.other_reason and 'Service Category:' in report.other_reason:
            import re
            category_match = re.search(r'Service Category:\s*([^,\n]+)', report.other_reason)
            if category_match:
                return category_match.group(1).strip()
        return report.service or 'Other'

    # Helper function to organize reports by category
    def organize_by_category(reports):
        from collections import defaultdict
        categorized = defaultdict(list)
        for report in reports:
            category = get_category_from_report(report)
            categorized[category].append(report)
        # Sort by number of entries (descending)
        return dict(sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True))

    # Organize each type by category
    waiting_list_by_category = organize_by_category(waiting_list_entries)
    pending_by_category = organize_by_category(pending_applications)
    approved_by_category = organize_by_category(approved_applications)
    rejected_by_category = organize_by_category(rejected_applications)

    # Calculate statistics
    stats = {
        'total_waiting_list': len(waiting_list_entries),
        'pending_applications': len(pending_applications),
        'approved_applications': len(approved_applications),
        'rejected_applications': len(rejected_applications),
        'recent_waiting_list': len([r for r in waiting_list_entries if r.timestamp >= datetime.utcnow() - timedelta(days=7)]),
        'recent_applications': len([r for r in pending_applications if r.timestamp >= datetime.utcnow() - timedelta(days=7)]),
        'categories_count': len(set(get_category_from_report(r) for r in all_reports))
    }

    return render_template('admin_waiting_list.html',
                         waiting_list_entries=waiting_list_entries,
                         pending_applications=pending_applications,
                         approved_applications=approved_applications,
                         rejected_applications=rejected_applications,
                         waiting_list_by_category=waiting_list_by_category,
                         pending_by_category=pending_by_category,
                         approved_by_category=approved_by_category,
                         rejected_by_category=rejected_by_category,
                         cities=cities,
                         selected_city=selected_city,
                         stats=stats)

@app.route('/admin/delete_entry/<int:entry_id>', methods=['DELETE'])
@admin_required
def delete_waiting_list_entry(entry_id):
    """Delete a waiting list entry or application"""
    try:
        entry = ServiceProviderReport.query.get_or_404(entry_id)

        # Store entry details for logging
        entry_name = entry.provider_name
        entry_type = entry.report_reason

        # Delete the entry
        db.session.delete(entry)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Successfully deleted {entry_type} entry for {entry_name}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting entry: {str(e)}'
        }), 500

@app.route('/admin/get_provider_data/<int:entry_id>', methods=['GET'])
@admin_required
def get_provider_data(entry_id):
    """Get provider data for editing"""
    try:
        # First check if this is a waiting list entry
        entry = ServiceProviderReport.query.get(entry_id)
        if entry:
            # Check if there's a corresponding ServiceProvider record
            provider = ServiceProvider.query.filter_by(
                name=entry.provider_name,
                phone=entry.provider_phone
            ).first()

            if provider:
                return jsonify({
                    'success': True,
                    'provider': {
                        'provider_name': provider.name,
                        'service_category': provider.service_category,
                        'provider_phone': provider.phone,
                        'user_email': provider.email,
                        'website': provider.website,
                        'business_address': provider.business_address,
                        'city': provider.city,
                        'province': provider.province,
                        'postal_code': provider.postal_code,
                        'star_rating': provider.star_rating,
                        'review_count': provider.review_count,
                        'description': provider.description,
                        'specialties': provider.specialties,
                        'years_experience': provider.years_experience,
                        'license_number': provider.license_number,
                        'insurance_verified': provider.insurance_verified,
                        'background_checked': provider.background_checked,
                        'status': provider.status,

                    }
                })
            else:
                # Return basic data from waiting list entry
                return jsonify({
                    'success': True,
                    'provider': {
                        'provider_name': entry.provider_name,
                        'service_category': entry.service,
                        'provider_phone': entry.provider_phone,
                        'user_email': entry.user_email,
                        'website': entry.google_reviews_link,
                        'business_address': entry.business_address,
                        'city': entry.city,
                        'province': entry.province,
                        'postal_code': entry.postal_code,
                        'star_rating': entry.rating,
                        'review_count': entry.review_count,
                        'description': entry.message,
                        'specialties': '',
                        'years_experience': None,
                        'license_number': '',
                        'insurance_verified': True,
                        'background_checked': True,
                        'status': 'active'
                    }
                })

        return jsonify({
            'success': False,
            'message': 'Provider not found'
        }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching provider data: {str(e)}'
        }), 500

@app.route('/admin/edit_provider/<int:entry_id>', methods=['PUT'])
@admin_required
def edit_approved_provider(entry_id):
    """Edit an approved provider's details"""
    try:
        entry = ServiceProviderReport.query.get_or_404(entry_id)
        data = request.get_json()

        # Update the waiting list entry
        entry.provider_name = data.get('provider_name', entry.provider_name)
        entry.provider_phone = data.get('provider_phone', entry.provider_phone)
        entry.business_address = data.get('business_address', entry.business_address)
        entry.user_email = data.get('user_email', entry.user_email)

        # Find or create corresponding ServiceProvider record
        provider = ServiceProvider.query.filter_by(
            name=entry.provider_name,
            phone=entry.provider_phone
        ).first()

        if not provider:
            # Create new ServiceProvider record
            provider = ServiceProvider()

        # Update all provider fields
        provider.name = data.get('provider_name')
        provider.service_category = data.get('service_category', provider.service_category if provider.id else 'General Maintenance & Repairs')
        provider.phone = data.get('provider_phone')
        provider.email = data.get('user_email')
        provider.website = data.get('website')
        provider.business_address = data.get('business_address')
        provider.city = data.get('city', provider.city if provider.id else 'Toronto')
        provider.province = data.get('province', provider.province if provider.id else 'Ontario')
        provider.postal_code = data.get('postal_code')
        provider.star_rating = data.get('star_rating', 4.5)
        provider.review_count = data.get('review_count', 100)
        provider.description = data.get('description')
        provider.specialties = data.get('specialties')
        provider.years_experience = data.get('years_experience')
        provider.license_number = data.get('license_number')
        provider.insurance_verified = data.get('insurance_verified', True)
        provider.background_checked = data.get('background_checked', True)
        provider.status = data.get('status', 'active')

        # Add to session if it's a new provider
        if not provider.id:
            db.session.add(provider)

        # Save all changes
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Successfully updated provider: {provider.name}',
            'trigger_update': True,
            'update_type': 'provider_data'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating provider: {str(e)}'
        }), 500



@app.route('/approve_application/<int:application_id>', methods=['POST'])
def approve_application(application_id):
    """Approve a service provider application"""
    try:
        application = ServiceProviderReport.query.get_or_404(application_id)
        # Accept both service-provider applications and waiting-list entries
        if application.report_reason not in ['service_provider_application', 'waiting_list']:
            return jsonify({'success': False, 'message': 'Invalid application'}), 400

        # Mark report as approved
        application.status = 'approved'

        # If this is a waiting-list entry, convert it into an "approved application"
        if application.report_reason == 'waiting_list':
            # Re-tag so the dashboard treats it like an approved application
            application.report_reason = 'service_provider_application'

        # If this is originally a waiting-list entry, copy the data into ServiceProvider (skip duplicates)
        if application.report_reason == 'service_provider_application' and not ServiceProvider.query.filter_by(name=application.provider_name, phone=application.provider_phone).first():
            existing_provider = ServiceProvider.query.filter_by(
                name=application.provider_name,
                phone=application.provider_phone
            ).first()

            if not existing_provider:
                try:
                    # Map raw category text to canonical category names used on the frontend
                    raw_cat = (application.service or '').strip()
                    mapped_cat = raw_cat
                    if raw_cat.lower() in ['house cleaning', 'house cleaning services', 'housecleaning']:
                        mapped_cat = 'House Cleaner'

                    new_provider = ServiceProvider(
                        name=application.provider_name,
                        phone=application.provider_phone,
                        business_address=application.business_address or '',
                        city=application.city or '',
                        province=application.province or '',
                        postal_code=application.postal_code or '',
                        service_category=mapped_cat or 'General',
                        star_rating=float(application.rating) if application.rating else 4.5,
                        review_count=int(application.review_count) if application.review_count else 0,
                        website=application.google_reviews_link or None,
                        email=application.user_email or None,
                    )
                    db.session.add(new_provider)
                except Exception as e:
                    logging.error(f"Error creating ServiceProvider from waiting list entry: {e}")

        db.session.commit()

        logging.info(f"Application approved: {application.provider_name} - {application.user_email}")
        return jsonify({'success': True, 'message': 'Application approved successfully'})
    except Exception as e:
        logging.error(f"Error approving application: {str(e)}")
        return jsonify({'success': False, 'message': 'Error approving application'}), 500

@app.route('/reject_application/<int:application_id>', methods=['POST'])
def reject_application(application_id):
    """Reject a service provider application"""
    try:
        application = ServiceProviderReport.query.get_or_404(application_id)
        if application.report_reason != 'service_provider_application':
            return jsonify({'success': False, 'message': 'Invalid application'}), 400

        application.status = 'rejected'
        db.session.commit()

        logging.info(f"Application rejected: {application.provider_name} - {application.user_email}")
        return jsonify({'success': True, 'message': 'Application rejected successfully'})
    except Exception as e:
        logging.error(f"Error rejecting application: {str(e)}")
        return jsonify({'success': False, 'message': 'Error rejecting application'}), 500

@app.route("/analytics")
@admin_required
def analytics_dashboard():
    # Date range for analysis (last 30 days)
    start_date = datetime.utcnow() - timedelta(days=30)

    # Get basic statistics
    total_submissions = ServiceProviderReport.query.count()
    total_provider_reports = ServiceProviderReport.query.filter(
        ServiceProviderReport.provider_name != 'App Feedback',
        ServiceProviderReport.report_reason.notin_(['waiting_list', 'service_provider_application'])
    ).count()
    total_feedback = ServiceProviderReport.query.filter(
        ServiceProviderReport.provider_name == 'App Feedback'
    ).count()
    total_waiting_list = ServiceProviderReport.query.filter(
        ServiceProviderReport.report_reason == 'waiting_list'
    ).count()

    # Recent activity (last 7 days)
    recent_date = datetime.utcnow() - timedelta(days=7)
    recent_submissions = ServiceProviderReport.query.filter(
        ServiceProviderReport.timestamp >= recent_date
    ).count()
    recent_provider_reports = ServiceProviderReport.query.filter(
        ServiceProviderReport.timestamp >= recent_date,
        ServiceProviderReport.provider_name != 'App Feedback',
        ServiceProviderReport.report_reason.notin_(['waiting_list', 'service_provider_application'])
    ).count()
    recent_feedback = ServiceProviderReport.query.filter(
        ServiceProviderReport.timestamp >= recent_date,
        ServiceProviderReport.provider_name == 'App Feedback'
    ).count()
    recent_waiting_list = ServiceProviderReport.query.filter(
        ServiceProviderReport.timestamp >= recent_date,
        ServiceProviderReport.report_reason == 'waiting_list'
    ).count()

    # Get communication statistics
    total_calls = CommunicationLog.query.filter(
        CommunicationLog.communication_type == 'call'
    ).count()

    total_texts = CommunicationLog.query.filter(
        CommunicationLog.communication_type == 'text'
    ).count()

    # Get top service categories from communication logs
    top_services = db.session.query(
        CommunicationLog.service_category,
        func.count(CommunicationLog.id).label('count')
    ).group_by(
        CommunicationLog.service_category
    ).order_by(
        func.count(CommunicationLog.id).desc()
    ).limit(10).all()

    # Get submission statistics instead of communication stats
    all_submissions = ServiceProviderReport.query.filter(
        ServiceProviderReport.timestamp >= start_date
    ).all()

    # Categorize submissions
    provider_reports = [r for r in all_submissions if r.provider_name != 'App Feedback' and r.report_reason not in ['waiting_list', 'service_provider_application']]
    feedback_submissions = [r for r in all_submissions if r.provider_name == 'App Feedback']
    waiting_list_entries = [r for r in all_submissions if r.report_reason == 'waiting_list']
    service_provider_applications = [r for r in all_submissions if r.report_reason == 'service_provider_application']

    # Submission breakdown for chart
    submission_breakdown = {
        'Provider Reports': len(provider_reports),
        'App Feedback': len(feedback_submissions),
        'Waiting List': len(waiting_list_entries),
        'Service Applications': len(service_provider_applications)
    }

    # Daily submission activity for the last 7 days
    daily_stats = []
    for i in range(7):
        day_start = datetime.utcnow() - timedelta(days=i+1)
        day_end = datetime.utcnow() - timedelta(days=i)

        day_submissions = ServiceProviderReport.query.filter(
            ServiceProviderReport.timestamp >= day_start,
            ServiceProviderReport.timestamp < day_end
        ).count()

        daily_stats.append({
            'date': day_start.strftime('%m/%d'),
            'count': day_submissions
        })

    daily_stats.reverse()  # Show in chronological order

    # Get report breakdown by reason
    reason_stats = db.session.query(
        ServiceProviderReport.report_reason,
        func.count(ServiceProviderReport.id).label('count')
    ).filter(
        ServiceProviderReport.provider_name != 'App Feedback',
        ServiceProviderReport.report_reason != 'waiting_list'
    ).group_by(ServiceProviderReport.report_reason).all()

    # Get report counts by status
    status_stats = db.session.query(
        ServiceProviderReport.status,
        func.count(ServiceProviderReport.id).label('count')
    ).group_by(ServiceProviderReport.status).all()

    # Count feedback types
    feedback_stats = db.session.query(
        ServiceProviderReport.report_reason,
        func.count(ServiceProviderReport.id).label('count')
    ).filter(
        ServiceProviderReport.provider_name == 'App Feedback'
    ).group_by(ServiceProviderReport.report_reason).all()

    stats = {
        'total_submissions': total_submissions,
        'total_provider_reports': total_provider_reports,
        'total_feedback': total_feedback,
        'total_waiting_list': total_waiting_list,
        'recent_submissions': recent_submissions,
        'recent_provider_reports': recent_provider_reports,
        'recent_feedback': recent_feedback,
        'recent_waiting_list': recent_waiting_list
    }

    # Separate applications by status for better organization
    pending_applications = ServiceProviderReport.query.filter(
        ServiceProviderReport.report_reason == 'service_provider_application',
        ServiceProviderReport.status == 'pending'
    ).count()

    approved_applications = ServiceProviderReport.query.filter(
        ServiceProviderReport.report_reason == 'service_provider_application',
        ServiceProviderReport.status == 'approved'
    ).count()

    rejected_applications = ServiceProviderReport.query.filter(
        ServiceProviderReport.report_reason == 'service_provider_application',
        ServiceProviderReport.status == 'rejected'
    ).count()

    application_stats = {
        'pending': pending_applications,
        'approved': approved_applications,
        'rejected': rejected_applications
    }

    return render_template('analytics.html',
                         stats=stats,
                         top_services=top_services,
                         submission_breakdown=submission_breakdown,
                         daily_stats=daily_stats,
                         reason_stats=reason_stats,
                         status_stats=status_stats,
                         feedback_stats=feedback_stats,
                         application_stats=application_stats,
                         total_calls=total_calls,
                         total_texts=total_texts)

@app.route('/provider_login')
def provider_login():
    """Redirect to external ConnectYou Pro login"""
    return redirect('https://newconnectyou.pythonanywhere.com/accounts/login/')

@app.route('/provider_register')
def provider_register():
    """Redirect to external ConnectYou Pro registration"""
    return redirect('https://connectyou.pro/accounts/register/')

@app.route('/submit_report', methods=['POST'])
def submit_report():
    """Handle service provider report submissions"""
    try:
        data = request.get_json()
        provider_name = data.get('provider_name')
        provider_phone = data.get('provider_phone')
        reason = data.get('reason')
        other_reason = data.get('other_reason', '')

        if not provider_name or not provider_phone or not reason:
            return jsonify({'success': False, 'message': 'Please fill in all required fields'}), 400

        # Get user IP address
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))

        # Create report entry
        report = ServiceProviderReport()
        report.provider_name = provider_name
        report.provider_phone = provider_phone
        report.report_reason = reason
        report.other_reason = other_reason
        report.user_ip = user_ip

        db.session.add(report)
        db.session.commit()

        # Send email notification to support
        try:
            send_report_email(provider_name, provider_phone, reason, other_reason, user_ip)
        except Exception as email_error:
            logging.error(f"Failed to send report email: {str(email_error)}")

        # Log the report for admin review
        logging.info(f"New provider report: {provider_name} ({provider_phone}) - {reason}")

        return jsonify({
            'success': True,
            'message': 'Thank you for your report. We will review this information and take appropriate action.'
        })

    except Exception as e:
        logging.error(f"Error in submit_report: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while submitting your report. Please try again later.'
        }), 500

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """Handle feedback submissions"""
    try:
        data = request.get_json()
        feedback_type = data.get('feedback_type')
        feedback_description = data.get('feedback_description')
        feedback_email = data.get('feedback_email', '')

        if not feedback_type or not feedback_description:
            return jsonify({'success': False, 'message': 'Please fill in all required fields'}), 400

        # Get user IP address
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))

        # Create feedback entry using ServiceProviderReport model
        feedback = ServiceProviderReport()
        feedback.provider_name = 'App Feedback'  # Special identifier for feedback
        feedback.provider_phone = feedback_email  # Store email in phone field for feedback
        feedback.report_reason = feedback_type
        feedback.other_reason = feedback_description
        feedback.user_ip = user_ip
        feedback.user_email = feedback_email

        db.session.add(feedback)
        db.session.commit()

        # Log the feedback for admin review
        logging.info(f"New feedback: {feedback_type} - {feedback_email}")

        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback! We appreciate your input and will use it to improve our service.'
        })

    except Exception as e:
        logging.error(f"Error in submit_feedback: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while submitting your feedback. Please try again later.'
        }), 500

@app.route('/submit_waiting_list', methods=['POST'])
def submit_waiting_list():
    """Handle service provider application submissions"""
    try:
        data = request.get_json()
        print(data)
        # Extract fields from request
        email = data.get('email')
        city = data.get('city')
        service = data.get('service')
        business_name = data.get('business_name')
        business_phone = data.get('business_phone')
        business_address = data.get('business_address')
        rating = data.get('rating', '')
        review_count = data.get('review_count', '')
        google_reviews_link = data.get('google_reviews_link', '')
        message = data.get('message', '')
        user_email = data.get('user_email', '')
        province = data.get('province', '')
        postal_code = data.get('postal_code', '')

        # Validate required fields
        if not email or not city or not service or not business_name or not business_phone or not business_address:
            return jsonify({'success': False, 'message': 'Please fill in all required fields'}), 400

        # Get IP address
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

        # Create readable summary for admin
        application_details = f"""Service Provider Application:
Business Name: {business_name}
Service Category: {service}
Business Phone: {business_phone}
Business Address: {business_address}
Rating: {rating}
Review Count: {review_count}
Google Reviews Link: {google_reviews_link}
Message: {message}
Contact Email: {email}
Alternative Email: {user_email}
Province: {province}
Postal Code: {postal_code}
"""

        # Create waiting list entry
        waiting_list = ServiceProviderReport()
        waiting_list.provider_name = business_name
        waiting_list.provider_phone = business_phone
        waiting_list.business_address = business_address
        waiting_list.report_reason = 'waiting_list'
        waiting_list.other_reason = application_details
        waiting_list.user_ip = user_ip
        waiting_list.user_email = email
        waiting_list.service = service
        waiting_list.city = city
        waiting_list.rating = rating
        waiting_list.review_count = review_count
        waiting_list.google_reviews_link = google_reviews_link
        waiting_list.message = message
        waiting_list.province = province
        waiting_list.postal_code = postal_code
        waiting_list.timestamp = datetime.utcnow()
        waiting_list.status = 'pending'
        waiting_list.is_hidden = False

        db.session.add(waiting_list)
        db.session.commit()

        # Log the submission
        logging.info(f"New waiting list submission: {business_name} ({service}) in {city}")

        return jsonify({
            'success': True,
            'message': 'Thank you for your application! We will review your information and contact you soon.'
        })

    except Exception as e:
        logging.error(f"Error in submit_waiting_list: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while submitting your application. Please try again later.'
        }), 500

@app.route('/get_approved_providers/<service_category>')
def get_approved_providers(service_category):
    """Get approved service providers for a specific category - filtered by city"""
    try:
        # Get city from query parameter (default to all cities if not specified)
        city_filter = request.args.get('city', '').strip()
        
        # Base query for approved applications that match the service category
        query = ServiceProviderReport.query.filter(
            ServiceProviderReport.report_reason.in_(['service_provider_application', 'join_application']),
            ServiceProviderReport.status == 'approved',
            ~ServiceProviderReport.is_hidden,
            or_(
                ServiceProviderReport.other_reason.contains(f'Service Category: {service_category}'),
                ServiceProviderReport.service == service_category
            )
        )
        
        # Add city filter if specified
        if city_filter:
            query = query.filter(func.lower(ServiceProviderReport.city) == city_filter.lower())
            
        # Build more flexible matching to handle variations like 'House Cleaner' vs 'House Cleaning'
        alt_category = ''
        if service_category.lower().endswith('er'):
            alt_category = service_category[:-2] + 'ing'  # cleaner -> cleaning

        approved_providers = query.order_by(ServiceProviderReport.timestamp.desc()).all()

        if alt_category:
            alt_query = ServiceProviderReport.query.filter(
                ServiceProviderReport.report_reason.in_(['service_provider_application', 'join_application']),
                ServiceProviderReport.status == 'approved',
                ~ServiceProviderReport.is_hidden,
                or_(
                    ServiceProviderReport.other_reason.ilike(f"%{alt_category}%"),
                    ServiceProviderReport.service.ilike(f"%{alt_category}%")
                )
            )
            if city_filter:
                alt_query = alt_query.filter(func.lower(ServiceProviderReport.city) == city_filter.lower())

            alt_providers = alt_query.all()

            # Merge while avoiding duplicates (by id)
            existing_ids = {p.id for p in approved_providers}
            approved_providers.extend([p for p in alt_providers if p.id not in existing_ids])

        providers_data = []
        # ---------------------------
        # 1) Approved APPLICATIONS
        # ---------------------------
        for provider in approved_providers:
            # Parse the application details from other_reason field
            details = provider.other_reason.split('\n') if provider.other_reason else []
            provider_info = {
                'business_name': provider.provider_name,
                'business_phone': provider.provider_phone,
                'primary_email': provider.user_email,
                'timestamp': provider.timestamp.strftime('%m/%d/%Y'),
                'service_category': service_category
            }

            # First, check if rating and review_count are stored directly in the model
            if provider.rating:
                provider_info['rating'] = provider.rating
            if provider.review_count:
                provider_info['review_count'] = provider.review_count

            # Then extract additional details from the stored application (may override above)
            for line in details:
                if 'Preferred City:' in line:
                    provider_info['city'] = line.split('Preferred City:')[1].strip()
                elif 'Star Rating:' in line:
                    provider_info['rating'] = line.split('Star Rating:')[1].strip()
                elif 'Number of Reviews:' in line:
                    provider_info['review_count'] = line.split('Number of Reviews:')[1].strip()
                elif 'Google Reviews Link:' in line:
                    provider_info['google_reviews'] = line.split('Google Reviews Link:')[1].strip()

            # Add business address from the database
            if provider.business_address:
                provider_info['business_address'] = provider.business_address

            providers_data.append(provider_info)

        # Sort providers by rating (desc) then review_count (desc)
        def sort_key(p):
            try:
                rating = float(p.get('rating', 0))
            except (ValueError, TypeError):
                rating = 0
            try:
                reviews = int(p.get('review_count', 0))
            except (ValueError, TypeError):
                reviews = 0
            return (-rating, -reviews)

        providers_data.sort(key=sort_key)

        return jsonify({
            'success': True,
            'providers': providers_data,
            'count': len(providers_data)
        })

    except Exception as e:
        logging.error(f"Error getting approved providers: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error retrieving approved providers'
        }), 500

@app.route('/search_all_providers')
def search_all_providers():
    """Search across all service providers including both active providers and approved applications"""
    try:
        query = request.args.get('q', '').strip().lower()
        city_filter = request.args.get('city', '').strip()

        if not query:
            return jsonify({
                'success': True,
                'providers': [],
                'count': 0
            })

        providers_data = []

        # First, search through actual ServiceProvider records (these have better data structure)
        service_providers = ServiceProvider.query.filter(
            ServiceProvider.status == 'active'
        ).all()

        for provider in service_providers:
            # Check if provider matches search query
            search_fields = [
                provider.name,
                provider.phone,
                provider.email or '',
                provider.business_address or '',
                provider.city or '',
                provider.service_category or '',
                provider.description or '',
                provider.specialties or ''
            ]

            if any(query in field.lower() for field in search_fields if field):
                # Check city filter if provided
                if not city_filter or provider.city.lower() == city_filter.lower():
                    provider_info = {
                        'name': provider.name,
                        'phone': provider.phone,
                        'email': provider.email,
                        'star_rating': provider.star_rating,
                        'review_count': provider.review_count,
                        'business_address': provider.business_address,
                        'city': provider.city,
                        'province': provider.province,
                        'service_category': provider.service_category,
                        'description': provider.description,
                        'specialties': provider.specialties,
                        'years_experience': provider.years_experience,
                        'formatted_phone': provider.formatted_phone(),
                        'full_address': provider.full_address(),
                        'source': 'active_provider'
                    }
                    providers_data.append(provider_info)

        # Also search through approved applications for additional coverage
        approved_reports = ServiceProviderReport.query.filter(
            ServiceProviderReport.status == 'approved'
        ).all()

        for report in approved_reports:
            # Parse the application details from other_reason field
            details = report.other_reason.split('\n') if report.other_reason else []
            report_info = {
                'business_name': report.provider_name,
                'business_phone': report.provider_phone,
                'primary_email': report.user_email,
                'business_address': report.business_address or '',
                'service_category': '',
                'city': report.city or '',
                'rating': '4.5',
                'review_count': '0'
            }

            # Extract additional details from the stored application
            for line in details:
                if 'Service Category:' in line:
                    report_info['service_category'] = line.split('Service Category:')[1].strip()
                elif 'Preferred City:' in line:
                    report_info['city'] = line.split('Preferred City:')[1].strip()
                elif 'Star Rating:' in line:
                    report_info['rating'] = line.split('Star Rating:')[1].strip()
                elif 'Number of Reviews:' in line:
                    report_info['review_count'] = line.split('Number of Reviews:')[1].strip()

            # Check if this provider is already in our active providers list
            already_included = any(
                p.get('name', '').lower() == report_info['business_name'].lower() and 
                p.get('phone', '') == report_info['business_phone']
                for p in providers_data
            )

            if not already_included:
                # Check if provider matches search query
                search_fields = [
                    report_info['business_name'],
                    report_info['business_phone'],
                    report_info['primary_email'],
                    report_info['business_address'],
                    report_info.get('city', ''),
                    report_info.get('service_category', '')
                ]

                if any(query in field.lower() for field in search_fields if field):
                    # Check city filter if provided
                    if not city_filter or report_info['city'].lower() == city_filter.lower():
                        # Convert to consistent format
                        provider_info = {
                            'name': report_info['business_name'],
                            'phone': report_info['business_phone'],
                            'email': report_info['primary_email'],
                            'star_rating': float(report_info.get('rating', 4.5)),
                            'review_count': int(report_info.get('review_count', 0)),
                            'business_address': report_info['business_address'],
                            'city': report_info['city'],
                            'service_category': report_info['service_category'],
                            'description': f"Professional {report_info['service_category']} service provider",
                            'source': 'approved_application'
                        }
                        providers_data.append(provider_info)

        # Sort by rating and review count
        providers_data.sort(key=lambda x: (
            x.get('star_rating', 0),
            x.get('review_count', 0)
        ), reverse=True)

        return jsonify({
            'success': True,
            'providers': providers_data,
            'count': len(providers_data)
        })

    except Exception as e:
        logging.error(f"Error searching all providers: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error searching providers'
        }), 500

# Provider Management Routes
@app.route('/admin/providers')
@admin_required
def admin_providers():
    """Provider management dashboard"""
    # Get all cities with providers
    cities = db.session.query(ServiceProvider.city).distinct().order_by(ServiceProvider.city).all()
    cities = [city[0] for city in cities] if cities else []
    all_cities = City.query.filter_by(status='active').order_by(City.name).all()

    # Get selected city from query params
    selected_city = request.args.get('city', cities[0] if cities else 'Toronto')
    new_categories = Category.query.filter_by(
        city_name=selected_city
    ).order_by(Category.name).all()

    # Get ACTIVE providers for selected city to mirror frontend lists
    providers = ServiceProvider.query.filter(
            func.lower(ServiceProvider.city) == selected_city.lower(),
            ServiceProvider.status == 'active'
        ).order_by(
            ServiceProvider.star_rating.desc(),
            ServiceProvider.review_count.desc(),
            ServiceProvider.name
        ).all()

    # Group providers by service category and maintain ranking within each category
    providers_by_category = {}
    for provider in providers:
        if provider.service_category not in providers_by_category:
            providers_by_category[provider.service_category] = []
        providers_by_category[provider.service_category].append(provider)
    
    # Sort providers within each category by the same ranking criteria
    for category in providers_by_category:
        providers_by_category[category].sort(
            key=lambda p: (p.star_rating, p.review_count, p.name.lower()), 
            reverse=True
        )

    # Get service categories in a consistent order
    category_names = {c.name.lower() for c in Category.query.all()}

# Step 2: Filter out keys that match any Category name (case-insensitive)
    categories = sorted([
        key for key in providers_by_category.keys()
        if key.lower() not in category_names
    ]) if providers_by_category else []

    return render_template('admin_providers.html',
                         providers=providers,
                         providers_by_category=providers_by_category,
                         cities=cities,
                         selected_city=selected_city,
                         categories=categories,
                         all_cities=all_cities,new_categories=new_categories)

@app.route('/admin/providers/add', methods=['GET', 'POST'])
@admin_required
def admin_add_provider():
    """Add new service provider"""
    provider_categories = {
        p.service_category for p in ServiceProvider.query.distinct(ServiceProvider.service_category).all()
        if p.service_category
   }
    cities = City.query.filter_by(status='active').order_by(City.name).all()
    category_model_names = {
        c.name for c in Category.query.filter_by(status='active').all()
    }

    service_categories = sorted(set(provider_categories).union(set(category_model_names)))


    if request.method == 'POST':
        try:
            provider = ServiceProvider()
            provider.name = request.form.get('name')
            provider.phone = request.form.get('phone')
            provider.email = request.form.get('email')
            provider.website = request.form.get('website')
            provider.business_address = request.form.get('business_address')
            provider.city = request.form.get('city')
            provider.sub_city=request.form.get('sub-city')
            provider.province = request.form.get('province')
            provider.postal_code = request.form.get('postal_code')
            provider.service_category = request.form.get('service_category')
            provider.star_rating = float(request.form.get('star_rating', 4.5))
            provider.review_count = int(request.form.get('review_count', 100))
            provider.description = request.form.get('description')
            provider.specialties = request.form.get('specialties')
            provider.years_experience = int(request.form.get('years_experience', 5)) if request.form.get('years_experience') else None
            provider.license_number = request.form.get('license_number')
            provider.insurance_verified = bool(request.form.get('insurance_verified'))
            provider.background_checked = bool(request.form.get('background_checked'))
            provider.status = request.form.get('status', 'active')

            db.session.add(provider)
            db.session.commit()

            flash('Provider added successfully!', 'success')
            return redirect(url_for('admin_providers', city=provider.city))
        except Exception as e:
            logging.error(f"Error adding provider: {str(e)}")
            flash('Error adding provider. Please check all fields.', 'danger')

    return render_template('admin_add_provider.html',service_categories=service_categories,cities=cities)

@app.route('/admin/providers/category', methods=['GET', 'POST'])
@admin_required
def admin_add_category():
    """Add new service provider category"""

    city_name = request.args.get('city')
    if not city_name:
        flash("City name is missing from the URL.", "danger")
        return redirect(url_for('admin_providers'))

    # Check if the city exists
    city = City.query.filter_by(name=city_name).first()
    if not city:
        flash(f"City '{city_name}' not found.", "danger")
        return redirect(url_for('admin_providers'))

    if request.method == 'POST':
        name = request.form.get('category_name')
        description = request.form.get('description')
        icon = request.form.get('icon')
        status = request.form.get('status')

        # Input validation
        if not name:
            flash("Category name is required.", "danger")
            return render_template('admin_add_category.html', city_name=city_name, city=city)

        # Create and save new category
        new_category = Category(
            name=name,
            description=description,
            icon=icon,
            status=status,
            city_name=city_name
        )

        try:
            db.session.add(new_category)
            db.session.commit()
            flash(f"Category '{name}' added successfully to {city_name}.", "success")
            return redirect(url_for('admin_providers', city=city_name))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while adding the category.", "danger")
            print(f"Error adding category: {e}")

    return render_template('admin_add_category.html', city_name=city_name, city=city)
@app.route('/admin/providers/edit/<int:provider_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_provider(provider_id):
    """Edit existing service provider and sync with external Django API"""
    provider = ServiceProvider.query.get_or_404(provider_id)
    cities = City.query.filter_by(status='active').order_by(City.name).all()
    provider_categories = {
        p.service_category for p in ServiceProvider.query.distinct(ServiceProvider.service_category).all()
        if p.service_category
    }
    category_model_names = {
        c.name for c in Category.query.filter_by(status='active').all()
    }
    all_service_categories = sorted(set(provider_categories).union(set(category_model_names)))

    if request.method == 'POST':
        try:
            provider.name = request.form.get('name')
            provider.phone = request.form.get('phone')
            provider.email = request.form.get('email')
            provider.website = request.form.get('website')
            provider.business_address = request.form.get('business_address')
            provider.city = request.form.get('city')
            provider.sub_city = request.form.get('sub-city')
            provider.province = request.form.get('province')
            provider.postal_code = request.form.get('postal_code')
            provider.service_category = request.form.get('service_category')
            provider.star_rating = float(request.form.get('star_rating', 4.5))
            provider.review_count = int(request.form.get('review_count', 100))
            provider.description = request.form.get('description')
            provider.specialties = request.form.get('specialties')
            provider.years_experience = int(request.form.get('years_experience')) if request.form.get('years_experience') else None
            provider.license_number = request.form.get('license_number')
            provider.insurance_verified = bool(request.form.get('insurance_verified'))
            provider.background_checked = bool(request.form.get('background_checked'))
            provider.status = request.form.get('status', 'active')

            db.session.commit()

            # After successful DB update, call external Django API
            if provider.username:
                api_url = f"https://newconnectyou.pythonanywhere.com/api/providers/update-by-username/{provider.username}/"
                payload = {
                    "name": provider.name or "",
                    "address": provider.business_address or "",
                    "city_name": provider.city or "",
                    "country": "Canada",  # Adjust if dynamic
                    "service_name": provider.service_category or "",
                    "service_description": provider.years_experience or "",
                    "service_image": "",  # Optional: add file upload support
                    "review_proof":provider.website or "",
                    "rating":float(provider.star_rating) if provider.star_rating else 0.0,
                    "review_count":int(provider.review_count) if provider.review_count else 0,
                    "phone_number":provider.phone or '',


                }

                try:
                    response = requests.patch(api_url, json=payload, timeout=5)
                    response.raise_for_status()
                except requests.RequestException as e:
                    logging.error(f"Failed to call external API: {e}")
                    flash("Provider saved locally, but failed to update external API.", "warning")

            flash('Provider updated successfully!', 'success')
            return render_template('admin_edit_provider.html', provider=provider)

        except Exception as e:
            logging.error(f"Error updating provider: {str(e)}")
            flash('Error updating provider. Please check all fields.', 'danger')

    return render_template(
        'admin_edit_provider.html',
        provider=provider,
        service_categories=all_service_categories,
        cities=cities
    )
@app.route('/admin/providers/delete/<int:provider_id>', methods=['POST'])
@admin_required
def admin_delete_provider(provider_id):
    """Delete service provider and call external API to delete by username"""
    try:
        provider = ServiceProvider.query.get_or_404(provider_id)
        city = provider.city

        username = None
        # Adjust this based on your model structure
        if hasattr(provider, 'username'):
            username = provider.username
        elif hasattr(provider, 'user') and provider.user:
            username = getattr(provider.user, 'username', None)

        # Delete provider locally
        db.session.delete(provider)
        db.session.commit()

        # Call external API to delete by username if username exists
        if username:
            api_url = f"https://newconnectyou.pythonanywhere.com/api/providers/delete-by-username/{username}/"
            try:
                response = requests.delete(api_url, timeout=5)
                if response.status_code == 204:
                    logging.info(f"Successfully deleted provider in Django API for username: {username}")
                else:
                    logging.warning(f"Django API delete returned status {response.status_code}: {response.text}")
            except requests.RequestException as e:
                logging.error(f"Error calling Django API to delete provider: {str(e)}")

        flash('Provider deleted successfully!', 'success')
        return redirect(url_for('admin_providers', city=city))

    except Exception as e:
        logging.error(f"Error deleting provider: {str(e)}")
        flash('Error deleting provider.', 'danger')
        return redirect(url_for('admin_providers'))

@app.route('/admin/init-sample-data', methods=['POST'])
@admin_required
def init_sample_data():
    """Initialize sample provider data for demonstration"""
    try:
        # Check if sample data already exists
        existing_count = ServiceProvider.query.count()
        if existing_count > 0:
            flash(f'Sample data not added - {existing_count} providers already exist in database.', 'warning')
            return redirect(url_for('admin_providers'))

        # Comprehensive providers for Toronto organized by service category
        sample_providers = [
            # General Maintenance & Repair
            {
                'name': 'Pro Handyman Services',
                'phone': '(416) 555-0101',
                'email': 'info@prohandyman.ca',
                'website': 'https://prohandyman.ca',
                'business_address': '1200 King St W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6K 1G2',
                'service_category': 'General Maintenance & Repair',
                'star_rating': 4.6,
                'review_count': 234,
                'description': 'Professional handyman services for all your home repair and maintenance needs.',
                'specialties': 'Furniture assembly, Drywall repair, Painting, Minor electrical',
                'years_experience': 8,
                'license_number': 'HM-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'Fix-It Fast Toronto',
                'phone': '(416) 555-0102',
                'email': 'service@fixitfast.com',
                'business_address': '2500 Bloor St W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6S 1P8',
                'service_category': 'General Maintenance & Repair',
                'star_rating': 4.4,
                'review_count': 189,
                'description': 'Quick and reliable repair services for residential and commercial properties.',
                'specialties': 'Emergency repairs, Appliance installation, Carpentry, Maintenance',
                'years_experience': 12,
                'license_number': 'HM-2024-002',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # Electrical
            {
                'name': 'Elite Electrical Solutions',
                'phone': '(416) 555-0201',
                'email': 'service@eliteelectrical.com',
                'business_address': '1250 Eglinton Ave W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6C 2E3',
                'service_category': 'Electrical',
                'star_rating': 4.7,
                'review_count': 298,
                'description': 'Licensed electrical contractors providing safe and reliable electrical services.',
                'specialties': 'Panel upgrades, Outlet installation, LED lighting, Emergency repairs',
                'years_experience': 12,
                'license_number': 'ELEC-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'PowerLine Electric Inc',
                'phone': '(416) 555-0202',
                'email': 'info@powerlineelectric.ca',
                'business_address': '3400 Dundas St W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6P 2A6',
                'service_category': 'Electrical',
                'star_rating': 4.8,
                'review_count': 425,
                'description': 'Master electricians specializing in residential and commercial electrical systems.',
                'specialties': 'Smart home installation, Industrial wiring, Code compliance, Troubleshooting',
                'years_experience': 18,
                'license_number': 'ELEC-2024-002',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # Plumbing
            {
                'name': 'Toronto Plumbing Pros',
                'phone': '(416) 555-0301',
                'email': 'info@torontoplumbingpros.com',
                'business_address': '45 Sheppard Ave E',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M2N 5W9',
                'service_category': 'Plumbing',
                'star_rating': 4.6,
                'review_count': 367,
                'description': 'Expert plumbing services including repairs, installations, and emergency services available 24/7.',
                'specialties': 'Drain cleaning, Pipe repairs, Fixture installation, Water heater service',
                'years_experience': 18,
                'license_number': 'PLB-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'AquaFlow Plumbing',
                'phone': '(416) 555-0302',
                'email': 'service@aquaflow.ca',
                'business_address': '890 St. Clair Ave W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6C 1C1',
                'service_category': 'Plumbing',
                'star_rating': 4.9,
                'review_count': 512,
                'description': 'Premium plumbing services with expert technicians and guaranteed satisfaction.',
                'specialties': 'Bathroom renovations, Kitchen plumbing, Sewer line repair, Leak detection',
                'years_experience': 22,
                'license_number': 'PLB-2024-002',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # HVAC
            {
                'name': 'ClimateCare HVAC Services',
                'phone': '(416) 555-0401',
                'email': 'contact@climatecare.ca',
                'website': 'https://climatecare.ca',
                'business_address': '285 Jevlan Drive',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'L4L 8A8',
                'service_category': 'HVAC',
                'star_rating': 5.0,
                'review_count': 482,
                'description': 'Complete HVAC solutions including heating, cooling, and air quality services.',
                'specialties': 'Furnace installation, Air conditioning, Duct cleaning, Smart thermostats',
                'years_experience': 20,
                'license_number': 'HVAC-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'Comfort Zone Heating & Cooling',
                'phone': '(416) 555-0402',
                'email': 'info@comfortzone.ca',
                'business_address': '1800 Lawrence Ave W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6L 1C5',
                'service_category': 'HVAC',
                'star_rating': 4.7,
                'review_count': 356,
                'description': 'Energy-efficient heating and cooling solutions for homes and businesses.',
                'specialties': 'Heat pump installation, Boiler service, Air quality systems, Energy audits',
                'years_experience': 15,
                'license_number': 'HVAC-2024-002',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # Roofing
            {
                'name': 'High Skillz Roofing Inc',
                'phone': '(416) 555-0501',
                'email': 'info@highskillzroofing.com',
                'website': 'https://highskillzroofing.com',
                'business_address': '62 Alness St Unit 2B',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M3J 2H5',
                'service_category': 'Roofing',
                'star_rating': 4.9,
                'review_count': 156,
                'description': 'Professional roofing services for residential and commercial properties.',
                'specialties': 'Emergency repairs, Shingle installation, Flat roof systems, Commercial roofing',
                'years_experience': 15,
                'license_number': 'ROF-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'Summit Roofing Solutions',
                'phone': '(416) 555-0502',
                'email': 'contact@summitroofing.ca',
                'business_address': '4200 Dufferin St',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M3H 5S2',
                'service_category': 'Roofing',
                'star_rating': 4.8,
                'review_count': 289,
                'description': 'Complete roofing solutions with warranty-backed workmanship.',
                'specialties': 'Metal roofing, Tile installation, Gutter systems, Storm damage repair',
                'years_experience': 25,
                'license_number': 'ROF-2024-002',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # Cleaning & Pest Control
            {
                'name': 'Sparkle Clean Toronto',
                'phone': '(416) 555-0601',
                'email': 'info@sparkleclean.ca',
                'business_address': '5600 Yonge St',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M2M 3S9',
                'service_category': 'Cleaning & Pest Control',
                'star_rating': 4.5,
                'review_count': 167,
                'description': 'Professional cleaning services for homes and offices.',
                'specialties': 'Deep cleaning, Move-in/out cleaning, Office cleaning, Post-construction cleanup',
                'years_experience': 7,
                'license_number': 'CLN-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'BugBusters Pest Control',
                'phone': '(416) 555-0602',
                'email': 'service@bugbusters.ca',
                'business_address': '900 Jane St',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6N 4C6',
                'service_category': 'Cleaning & Pest Control',
                'star_rating': 4.7,
                'review_count': 245,
                'description': 'Effective pest control solutions for residential and commercial properties.',
                'specialties': 'Rodent control, Insect extermination, Wildlife removal, Prevention programs',
                'years_experience': 12,
                'license_number': 'PEST-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # Outdoor & Landscaping
            {
                'name': 'GreenScape Landscaping',
                'phone': '(416) 555-0701',
                'email': 'hello@greenscapeto.com',
                'website': 'https://greenscapeto.com',
                'business_address': '789 Dundas St W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6J 1T9',
                'service_category': 'Outdoor & Landscaping',
                'star_rating': 4.8,
                'review_count': 201,
                'description': 'Creative landscaping and outdoor design services to enhance your property.',
                'specialties': 'Garden design, Tree services, Lawn maintenance, Hardscaping',
                'years_experience': 10,
                'license_number': 'LAND-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'Toronto Tree Care',
                'phone': '(416) 555-0702',
                'email': 'info@torontotreecare.com',
                'business_address': '1500 Keele St',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6M 3W6',
                'service_category': 'Outdoor & Landscaping',
                'star_rating': 4.6,
                'review_count': 178,
                'description': 'Certified arborists providing expert tree care and landscape maintenance.',
                'specialties': 'Tree removal, Pruning, Stump grinding, Landscape maintenance',
                'years_experience': 16,
                'license_number': 'TREE-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # Technology & Security
            {
                'name': 'SecureHome Systems',
                'phone': '(416) 555-0801',
                'email': 'info@securehome.ca',
                'website': 'https://securehome.ca',
                'business_address': '2100 Bloor St W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6S 1M8',
                'service_category': 'Technology & Security',
                'star_rating': 4.8,
                'review_count': 312,
                'description': 'Advanced security systems and smart home technology installation.',
                'specialties': 'Security cameras, Alarm systems, Smart locks, Home automation',
                'years_experience': 9,
                'license_number': 'SEC-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'TechConnect Solutions',
                'phone': '(416) 555-0802',
                'email': 'support@techconnect.ca',
                'business_address': '3300 Bathurst St',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6A 2A7',
                'service_category': 'Technology & Security',
                'star_rating': 4.5,
                'review_count': 267,
                'description': 'IT support and technology solutions for homes and small businesses.',
                'specialties': 'Network setup, Computer repair, Smart home integration, Tech support',
                'years_experience': 8,
                'license_number': 'TECH-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            }
        ]

        # Add providers to database
        for provider_data in sample_providers:
            provider = ServiceProvider(**provider_data)
            db.session.add(provider)

        db.session.commit()

        flash(f'Successfully added {len(sample_providers)} sample providers to the database!', 'success')
        logging.info(f"Sample data initialized: {len(sample_providers)} providers added")

    except Exception as e:
        logging.error(f"Error initializing sample data: {str(e)}")
        flash('Error adding sample data. Please try again.', 'danger')

    return redirect(url_for('admin_providers'))

@app.route('/admin/init-all-providers', methods=['POST'])
@admin_required
def init_all_providers():
    """Initialize all providers automatically"""
    try:
        # Delete existing providers first
        ServiceProvider.query.delete()
        db.session.commit()

        # All providers organized by service category
        all_providers = [
            # General Maintenance & Repair
            {
                'name': 'Pro Handyman Services',
                'phone': '(416) 555-0101',
                'email': 'info@prohandyman.ca',
                'website': 'https://prohandyman.ca',
                'business_address': '1200 King St W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6K 1G2',
                'service_category': 'General Maintenance & Repair',
                'star_rating': 4.6,
                'review_count': 234,
                'description': 'Professional handyman services for all your home repair and maintenance needs.',
                'specialties': 'Furniture assembly, Drywall repair, Painting, Minor electrical',
                'years_experience': 8,
                'license_number': 'HM-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'Fix-It Fast Toronto',
                'phone': '(416) 555-0102',
                'email': 'service@fixitfast.com',
                'business_address': '2500 Bloor St W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6S 1P8',
                'service_category': 'General Maintenance & Repair',
                'star_rating': 4.4,
                'review_count': 189,
                'description': 'Quick and reliable repair services for residential and commercial properties.',
                'specialties': 'Emergency repairs, Appliance installation, Carpentry, Maintenance',
                'years_experience': 12,
                'license_number': 'HM-2024-002',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # Electrical
            {
                'name': 'Elite Electrical Solutions',
                'phone': '(416) 555-0201',
                'email': 'service@eliteelectrical.com',
                'business_address': '1250 Eglinton Ave W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6C 2E3',
                'service_category': 'Electrical',
                'star_rating': 4.7,
                'review_count': 298,
                'description': 'Licensed electrical contractors providing safe and reliable electrical services.',
                'specialties': 'Panel upgrades, Outlet installation, LED lighting, Emergency repairs',
                'years_experience': 12,
                'license_number': 'ELEC-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'PowerLine Electric Inc',
                'phone': '(416) 555-0202',
                'email': 'info@powerlineelectric.ca',
                'business_address': '3400 Dundas St W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6P 2A6',
                'service_category': 'Electrical',
                'star_rating': 4.8,
                'review_count': 425,
                'description': 'Master electricians specializing in residential and commercial electrical systems.',
                'specialties': 'Smart home installation, Industrial wiring, Code compliance, Troubleshooting',
                'years_experience': 18,
                'license_number': 'ELEC-2024-002',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # Plumbing
            {
                'name': 'Toronto Plumbing Pros',
                'phone': '(416) 555-0301',
                'email': 'info@torontoplumbingpros.com',
                'business_address': '45 Sheppard Ave E',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M2N 5W9',
                'service_category': 'Plumbing',
                'star_rating': 4.6,
                'review_count': 367,
                'description': 'Expert plumbing services including repairs, installations, and emergency services available 24/7.',
                'specialties': 'Drain cleaning, Pipe repairs, Fixture installation, Water heater service',
                'years_experience': 18,
                'license_number': 'PLB-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'AquaFlow Plumbing',
                'phone': '(416) 555-0302',
                'email': 'service@aquaflow.ca',
                'business_address': '890 St. Clair Ave W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6C 1C1',
                'service_category': 'Plumbing',
                'star_rating': 4.9,
                'review_count': 512,
                'description': 'Premium plumbing services with expert technicians and guaranteed satisfaction.',
                'specialties': 'Bathroom renovations, Kitchen plumbing, Sewer line repair, Leak detection',
                'years_experience': 22,
                'license_number': 'PLB-2024-002',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # HVAC
            {
                'name': 'ClimateCare HVAC Services',
                'phone': '(416) 555-0401',
                'email': 'contact@climatecare.ca',
                'website': 'https://climatecare.ca',
                'business_address': '285 Jevlan Drive',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'L4L 8A8',
                'service_category': 'HVAC',
                'star_rating': 5.0,
                'review_count': 482,
                'description': 'Complete HVAC solutions including heating, cooling, and air quality services.',
                'specialties': 'Furnace installation, Air conditioning, Duct cleaning, Smart thermostats',
                'years_experience': 20,
                'license_number': 'HVAC-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'Comfort Zone Heating & Cooling',
                'phone': '(416) 555-0402',
                'email': 'info@comfortzone.ca',
                'business_address': '1800 Lawrence Ave W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6L 1C5',
                'service_category': 'HVAC',
                'star_rating': 4.7,
                'review_count': 356,
                'description': 'Energy-efficient heating and cooling solutions for homes and businesses.',
                'specialties': 'Heat pump installation, Boiler service, Air quality systems, Energy audits',
                'years_experience': 15,
                'license_number': 'HVAC-2024-002',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # Roofing
            {
                'name': 'High Skillz Roofing Inc',
                'phone': '(416) 555-0501',
                'email': 'info@highskillzroofing.com',
                'website': 'https://highskillzroofing.com',
                'business_address': '62 Alness St Unit 2B',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M3J 2H5',
                'service_category': 'Roofing',
                'star_rating': 4.9,
                'review_count': 156,
                'description': 'Professional roofing services for residential and commercial properties.',
                'specialties': 'Emergency repairs, Shingle installation, Flat roof systems, Commercial roofing',
                'years_experience': 15,
                'license_number': 'ROF-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'Summit Roofing Solutions',
                'phone': '(416) 555-0502',
                'email': 'contact@summitroofing.ca',
                'business_address': '4200 Dufferin St',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M3H 5S2',
                'service_category': 'Roofing',
                'star_rating': 4.8,
                'review_count': 289,
                'description': 'Complete roofing solutions with warranty-backed workmanship.',
                'specialties': 'Metal roofing, Tile installation, Gutter systems, Storm damage repair',
                'years_experience': 25,
                'license_number': 'ROF-2024-002',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # Cleaning & Pest Control
            {
                'name': 'Sparkle Clean Toronto',
                'phone': '(416) 555-0601',
                'email': 'info@sparkleclean.ca',
                'business_address': '5600 Yonge St',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M2M 3S9',
                'service_category': 'Cleaning & Pest Control',
                'star_rating': 4.5,
                'review_count': 167,
                'description': 'Professional cleaning services for homes and offices.',
                'specialties': 'Deep cleaning, Move-in/out cleaning, Office cleaning, Post-construction cleanup',
                'years_experience': 7,
                'license_number': 'CLN-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'BugBusters Pest Control',
                'phone': '(416) 555-0602',
                'email': 'service@bugbusters.ca',
                'business_address': '900 Jane St',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6N 4C6',
                'service_category': 'Cleaning & Pest Control',
                'star_rating': 4.7,
                'review_count': 245,
                'description': 'Effective pest control solutions for residential and commercial properties.',
                'specialties': 'Rodent control, Insect extermination, Wildlife removal, Prevention programs',
                'years_experience': 12,
                'license_number': 'PEST-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # Outdoor & Landscaping
            {
                'name': 'GreenScape Landscaping',
                'phone': '(416) 555-0701',
                'email': 'hello@greenscapeto.com',
                'website': 'https://greenscapeto.com',
                'business_address': '789 Dundas St W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6J 1T9',
                'service_category': 'Outdoor & Landscaping',
                'star_rating': 4.8,
                'review_count': 201,
                'description': 'Creative landscaping and outdoor design services to enhance your property.',
                'specialties': 'Garden design, Tree services, Lawn maintenance, Hardscaping',
                'years_experience': 10,
                'license_number': 'LAND-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'Toronto Tree Care',
                'phone': '(416) 555-0702',
                'email': 'info@torontotreecare.com',
                'business_address': '1500 Keele St',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6M 3W6',
                'service_category': 'Outdoor & Landscaping',
                'star_rating': 4.6,
                'review_count': 178,
                'description': 'Certified arborists providing expert tree care and landscape maintenance.',
                'specialties': 'Tree removal, Pruning, Stump grinding, Landscape maintenance',
                'years_experience': 16,
                'license_number': 'TREE-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },

            # Technology & Security
            {
                'name': 'SecureHome Systems',
                'phone': '(416) 555-0801',
                'email': 'info@securehome.ca',
                'website': 'https://securehome.ca',
                'business_address': '2100 Bloor St W',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6S 1M8',
                'service_category': 'Technology & Security',
                'star_rating': 4.8,
                'review_count': 312,
                'description': 'Advanced security systems and smart home technology installation.',
                'specialties': 'Security cameras, Alarm systems, Smart locks, Home automation',
                'years_experience': 9,
                'license_number': 'SEC-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            },
            {
                'name': 'TechConnect Solutions',
                'phone': '(416) 555-0802',
                'email': 'support@techconnect.ca',
                'business_address': '3300 Bathurst St',
                'city': 'Toronto',
                'province': 'ON',
                'postal_code': 'M6A 2A7',
                'service_category': 'Technology & Security',
                'star_rating': 4.5,
                'review_count': 267,
                'description': 'IT support and technology solutions for homes and small businesses.',
                'specialties': 'Network setup, Computer repair, Smart home integration, Tech support',
                'years_experience': 8,
                'license_number': 'TECH-2024-001',
                'insurance_verified': True,
                'background_checked': True,
                'status': 'active'
            }
        ]

        # Add all providers to database
        for provider_data in all_providers:
            provider = ServiceProvider(**provider_data)
            db.session.add(provider)

        db.session.commit()

        flash(f'Successfully added {len(all_providers)} providers across all service categories!', 'success')
        logging.info(f"All providers initialized: {len(all_providers)} providers added")

    except Exception as e:
        logging.error(f"Error initializing all providers: {str(e)}")
        flash('Error adding providers. Please try again.', 'danger')

    return redirect(url_for('admin_providers'))

@app.route('/populate-providers')
def populate_providers():
    """Public route to populate providers - for initial setup only"""
    try:
        # Clear existing providers first
        ServiceProvider.query.delete()
        db.session.commit()

        # Complete authentic provider database from your frontend application
        all_providers = [
            # Electrician Service Category (6 providers)
            {'name': 'Alkon Electric Inc', 'phone': '+14379834063', 'email': 'info@alkonelectric.ca', 'business_address': '8 Holswade Rd, Scarborough', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M1L 2G2', 'service_category': 'Electrician', 'star_rating': 5.0, 'review_count': 202, 'description': 'Family owned local business with 12+ years experience serving Toronto.', 'specialties': 'Electrical systems, wiring, outlets, lighting', 'years_experience': 12, 'license_number': 'ELEC-001', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Tron Electrical & Automation', 'phone': '+16474921989', 'email': 'info@tronelectrical.ca', 'business_address': '71 Silton Rd #1, Woodbridge', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'L4L 7Z8', 'service_category': 'Electrician', 'star_rating': 4.9, 'review_count': 353, 'description': 'Background checked electrical contractor with 12+ years experience.', 'specialties': 'Electrical automation, industrial systems, residential wiring', 'years_experience': 12, 'license_number': 'ELEC-002', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Reliance Home Comfort Electrical', 'phone': '(647) 735-6612', 'email': 'info@reliancehomecomfort.com', 'business_address': 'Multiple Locations', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M5V 3A8', 'service_category': 'Electrician', 'star_rating': 4.8, 'review_count': 17956, 'description': 'Background checked electrical service provider with 61+ years experience.', 'specialties': 'Home electrical systems, installations, emergency repairs', 'years_experience': 61, 'license_number': 'ELEC-003', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Enercare', 'phone': '(888) 921-7990', 'email': 'info@enercare.ca', 'business_address': 'Multiple Locations', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M5V 3A8', 'service_category': 'Electrician', 'star_rating': 4.8, 'review_count': 9906, 'description': 'Large-scale electrical service provider with 66+ years experience.', 'specialties': 'Electrical installations, energy solutions, home services', 'years_experience': 66, 'license_number': 'ELEC-004', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Plugin Electric LTD', 'phone': '(416) 832-3370', 'email': 'info@pluginelectric.ca', 'business_address': '372 Hwy 7 Unit 518B, Richmond Hill', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'L4B 0C6', 'service_category': 'Electrician', 'star_rating': 4.9, 'review_count': 62, 'description': 'Background checked electrical contractor with 4+ years experience.', 'specialties': 'Residential electrical, commercial installations, electrical repairs', 'years_experience': 4, 'license_number': 'ELEC-005', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Power Blitz Electrical', 'phone': '+18556080178', 'email': 'info@powerblitzelectrical.com', 'business_address': '20 De Boers Dr Suite 511, North York', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M3J 0G7', 'service_category': 'Electrician', 'star_rating': 4.8, 'review_count': 181, 'description': 'Free estimate, accepts urgent jobs with 32+ years experience.', 'specialties': 'Emergency electrical repairs, installations, electrical upgrades', 'years_experience': 32, 'license_number': 'ELEC-006', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            # HVAC Technician Service Category (6 providers)
            {'name': 'Woodbridge GTA ClimateCare', 'phone': '(905) 851-7007', 'email': 'info@climatecaregtac.ca', 'website': 'https://climatecaregtac.ca', 'business_address': '285 Jevlan Drive, Woodbridge', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'L4L 8G6', 'service_category': 'HVAC Technician', 'star_rating': 5.0, 'review_count': 482, 'description': 'Free in-home estimate, flat rate pricing with 45+ years experience.', 'specialties': 'Heating systems, air conditioning, ventilation, HVAC maintenance', 'years_experience': 45, 'license_number': 'HVAC-001', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Home Trade Standards - Condo HVAC Specialists', 'phone': '(416) 736-7001', 'email': 'info@hometradestandards.com', 'website': 'https://hometradestandards.com', 'business_address': '3983 Chesswood Dr, North York', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M3J 2R8', 'service_category': 'HVAC Technician', 'star_rating': 5.0, 'review_count': 427, 'description': 'HVAC contractor specializing in condo systems.', 'specialties': 'Condo HVAC systems, commercial HVAC, residential heating and cooling', 'years_experience': 15, 'license_number': 'HVAC-002', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Elite Air Quality Indoor', 'phone': '+16477876879', 'email': 'elite.aqi@gmail.com', 'business_address': '1176 Albion Rd', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M9V 1A8', 'service_category': 'HVAC Technician', 'star_rating': 5.0, 'review_count': 366, 'description': 'Background checked HVAC contractor with 8+ years experience.', 'specialties': 'Air quality improvement, HVAC installations, ventilation systems', 'years_experience': 8, 'license_number': 'HVAC-003', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Heat and Cool Brothers Inc', 'phone': '+14162571666', 'email': 'info@heatcoolbrothers.ca', 'business_address': '430 The Queensway S Unit 27, Keswick', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'L4P 2E1', 'service_category': 'HVAC Technician', 'star_rating': 5.0, 'review_count': 139, 'description': 'Accepts urgent jobs, free in-home estimate with 4+ years experience.', 'specialties': 'Emergency HVAC repairs, heating installations, cooling systems', 'years_experience': 4, 'license_number': 'HVAC-004', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Smile HVAC', 'phone': '(437) 777-4555', 'email': 'info@smilehvac.ca', 'website': 'https://smilehvac.ca', 'business_address': '8540 Keele St Unit 41, Vaughan', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'L4K 2A6', 'service_category': 'HVAC Technician', 'star_rating': 5.0, 'review_count': 1164, 'description': 'Established HVAC company with 25+ years serving Toronto area.', 'specialties': 'Complete HVAC solutions, heating and cooling installations, maintenance', 'years_experience': 25, 'license_number': 'HVAC-005', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Grace Comfort Air', 'phone': '+14168213302', 'email': 'info@gracecomfortair.ca', 'business_address': 'Toronto Service Area', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M5V 3A8', 'service_category': 'HVAC Technician', 'star_rating': 5.0, 'review_count': 311, 'description': 'Comfort air solutions with 20+ years experience serving Toronto.', 'specialties': 'Air conditioning, heating systems, HVAC maintenance, comfort solutions', 'years_experience': 20, 'license_number': 'HVAC-006', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            # Roofing Specialist Service Category (5 providers)
            {'name': 'High Skillz Roofing Inc', 'phone': '+16477043529', 'email': 'info@highskillzroofing.com', 'website': 'https://highskillzroofing.ca', 'business_address': '62 Alness St Unit 2-B', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M3J 2H1', 'service_category': 'Roofing Specialist', 'star_rating': 4.9, 'review_count': 156, 'description': 'Professional roofing contractor with quality craftsmanship.', 'specialties': 'Roof repairs, roof replacement, commercial roofing, residential roofing', 'years_experience': 10, 'license_number': 'ROOF-001', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Coverall Roofing - Toronto', 'phone': '(647) 470-4076', 'email': 'info@coverallroofing.ca', 'website': 'https://coverallroofing.ca', 'business_address': '1620A Dupont St', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M6P 3S7', 'service_category': 'Roofing Specialist', 'star_rating': 5.0, 'review_count': 154, 'description': 'Complete roofing solutions with excellent customer service.', 'specialties': 'Roof installation, roof repairs, emergency roofing, commercial roofing', 'years_experience': 12, 'license_number': 'ROOF-002', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Prime Roof Repairs', 'phone': '+16476331917', 'email': 'info@primeroofrepairs.com', 'website': 'https://primeroofrepairs.com', 'business_address': '151 Beecroft Rd, North York', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M2N 7C4', 'service_category': 'Roofing Specialist', 'star_rating': 5.0, 'review_count': 141, 'description': 'Roof repair specialists focusing on quality and customer satisfaction.', 'specialties': 'Roof repairs, leak detection, emergency roofing, roof maintenance', 'years_experience': 8, 'license_number': 'ROOF-003', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Unique Roofing Limited', 'phone': '+14165223063', 'email': 'info@uniqueroofing.ca', 'business_address': '266 Valleymede Dr, Richmond Hill', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'L4B 2C4', 'service_category': 'Roofing Specialist', 'star_rating': 5.0, 'review_count': 61, 'description': 'Background checked roofing contractor serving Toronto area.', 'specialties': 'Custom roofing, roof installations, roofing materials, roof design', 'years_experience': 15, 'license_number': 'ROOF-004', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'T DOT Roofers Inc', 'phone': '(416) 451-9293', 'email': 'info@tdotroofers.ca', 'business_address': '51 Sutherland Ave, Brampton', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'L6V 2H6', 'service_category': 'Roofing Specialist', 'star_rating': 5.0, 'review_count': 41, 'description': 'Roofing contractor with 10+ years serving the GTA.', 'specialties': 'Residential roofing, commercial roofing, roof repairs, roof installation', 'years_experience': 10, 'license_number': 'ROOF-005', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            # Plumber Service Category (6 providers)
            {'name': 'True Service Plumbing', 'phone': '+16472005238', 'email': 'info@trueserviceplumbing.ca', 'business_address': '180 Brock Avenue', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M6K 2L6', 'service_category': 'Plumber', 'star_rating': 5.0, 'review_count': 829, 'description': 'Family owned plumbing business with free estimate.', 'specialties': 'Plumbing repairs, pipe installation, drain cleaning, emergency plumbing', 'years_experience': 3, 'license_number': 'PLUMB-001', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Leslieville Drain & Plumbing', 'phone': '(647) 697-7026', 'email': 'info@leslievilledrain.ca', 'business_address': '1238 Queen Street East', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M4L 1C3', 'service_category': 'Plumber', 'star_rating': 5.0, 'review_count': 213, 'description': 'Background checked plumbing professionals with 36+ years experience.', 'specialties': 'Drain cleaning, plumbing installations, pipe repairs, sewer services', 'years_experience': 36, 'license_number': 'PLUMB-002', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Local Drain Expert', 'phone': '+16473710948', 'email': 'info@localdrainexpert.ca', 'business_address': '2220 Midland Ave, Scarborough', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M1P 3E6', 'service_category': 'Plumber', 'star_rating': 5.0, 'review_count': 85, 'description': 'Background checked drain expert with 39+ years experience.', 'specialties': 'Drain repairs, plumbing diagnostics, pipe cleaning, emergency services', 'years_experience': 39, 'license_number': 'PLUMB-003', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Yess Boss Plumbing Inc', 'phone': '+14372452324', 'email': 'info@yessbossplumbing.ca', 'business_address': '794 Neighbourhood Cir Unit # 2, Mississauga', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'L5B 0A6', 'service_category': 'Plumber', 'star_rating': 5.0, 'review_count': 69, 'description': 'Free estimate, accepts urgent jobs with 10+ years experience.', 'specialties': 'Emergency plumbing, installations, repairs, residential plumbing', 'years_experience': 10, 'license_number': 'PLUMB-004', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Coldstream Plumbing & Heating Ltd', 'phone': '+19059494400', 'email': 'info@coldstreamplumbing.ca', 'business_address': '5-2408 Haines Rd, Mississauga', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'L4Y 1Y6', 'service_category': 'Plumber', 'star_rating': 5.0, 'review_count': 62, 'description': 'Free estimate, accepts urgent jobs with 9+ years experience.', 'specialties': 'Plumbing and heating, installations, emergency services, residential services', 'years_experience': 9, 'license_number': 'PLUMB-005', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'City Rooter Plumbing and Drain Services', 'phone': '+16475346875', 'email': 'info@cityrooter.ca', 'business_address': '880 Hollyhill Ct, Mississauga', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'L4Y 2E1', 'service_category': 'Plumber', 'star_rating': 5.0, 'review_count': 53, 'description': 'Background checked plumbing specialists with 11+ years experience.', 'specialties': 'Drain services, rooter services, plumbing repairs, emergency plumbing', 'years_experience': 11, 'license_number': 'PLUMB-006', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            # General Handyman Service Category (6 providers)
            {'name': 'Handld - Handyman on Demand', 'phone': '+16472063243', 'email': 'info@handld.ca', 'website': 'https://handld.ca', 'business_address': '38 Joe Shuster Way', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M6K 0A5', 'service_category': 'General Handyman', 'star_rating': 5.0, 'review_count': 68, 'description': 'On-demand handyman services Mon-Sat 8AM-9PM, Sun Closed.', 'specialties': 'Home repairs, installations, maintenance, general handyman services', 'years_experience': 5, 'license_number': 'HAND-001', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Consider it Fixed', 'phone': '+14379846012', 'email': 'info@consideritfixed.ca', 'website': 'https://consideritfixed.ca', 'business_address': '55 Halton St', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M6J 1R5', 'service_category': 'General Handyman', 'star_rating': 5.0, 'review_count': 47, 'description': 'Professional handyman services Mon-Sun 8AM-8PM.', 'specialties': 'Home fixes, installations, repairs, maintenance solutions', 'years_experience': 6, 'license_number': 'HAND-002', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Odd Job Handyman Services Toronto', 'phone': '+14165201161', 'email': 'info@oddjobhandyman.ca', 'website': 'https://oddjobhandyman.ca', 'business_address': '46 Noble St', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M6K 2C9', 'service_category': 'General Handyman', 'star_rating': 4.9, 'review_count': 190, 'description': 'Handyman services Mon-Fri 9AM-5PM, Sat-Sun Closed.', 'specialties': 'Odd jobs, home repairs, installations, maintenance work', 'years_experience': 8, 'license_number': 'HAND-003', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Star Handyman', 'phone': '+16476292148', 'email': 'info@starhandyman.ca', 'website': 'https://starhandyman.ca', 'business_address': '75 St Nicholas St', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M4Y 0A5', 'service_category': 'General Handyman', 'star_rating': 4.9, 'review_count': 166, 'description': '24-hour handyman services available for emergency repairs.', 'specialties': 'Emergency repairs, 24-hour service, home maintenance, installations', 'years_experience': 12, 'license_number': 'HAND-004', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'X-Engineer Handyman Services', 'phone': '+16477495888', 'email': 'info@xengineerhandyman.ca', 'website': 'https://xengineerhandyman.ca', 'business_address': '15 Roehampton Ave', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M4P 0C2', 'service_category': 'General Handyman', 'star_rating': 4.9, 'review_count': 69, 'description': 'Engineer-quality handyman services Mon-Sun 9AM-8PM.', 'specialties': 'Technical repairs, engineering solutions, home improvements, installations', 'years_experience': 7, 'license_number': 'HAND-005', 'insurance_verified': True, 'background_checked': True, 'status': 'active'},

            {'name': 'Mike the Downtown Handyman', 'phone': '+16479897217', 'email': 'mike@downtownhandyman.ca', 'website': 'https://downtownhandyman.ca', 'business_address': '1163 Lansdowne Ave', 'city': 'Toronto', 'province': 'ON', 'postal_code': 'M6H 3Z7', 'service_category': 'General Handyman', 'star_rating': 4.9, 'review_count': 51, 'description': 'Downtown handyman Mon-Sun 8AM-8PM for all home repairs.', 'specialties': 'Downtown Toronto service, home repairs, maintenance, installations', 'years_experience': 9, 'license_number': 'HAND-006', 'insurance_verified': True, 'background_checked': True, 'status': 'active'}
        ]

        # Add all providers to database
        for provider_data in all_providers:
            provider = ServiceProvider(**provider_data)
            db.session.add(provider)

        db.session.commit()
        return f'Successfully added {len(all_providers)} providers to the database!'

    except Exception as e:
        return f'Error adding providers: {str(e)}'
@app.route('/api/providers/<service_category>')
def api_get_providers(service_category):
    """API endpoint to get providers for a specific service category and city with advertisements"""
    try:
        city = request.args.get('city')  # Get city from query param

        # Build the query
        query = ServiceProvider.query.filter(
            func.lower(ServiceProvider.service_category) == service_category.lower(),
            ServiceProvider.status == 'active'
        )

        if city:
            query = query.filter(func.lower(ServiceProvider.city) == city.lower())
        # Execute the query
        providers = query.order_by(
            ServiceProvider.star_rating.desc(),
            ServiceProvider.review_count.desc()
        ).all()

        # Get advertisements for this category and city
        ads_query = Advertisement.query.filter(
            func.lower(Advertisement.category_name) == service_category.lower(),
            Advertisement.status == 'active'
        )
        
        if city:
            ads_query = ads_query.filter(func.lower(Advertisement.city_name) == city.lower())
        
        advertisements = ads_query.order_by(Advertisement.position).all()

        providers_data = []
        for provider in providers:
            providers_data.append({
                'id': provider.id,
                'name': provider.name,
                'phone': provider.phone,
                'email': provider.email,
                'website': provider.website,
                'business_address': provider.business_address,
                'city': provider.city,
                'province': provider.province,
                'postal_code': provider.postal_code,
                'star_rating': provider.star_rating,
                'review_count': provider.review_count,
                'description': provider.description,
                'specialties': provider.specialties,
                'years_experience': provider.years_experience,
                'license_number': provider.license_number,
                'insurance_verified': provider.insurance_verified,
                'background_checked': provider.background_checked,
                'formatted_phone': provider.formatted_phone(),
                'full_address': provider.full_address(),
                'type': 'provider'  # Add type to distinguish from ads
            })

        # Convert advertisements to similar format
        ads_data = []
        for ad in advertisements:
            ads_data.append({
                'id': f'ad_{ad.id}',
                'title': ad.title,
                'description': ad.description,
                'image_url': ad.image_url,
                'phone': ad.phone_number,
                'email': ad.email,
                'website': ad.website,
                'city': ad.city_name,
                'category': ad.category_name,
                'position': ad.position,
                'star_rating': ad.star_rating,
                'review_count': ad.review_count,
                'review_text': ad.review_text,
                'formatted_phone': ad.formatted_phone(),
                'type': 'advertisement'  # Add type to distinguish from providers
            })

        return jsonify({
            'success': True,
            'providers': providers_data,
            'advertisements': ads_data,
            'count': len(providers_data)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/providers/all')
def api_get_all_providers():
    """API endpoint to get all active providers grouped by category"""
    try:
        providers = ServiceProvider.query.filter_by(status='active').all()

        providers_data = {}
        for provider in providers:
            category = provider.service_category
            if category not in providers_data:
                providers_data[category] = []

            providers_data[category].append({
                'id': provider.id,
                'name': provider.name,
                'phone': provider.phone,
                'email': provider.email,
                'website': provider.website,
                'business_address': provider.business_address,
                'city': provider.city,
                'province': provider.province,
                'postal_code': provider.postal_code,
                'star_rating': provider.star_rating,
                'review_count': provider.review_count,
                'description': provider.description,
                'specialties': provider.specialties,
                'years_experience': provider.years_experience,
                'license_number': provider.license_number,
                'insurance_verified': provider.insurance_verified,
                'background_checked': provider.background_checked,
                'formatted_phone': provider.formatted_phone(),
                'full_address': provider.full_address()
            })

        return jsonify({
            'success': True,
            'providers': providers_data,
            'total_count': len(providers)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
def send_update_async(payload):
    try:
        app.logger.debug(f"Sending async call/text update payload: {payload}")
        response = requests.post(
            'http://newconnectyou.pythonanywhere.com/api/update-call-text-counts/',
            json=payload,
            timeout=1
        )
        response.raise_for_status()
        app.logger.info(f"Successfully sent async call/text update: {payload}")
    except Exception as e:
        app.logger.error(f"Async API call/text update failed: {e}", exc_info=True)

def send_category_update_async(payload):
    try:
        app.logger.debug(f"Sending async category update payload: {payload}")
        response = requests.post(
            'https://newconnectyou.pythonanywhere.com/api/update-category-view-counts/',
            json=payload,
            timeout=1
        )
        response.raise_for_status()
        app.logger.info(f"Successfully sent async category update: {payload}")
    except Exception as e:
        app.logger.error(f"Async API category update failed: {e}", exc_info=True)

@app.route('/track_download', methods=['POST'])
def track_download():
    try:
        # Parse JSON data from request
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = json.loads(request.data.decode('utf-8'))
        app.logger.debug(f"Incoming data received: {data}")

        source = data.get('source')
        email = data.get('email')  # optional field
        name=data.get('name')

        if not source:
            app.logger.warning("Missing 'source' field in incoming request")
            return jsonify({'success': False, 'error': 'Missing source'}), 400

        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        app.logger.debug(f"User IP: {user_ip}, User Agent: {user_agent}")

        # Save tracking record in DB
        tracking = AppDownloadTracking(
            source=source,
            name=name,
            user_ip=user_ip,
            user_agent=user_agent,
            email=email
        )
        db.session.add(tracking)
        db.session.commit()
        app.logger.info(f"Tracked event - source: {source}, email: {email}, IP: {user_ip}")

        # Depending on presence of email and source, send async updates
        if email and source in ['call', 'text']:
            sums = get_event_sums(email)
            app.logger.debug(f"Event sums for email {email}: {sums}")
            payload = {
                'email': email,
                'name':name,
                'call': sums.get('call', 0),
                'text': sums.get('text', 0),
            }
            threading.Thread(target=send_update_async, args=(payload,)).start()

        elif not email:
            sums = get_category_sums(source)
            app.logger.debug(f"Category sums for source {source}: {sums}")
            payload = {
                'category_name': 'Electrician',
                'category': sums.get('category', 0)
            }
            threading.Thread(target=send_category_update_async, args=(payload,)).start()

        return jsonify({'success': True})

    except Exception as e:
        app.logger.error(f"Error in /track_download: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to track download'}), 500


def get_event_sums(email):
    call_count = db.session.query(AppDownloadTracking).filter_by(email=email, source='call').count()
    text_count = db.session.query(AppDownloadTracking).filter_by(email=email, source='text').count()
    app.logger.debug(f"Counts for email {email} -> calls: {call_count}, texts: {text_count}")
    return {
        'call': call_count,
        'text': text_count
    }

def get_category_sums(source):
    category_count = db.session.query(AppDownloadTracking).filter(
        func.lower(AppDownloadTracking.source) == source.lower()
    ).count()
    app.logger.debug(f"Category count for source {source}: {category_count}")
    return {
        'category': category_count
    }
@app.route('/admin/download_analytics')
@admin_required
def download_analytics():
    """Admin dashboard for app download analytics"""
    try:
        # Get download stats by source
        download_stats = db.session.query(
            AppDownloadTracking.source,
            func.count(AppDownloadTracking.id).label('count')
        ).group_by(AppDownloadTracking.source).all()

        # Get recent downloads (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_downloads = db.session.query(AppDownloadTracking).filter(
            AppDownloadTracking.timestamp >= thirty_days_ago
        ).order_by(desc(AppDownloadTracking.timestamp)).limit(100).all()

        # Get daily download counts for the last 30 days
        daily_stats = db.session.query(
            func.date(AppDownloadTracking.timestamp).label('date'),
            AppDownloadTracking.source,
            func.count(AppDownloadTracking.id).label('count')
        ).filter(
            AppDownloadTracking.timestamp >= thirty_days_ago
        ).group_by(
            func.date(AppDownloadTracking.timestamp),
            AppDownloadTracking.source
        ).order_by('date').all()

        # Calculate total downloads
        total_downloads = sum(stat.count for stat in download_stats)

        return render_template('admin_download_analytics.html',
                             download_stats=download_stats,
                             recent_downloads=recent_downloads,
                             daily_stats=daily_stats,
                             total_downloads=total_downloads)

    except Exception as e:
        flash(f'Error loading download analytics: {str(e)}', 'danger')
        return redirect(url_for('reports_dashboard'))

@app.route('/api/notification_change', methods=['POST'])
def add_notification_change():
    data = request.get_json()

    user_email = data.get('user_email')
    rating_change = data.get('rating_change')
    review_change = data.get('review_change')
    user_name=data.get('provider')
    if not user_email:
        return jsonify({'error': 'user_email is required'}), 400

    # Validate and convert fields
    rating_change = rating_change if rating_change is not None else 0

    try:
        review_change = int(review_change)
    except (TypeError, ValueError):
        review_change = 100  # fallback default

    notification = NotificationChange(
        user_email=user_email,
        rating_change=rating_change,
        review_change=review_change,
        p_name=user_name,
        created_at=datetime.utcnow()
    )

    try:
        db.session.add(notification)
        db.session.commit()


    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500


    return jsonify({'message': 'NotificationChange saved successfully'}), 201


@app.route('/admin/notifications')
@admin_required
def show_notifications():
    # Get all notifications sorted by newest first
    notifications = NotificationChange.query.order_by(
        NotificationChange.created_at.desc()
    ).all()

    # Create dictionary to store matched providers {notification_id: provider}
    matched_providers = {}

    for notification in notifications:
        # Try to find provider by exact email match
        provider = ServiceProvider.query.filter(
            db.func.lower(ServiceProvider.name) == db.func.lower(notification.p_name)
        ).first()

        # If not found by email and user_email looks like phone number, try phone
        if not provider and '@' not in notification.user_email:
            # Clean phone number for comparison
            clean_phone = ''.join(c for c in notification.user_email if c.isdigit())
            provider = ServiceProvider.query.filter(
                db.func.replace(
                    db.func.replace(ServiceProvider.phone, '-', ''),
                    ' ', ''
                ).contains(clean_phone)
            ).first()

        if provider:
            matched_providers[notification.id] = provider

    return render_template('notification_list.html',
                         notifications=notifications,
                         matched_providers=matched_providers)

@app.route('/admin/notifications/<int:notification_id>', methods=['DELETE'])
@admin_required
def delete_notification(notification_id):
    notification = NotificationChange.query.get_or_404(notification_id)
    db.session.delete(notification)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Notification deleted'})

import requests
import logging
import requests

@app.route('/api/service_providers/update_rating', methods=['POST'])
@admin_required
def update_service_provider_rating():
    data = request.get_json()

    required_fields = ['name']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields (email, name, service_category)'}), 400

    provider = ServiceProvider.query.filter(
        func.lower(ServiceProvider.name) == func.lower(data['name'])
    ).first()

    if not provider:
        return jsonify({'error': 'Service provider not found'}), 404

    if 'new_rating' in data and 'new_review' in data:
        try:
            new_rating = float(data['new_rating'])
            new_review = int(data['new_review'])
            provider.star_rating = new_rating
            provider.review_count = new_review
            provider.potential_rating = 0
            provider.potential_review_count = 0
            db.session.commit()
        except ValueError:
            return jsonify({'error': 'Invalid rating or review count value'}), 400

        # Prepare to call the Django API
        django_api_url = 'https://newconnectyou.pythonanywhere.com/api/update-provider-review/'
 # Update with your real URL
        payload = {
            'user_email': data['email'],
            'business_name': data['name'],
            'category': data['service_category'],
            'rating': new_rating,
            'review_count': new_review
        }

        try:
            print(f"Sending POST request to Django API at {django_api_url} with payload: {payload}")
            response = requests.post(django_api_url, json=payload, timeout=5)
            print(f"Django API response status code: {response.status_code}")
            print(f"Django API response content: {response.text}")
            response.raise_for_status()  # Raise for HTTP errors
        except requests.RequestException as e:
            # Log error but don't fail main update
            print(f"Warning: Failed to update Django provider: {e}")

    return jsonify({
        'message': 'Service provider updated successfully',
        'provider': {
            'id': provider.id,
            'email': provider.email,
            'name': provider.name,
            'service_category': provider.service_category,
            'star_rating': provider.star_rating,
            'review_count': provider.review_count,
            'potential_rating': getattr(provider, 'potential_rating', None),
            'potential_review_count': getattr(provider, 'potential_review_count', None)
        }
    }), 200
@app.route('/api/service-provider-report/<int:report_id>/hide', methods=['PUT'])
@admin_required
def update_is_hidden(report_id):
    data = request.get_json()
    if not data or 'is_hidden' not in data:
        return jsonify({"error": "Missing 'is_hidden' in request body"}), 400

    is_hidden_value = data['is_hidden']
    if not isinstance(is_hidden_value, bool):
        return jsonify({"error": "'is_hidden' must be a boolean"}), 400

    report = ServiceProviderReport.query.get(report_id)
    if not report:
        return jsonify({"error": "ServiceProviderReport not found"}), 404

    report.is_hidden = is_hidden_value
    db.session.commit()

    return jsonify({
        "message": f"ServiceProviderReport {report_id} updated",
        "id": report.id,
        "is_hidden": report.is_hidden
    }), 200


# City Management Routes
@app.route('/admin/cities')
@admin_required
def admin_cities():
    """City management dashboard"""
    cities = City.query.order_by(City.created_at.desc()).all()
    return render_template('admin_cities.html', cities=cities)

@app.route('/admin/cities/add', methods=['GET', 'POST'])
@admin_required
def admin_add_city():
    """Add new city"""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            country = request.form.get('country', '').strip()
            flag_emoji = request.form.get('flag', '').strip()

            if not all([name, country, flag_emoji]):
                flash('All fields are required.', 'danger')
                return render_template('admin_add_city.html')

            # Check if city already exists
            existing_city = City.query.filter_by(name=name).first()
            if existing_city:
                flash(f'City "{name}" already exists.', 'danger')
                return render_template('admin_add_city.html')

            # Create new city
            city = City(
                name=name,
                country=country,
                flag_emoji=flag_emoji,
                status='active'
            )

            db.session.add(city)
            db.session.commit()

            flash(f'City "{name}" added successfully!', 'success')
            return redirect(url_for('admin_cities'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding city: {str(e)}")
            flash('Error adding city. Please try again.', 'danger')

    return render_template('admin_add_city.html')

@app.route('/admin/cities/edit/<int:city_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_city(city_id):
    """Edit existing city"""
    city = City.query.get_or_404(city_id)

    if request.method == 'POST':
        try:
            city.name = request.form.get('name', '').strip()
            city.country = request.form.get('country', '').strip()
            city.flag_emoji = request.form.get('flag', '').strip()
            city.status = request.form.get('status', 'active')

            if not all([city.name, city.country, city.flag_emoji]):
                flash('All fields are required.', 'danger')
                return render_template('admin_edit_city.html', city=city)

            db.session.commit()
            flash(f'City "{city.name}" updated successfully!', 'success')
            return redirect(url_for('admin_cities'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating city: {str(e)}")
            flash('Error updating city. Please try again.', 'danger')

    return render_template('admin_edit_city.html', city=city)

@app.route('/admin/cities/delete/<int:city_id>', methods=['POST'])
@admin_required
def admin_delete_city(city_id):
    """Delete city"""
    try:
        city = City.query.get_or_404(city_id)
        city_name = city.name

        # Check if city has providers
        provider_count = ServiceProvider.query.filter_by(city=city_name).count()
        if provider_count > 0:
            flash(f'Cannot delete "{city_name}" because it has {provider_count} service providers. Please move or delete providers first.', 'danger')
            return redirect(url_for('admin_cities'))

        db.session.delete(city)
        db.session.commit()

        flash(f'City "{city_name}" deleted successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting city: {str(e)}")
        flash('Error deleting city. Please try again.', 'danger')

    return redirect(url_for('admin_cities'))

@app.route('/api/cities')
def api_get_cities():
    """API endpoint to get all active cities"""
    try:
        cities = City.query.filter_by(status='active').order_by(City.name).all()

        cities_data = []
        for city in cities:
            cities_data.append({
                'id': city.id,
                'name': city.name,
                'country': city.country,
                'flag': city.flag_emoji,
                'provider_count': city.provider_count,
                'category_count': city.category_count
            })

        return jsonify({
            'success': True,
            'cities': cities_data,
            'count': len(cities_data)
        })

    except Exception as e:
        logging.error(f"Error fetching cities: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching cities',
            'cities': [],
            'count': 0
        }), 500

@app.route('/admin/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def admin_delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    try:
        # Delete service providers with case-insensitive match on category name
        providers_to_delete = ServiceProvider.query.filter(
            db.func.lower(ServiceProvider.service_category) == category.name.lower()
        ).all()

        for provider in providers_to_delete:
            db.session.delete(provider)

        # Now delete the category
        db.session.delete(category)
        db.session.commit()

        flash(f"Category '{category.name}' and {len(providers_to_delete)} related provider(s) have been deleted.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the category: {str(e)}", "danger")

    return redirect(url_for('admin_providers', city=category.city_name))
@app.route('/admin/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_category(category_id):
    category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.icon = request.form.get('icon')
        category.status = request.form.get('status')
        db.session.commit()
        flash("Category updated successfully.", "success")
        return redirect(url_for('admin_providers', city=category.city_name))

    return render_template('admin_edit_category.html', category=category)
@app.route('/admin/categories/toggle/<int:category_id>', methods=['POST'])
@admin_required
def admin_toggle_category_visibility(category_id):
    category = Category.query.get_or_404(category_id)
    
    try:
        # Toggle between active and inactive
        if category.status == 'active':
            category.status = 'inactive'
            status_text = 'hidden from'
        else:
            category.status = 'active'
            status_text = 'visible on'
        
        db.session.commit()
        flash(f"Category '{category.name}' is now {status_text} the frontend.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while updating the category: {str(e)}", "danger")
    
    return redirect(url_for('admin_providers', city=category.city_name))
@app.route('/create-user-provider', methods=['POST'])
@admin_required
def create_user_provider():
    data = request.json

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    password2 = data.get('password2')
    provider_id = data.get('id')

    # Log incoming data
    logging.info(f"Received data: {json.dumps(data)}")

    # Register user on Django
    register_payload = {
        "username": username,
        "email": email ,
        "password": password,
        "password2": password2
    }
    existing_provider = ServiceProvider.query.filter_by(username=username).first()
    if existing_provider:
        logging.warning(f"Username '{username}' already exists in ServiceProvider.")
        return jsonify({"error": "Username already exists for a provider."}), 400

    try:
        register_resp = requests.post('https://newconnectyou.pythonanywhere.com/api/auth/register/', json=register_payload)
        register_resp.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"User registration failed: {e}")
        # Try to get more details from response if possible
        details = None
        if hasattr(e, 'response') and e.response is not None:
            try:
                details = e.response.json()
            except Exception:
                details = e.response.text
        return jsonify({"error": "User registration failed", "details": details or str(e)}), 500

    # Fetch provider data from Flask DB
    provider = ServiceProvider.query.get(provider_id)
    if not provider:
        logging.error(f"Provider with ID {provider_id} not found")
        return jsonify({"error": "Provider not found"}), 404

    provider.username = username
    provider.email1=email
    provider.password=password
    db.session.commit()

    provider_payload = {
        "username": username,
        "name": provider.name,
        "address": provider.business_address,
        "email": provider.email,
        "phone_number": provider.phone,
        "status": True if provider.status == 'active' else False,
        "city_name": provider.city,
        "country": "Nepal",  # Adjust accordingly if you have country info
        "service_name": provider.service_category,
        "service_description": provider.description or "",
        "service_image": "",  # add real image url if available
        "rating": provider.star_rating,
        "review_count": provider.review_count,
        "potential_rating": 0,
        "potential_review_count": 0,
        "review_proof": provider.website,
        "additional_info": f" {provider.years_experience}"
    }

    logging.info(f"Sending provider payload to Django: {json.dumps(provider_payload)}")

    try:
        add_provider_resp = requests.post('https://newconnectyou.pythonanywhere.com/api/add-provider/', json=provider_payload)
        add_provider_resp.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Provider creation failed: {e}")
        # Try to get more details from response if possible
        details = None
        if hasattr(e, 'response') and e.response is not None:
            try:
                details = e.response.json()
            except Exception:
                details = e.response.text
        return jsonify({"error": "Provider creation failed", "details": details or str(e)}), 500

    logging.info("User and provider created successfully")
    return jsonify({
        "message": "User and provider created successfully",
        "user": register_resp.json(),
        "provider": add_provider_resp.json()
    }), 201

@app.route('/service-provider/<int:provider_id>/clear_credentials', methods=['POST'])
@admin_required
def clear_service_provider_credentials(provider_id):
    provider = ServiceProvider.query.get(provider_id)
    if not provider:
        return jsonify({"error": "ServiceProvider not found"}), 404

    # Prepare data to send to Django API
    data = {
        "username": provider.username,
        "email": provider.email1
    }

    try:
        # 🔗 Call external Django API to delete the user
        response = requests.post("https://newconnectyou.pythonanywhere.com/api/delete-user/", json=data)
        if response.status_code != 200:
            return jsonify({"error": "Failed to delete user via external API", "details": response.json()}), response.status_code
    except Exception as e:
        return jsonify({"error": f"Error calling external API: {str(e)}"}), 500

    # ✅ If user deleted, clear local credentials
    provider.username = ''
    provider.email1 = ''
    provider.password = ''
    db.session.commit()

    return jsonify({"message": "User deleted remotely and credentials cleared locally."}), 200

@app.route('/api/password-changed', methods=['POST'])

def password_changed():
    # Check API Key in header
    api_key = request.headers.get('X-API-KEY')
    if api_key != EXPECTED_API_KEY:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    username = data.get('username')
    new_password = data.get('new_password')

    if not username or not new_password:
        return jsonify({'error': 'Username and password required'}), 400

    provider = ServiceProvider.query.filter_by(username=username).first()

    if not provider:
        return jsonify({'error': 'Service provider not found'}), 404

    # (Optional) Hash password before saving:
    # from werkzeug.security import generate_password_hash
    # provider.password = generate_password_hash(new_password)

    provider.password = new_password
    db.session.commit()

    return jsonify({'message': 'Password updated successfully'}), 200

@app.route('/update-provider', methods=['POST'])
@admin_required
def update_provider():
    data = request.get_json()

    username = data.get('username')
    new_email = data.get('email')
    new_password = data.get('password')

    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Call Django API first
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": EXPECTED_API_KEY
    }
    payload = {
        "username": username,
        "email": new_email,
        "password": new_password
    }

    try:
        django_response = requests.post("https://newconnectyou.pythonanywhere.com/api/update-provider-info/", json=payload, headers=headers, timeout=15)
        django_json = django_response.json()
    except Exception as e:
        return jsonify({"error": "Failed to contact Django API", "details": str(e)}), 500

    if django_response.status_code != 200:
        # Forward Django API error response
        return jsonify({
            "error": "Django API error",
            "details": django_json
        }), django_response.status_code

    # Django API success, now update local ServiceProvider
    provider = ServiceProvider.query.filter_by(username=username).first()
    if not provider:
        return jsonify({"error": "ServiceProvider with given username not found"}), 404

    if new_email:
        provider.email1 = new_email

    if new_password:
        # If you want to hash password, do it here; otherwise store raw (not recommended)
        provider.password = new_password

    db.session.commit()

    return jsonify({"message": "Provider updated locally and remotely successfully."}), 200

@app.route('/api/waiting_list', methods=['GET'])
def get_waiting_list():
    """API endpoint to get waiting list providers by status."""
    city = request.args.get('city')
    service = request.args.get('service')
    status = request.args.get('status', 'approved')  # Default to approved

    if not city or not service:
        return jsonify({'success': False, 'message': 'City and service are required'}), 400

    try:
        # Map URL-style service names to database service names
        service_mapping = {
            'electrician': 'Electrician',
            'plumber': 'Plumber',
            'hvac': 'HVAC',
            'handyman': 'General Handyman',
            'carpenter': 'Carpenter',
            'painter': 'Painter',
            'masonry': 'Masonry',
            'flooring': 'Flooring',
            'appliance': 'Appliance Repair Technician',
            'moving': 'Moving Services',
            'window-door': 'Window & Door Specialist',
            'locksmith': 'Locksmith',
            'garage-door': 'Garage Door Technician',
            'house-cleaner': 'House Cleaner',
            'window-cleaner': 'Window Cleaner',
            'gutter-cleaning': 'Gutter Cleaning Specialist',
            'chimney-sweep': 'Chimney Sweep',
            'pest-control': 'Pest Control',
            'mold-remediation': 'Mold Remediation Specialist',
            'junk-removal': 'Junk Removal Specialist',
            'pressure-washer': 'Pressure Washer',
            'lawn-care': 'Lawn Care Specialist',
            'tree-service': 'Tree Service Technician',
            'fence-gate': 'Fence & Gate Installer',
            'pool-maintenance': 'Pool Maintenance Technician',
            'security-system': 'Security System Installer',
            'smart-home': 'Smart Home Technician',
            'solar-panel': 'Solar Panel Installer',
            'roofing': 'Roofing Specialist'
        }
        
        # Map the service name to the database format
        mapped_service = service_mapping.get(service.lower(), service)
        
        # Get approved service provider applications for this service and city (for waiting list display)
        providers = ServiceProviderReport.query.filter(
            ServiceProviderReport.city == city,
            ServiceProviderReport.service == mapped_service,
            ServiceProviderReport.report_reason == 'service_provider_application',
            ServiceProviderReport.status == status
        ).all()

        provider_list = [{
            'id': p.id,
            'business_name': p.provider_name,
            'business_phone': p.provider_phone,
            'primary_email': p.user_email,
            'service_category': p.service,
            'city': p.city,
            'business_address': p.business_address,
            'rating': p.rating,
            'review_count': p.review_count,
        } for p in providers]
        
        # Sort providers by rating (highest first), then by review count (highest first) - same as main providers
        def sort_key(p):
            try:
                rating = float(p.get('rating', 0))
            except (ValueError, TypeError):
                rating = 0
            try:
                reviews = int(p.get('review_count', 0))
            except (ValueError, TypeError):
                reviews = 0
            return (-rating, -reviews)
        
        provider_list.sort(key=sort_key)
        
        return jsonify({'success': True, 'providers': provider_list})

    except Exception as e:
        logging.error(f"Error fetching waiting list: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
@app.route('/api/send-chat-message', methods=['POST'])
def send_chat_message():
    """Handle chat widget messages"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        message = data.get('message', '').strip()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        # Import chat service
        from chat_service import validate_chat_message, send_chat_message as send_message
        
        # Validate input
        validation = validate_chat_message(message, name, email, phone)

        if not validation['valid']:
            return jsonify({
                'success': False,
                'error': '; '.join(validation['errors'])
            }), 400
        
        # Send message
        result = send_message(message, name, email,phone)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Message sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logging.error(f"Error in chat message API: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/admin/chat-stats')
@admin_required
def admin_chat_stats():
    """API endpoint for real-time chat statistics"""
    try:
        from chat_models import ChatConversation, ChatMessage
        
        total_conversations = ChatConversation.query.count()
        open_conversations = ChatConversation.query.filter_by(status='open').count()
        unread_messages = ChatMessage.query.filter_by(is_from_admin=False, is_read=False).count()
        
        return jsonify({
            'success': True,
            'total': total_conversations,
            'open': open_conversations,
            'unread_messages': unread_messages
        })
    except Exception as e:
        logging.error(f"Error fetching chat stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch chat statistics'
        }), 500

@app.route('/api/get-chat-messages', methods=['GET'])
def get_chat_messages():
    phone = session.get('chat_phone')
    conversation = ChatConversation.query.filter_by(phone_number=phone).first()

    if not conversation:
        # No conversation found, clear session or prompt new info
        session.pop('chat_phone', None)
        session.pop('conversation_id', None)
        return jsonify({'success': False, 'error': 'No conversation found. Please start a new chat.'}), 404


    conversation = ChatConversation.query.filter_by(phone_number=phone).first()
    if not conversation:
        return jsonify({"success": True, "messages": []})

    messages = [{
        "text": m.message_text,
        "sender": "admin" if m.is_from_admin else "user",
        "time": m.created_at.strftime("%Y-%m-%d %H:%M")
    } for m in conversation.messages]

    return jsonify({"success": True, "messages": messages})

@app.route('/api/get-chat-messages-by-phone', methods=['POST'])
def get_chat_messages_by_phone():
    data = request.get_json()
    phone = data.get('phone')
    if not phone:
        return jsonify({'success': False, 'error': 'Phone number is required'}), 400

    # Query conversations by phone number
    conversations = ChatConversation.query.filter_by(phone_number=phone).all()

    if not conversations:
        # Return success with empty messages list instead of error
        return jsonify({'success': True, 'messages': []})

    messages = []
    for conv in conversations:
        for msg in conv.messages:
            messages.append({
                'id': msg.id,
                'conversation_id': conv.id,
                'text': msg.message_text,
                'sender': 'admin' if msg.is_from_admin else 'user',
                'time': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_read': msg.is_read
            })

    # Sort messages by time ascending
    messages.sort(key=lambda x: x['time'])

    return jsonify({'success': True, 'messages': messages})


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_image_url(filename):
    return f'/static/uploads/chat_icons/{filename}'

@app.route('/static/uploads/chat_icons/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/chat-icons', methods=['GET'])
def get_chat_icons():
    icons = ChatIcon.query.order_by(ChatIcon.created_at.desc()).all()
    return jsonify([icon.to_dict() for icon in icons]), 200


@app.route('/api/chat-icons', methods=['POST'])
def add_chat_icon():
    # Check if an icon already exists — only one allowed
    existing_icon = ChatIcon.query.first()
    if existing_icon:
        return jsonify({'error': 'Only one chat icon is allowed.'}), 400

    name = request.form.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400

    if 'image' not in request.files:
        return jsonify({'error': 'Image file is required'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected image file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'Allowed image types: {ALLOWED_EXTENSIONS}'}), 400

    filename = secure_filename(file.filename)
    filename = f"{int(datetime.utcnow().timestamp())}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    image_url = get_image_url(filename)

    description = request.form.get('description', '').strip() or None
    is_active = bool(request.form.get('is_active'))

    icon = ChatIcon(
        name=name,
        image_url=image_url,
        description=description,
        is_active=is_active
    )
    db.session.add(icon)
    db.session.commit()
    return jsonify(icon.to_dict()), 201

@app.route('/api/chat-icons/<int:icon_id>', methods=['PUT'])
def edit_chat_icon(icon_id):
    icon = ChatIcon.query.get(icon_id)
    if not icon:
        return jsonify({'error': 'ChatIcon not found'}), 404

    name = request.form.get('name')
    if name is not None:
        name = name.strip()
        if not name:
            return jsonify({'error': 'Name cannot be empty'}), 400
        icon.name = name

    # Update description if present in form data
    if 'description' in request.form:
        icon.description = request.form.get('description', '').strip() or None

    icon.is_active = bool(request.form.get('is_active'))

    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            if not allowed_file(file.filename):
                return jsonify({'error': f'Allowed image types: {ALLOWED_EXTENSIONS}'}), 400
            filename = secure_filename(file.filename)
            filename = f"{int(datetime.utcnow().timestamp())}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            icon.image_url = get_image_url(filename)

    db.session.commit()
    return jsonify(icon.to_dict()), 200

@app.route('/api/chat-icons/<int:icon_id>', methods=['DELETE'])
def delete_chat_icon(icon_id):
    icon = ChatIcon.query.get_or_404(icon_id)
    try:
        db.session.delete(icon)
        db.session.commit()
        return jsonify({'message': 'Chat icon deleted successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete chat icon.', 'details': str(e)}), 500
    
@app.route('/api/get-active-cities')
def get_active_cities():
    cities = City.query.filter_by(status='active').all()
    city_list = [
        {"name": city.name, "emoji": city.flag_emoji}
        for city in cities
    ]
    return jsonify({"success": True, "cities": city_list})

@app.route('/admin/chat/<int:conversation_id>/messages')
def get_messages(conversation_id):
    last_message_id = request.args.get('last_message_id', 0, type=int)
    messages = ChatMessage.query.filter(
        ChatMessage.conversation_id == conversation_id,
        ChatMessage.id > last_message_id
    ).order_by(ChatMessage.created_at).all()

    messages_data = [{
        'id': m.id,
        'message_text': m.message_text,
        'is_from_admin': m.is_from_admin,
        'admin_user': m.admin_user,
        'formatted_time': m.formatted_time
    } for m in messages]

    return jsonify(messages=messages_data)

# Advertisement Management Routes
@app.route('/admin/advertisements')
@admin_required
def admin_advertisements():
    """Advertisement management dashboard"""
    ads = Advertisement.query.order_by(desc(Advertisement.created_at)).all()
    cities = City.query.filter_by(status='active').order_by(City.name).all()
    
    # Get unique categories across all cities for the dropdown
    categories = db.session.query(ServiceProvider.service_category).distinct().order_by(ServiceProvider.service_category).all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('admin_advertisements.html', 
                         advertisements=ads, 
                         cities=cities, 
                         categories=categories)

@app.route('/admin/advertisements/add', methods=['GET', 'POST'])
@admin_required
def admin_add_advertisement():
    """Add new advertisement"""
    if request.method == 'POST':
        try:
            # Handle file upload
            uploaded_file = request.files.get('image')
            if not uploaded_file or uploaded_file.filename == '':
                flash('Please upload an image for the advertisement.', 'danger')
                return redirect(request.url)
            
            # Save the uploaded file
            import os
            import uuid
            filename = f"{uuid.uuid4()}_{uploaded_file.filename}"
            upload_path = os.path.join('static', 'uploads', 'advertisements')
            os.makedirs(upload_path, exist_ok=True)
            file_path = os.path.join(upload_path, filename)
            uploaded_file.save(file_path)
            
            # Process rating and review fields
            star_rating = request.form.get('star_rating')
            star_rating = float(star_rating) if star_rating and star_rating.strip() else None
            
            review_count = request.form.get('review_count')
            review_count = int(review_count) if review_count and review_count.strip() else 0
            
            review_text = request.form.get('review_text')
            review_text = review_text.strip() if review_text and review_text.strip() else None
            
            # Create new advertisement
            ad = Advertisement(
                title=request.form.get('title'),
                description=request.form.get('description'),
                image_url=f"uploads/advertisements/{filename}",
                phone_number=request.form.get('phone_number'),
                email=request.form.get('email'),
                website=request.form.get('website'),
                city_name=request.form.get('city_name'),
                category_name=request.form.get('category_name'),
                position=int(request.form.get('position', 3)),
                status=request.form.get('status', 'active'),
                star_rating=star_rating,
                review_count=review_count,
                review_text=review_text
            )
            
            db.session.add(ad)
            db.session.commit()
            
            flash(f'Advertisement "{ad.title}" added successfully!', 'success')
            return redirect(url_for('admin_advertisements'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding advertisement: {str(e)}")
            flash('Error adding advertisement. Please try again.', 'danger')
    
    # GET request - show form
    cities = City.query.filter_by(status='active').order_by(City.name).all()
    categories = db.session.query(ServiceProvider.service_category).distinct().order_by(ServiceProvider.service_category).all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('admin_add_advertisement.html', cities=cities, categories=categories)

@app.route('/admin/advertisements/edit/<int:ad_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_advertisement(ad_id):
    """Edit advertisement"""
    ad = Advertisement.query.get_or_404(ad_id)
    
    if request.method == 'POST':
        try:
            # Handle file upload if new image provided
            uploaded_file = request.files.get('image')
            if uploaded_file and uploaded_file.filename != '':
                import os
                import uuid
                filename = f"{uuid.uuid4()}_{uploaded_file.filename}"
                upload_path = os.path.join('static', 'uploads', 'advertisements')
                os.makedirs(upload_path, exist_ok=True)
                file_path = os.path.join(upload_path, filename)
                uploaded_file.save(file_path)
                
                # Delete old image if it exists
                if ad.image_url:
                    old_path = os.path.join('static', ad.image_url)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                ad.image_url = f"uploads/advertisements/{filename}"
            
            # Process rating and review fields
            star_rating = request.form.get('star_rating')
            star_rating = float(star_rating) if star_rating and star_rating.strip() else None
            
            review_count = request.form.get('review_count')
            review_count = int(review_count) if review_count and review_count.strip() else 0
            
            review_text = request.form.get('review_text')
            review_text = review_text.strip() if review_text and review_text.strip() else None
            
            # Update advertisement fields
            ad.title = request.form.get('title')
            ad.description = request.form.get('description')
            ad.phone_number = request.form.get('phone_number')
            ad.email = request.form.get('email')
            ad.website = request.form.get('website')
            ad.city_name = request.form.get('city_name')
            ad.category_name = request.form.get('category_name')
            ad.position = int(request.form.get('position', 3))
            ad.status = request.form.get('status', 'active')
            ad.star_rating = star_rating
            ad.review_count = review_count
            ad.review_text = review_text
            ad.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Advertisement "{ad.title}" updated successfully!', 'success')
            return redirect(url_for('admin_advertisements'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating advertisement: {str(e)}")
            flash('Error updating advertisement. Please try again.', 'danger')
    
    # GET request - show form
    cities = City.query.filter_by(status='active').order_by(City.name).all()
    categories = db.session.query(ServiceProvider.service_category).distinct().order_by(ServiceProvider.service_category).all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('admin_edit_advertisement.html', advertisement=ad, cities=cities, categories=categories)

@app.route('/admin/advertisements/delete/<int:ad_id>', methods=['POST'])
@admin_required
def admin_delete_advertisement(ad_id):
    """Delete advertisement"""
    try:
        ad = Advertisement.query.get_or_404(ad_id)
        
        # Delete image file if it exists
        if ad.image_url:
            import os
            file_path = os.path.join('static', ad.image_url)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.session.delete(ad)
        db.session.commit()
        
        flash(f'Advertisement "{ad.title}" deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting advertisement: {str(e)}")
        flash('Error deleting advertisement. Please try again.', 'danger')
    
    return redirect(url_for('admin_advertisements'))

@app.route('/test_phone_simple.html')
def test_phone_simple():
    """Test page for phone number redirects"""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Simple Phone Test</title>
    <meta name="format-detection" content="telephone=no">
</head>
<body style="padding: 50px; font-family: Arial;">
    <h1>Phone Number Test Page</h1>
    
    <h2>1. Direct tel: links:</h2>
    <a href="tel:+14379834063" style="display: block; margin: 10px 0; padding: 10px; background: green; color: white; text-decoration: none;">
        ✅ Direct Link: Call +1 (437) 983-4063
    </a>
    
    <h2>2. JavaScript button test:</h2>
    <button onclick="makeCall()" style="padding: 10px; margin: 10px 0; background: blue; color: white; border: none;">
        📞 JavaScript Call Button
    </button>
    
    <h2>3. Plain text (should NOT be clickable):</h2>
    <div style="padding: 10px; background: #f0f0f0;">
        Phone number as text: +1 (437) 983-4063
    </div>
    
    <h2>4. Test with old number (should redirect):</h2>
    <button onclick="testOldNumber()" style="padding: 10px; margin: 10px 0; background: red; color: white; border: none;">
        🔄 Test Old Number (416) 882-0852 → Should redirect to 437
    </button>
    
    <div id="output" style="margin-top: 20px; padding: 10px; background: #e8f4fd;"></div>
    
    <script>
        function makeCall() {
            console.log('JavaScript call function triggered');
            document.getElementById('output').innerHTML = 'Calling +1 (437) 983-4063...';
            window.location.href = 'tel:+14379834063';
        }
        
        function testOldNumber() {
            console.log('Testing old number redirect');
            document.getElementById('output').innerHTML = 'Redirecting (416) 882-0852 → +1 (437) 983-4063...';
            alert('Redirecting old number to: +1 (437) 983-4063');
            window.location.href = 'tel:+14379834063';
        }
        
        // Log page load
        console.log('Test page loaded successfully');
        document.getElementById('output').innerHTML = 'Page loaded. All calls should go to +1 (437) 983-4063';
    </script>
</body>
</html>"""
