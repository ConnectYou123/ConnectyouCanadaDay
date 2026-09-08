# System Patterns: ConnectYou Canada Day

## Architecture Overview

### Monolithic Flask Application
- Single Flask application serving both web pages and API endpoints
- SQLAlchemy ORM for database abstraction
- Jinja2 templating for server-side rendering
- Static assets served directly by Flask

### Database Design Patterns

#### Entity Relationships
- **Users** (admin/employee roles) → **ContactLists** → **Contacts**
- **Cities** → **ServiceProviders** (string-based relationship)
- **Cities** → **Categories** (foreign key relationship)
- **ServiceProviders** referenced in **ServiceProviderReports**

#### Key Models
1. **ServiceProvider**: Core provider entity with comprehensive business information
2. **City**: Geographic container for providers and categories
3. **Category**: Service type definition per city
4. **CommunicationLog**: Audit trail for customer-provider interactions
5. **User**: Internal platform users (admin/employee)

### API Design Patterns

#### RESTful Endpoints
- `/api/providers/<category>` - Get providers by service category
- `/api/cities` - Get available cities
- `/api/categories` - Get categories by city
- `/api/notification_change` - Track provider updates

#### Frontend-Backend Communication
- AJAX calls for dynamic content loading
- JSON responses for API endpoints
- Form submissions for user actions
- Real-time updates via direct API calls

#### Agent Admin API (`/agent-api/*`)
- Bearer token authentication via `AGENT_API_KEY`
- Full CRUD operations for all admin resources
- Tool definitions endpoint for agent integration
- Used by external agents (e.g. Telegram bot "Roger That")
- Mirrors admin panel functionality without session-based auth

### Security Patterns

#### Authentication & Authorization
- Session-based authentication for admin users (browser)
- Bearer token authentication for external agents (`@agent_api_auth`)
- Role-based access control (admin, manager, employee)
- Decorator-based route protection (`@admin_required`, `@login_required`, `@agent_api_auth`)
- Password hashing with PBKDF2

#### Data Protection
- SQL injection prevention via SQLAlchemy ORM
- CSRF protection through Flask's built-in mechanisms
- Input validation and sanitization
- Rate limiting considerations for API endpoints

### Communication Patterns

#### Twilio Integration
- SMS sending via `send_sms()` function
- Voice calling via `make_call()` function
- Communication logging for audit trails
- Error handling for failed communications

#### Email Services
- Report notifications via email
- Admin notifications for platform events
- Asynchronous email sending patterns

### Frontend Patterns

#### Progressive Enhancement
- Base HTML structure with CSS styling
- JavaScript enhancement for interactivity
- Fallback functionality for non-JS environments
- Mobile-first responsive design

#### User Interface Components
- Service category cards with consistent styling
- Provider profile cards with standardized information
- Modal dialogs for user interactions
- Theme switching (light/dark) with persistence

### Data Management Patterns

#### Database Migrations
- Flask-Migrate for schema versioning
- Incremental migration files for database evolution
- Rollback capabilities for deployment safety

#### Data Validation
- Model-level validation via SQLAlchemy
- Form validation in routes
- Client-side validation for user experience
- Server-side validation for security

### Error Handling Patterns

#### User-Friendly Error Pages
- Custom 404 and 500 error handlers
- Graceful degradation for missing data
- Flash messages for user feedback
- Logging for debugging and monitoring

#### API Error Responses
- Consistent JSON error format
- HTTP status codes for different error types
- Detailed error messages for debugging
- Fallback responses for edge cases

### Performance Patterns

#### Database Optimization
- Relationship lazy loading configuration
- Query optimization with proper indexing
- Connection pooling for database efficiency
- Pagination for large result sets

#### Caching Strategies
- Static asset caching via HTTP headers
- Database query result caching opportunities
- Session-based caching for user preferences

### Deployment Patterns

#### Environment Configuration
- Environment variables for sensitive settings
- Development vs. production configurations
- Database URL configuration flexibility
- Secret key management 