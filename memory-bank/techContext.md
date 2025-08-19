# Technical Context: ConnectYou Canada Day

## Technology Stack

### Backend Framework
- **Flask 3.1.1**: Lightweight Python web framework
- **SQLAlchemy 2.0.41**: Modern ORM with async support
- **Flask-SQLAlchemy 3.1.1**: Flask integration for SQLAlchemy
- **Flask-Migrate 4.1.0**: Database migration management
- **Alembic 1.16.1**: Database migration engine

### Database
- **SQLite**: Development and potentially production database
- **Location**: `instance/contacts.db`
- **Migration System**: Flask-Migrate with version control

### Communication Services
- **Twilio 9.6.3**: SMS and voice calling capabilities
- **MailerSend 0.6.0**: Email service for notifications
- **Simple Email Service**: Custom email wrapper

### Frontend Technologies
- **HTML5**: Semantic markup structure
- **CSS3**: Modern styling with custom properties
- **JavaScript ES6+**: Interactive functionality
- **Bootstrap**: Responsive UI framework (referenced but not in requirements)
- **FontAwesome**: Icon library for UI elements

### Development Tools
- **PyProject.toml**: Modern Python project configuration
- **UV Lock**: Dependency management and locking
- **Git**: Version control system
- **Requirements.txt**: Traditional Python dependencies

## Development Setup

### Environment Requirements
- **Python 3.8+**: Modern Python version
- **Flask Development Server**: For local development
- **SQLite**: No additional database server required

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
flask db upgrade

# Start development server
python app.py  # or flask run
```

### Key Configuration
- **Database URI**: Configurable via `DATABASE_URL` environment variable
- **Secret Key**: Session management via `SESSION_SECRET`
- **Debug Mode**: Enabled for development

## Technical Constraints

### Database Limitations
- **SQLite**: Single-writer limitation for high-concurrency scenarios
- **File-based**: Requires proper backup and deployment strategies
- **Scalability**: May need migration to PostgreSQL for production

### Communication Dependencies
- **Twilio Account**: Required for SMS/calling functionality
- **Email Service**: MailerSend account needed for notifications
- **API Keys**: Secure management of external service credentials

### Deployment Considerations
- **Single Process**: Flask development server not suitable for production
- **Static Files**: Need proper serving in production environment
- **Database Persistence**: SQLite file needs proper backup strategy

## API Structure

### Internal API Endpoints
- **Provider Data**: `/api/providers/<category>`
- **City Management**: `/api/cities`
- **Category Data**: `/api/categories`
- **Analytics**: Various admin endpoints

### External Integrations
- **Twilio SMS**: Voice and messaging services
- **Email Services**: Notification and reporting
- **Frontend Ajax**: Dynamic content loading

## Security Configuration

### Authentication
- **Session-based**: Server-side session management
- **Password Hashing**: PBKDF2 with salt
- **Role-based Access**: Admin/manager/employee roles

### Data Protection
- **SQL Injection**: Protected via SQLAlchemy ORM
- **CSRF**: Flask built-in protection
- **Input Validation**: Server-side validation required

## File Structure

### Core Application Files
- `app.py`: Application factory and configuration
- `models.py`: Database models and relationships
- `routes.py`: URL routing and business logic
- `main.py`: Application entry point

### Service Modules
- `twilio_service.py`: SMS and calling functionality
- `email_service.py`: Email notifications
- `simple_email_service.py`: Simplified email wrapper
- `category_detector.py`: Service category logic

### Frontend Assets
- `templates/`: Jinja2 HTML templates
- `static/css/`: Custom styling
- `static/js/`: JavaScript functionality

### Database Management
- `migrations/`: Database version control
- `instance/`: Database files and instance-specific data

## Development Workflow

### Database Changes
1. Modify models in `models.py`
2. Generate migration: `flask db migrate -m "description"`
3. Apply migration: `flask db upgrade`
4. Test changes thoroughly

### Feature Development
1. Update models if needed
2. Add/modify routes in `routes.py`
3. Create/update templates
4. Add JavaScript functionality if needed
5. Test across different devices and browsers

### Deployment Preparation
1. Update requirements.txt
2. Set environment variables
3. Configure production database
4. Set up proper web server (Gunicorn, uWSGI)
5. Configure reverse proxy (nginx) 