"""
Enhanced chat service with conversation logging and management
"""
import os
import logging
from datetime import datetime
from flask import request
from app import db
from chat_models import ChatConversation, ChatMessage
from twilio_service import send_sms
from simple_email_service import send_simple_report_email

class ChatManager:
    """Manages chat conversations and logging"""
    
    @staticmethod
    def create_or_get_conversation(user_name, user_email=None,user_phone=None):
        """
        Create a new conversation or get existing open conversation for user
        
        Args:
            user_name: Name of the user
            user_email: Email of the user (optional)
            
        Returns:
            ChatConversation: The conversation object
        """
        try:
            # Get user IP
            user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if user_ip and ',' in user_ip:
                user_ip = user_ip.split(',')[0].strip()
            
            # Check for existing open conversation from same user (by email or name+IP)
            existing_conversation = None
            if user_email:
                existing_conversation = ChatConversation.query.filter_by(
                    user_email=user_email,
                    status='open'
                ).first()
            
            if not existing_conversation:
                # Look for recent conversation by name and IP
                existing_conversation = ChatConversation.query.filter_by(
                    user_name=user_name,
                    user_ip=user_ip,
                    status='open'
                ).first()
            
            if existing_conversation:
                # Update existing conversation
                existing_conversation.updated_at = datetime.utcnow()
                if user_email and not existing_conversation.user_email:
                    existing_conversation.user_email = user_email
                return existing_conversation
            
            # Create new conversation
            conversation = ChatConversation(
                user_name=user_name,
                user_email=user_email,
                phone_number=user_phone,
                user_ip=user_ip,
                status='open'
            )
            
            db.session.add(conversation)
            db.session.commit()
            
            logging.info(f"Created new chat conversation {conversation.id} for {user_name}")
            return conversation
            
        except Exception as e:
            logging.error(f"Error creating/getting conversation: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def log_user_message(conversation, message_text):
        """
        Log a message from the user
        
        Args:
            conversation: ChatConversation object
            message_text: The message text
            
        Returns:
            ChatMessage: The created message object
        """
        try:
            chat_message = ChatMessage(
                conversation_id=conversation.id,
                message_text=message_text,
                is_from_admin=False,
                is_read=False,
                delivery_method='received',
                delivery_status='received'
            )
            
            db.session.add(chat_message)
            
            # Update conversation
            conversation.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logging.info(f"Logged user message in conversation {conversation.id}")
            return chat_message
            
        except Exception as e:
            logging.error(f"Error logging user message: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def send_and_log_admin_reply(conversation_id, admin_message, admin_user):
        """
        Log admin reply (no SMS) and update the conversation
        
        Args:
            conversation_id: ID of the conversation
            admin_message: The admin's reply message
            admin_user: Username of the admin
            
        Returns:
            dict: Success or error response
        """
        try:
            conversation = ChatConversation.query.get(conversation_id)
            if not conversation:
                return {'success': False, 'error': 'Conversation not found'}

            # Log the admin message
            chat_message = ChatMessage(
                conversation_id=conversation_id,
                message_text=admin_message,
                is_from_admin=True,
                admin_user=admin_user,
                is_read=True,  # Admin messages are marked as read
                delivery_method='internal',
                delivery_status='sent',
                delivery_id=None
            )

            db.session.add(chat_message)

            # Update conversation timestamps
            conversation.updated_at = datetime.utcnow()
            conversation.last_admin_reply = datetime.utcnow()

            db.session.commit()

            logging.info(f"Admin reply logged for conversation {conversation_id}")
            return {
                'success': True,
                'message': 'Reply logged successfully'
            }

        except Exception as e:
            logging.error(f"Error logging admin reply: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error': f'Error logging reply: {str(e)}'
            }
    
    @staticmethod
    def mark_messages_as_read(conversation_id, admin_user):
        """
        Mark all user messages in conversation as read
        
        Args:
            conversation_id: ID of the conversation
            admin_user: Username of the admin marking as read
        """
        try:
            ChatMessage.query.filter_by(
                conversation_id=conversation_id,
                is_from_admin=False,
                is_read=False
            ).update({'is_read': True})
            
            db.session.commit()
            logging.info(f"Marked messages as read in conversation {conversation_id} by {admin_user}")
            
        except Exception as e:
            logging.error(f"Error marking messages as read: {str(e)}")
            db.session.rollback()
    
    @staticmethod
    def update_conversation_status(conversation_id, status, admin_user, notes=None):
        """
        Update conversation status and notes
        
        Args:
            conversation_id: ID of the conversation
            status: New status (open, closed, archived)
            admin_user: Username of the admin
            notes: Optional admin notes
            
        Returns:
            bool: Success status
        """
        try:
            conversation = ChatConversation.query.get(conversation_id)
            if not conversation:
                return False
            
            conversation.status = status
            conversation.updated_at = datetime.utcnow()
            
            if notes:
                conversation.admin_notes = notes
            
            db.session.commit()
            logging.info(f"Updated conversation {conversation_id} status to {status} by {admin_user}")
            return True
            
        except Exception as e:
            logging.error(f"Error updating conversation status: {str(e)}")
            db.session.rollback()
            return False