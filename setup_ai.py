#!/usr/bin/env python3
"""
Quick Setup Script for ConnectYou AI Chat Service
"""

import os
import sys
from config import setup_ai_config

def main():
    print("🤖 ConnectYou AI Chat Setup")
    print("=" * 40)
    print("This script will help you configure the AI chat service.")
    print("You'll need:")
    print("• An AI provider API key (Claude, OpenAI, or Google)")
    print("• Twilio credentials for SMS functionality")
    print()
    
    # Check if running in virtual environment
    if not hasattr(sys, 'real_prefix') and sys.base_prefix == sys.prefix:
        print("⚠️  Warning: You don't appear to be in a virtual environment.")
        print("   Consider running 'source venv/bin/activate' first.")
        print()
    
    try:
        success = setup_ai_config()
        
        if success:
            print()
            print("✅ Setup Complete!")
            print("Your AI chat service is ready to use.")
            print()
            print("Next steps:")
            print("1. Start your Flask application: python main.py")
            print("2. Test the AI chat by clicking the robot button on your website")
            print("3. Test the configuration at: http://localhost:3000/api/ai-agent/test")
            print()
            print("💡 Tip: You can reconfigure anytime by running this script again.")
        else:
            print()
            print("❌ Setup Incomplete")
            print("Please ensure all required fields are filled out.")
            print("Run this script again to complete the setup.")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user.")
    
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        print("Please check your inputs and try again.")

if __name__ == "__main__":
    main()