"""
Chat service for handling chat widget messages
"""
import os
import logging
from datetime import datetime
from twilio_service import send_sms
from simple_email_service import send_simple_report_email
import re
def send_chat_message(message, name, email=None,phone=None):
    """
    Send a chat message and log it in the conversation system
    
    Args:
        message: The user's message
        name: The user's name
        email: The user's email (optional)
        
    Returns:
        dict: Success/error response
    """
    try:
        # Import here to avoid circular imports
        from chat_manager import ChatManager
        
        # Create or get conversation
        conversation = ChatManager.create_or_get_conversation(name, email,phone)
        if not conversation:
            logging.error("Failed to create/get conversation")
            # Fallback to original behavior if database fails
            return send_chat_message_fallback(message, name, email)
        
        # Log the user message
        chat_message = ChatManager.log_user_message(conversation, message)
        if not chat_message:
            logging.error("Failed to log user message")
        
        # Format the message for SMS notification to business
        formatted_message = f"💬 New Chat Message from ConnectYou Website\n\n"
        formatted_message += f"From: {name}\n"
        if email:
            formatted_message += f"Email: {email}\n"
        if phone:
            formatted_message += f"Phone: {phone}\n"
        formatted_message += f"Message: {message}\n\n"
        formatted_message += f"Conversation ID: {conversation.id}\n"
        formatted_message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        formatted_message += f"View in admin panel to reply."
        
        # Try sending SMS notification to business first
        business_phone = "+14379834063"
        message_sid = send_sms(business_phone, formatted_message)
        
        if message_sid:
            logging.info(f"Chat notification sent via SMS with SID: {message_sid} for conversation {conversation.id}")
            return {
                'success': True,
                'message': 'Message sent successfully and logged',
                'conversation_id': conversation.id
            }
        else:
            # SMS failed, try email fallback for notification
            logging.warning("SMS notification failed, attempting email fallback")
            
            try:
                # Format message details for email
                email_notification = f"""
                New chat message received from ConnectYou website:
                
                Conversation ID: {conversation.id}
                From: {name}
                Email: {email if email else 'Not provided'}
                
                Message: {message}
                
                Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                
                Log into the admin panel to view the full conversation and reply.
                The message has been logged in the system.
                """
                
                send_simple_report_email(
                    provider_name=f"💬 Chat Notification: {name}",
                    provider_phone=email if email else "No email provided", 
                    reason="New Chat Message",
                    other_reason=email_notification
                )
                
                logging.info(f"Chat notification sent via email fallback for conversation {conversation.id}")
                return {
                    'success': True,
                    'message': 'Message logged successfully, notification sent via email',
                    'conversation_id': conversation.id
                }
            except Exception as email_error:
                logging.error(f"Email notification also failed: {str(email_error)}")
                # Still return success because the message was logged
                return {
                    'success': True,
                    'message': 'Message logged successfully, but notification delivery failed',
                    'conversation_id': conversation.id
                }
            
    except Exception as e:
        logging.error(f"Error in chat service: {str(e)}")
        # Fallback to original behavior if anything fails
        return send_chat_message_fallback(message, name, email,phone)

def send_chat_message_fallback(message, name, email=None,phone=None):
    """
    Fallback chat message handler (original behavior)
    """
    try:
        # Format the message for SMS
        formatted_message = f"💬 Chat Message from ConnectYou Website\n\n"
        formatted_message += f"Name: {name}\n"
        if email:
            formatted_message += f"Email: {email}\n"
        formatted_message += f"Message: {message}\n\n"
        formatted_message += f"Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Try sending SMS first
        business_phone = "+14379834063"
        message_sid = send_sms(business_phone, formatted_message)
        
        if message_sid:
            logging.info(f"Chat message sent via SMS with SID: {message_sid}")
            return {
                'success': True,
                'message': 'Message sent successfully via SMS'
            }
        else:
            # SMS failed, try email fallback
            logging.warning("SMS failed, attempting email fallback")
            
            try:
                email_message = f"""
                New chat message from ConnectYou website:
                
                From: {name}
                Email: {email if email else 'Not provided'}
                
                Message: {message}
                
                Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                
                send_simple_report_email(
                    provider_name=f"💬 Chat: {name}",
                    provider_phone=email if email else "No email provided", 
                    reason="Website Chat Message",
                    other_reason=email_message
                )
                
                logging.info("Chat message sent via email fallback")
                return {
                    'success': True,
                    'message': 'Message sent successfully via email'
                }
            except Exception as email_error:
                logging.error(f"Email fallback also failed: {str(email_error)}")
                return {
                    'success': False,
                    'error': 'Both SMS and email delivery failed. Please try again later or contact us directly.'
                }
            
    except Exception as e:
        logging.error(f"Error in fallback chat service: {str(e)}")
        return {
            'success': False,
            'error': f'Error sending message: {str(e)}'
        }

def validate_chat_message(message, name, email=None, phone=None):
    """
    Validate chat message data
    
    Args:
        message: The user's message
        name: The user's name
        email: The user's email (optional)
        phone: The user's phone number (required, E.164 format)
        
    Returns:
        dict: Validation result
    """
    errors = []
    
    if not message or not message.strip():
        errors.append("Message is required")
    elif len(message.strip()) > 1000:
        errors.append("Message is too long (max 1000 characters)")
    
    if not name or not name.strip():
        errors.append("Name is required")
    elif len(name.strip()) > 100:
        errors.append("Name is too long (max 100 characters)")
    
    if email and email.strip():
        if len(email.strip()) > 200:
            errors.append("Email is too long (max 200 characters)")
        elif '@' not in email or '.' not in email:
            errors.append("Invalid email format")
    
    # Phone validation: required & E.164 format
    e164_pattern = re.compile(r'^\+?[1-9]\d{7,14}$')
    if not phone or not phone.strip():
        errors.append("Phone number is required")
    elif not e164_pattern.match(phone.strip()):
        errors.append("Invalid phone number. Use E.164 format like +9779812345678")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
