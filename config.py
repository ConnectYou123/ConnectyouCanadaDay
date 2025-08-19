"""
Configuration file for ConnectYou AI Chat Service
Handles API keys and service settings
"""

import os
from typing import Dict, Optional

class AIConfig:
    """
    Configuration manager for AI services and API keys
    """
    
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), '.ai_config')
        self._config = self._load_config()
    
    def _get_default_model(self, provider: str) -> str:
        """Get default model for provider"""
        defaults = {
            'claude': 'claude-3-sonnet-20240229',
            'openai': 'gpt-3.5-turbo',
            'google': 'gemini-pro'
        }
        return defaults.get(provider.lower(), 'claude-3-sonnet-20240229')
    
    def _load_config(self) -> Dict:
        """Load configuration from file or environment variables"""
        config = {}
        
        # Try to load from file first
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            config[key] = value
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        # Override with environment variables
        config.update({
            'CLAUDE_API_KEY': os.environ.get('CLAUDE_API_KEY', config.get('CLAUDE_API_KEY', '')),
            'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', config.get('OPENAI_API_KEY', '')),
            'GOOGLE_API_KEY': os.environ.get('GOOGLE_API_KEY', config.get('GOOGLE_API_KEY', '')),
            'AI_PROVIDER': os.environ.get('AI_PROVIDER', config.get('AI_PROVIDER', 'openai')),
            'AI_MODEL': os.environ.get('AI_MODEL', config.get('AI_MODEL', self._get_default_model(os.environ.get('AI_PROVIDER', config.get('AI_PROVIDER', 'openai'))))),
            'MAX_TOKENS': int(os.environ.get('AI_MAX_TOKENS', config.get('MAX_TOKENS', '1024'))),
            'TEMPERATURE': float(os.environ.get('AI_TEMPERATURE', config.get('TEMPERATURE', '0.7'))),
            'TWILIO_ACCOUNT_SID': os.environ.get('TWILIO_ACCOUNT_SID', config.get('TWILIO_ACCOUNT_SID', '')),
            'TWILIO_AUTH_TOKEN': os.environ.get('TWILIO_AUTH_TOKEN', config.get('TWILIO_AUTH_TOKEN', '')),
            'TWILIO_PHONE_NUMBER': os.environ.get('TWILIO_PHONE_NUMBER', config.get('TWILIO_PHONE_NUMBER', '')),
        })
        
        return config
    
    def save_config(self, updates: Dict):
        """Save configuration updates to file"""
        self._config.update(updates)
        
        try:
            with open(self.config_file, 'w') as f:
                f.write("# ConnectYou AI Configuration\n")
                f.write("# You can set these values here or as environment variables\n\n")
                
                for key, value in self._config.items():
                    if value:  # Only write non-empty values
                        f.write(f"{key}={value}\n")
                        
            print("Configuration saved successfully!")
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: str):
        """Set configuration value"""
        self._config[key] = value
    
    def get_api_key(self, provider: str = None) -> Optional[str]:
        """Get API key for specified provider from database first, then fallback to config"""
        if not provider:
            provider = self.get('AI_PROVIDER', 'claude')
        
        # Provider name mapping from config names to database names
        provider_map = {
            'claude': 'anthropic',
            'anthropic': 'anthropic',
            'openai': 'openai',
            'google': 'gemini',
            'gemini': 'gemini'
        }
        
        db_provider = provider_map.get(provider.lower())
        
        # Try to get from database first
        if db_provider:
            try:
                from models import APIKey
                api_key = APIKey.get_active_key(db_provider)
                if api_key:
                    # Update last used timestamp
                    APIKey.update_last_used(db_provider)
                    return api_key
            except Exception as e:
                # If database access fails, fall back to config/env
                pass
        
        # Fallback to config file/environment variables
        key_map = {
            'claude': 'CLAUDE_API_KEY',
            'anthropic': 'CLAUDE_API_KEY',
            'openai': 'OPENAI_API_KEY', 
            'google': 'GOOGLE_API_KEY',
            'gemini': 'GOOGLE_API_KEY'
        }
        
        key_name = key_map.get(provider.lower())
        if key_name:
            return self.get(key_name)
        return None
    
    def is_configured(self, provider: str = None) -> bool:
        """Check if AI provider is properly configured"""
        api_key = self.get_api_key(provider)
        twilio_sid = self.get('TWILIO_ACCOUNT_SID')
        twilio_token = self.get('TWILIO_AUTH_TOKEN')
        
        return bool(api_key and twilio_sid and twilio_token)
    
    def get_status(self) -> Dict:
        """Get configuration status"""
        return {
            'ai_provider': self.get('AI_PROVIDER', 'claude'),
            'ai_model': self.get('AI_MODEL', 'claude-3-sonnet-20240229'),
            'claude_configured': bool(self.get('CLAUDE_API_KEY')),
            'openai_configured': bool(self.get('OPENAI_API_KEY')),
            'google_configured': bool(self.get('GOOGLE_API_KEY')),
            'twilio_configured': bool(self.get('TWILIO_ACCOUNT_SID') and self.get('TWILIO_AUTH_TOKEN')),
            'fully_configured': self.is_configured()
        }

