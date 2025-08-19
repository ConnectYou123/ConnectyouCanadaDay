# ConnectYou - AI-Powered Service Provider Platform

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-ChatGPT-orange.svg)](https://openai.com)

ConnectYou is an intelligent service provider platform that uses AI to connect customers with the right service professionals in their area. The platform features an AI-powered chatbot that understands customer needs and automatically connects them with qualified service providers.

## 🚀 Features

### 🤖 AI-Powered Chatbot
- **ChatGPT Integration**: Advanced conversational AI for natural customer interactions
- **Smart Service Matching**: Automatically identifies customer needs and matches with appropriate service categories
- **Urgency Assessment**: Prioritizes emergency requests for faster response
- **Multi-Provider Support**: Supports OpenAI ChatGPT, Anthropic Claude, and Google Gemini

### 🔧 Service Management
- **20+ Service Categories**: Electricians, Plumbers, HVAC, Handymen, House Cleaners, and more
- **Provider Profiles**: Comprehensive profiles with ratings, photos, and contact information
- **Geographic Coverage**: City-based service provider matching
- **Automated Notifications**: SMS integration for instant provider alerts

### 📊 Admin Dashboard
- **Real-time Analytics**: Track conversations, provider performance, and user engagement
- **Chat Management**: Monitor and manage all customer conversations
- **Provider Management**: Add, edit, and manage service provider listings
- **API Key Management**: Secure encrypted storage of AI provider API keys

### 🔐 Security & Encryption
- **Encrypted API Keys**: All AI provider keys stored with Fernet encryption
- **Secure Authentication**: Admin authentication system
- **Database Security**: SQLite with proper data validation

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **AI Integration**: OpenAI GPT, Anthropic Claude, Google Gemini
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **SMS Service**: Twilio integration
- **Security**: Cryptography library for encryption

## 📦 Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/connectyou.git
   cd connectyou
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Access the application**
   - Main site: http://localhost:3000
   - Admin panel: http://localhost:3000/admin/login
   - Default admin credentials: username=admin, password=admin123

## ⚙️ Configuration

### AI Provider Setup
1. Access the admin panel at `/admin/login`
2. Navigate to the API Keys section
3. Add your API keys for:
   - **OpenAI**: Get from [OpenAI Platform](https://platform.openai.com/account/api-keys)
   - **Anthropic**: Get from [Anthropic Console](https://console.anthropic.com/)
   - **Google Gemini**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

### SMS Integration (Optional)
Set up Twilio for SMS notifications:
```python
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
```

## 🏗️ Project Structure

```
connectyou/
├── app.py                 # Flask application factory
├── main.py               # Application entry point
├── config.py             # Configuration management
├── models.py             # Database models
├── routes.py             # Main application routes
├── ai_agent_service.py   # AI chatbot service
├── admin_chat_routes.py  # Admin panel routes
├── chat_service.py       # Chat management
├── twilio_service.py     # SMS integration
├── templates/            # HTML templates
├── static/              # CSS, JS, images
├── migrations/          # Database migrations
└── requirements.txt     # Python dependencies
```

## 🎯 Usage

### For Customers
1. Visit the main website
2. Start a conversation with the AI chatbot
3. Describe your service needs
4. Provide contact information
5. Get connected with qualified service providers

### For Service Providers
1. Contact admin to get listed
2. Receive SMS notifications for relevant requests
3. Contact customers directly
4. Build your reputation through the platform

### For Administrators
1. Access the admin dashboard
2. Monitor chat conversations
3. Manage service provider listings
4. Configure AI settings
5. View analytics and reports

## 🔧 API Endpoints

### Chat API
- `POST /api/ai-agent/chat` - Process customer messages
- `GET /api/chat-icons` - Get chat interface icons

### Admin API
- `GET /admin/api-keys` - Manage AI provider keys
- `POST /admin/api-keys/update` - Update API keys
- `POST /admin/api-keys/test` - Test API connections

## 🚀 Deployment

### Development
The application runs in debug mode by default for development.

### Production
For production deployment:
1. Set `debug=False` in main.py
2. Use a production WSGI server (gunicorn, uWSGI)
3. Set up proper database (PostgreSQL recommended)
4. Configure environment variables
5. Set up SSL/HTTPS

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, please contact the development team or create an issue in the GitHub repository.

## 🔄 Updates

- **Latest Update**: August 2025 - Enhanced ChatGPT integration
- **Previous**: July 2025 - Core platform development

---

**Built with ❤️ for connecting people with quality service providers**