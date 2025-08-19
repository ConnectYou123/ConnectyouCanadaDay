import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

# Twilio configuration from environment variables
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

def get_twilio_client():
    """Get Twilio client or return None if not configured"""
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        logging.warning("Twilio credentials not fully configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER environment variables.")
        return None
    
    try:
        return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        logging.error(f"Failed to create Twilio client: {str(e)}")
        return None

def send_sms(to_phone_number: str, message: str) -> str:
    """
    Send SMS message using Twilio - ALL TEXTS REDIRECTED TO +14379834063
    
    Args:
        to_phone_number: Original phone number (ignored, redirects to main number)
        message: Message text to send
        
    Returns:
        Message SID if successful, None if failed
    """
    client = get_twilio_client()
    if not client:
        return None
    
    try:
        # REDIRECT ALL TEXTS TO MAIN NUMBER: +14379834063
        main_phone_number = '+14379834063'
        logging.info(f"Redirecting SMS from {to_phone_number} to main number: {main_phone_number}")
        
        message_obj = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=main_phone_number
        )
        
        logging.info(f"SMS sent successfully with SID: {message_obj.sid}")
        return message_obj.sid
        
    except TwilioException as e:
        logging.error(f"Twilio error sending SMS to {to_phone_number}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error sending SMS to {to_phone_number}: {str(e)}")
        return None

def make_call(to_phone_number: str, message: str = None) -> str:
    """
    Make a call using Twilio - ALL CALLS REDIRECTED TO +14379834063
    
    Args:
        to_phone_number: Original phone number (ignored, redirects to main number)
        message: Optional message to speak (uses TwiML)
        
    Returns:
        Call SID if successful, None if failed
    """
    client = get_twilio_client()
    if not client:
        return None
    
    try:
        # REDIRECT ALL CALLS TO MAIN NUMBER: +14379834063
        main_phone_number = '+14379834063'
        logging.info(f"Redirecting call from {to_phone_number} to main number: {main_phone_number}")
        
        # Create TwiML if message is provided
        twiml_url = None
        if message:
            # For simplicity, we'll use a basic TwiML that just says the message
            # In production, you might want to create a proper TwiML endpoint
            twiml_url = f"http://twimlets.com/message?Message={message}"
        
        call = client.calls.create(
            to=main_phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=twiml_url or "http://demo.twilio.com/docs/voice.xml"  # Default demo TwiML
        )
        
        logging.info(f"Call initiated successfully with SID: {call.sid}")
        return call.sid
        
    except TwilioException as e:
        logging.error(f"Twilio error making call to {to_phone_number}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error making call to {to_phone_number}: {str(e)}")
        return None

def format_phone_number(phone_number: str) -> str:
    """
    Format phone number for display
    
    Args:
        phone_number: Raw phone number
        
    Returns:
        Formatted phone number string
    """
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone_number))
    
    # Handle US phone numbers (10 digits)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        # US number with country code
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        # Return original if we can't format it
        return phone_number