# Global configuration instance
ai_config = AIConfig()

# Configuration setup helper
def setup_ai_config():
    """Interactive configuration setup"""
    print("🤖 ConnectYou AI Chat Configuration Setup")
    print("=" * 50)
    
    current_status = ai_config.get_status()
    print(f"Current AI Provider: {current_status['ai_provider']}")
    print(f"Fully Configured: {'✅' if current_status['fully_configured'] else '❌'}")
    print()
    
    # AI Provider Selection
    print("1. Choose AI Provider:")
    print("   a) Claude (Anthropic) - Recommended")
    print("   b) OpenAI (ChatGPT)")
    print("   c) Google (Gemini)")
    
    provider_choice = input("Select provider (a/b/c) [current: a]: ").lower().strip()
    
    provider_map = {'a': 'claude', 'b': 'openai', 'c': 'google', '': 'claude'}
    provider = provider_map.get(provider_choice, 'claude')
    
    ai_config.set('AI_PROVIDER', provider)
    print(f"Selected: {provider}")
    print()
    
    # API Key Setup
    print(f"2. {provider.title()} API Key:")
    current_key = ai_config.get_api_key(provider)
    if current_key:
        print(f"   Current key: {'*' * 20}{current_key[-8:]}")
        update_key = input("   Update API key? (y/n) [n]: ").lower().strip()
        if update_key != 'y':
            current_key = None
    
    if not current_key:
        if provider == 'claude':
            print("   Get your Claude API key from: https://console.anthropic.com/")
        elif provider == 'openai':
            print("   Get your OpenAI API key from: https://platform.openai.com/api-keys")
        elif provider == 'google':
            print("   Get your Google API key from: https://makersuite.google.com/app/apikey")
        
        api_key = input(f"   Enter {provider.title()} API key: ").strip()
        if api_key:
            key_name = f"{provider.upper()}_API_KEY"
            ai_config.set(key_name, api_key)
            print("   ✅ API key saved")
        else:
            print("   ⚠️ No API key provided")
    
    # Twilio Configuration
    print()
    print("3. Twilio SMS Configuration:")
    print("   Get your Twilio credentials from: https://console.twilio.com/")
    
    twilio_sid = ai_config.get('TWILIO_ACCOUNT_SID')
    if twilio_sid:
        print(f"   Current SID: {'*' * 20}{twilio_sid[-8:]}")
        update_twilio = input("   Update Twilio config? (y/n) [n]: ").lower().strip()
        if update_twilio != 'y':
            twilio_sid = None
    
    if not twilio_sid:
        twilio_sid = input("   Enter Twilio Account SID: ").strip()
        twilio_token = input("   Enter Twilio Auth Token: ").strip()
        twilio_phone = input("   Enter Twilio Phone Number (+1234567890): ").strip()
        
        if twilio_sid and twilio_token and twilio_phone:
            ai_config.set('TWILIO_ACCOUNT_SID', twilio_sid)
            ai_config.set('TWILIO_AUTH_TOKEN', twilio_token)
            ai_config.set('TWILIO_PHONE_NUMBER', twilio_phone)
            print("   ✅ Twilio configuration saved")
        else:
            print("   ⚠️ Incomplete Twilio configuration")
    
    # Save configuration
    print()
    ai_config.save_config({})
    
    final_status = ai_config.get_status()
    print("Configuration Complete!")
    print(f"Status: {'✅ Ready to use' if final_status['fully_configured'] else '❌ Needs completion'}")
    
    return final_status['fully_configured']

if __name__ == "__main__":
    setup_ai_config()