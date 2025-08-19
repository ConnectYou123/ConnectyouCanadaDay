"""
Admin routes for chat conversation management
"""
import logging
from datetime import datetime
from flask import request, render_template, redirect, url_for, flash, jsonify, session
from sqlalchemy import desc, func
from app import app, db
from chat_models import ChatConversation, ChatMessage
from chat_manager import ChatManager

def admin_required_chat(f):
    """Decorator to require admin login for chat routes"""
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/admin/chat-conversations')
@admin_required_chat
def admin_chat_conversations():
    """Admin dashboard for viewing all chat conversations"""
    try:
        # Get filter parameters
        status_filter = request.args.get('status', 'all')
        priority_filter = request.args.get('priority', 'all')
        page = request.args.get('page', 1, type=int)
        
        # Build query
        query = ChatConversation.query
        
        if status_filter != 'all':
            query = query.filter_by(status=status_filter)
        
        if priority_filter != 'all':
            query = query.filter_by(priority=priority_filter)
        
        # Order by most recent activity
        conversations = query.order_by(desc(ChatConversation.updated_at)).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Get conversation statistics
        stats = {
            'total': ChatConversation.query.count(),
            'open': ChatConversation.query.filter_by(status='open').count(),
            'closed': ChatConversation.query.filter_by(status='closed').count(),
            'unread_messages': db.session.query(func.count(ChatMessage.id)).filter(
                ChatMessage.is_from_admin == False,
                ChatMessage.is_read == False
            ).scalar()
        }
        
        return render_template('admin_chat_conversations.html', 
                             conversations=conversations, 
                             stats=stats,
                             status_filter=status_filter,
                             priority_filter=priority_filter)
        
    except Exception as e:
        logging.error(f"Error in admin chat conversations: {str(e)}")
        flash('Error loading conversations', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/chat-conversation/<int:conversation_id>')
@admin_required_chat
def admin_chat_conversation_detail(conversation_id):
    """View detailed conversation with all messages"""
    try:
        conversation = ChatConversation.query.get_or_404(conversation_id)

        # DEBUG: Check the type
        logging.debug(f"Type of ChatManager.mark_messages_as_read: {type(ChatManager.mark_messages_as_read)}")

        admin_user = session.get('admin_username', 'admin')
        ChatManager.mark_messages_as_read(conversation_id, admin_user)

        return render_template('admin_chat_conversation_detail.html', 
                             conversation=conversation)
        
    except Exception as e:
        logging.error(f"Error viewing conversation {conversation_id}: {str(e)}")
        flash('Error loading conversation', 'error')
        return redirect(url_for('admin_chat_conversations'))

@app.route('/admin/chat-conversation/<int:conversation_id>/reply', methods=['POST'])
@admin_required_chat
def admin_chat_reply(conversation_id):
    """Send admin reply (JSON-only, optimized)"""
    if not request.is_json:
        return jsonify(success=False, error='Only JSON allowed'), 400

    data = request.get_json()
    admin_message = data.get('admin_message', '').strip()
    if not admin_message:
        return jsonify(success=False, error='Message cannot be empty'), 400

    admin_user = session.get('admin_username', 'admin')

    try:
        # Create and save message
        new_msg = ChatMessage(
            conversation_id=conversation_id,
            message_text=admin_message,
            is_from_admin=True,
            admin_user=admin_user,
            created_at=datetime.utcnow()
        )
        db.session.add(new_msg)
        db.session.commit()

        # Return only the essential message details
        return jsonify(success=True, message={
            'id': new_msg.id,
            'message_text': new_msg.message_text,
            'formatted_time': new_msg.created_at.strftime('%I:%M %p'),
            'is_from_admin': new_msg.is_from_admin,
            'admin_user': new_msg.admin_user
        })

    except Exception as e:
        import logging
        logging.error(f"Failed to send admin reply: {str(e)}")
        return jsonify(success=False, error='Internal server error'), 500
@app.route('/admin/chat-conversation/<int:conversation_id>/update-status', methods=['POST'])
@admin_required_chat
def admin_chat_update_status(conversation_id):
    """Update conversation status and notes"""
    try:
        new_status = request.form.get('status')
        priority = request.form.get('priority')
        admin_notes = request.form.get('admin_notes', '').strip()
        admin_user = session.get('admin_username', 'admin')
        
        conversation = ChatConversation.query.get_or_404(conversation_id)
        
        if new_status:
            conversation.status = new_status
        
        if priority:
            conversation.priority = priority
            
        if admin_notes:
            conversation.admin_notes = admin_notes
            
        conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Conversation updated successfully', 'success')
        return redirect(url_for('admin_chat_conversation_detail', conversation_id=conversation_id))
        
    except Exception as e:
        logging.error(f"Error updating conversation status: {str(e)}")
        flash('Error updating conversation', 'error')
        return redirect(url_for('admin_chat_conversation_detail', conversation_id=conversation_id))

@app.route('/admin/chat-conversations/bulk-action', methods=['POST'])
@admin_required_chat
def admin_chat_bulk_action():
    """Perform bulk actions on multiple conversations"""
    try:
        action = request.form.get('bulk_action')
        conversation_ids = request.form.getlist('conversation_ids')
        admin_user = session.get('admin_username', 'admin')
        
        if not conversation_ids:
            flash('No conversations selected', 'error')
            return redirect(url_for('admin_chat_conversations'))
        
        conversation_ids = [int(id) for id in conversation_ids]
        
        if action == 'mark_read':
            for conv_id in conversation_ids:
                ChatManager.mark_messages_as_read(conv_id, admin_user)
            flash(f'Marked {len(conversation_ids)} conversations as read', 'success')
            
        elif action == 'close':
            ChatConversation.query.filter(ChatConversation.id.in_(conversation_ids)).update(
                {'status': 'closed', 'updated_at': datetime.utcnow()}, synchronize_session=False
            )
            db.session.commit()
            flash(f'Closed {len(conversation_ids)} conversations', 'success')
            
        elif action == 'archive':
            ChatConversation.query.filter(ChatConversation.id.in_(conversation_ids)).update(
                {'status': 'archived', 'updated_at': datetime.utcnow()}, synchronize_session=False
            )
            db.session.commit()
            flash(f'Archived {len(conversation_ids)} conversations', 'success')
        elif action == 'delete':
            conversations = ChatConversation.query.filter(ChatConversation.id.in_(conversation_ids)).all()
            for conv in conversations:
                db.session.delete(conv)
            db.session.commit()
            flash(f'Deleted {len(conversations)} conversations', 'success')

        else:
            flash('Invalid action', 'error')
        
        return redirect(url_for('admin_chat_conversations'))
        
    except Exception as e:
        logging.error(f"Error in bulk action: {str(e)}")
        flash('Error performing bulk action', 'error')
        return redirect(url_for('admin_chat_conversations'))

@app.route('/admin/chat-conversations/api/unread-count')
@admin_required_chat
def admin_chat_unread_count():
    """API endpoint to get count of unread messages"""
    try:
        unread_count = db.session.query(func.count(ChatMessage.id)).filter(
            ChatMessage.is_from_admin == False,
            ChatMessage.is_read == False
        ).scalar()
        
        return jsonify({'unread_count': unread_count})
        
    except Exception as e:
        logging.error(f"Error getting unread count: {str(e)}")
        return jsonify({'error': 'Failed to get unread count'}), 500

@app.route('/admin/chat-conversations/search')
@admin_required_chat
def admin_chat_search():
    """Search conversations by user name, email, or message content"""
    try:
        search_query = request.args.get('q', '').strip()
        
        if not search_query:
            return redirect(url_for('admin_chat_conversations'))
        
        # Search in conversations and messages
        conversations = ChatConversation.query.filter(
            db.or_(
                ChatConversation.user_name.ilike(f'%{search_query}%'),
                ChatConversation.user_email.ilike(f'%{search_query}%'),
                ChatConversation.admin_notes.ilike(f'%{search_query}%')
            )
        ).order_by(desc(ChatConversation.updated_at)).limit(50).all()
        
        # Also search in message content
        message_conversations = db.session.query(ChatConversation).join(ChatMessage).filter(
            ChatMessage.message_text.ilike(f'%{search_query}%')
        ).distinct().order_by(desc(ChatConversation.updated_at)).limit(20).all()
        
        # Combine and deduplicate results
        all_conversations = {conv.id: conv for conv in conversations + message_conversations}
        results = list(all_conversations.values())
        
        return render_template('admin_chat_search_results.html', 
                             conversations=results, 
                             search_query=search_query)
        
    except Exception as e:
        logging.error(f"Error in chat search: {str(e)}")
        flash('Error performing search', 'error')
        return redirect(url_for('admin_chat_conversations'))
    
    
    


@app.route('/admin/chat-conversation/<int:conversation_id>/delete', methods=['POST'])
@admin_required_chat
def admin_chat_delete_conversation(conversation_id):
    """Delete a single chat conversation"""
    try:
        conversation = ChatConversation.query.get_or_404(conversation_id)
        db.session.delete(conversation)
        db.session.commit()
        flash(f'Conversation #{conversation_id} deleted successfully.', 'success')
    except Exception as e:
        logging.error(f"Error deleting conversation {conversation_id}: {str(e)}")
        flash('Error deleting conversation', 'error')
    return redirect(url_for('admin_chat_conversations'))
