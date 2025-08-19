# ConnectYou AI Chat Setup Guide

## 🤖 AI Provider Integration

Your AI chat system supports three major AI providers. Choose one and follow the setup instructions below.

### 🔧 Quick Setup

1. **Run the setup script:**
   ```bash
   python setup_ai.py
   ```

2. **Or manually configure:**
   - Set environment variables
   - Use the admin panel
   - Edit the config file directly

### 🔑 Getting API Keys

#### Option 1: Claude (Anthropic) - Recommended
- **Website:** https://console.anthropic.com/
- **Cost:** $3-15 per million tokens
- **Best for:** Natural conversations, complex reasoning
- **Setup:**
  1. Create account at https://console.anthropic.com/
  2. Go to API Keys section
  3. Create a new API key
  4. Copy the key (starts with `sk-ant-`)

#### Option 2: OpenAI (ChatGPT)
- **Website:** https://platform.openai.com/
- **Cost:** $0.50-30 per million tokens
- **Best for:** Wide knowledge, popular choice
- **Setup:**
  1. Create account at https://platform.openai.com/
  2. Add billing information
  3. Go to API Keys
  4. Create new secret key
  5. Copy the key (starts with `sk-`)

#### Option 3: Google Gemini
- **Website:** https://makersuite.google.com/
- **Cost:** Free tier available, then $1-7 per million tokens
- **Best for:** Free usage, Google integration
- **Setup:**
  1. Go to https://makersuite.google.com/app/apikey
  2. Create API key
  3. Copy the key

### 🔧 Configuration Methods

#### Method 1: Environment Variables (Recommended)
Create a `.env` file in your project root:

```bash
# AI Provider
AI_PROVIDER=claude
CLAUDE_API_KEY=your_api_key_here

# SMS Service
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
```

#### Method 2: Setup Script
```bash
python setup_ai.py
```

#### Method 3: Admin Panel
1. Login to your admin panel
2. Go to AI Configuration
3. Enter your API keys
4. Save settings

### 📱 SMS Setup (Twilio)

To contact providers via SMS, you need Twilio:

1. **Sign up:** https://www.twilio.com/try-twilio
2. **Get credentials:**
   - Account SID
   - Auth Token
   - Phone Number
3. **Add to configuration**

### ✅ Testing Your Setup

1. **Check configuration:**
   ```bash
   curl http://localhost:3000/api/ai-agent/config
   ```

2. **Test AI response:**
   ```bash
   curl http://localhost:3000/api/ai-agent/test
   ```

3. **Test chat interface:**
   - Open your website
   - Click the robot button
   - Send a message: "I need an electrician"

### 🎯 How It Works

1. **User sends message** → AI analyzes request
2. **AI identifies service** → Searches your provider database
3. **Collects contact info** → Gets user's name and phone
4. **Texts providers** → Sends professional lead messages
5. **Confirms success** → Tells user providers will contact them

### 🛠 Troubleshooting

#### Chat not responding?
- Check API key is valid
- Verify provider is configured
- Look at server logs for errors

#### No providers contacted?
- Check Twilio configuration
- Verify providers exist in database
- Check provider phone numbers

#### API errors?
- Verify API key format
- Check billing/usage limits
- Test with curl commands

### 💰 Cost Estimates

**Typical usage for 1000 chats per month:**

- **Claude:** $5-15/month
- **OpenAI:** $3-20/month  
- **Google:** $0-10/month (free tier covers most usage)
- **Twilio SMS:** $10-30/month (depending on provider contacts)

### 🔒 Security Tips

- Never commit API keys to version control
- Use environment variables
- Rotate keys regularly
- Monitor usage and costs
- Set up billing alerts

### 📞 Support

If you need help:
1. Check the logs: `tail -f /var/log/flask.log`
2. Test endpoints with curl
3. Verify API key formats
4. Check provider documentation

---

**Ready to get started?** Run `python setup_ai.py` to begin!