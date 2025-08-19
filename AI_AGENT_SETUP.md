# AI Agent Setup Instructions

## 🤖 ConnectYou AI Agent Integration

Your search box now includes an intelligent AI agent that can understand user needs and automatically connect them with the right service providers via SMS!

## 🔑 Required Setup

### 1. Claude API Key
To use the AI agent, you need to set up a Claude API key:

1. Go to [https://console.anthropic.com/](https://console.anthropic.com/)
2. Create an account or sign in
3. Generate an API key
4. Set the environment variable:
   ```bash
   export CLAUDE_API_KEY="your_api_key_here"
   ```

### 2. Install Dependencies
The AI agent uses the `requests` library (already in your requirements.txt):
```bash
pip install requests
```

## 🚀 How It Works

### User Experience:
1. **Toggle Search Mode**: Users can switch between "Quick Search" and "AI Assistant"
2. **Natural Language**: Users describe their needs: "I need an electrician to fix my lights"
3. **AI Conversation**: The AI asks follow-up questions to understand the problem
4. **Contact Collection**: AI collects user's name and phone number
5. **Auto-SMS**: AI automatically texts top 3 matching providers with the lead

### Example Conversation:
```
User: "My sink is leaking and it's urgent"
AI: "I can help you find a plumber right away! Can you tell me more about the leak? Is it under the sink, from the faucet, or elsewhere?"
User: "It's leaking under the kitchen sink, water is getting everywhere"
AI: "That sounds urgent! What's the best phone number for plumbers to reach you?"
User: [Provides contact info]
AI: "Perfect! I'm sending your request to 3 qualified plumbers in Toronto who can handle urgent kitchen sink leaks. They should contact you within the next hour."
```

## 🛠️ Features

### AI Capabilities:
- **Natural Language Understanding**: Understands user problems in plain English
- **Service Category Detection**: Automatically identifies needed service type
- **Urgency Assessment**: Recognizes urgent vs. non-urgent requests
- **Detail Gathering**: Asks relevant follow-up questions
- **Provider Matching**: Finds best-rated providers in user's city

### Technical Features:
- **Conversation Memory**: Maintains context throughout the chat
- **Automatic SMS**: Sends professional messages to providers
- **Real-time Chat UI**: Modern chat interface with typing indicators
- **Contact Form**: Secure collection of user contact information
- **Error Handling**: Graceful fallbacks if AI service is unavailable

## 📋 Testing the AI Agent

### 1. Test Without API Key (Fallback Mode):
- The AI will respond with a fallback message
- Regular search functionality still works

### 2. Test With API Key:
```bash
# Set the API key
export CLAUDE_API_KEY="your_key_here"

# Restart the application
python main.py

# Test endpoints:
curl http://localhost:3000/api/ai-agent/test
```

### 3. Test Examples:
Try these prompts in the AI Assistant:
- "I need an electrician to fix my lights"
- "My toilet is clogged and overflowing"
- "I want to paint my living room next week"
- "Emergency! My furnace stopped working in winter"

## 🔍 API Endpoints

The AI agent adds these new endpoints:

- `POST /api/ai-agent/chat` - Main chat endpoint
- `GET /api/ai-agent/providers/<category>` - Get providers for service
- `POST /api/ai-agent/send-leads` - Manually send leads to providers
- `GET /api/ai-agent/test` - Test AI agent functionality

## ⚙️ Configuration

### Environment Variables:
```bash
CLAUDE_API_KEY=your_claude_api_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_number
```

### Service Categories Supported:
- Electrician
- Plumber
- HVAC
- General Handyman
- House Cleaner
- Carpenter
- Painter
- Roofing Specialist
- Appliance Repair Technician
- Locksmith
- Pest Control
- Moving Services
- And 15+ more categories

## 💡 Usage Tips

### For Maximum Effectiveness:
1. **Ensure Twilio is configured** - The AI needs to send SMS
2. **Have active providers** - AI works best with providers in your database
3. **Monitor conversations** - Check logs to see AI performance
4. **Customize prompts** - Edit `ai_agent_service.py` to modify AI behavior

### Customization Options:
- Modify the system prompt in `ai_agent_service.py`
- Adjust provider selection logic
- Customize SMS message templates
- Add new service categories

## 🚨 Production Considerations

### Security:
- Store API keys securely
- Validate user inputs
- Rate limit API calls

### Monitoring:
- Log AI conversations
- Track conversion rates
- Monitor SMS delivery
- Measure provider response times

## 🎉 Success!

Your ConnectYou platform now has an intelligent AI agent that can:
✅ Understand user problems in natural language
✅ Automatically match users with the right providers
✅ Send professional SMS leads to providers
✅ Provide a modern chat experience
✅ Handle edge cases and errors gracefully

Users can now simply describe their problem and get connected with professionals automatically!