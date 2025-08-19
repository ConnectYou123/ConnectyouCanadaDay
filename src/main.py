#!/usr/bin/env python3
"""
Main entry point for the Value Investing Stock Finder application.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    """Main function to run the stock screening process."""
    # Load environment variables
    load_dotenv()
    
    # Import and run the web application
    from web_app import app, initialize_app
    
    # Initialize the application
    if not initialize_app():
        print("Failed to initialize application. Check logs for details.")
        sys.exit(1)
    
    # Run the Flask app
    print("🚀 Starting Value Investing Stock Finder Web Application...")
    print("📊 Web interface available at: http://localhost:3000")
    print("🔍 API endpoints available at: http://localhost:3000/api/")
    print("⏹️  Press Ctrl+C to stop the application")
    
    app.run(host='0.0.0.0', port=3000, debug=False)

if __name__ == "__main__":
    main()
