"""
Chat conversation models for logging and management
"""
from datetime import datetime
from app import db


class ChatIcon(db.Model):
    __tablename__ = 'chat_icons'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))  # NEW FIELD
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'image_url': self.image_url,
            'description': self.description,  # NEW FIELD
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }



class ChatConversation(db.Model):
    """Model for storing chat conversations"""
    __tablename__ = 'chat_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(120), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    user_ip = db.Column(db.String(45), nullable=True)
    status = db.Column(db.String(20), default='open')  # open, closed, archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_admin_reply = db.Column(db.DateTime, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(10), default='normal')  # low, normal, high, urgent

    # 🔗 Avatar (chat icon) relationship
    chat_icon_id = db.Column(
    db.Integer,
    db.ForeignKey('chat_icons.id', name='fk_chat_conversations_chat_icon_id'),
    nullable=True
)

    chat_icon = db.relationship('ChatIcon', backref='conversations', lazy=True)

    # 🔗 Related messages
    messages = db.relationship('ChatMessage', backref='conversation', lazy=True, 
                               cascade='all, delete-orphan', order_by='ChatMessage.created_at')
    
    def __repr__(self):
        return f'<ChatConversation {self.id}: {self.user_name}>'
    
    @property
    def message_count(self):
        return len(self.messages)
    
    @property
    def unread_user_messages(self):
        return ChatMessage.query.filter_by(
            conversation_id=self.id,
            is_from_admin=False,
            is_read=False
        ).count()
    
    @property
    def last_message(self):
        return self.messages[-1] if self.messages else None
    
    @property
    def formatted_status(self):
        status_colors = {
            'open': 'success',
            'closed': 'secondary', 
            'archived': 'dark'
        }
        return {
            'text': self.status.title(),
            'color': status_colors.get(self.status, 'secondary')
        }


class ChatMessage(db.Model):
    """Model for individual chat messages"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversations.id'), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    is_from_admin = db.Column(db.Boolean, default=False)
    admin_user = db.Column(db.String(50), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    delivery_method = db.Column(db.String(10), default='sms')  # sms, email
    delivery_status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    delivery_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ChatMessage {self.id}: {"Admin" if self.is_from_admin else "User"}>'
    
    @property
    def formatted_time(self):
        return self.created_at.strftime('%Y-%m-%d %H:%M:%S')
    
    @property
    def sender_type(self):
        return "Admin" if self.is_from_admin else "User"
    
    @property
    def message_preview(self):
        return self.message_text[:100] + "..." if len(self.message_text) > 100 else self.message_text
