"""
Agent Admin API - Exposes admin panel functionality as API endpoints
for external agents (e.g. Telegram bot "Roger That") to access.

All endpoints require Bearer token authentication via the AGENT_API_KEY
environment variable or .ai_config setting.
"""

import os
import logging
from functools import wraps
from datetime import datetime

from flask import request, jsonify
from sqlalchemy import func, desc

from app import app, db
from models import (
    ServiceProvider, ServiceProviderReport, City, Category,
    Advertisement, InteractionLog, InteractionAttachment,
    EmailLog, CommunicationLog, AppDownloadTracking, NotificationChange,
)
from chat_models import ChatConversation, ChatMessage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def _get_agent_api_key() -> str:
    key = os.environ.get("AGENT_API_KEY", "")
    if key:
        return key
    try:
        config_path = os.path.join(os.path.dirname(__file__), ".ai_config")
        if os.path.exists(config_path):
            with open(config_path) as fh:
                for line in fh:
                    if line.startswith("AGENT_API_KEY="):
                        return line.strip().split("=", 1)[1]
    except Exception:
        pass
    return ""


def agent_api_auth(f):
    """Require valid Bearer token matching AGENT_API_KEY."""
    @wraps(f)
    def decorated(*args, **kwargs):
        expected = _get_agent_api_key()
        if not expected:
            return jsonify({"error": "Agent API key not configured on the server. Set AGENT_API_KEY env var."}), 503

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed Authorization header. Use: Bearer <token>"}), 401

        token = auth_header[7:]
        if token != expected:
            return jsonify({"error": "Invalid API key"}), 403

        return f(*args, **kwargs)
    return decorated

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _provider_to_dict(p: ServiceProvider) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "phone": p.phone,
        "email": p.email,
        "website": p.website,
        "business_address": p.business_address,
        "city": p.city,
        "sub_city": p.sub_city,
        "province": p.province,
        "postal_code": p.postal_code,
        "service_category": p.service_category,
        "star_rating": p.star_rating,
        "review_count": p.review_count,
        "description": p.description,
        "specialties": p.specialties,
        "years_experience": p.years_experience,
        "license_number": p.license_number,
        "insurance_verified": p.insurance_verified,
        "background_checked": p.background_checked,
        "status": p.status,
        "google_place_id": p.google_place_id,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def _city_to_dict(c: City) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "country": c.country,
        "flag_emoji": c.flag_emoji,
        "status": c.status,
        "provider_count": c.provider_count,
        "category_count": c.category_count,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _category_to_dict(cat: Category) -> dict:
    return {
        "id": cat.id,
        "name": cat.name,
        "description": cat.description,
        "icon": cat.icon,
        "status": cat.status,
        "city_name": cat.city_name,
        "created_at": cat.created_at.isoformat() if cat.created_at else None,
    }


def _ad_to_dict(ad: Advertisement) -> dict:
    return {
        "id": ad.id,
        "title": ad.title,
        "description": ad.description,
        "image_url": ad.image_url,
        "phone_number": ad.phone_number,
        "email": ad.email,
        "website": ad.website,
        "city_name": ad.city_name,
        "category_name": ad.category_name,
        "position": ad.position,
        "star_rating": ad.star_rating,
        "review_count": ad.review_count,
        "review_text": ad.review_text,
        "status": ad.status,
        "created_at": ad.created_at.isoformat() if ad.created_at else None,
        "updated_at": ad.updated_at.isoformat() if ad.updated_at else None,
    }


def _interaction_to_dict(log: InteractionLog) -> dict:
    return {
        "id": log.id,
        "title": log.title,
        "description": log.description,
        "author_name": log.author_name,
        "client_address": log.client_address,
        "service_needed": log.service_needed,
        "client_phone": log.client_phone,
        "client_email": log.client_email,
        "service_city": log.service_city,
        "referral_source": log.referral_source,
        "status": log.status,
        "status_note": log.status_note,
        "occurred_at": log.occurred_at.isoformat() if log.occurred_at else None,
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "attachment_count": len(log.attachments) if log.attachments else 0,
    }


def _conversation_to_dict(conv: ChatConversation) -> dict:
    return {
        "id": conv.id,
        "user_name": conv.user_name,
        "user_email": conv.user_email,
        "phone_number": conv.phone_number,
        "status": conv.status,
        "priority": conv.priority,
        "admin_notes": conv.admin_notes,
        "message_count": conv.message_count,
        "unread_user_messages": conv.unread_user_messages,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
        "last_admin_reply": conv.last_admin_reply.isoformat() if conv.last_admin_reply else None,
    }


def _message_to_dict(msg: ChatMessage) -> dict:
    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "message_text": msg.message_text,
        "is_from_admin": msg.is_from_admin,
        "admin_user": msg.admin_user,
        "is_read": msg.is_read,
        "delivery_method": msg.delivery_method,
        "delivery_status": msg.delivery_status,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


def _email_log_to_dict(el: EmailLog) -> dict:
    return {
        "id": el.id,
        "subject": el.subject,
        "body": el.body,
        "recipients": el.recipients,
        "attachments": el.attachments,
        "status": el.status,
        "error": el.error,
        "created_at": el.created_at.isoformat() if el.created_at else None,
    }

# ===================================================================
# PROVIDER ENDPOINTS
# ===================================================================

@app.route("/agent-api/providers", methods=["GET"])
@agent_api_auth
def agent_list_providers():
    """List providers with optional filters: city, category, status, search, limit, offset."""
    city = request.args.get("city")
    category = request.args.get("category")
    status = request.args.get("status", "active")
    search = request.args.get("search")
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    q = ServiceProvider.query
    if city:
        q = q.filter(func.lower(ServiceProvider.city) == city.lower())
    if category:
        q = q.filter(ServiceProvider.service_category.ilike(f"%{category}%"))
    if status and status != "all":
        q = q.filter_by(status=status)
    if search:
        q = q.filter(
            db.or_(
                ServiceProvider.name.ilike(f"%{search}%"),
                ServiceProvider.phone.ilike(f"%{search}%"),
                ServiceProvider.email.ilike(f"%{search}%"),
                ServiceProvider.description.ilike(f"%{search}%"),
            )
        )

    total = q.count()
    providers = q.order_by(
        ServiceProvider.star_rating.desc(), ServiceProvider.review_count.desc()
    ).offset(offset).limit(limit).all()

    return jsonify({"total": total, "providers": [_provider_to_dict(p) for p in providers]})


@app.route("/agent-api/providers/<int:provider_id>", methods=["GET"])
@agent_api_auth
def agent_get_provider(provider_id):
    """Get a single provider by ID."""
    p = ServiceProvider.query.get(provider_id)
    if not p:
        return jsonify({"error": "Provider not found"}), 404
    return jsonify(_provider_to_dict(p))


@app.route("/agent-api/providers", methods=["POST"])
@agent_api_auth
def agent_create_provider():
    """Create a new service provider."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    required = ["name", "phone", "business_address", "city", "province", "service_category"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    provider = ServiceProvider(
        name=data["name"],
        phone=data["phone"],
        email=data.get("email"),
        website=data.get("website"),
        business_address=data["business_address"],
        city=data["city"],
        sub_city=data.get("sub_city"),
        province=data["province"],
        postal_code=data.get("postal_code"),
        service_category=data["service_category"],
        star_rating=data.get("star_rating", 4.5),
        review_count=data.get("review_count", 0),
        description=data.get("description"),
        specialties=data.get("specialties"),
        years_experience=data.get("years_experience"),
        license_number=data.get("license_number"),
        insurance_verified=data.get("insurance_verified", True),
        background_checked=data.get("background_checked", True),
        status=data.get("status", "active"),
    )
    db.session.add(provider)
    db.session.commit()
    return jsonify({"message": "Provider created", "provider": _provider_to_dict(provider)}), 201


@app.route("/agent-api/providers/<int:provider_id>", methods=["PUT"])
@agent_api_auth
def agent_update_provider(provider_id):
    """Update an existing provider."""
    p = ServiceProvider.query.get(provider_id)
    if not p:
        return jsonify({"error": "Provider not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    updatable = [
        "name", "phone", "email", "website", "business_address", "city",
        "sub_city", "province", "postal_code", "service_category",
        "star_rating", "review_count", "description", "specialties",
        "years_experience", "license_number", "insurance_verified",
        "background_checked", "status",
    ]
    for field in updatable:
        if field in data:
            setattr(p, field, data[field])

    db.session.commit()
    return jsonify({"message": "Provider updated", "provider": _provider_to_dict(p)})


@app.route("/agent-api/providers/<int:provider_id>", methods=["DELETE"])
@agent_api_auth
def agent_delete_provider(provider_id):
    """Delete a provider."""
    p = ServiceProvider.query.get(provider_id)
    if not p:
        return jsonify({"error": "Provider not found"}), 404
    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": f"Provider '{p.name}' deleted"})

# ===================================================================
# CITY ENDPOINTS
# ===================================================================

@app.route("/agent-api/cities", methods=["GET"])
@agent_api_auth
def agent_list_cities():
    """List all cities with optional status filter."""
    status = request.args.get("status")
    q = City.query
    if status:
        q = q.filter_by(status=status)
    cities = q.order_by(City.name).all()
    return jsonify({"cities": [_city_to_dict(c) for c in cities]})


@app.route("/agent-api/cities", methods=["POST"])
@agent_api_auth
def agent_create_city():
    """Create a new city."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    required = ["name", "country", "flag_emoji"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if City.query.filter_by(name=data["name"]).first():
        return jsonify({"error": f"City '{data['name']}' already exists"}), 409

    city = City(
        name=data["name"],
        country=data["country"],
        flag_emoji=data["flag_emoji"],
        status=data.get("status", "active"),
    )
    db.session.add(city)
    db.session.commit()
    return jsonify({"message": "City created", "city": _city_to_dict(city)}), 201


@app.route("/agent-api/cities/<int:city_id>", methods=["PUT"])
@agent_api_auth
def agent_update_city(city_id):
    """Update a city."""
    c = City.query.get(city_id)
    if not c:
        return jsonify({"error": "City not found"}), 404
    data = request.get_json(silent=True) or {}
    for field in ("name", "country", "flag_emoji", "status"):
        if field in data:
            setattr(c, field, data[field])
    db.session.commit()
    return jsonify({"message": "City updated", "city": _city_to_dict(c)})


@app.route("/agent-api/cities/<int:city_id>", methods=["DELETE"])
@agent_api_auth
def agent_delete_city(city_id):
    """Delete a city."""
    c = City.query.get(city_id)
    if not c:
        return jsonify({"error": "City not found"}), 404
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": f"City '{c.name}' deleted"})

# ===================================================================
# CATEGORY ENDPOINTS
# ===================================================================

@app.route("/agent-api/categories", methods=["GET"])
@agent_api_auth
def agent_list_categories():
    """List categories, optionally filtered by city_name or status."""
    city_name = request.args.get("city_name")
    status = request.args.get("status")
    q = Category.query
    if city_name:
        q = q.filter_by(city_name=city_name)
    if status:
        q = q.filter_by(status=status)
    cats = q.order_by(Category.name).all()
    return jsonify({"categories": [_category_to_dict(c) for c in cats]})


@app.route("/agent-api/categories", methods=["POST"])
@agent_api_auth
def agent_create_category():
    """Create a new category."""
    data = request.get_json(silent=True) or {}
    required = ["name", "city_name"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    cat = Category(
        name=data["name"],
        description=data.get("description"),
        icon=data.get("icon", "fas fa-tools"),
        status=data.get("status", "active"),
        city_name=data["city_name"],
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify({"message": "Category created", "category": _category_to_dict(cat)}), 201


@app.route("/agent-api/categories/<int:cat_id>", methods=["PUT"])
@agent_api_auth
def agent_update_category(cat_id):
    """Update a category."""
    cat = Category.query.get(cat_id)
    if not cat:
        return jsonify({"error": "Category not found"}), 404
    data = request.get_json(silent=True) or {}
    for field in ("name", "description", "icon", "status", "city_name"):
        if field in data:
            setattr(cat, field, data[field])
    db.session.commit()
    return jsonify({"message": "Category updated", "category": _category_to_dict(cat)})


@app.route("/agent-api/categories/<int:cat_id>", methods=["DELETE"])
@agent_api_auth
def agent_delete_category(cat_id):
    """Delete a category."""
    cat = Category.query.get(cat_id)
    if not cat:
        return jsonify({"error": "Category not found"}), 404
    db.session.delete(cat)
    db.session.commit()
    return jsonify({"message": f"Category '{cat.name}' deleted"})

# ===================================================================
# ADVERTISEMENT ENDPOINTS
# ===================================================================

@app.route("/agent-api/advertisements", methods=["GET"])
@agent_api_auth
def agent_list_advertisements():
    """List advertisements with optional filters."""
    city = request.args.get("city_name")
    category = request.args.get("category_name")
    status = request.args.get("status")
    q = Advertisement.query
    if city:
        q = q.filter_by(city_name=city)
    if category:
        q = q.filter_by(category_name=category)
    if status:
        q = q.filter_by(status=status)
    ads = q.order_by(desc(Advertisement.created_at)).all()
    return jsonify({"advertisements": [_ad_to_dict(a) for a in ads]})


@app.route("/agent-api/advertisements/<int:ad_id>", methods=["GET"])
@agent_api_auth
def agent_get_advertisement(ad_id):
    """Get a single advertisement."""
    ad = Advertisement.query.get(ad_id)
    if not ad:
        return jsonify({"error": "Advertisement not found"}), 404
    return jsonify(_ad_to_dict(ad))


@app.route("/agent-api/advertisements", methods=["POST"])
@agent_api_auth
def agent_create_advertisement():
    """Create a new advertisement."""
    data = request.get_json(silent=True) or {}
    required = ["title", "image_url", "phone_number", "city_name", "category_name"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    ad = Advertisement(
        title=data["title"],
        description=data.get("description"),
        image_url=data["image_url"],
        phone_number=data["phone_number"],
        email=data.get("email"),
        website=data.get("website"),
        city_name=data["city_name"],
        category_name=data["category_name"],
        position=data.get("position", 3),
        star_rating=data.get("star_rating"),
        review_count=data.get("review_count", 0),
        review_text=data.get("review_text"),
        status=data.get("status", "active"),
    )
    db.session.add(ad)
    db.session.commit()
    return jsonify({"message": "Advertisement created", "advertisement": _ad_to_dict(ad)}), 201


@app.route("/agent-api/advertisements/<int:ad_id>", methods=["PUT"])
@agent_api_auth
def agent_update_advertisement(ad_id):
    """Update an advertisement."""
    ad = Advertisement.query.get(ad_id)
    if not ad:
        return jsonify({"error": "Advertisement not found"}), 404
    data = request.get_json(silent=True) or {}
    updatable = [
        "title", "description", "image_url", "phone_number", "email",
        "website", "city_name", "category_name", "position",
        "star_rating", "review_count", "review_text", "status",
    ]
    for field in updatable:
        if field in data:
            setattr(ad, field, data[field])
    db.session.commit()
    return jsonify({"message": "Advertisement updated", "advertisement": _ad_to_dict(ad)})


@app.route("/agent-api/advertisements/<int:ad_id>", methods=["DELETE"])
@agent_api_auth
def agent_delete_advertisement(ad_id):
    """Delete an advertisement."""
    ad = Advertisement.query.get(ad_id)
    if not ad:
        return jsonify({"error": "Advertisement not found"}), 404
    db.session.delete(ad)
    db.session.commit()
    return jsonify({"message": f"Advertisement '{ad.title}' deleted"})

# ===================================================================
# INTERACTION LOG ENDPOINTS
# ===================================================================

@app.route("/agent-api/interactions", methods=["GET"])
@agent_api_auth
def agent_list_interactions():
    """List interaction logs with optional filters."""
    status = request.args.get("status")
    city = request.args.get("city")
    search = request.args.get("search")
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    q = InteractionLog.query
    if status:
        q = q.filter_by(status=status)
    if city:
        q = q.filter(InteractionLog.service_city.ilike(f"%{city}%"))
    if search:
        q = q.filter(
            db.or_(
                InteractionLog.title.ilike(f"%{search}%"),
                InteractionLog.description.ilike(f"%{search}%"),
                InteractionLog.client_phone.ilike(f"%{search}%"),
                InteractionLog.client_email.ilike(f"%{search}%"),
            )
        )

    total = q.count()
    logs = q.order_by(desc(InteractionLog.created_at)).offset(offset).limit(limit).all()
    return jsonify({"total": total, "interactions": [_interaction_to_dict(l) for l in logs]})


@app.route("/agent-api/interactions/<int:log_id>", methods=["GET"])
@agent_api_auth
def agent_get_interaction(log_id):
    """Get a single interaction log."""
    log = InteractionLog.query.get(log_id)
    if not log:
        return jsonify({"error": "Interaction not found"}), 404
    data = _interaction_to_dict(log)
    data["attachments"] = [
        {"id": a.id, "file_path": a.file_path, "original_filename": a.original_filename}
        for a in log.attachments
    ]
    return jsonify(data)


@app.route("/agent-api/interactions", methods=["POST"])
@agent_api_auth
def agent_create_interaction():
    """Create a new interaction log."""
    data = request.get_json(silent=True) or {}
    if not data.get("title"):
        return jsonify({"error": "title is required"}), 400

    log = InteractionLog(
        title=data["title"],
        description=data.get("description"),
        author_name=data.get("author_name"),
        client_address=data.get("client_address"),
        service_needed=data.get("service_needed"),
        client_phone=data.get("client_phone"),
        client_email=data.get("client_email"),
        service_city=data.get("service_city"),
        referral_source=data.get("referral_source"),
        status=data.get("status", "incomplete"),
        status_note=data.get("status_note"),
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"message": "Interaction created", "interaction": _interaction_to_dict(log)}), 201


@app.route("/agent-api/interactions/<int:log_id>", methods=["PUT"])
@agent_api_auth
def agent_update_interaction(log_id):
    """Update an interaction log."""
    log = InteractionLog.query.get(log_id)
    if not log:
        return jsonify({"error": "Interaction not found"}), 404
    data = request.get_json(silent=True) or {}
    updatable = [
        "title", "description", "author_name", "client_address",
        "service_needed", "client_phone", "client_email",
        "service_city", "referral_source", "status", "status_note",
    ]
    for field in updatable:
        if field in data:
            setattr(log, field, data[field])
    db.session.commit()
    return jsonify({"message": "Interaction updated", "interaction": _interaction_to_dict(log)})


@app.route("/agent-api/interactions/<int:log_id>", methods=["DELETE"])
@agent_api_auth
def agent_delete_interaction(log_id):
    """Delete an interaction log."""
    log = InteractionLog.query.get(log_id)
    if not log:
        return jsonify({"error": "Interaction not found"}), 404
    db.session.delete(log)
    db.session.commit()
    return jsonify({"message": f"Interaction '{log.title}' deleted"})

# ===================================================================
# CHAT CONVERSATION ENDPOINTS
# ===================================================================

@app.route("/agent-api/chat/conversations", methods=["GET"])
@agent_api_auth
def agent_list_conversations():
    """List chat conversations with filters."""
    status = request.args.get("status")
    priority = request.args.get("priority")
    search = request.args.get("search")
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    q = ChatConversation.query
    if status:
        q = q.filter_by(status=status)
    if priority:
        q = q.filter_by(priority=priority)
    if search:
        q = q.filter(
            db.or_(
                ChatConversation.user_name.ilike(f"%{search}%"),
                ChatConversation.user_email.ilike(f"%{search}%"),
                ChatConversation.phone_number.ilike(f"%{search}%"),
            )
        )

    total = q.count()
    conversations = q.order_by(desc(ChatConversation.updated_at)).offset(offset).limit(limit).all()

    stats = {
        "total_all": ChatConversation.query.count(),
        "open": ChatConversation.query.filter_by(status="open").count(),
        "closed": ChatConversation.query.filter_by(status="closed").count(),
        "unread_messages": db.session.query(func.count(ChatMessage.id)).filter(
            ChatMessage.is_from_admin == False,
            ChatMessage.is_read == False,
        ).scalar(),
    }

    return jsonify({
        "total": total,
        "stats": stats,
        "conversations": [_conversation_to_dict(c) for c in conversations],
    })


@app.route("/agent-api/chat/conversations/<int:conv_id>", methods=["GET"])
@agent_api_auth
def agent_get_conversation(conv_id):
    """Get a conversation with all its messages."""
    conv = ChatConversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404

    data = _conversation_to_dict(conv)
    data["messages"] = [_message_to_dict(m) for m in conv.messages]
    return jsonify(data)


@app.route("/agent-api/chat/conversations/<int:conv_id>/reply", methods=["POST"])
@agent_api_auth
def agent_reply_conversation(conv_id):
    """Send an admin reply to a conversation."""
    conv = ChatConversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404

    data = request.get_json(silent=True) or {}
    message_text = data.get("message", "").strip()
    admin_user = data.get("admin_user", "agent-bot")

    if not message_text:
        return jsonify({"error": "message is required"}), 400

    msg = ChatMessage(
        conversation_id=conv_id,
        message_text=message_text,
        is_from_admin=True,
        admin_user=admin_user,
        is_read=True,
        delivery_method="agent_api",
        delivery_status="sent",
    )
    db.session.add(msg)
    conv.updated_at = datetime.utcnow()
    conv.last_admin_reply = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Reply sent", "chat_message": _message_to_dict(msg)}), 201


@app.route("/agent-api/chat/conversations/<int:conv_id>/status", methods=["PUT"])
@agent_api_auth
def agent_update_conversation_status(conv_id):
    """Update conversation status, priority, or notes."""
    conv = ChatConversation.query.get(conv_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404

    data = request.get_json(silent=True) or {}
    if "status" in data:
        conv.status = data["status"]
    if "priority" in data:
        conv.priority = data["priority"]
    if "admin_notes" in data:
        conv.admin_notes = data["admin_notes"]

    conv.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Conversation updated", "conversation": _conversation_to_dict(conv)})

# ===================================================================
# ANALYTICS / DASHBOARD ENDPOINTS
# ===================================================================

@app.route("/agent-api/analytics/dashboard", methods=["GET"])
@agent_api_auth
def agent_analytics_dashboard():
    """Get dashboard analytics summary."""
    total_providers = ServiceProvider.query.filter_by(status="active").count()
    total_cities = City.query.filter_by(status="active").count()
    total_categories = Category.query.filter_by(status="active").count()
    total_ads = Advertisement.query.filter_by(status="active").count()
    total_interactions = InteractionLog.query.count()
    incomplete_interactions = InteractionLog.query.filter_by(status="incomplete").count()
    total_conversations = ChatConversation.query.count()
    open_conversations = ChatConversation.query.filter_by(status="open").count()
    unread_messages = db.session.query(func.count(ChatMessage.id)).filter(
        ChatMessage.is_from_admin == False, ChatMessage.is_read == False
    ).scalar()
    total_reports = ServiceProviderReport.query.count()
    pending_reports = ServiceProviderReport.query.filter_by(status="pending").count()
    total_email_logs = EmailLog.query.count()

    providers_by_city = {}
    city_counts = db.session.query(
        ServiceProvider.city, func.count(ServiceProvider.id)
    ).filter_by(status="active").group_by(ServiceProvider.city).all()
    for city_name, count in city_counts:
        providers_by_city[city_name] = count

    return jsonify({
        "providers": {"active": total_providers, "by_city": providers_by_city},
        "cities": {"active": total_cities},
        "categories": {"active": total_categories},
        "advertisements": {"active": total_ads},
        "interactions": {"total": total_interactions, "incomplete": incomplete_interactions},
        "chat": {
            "total_conversations": total_conversations,
            "open_conversations": open_conversations,
            "unread_messages": unread_messages,
        },
        "reports": {"total": total_reports, "pending": pending_reports},
        "emails": {"total_sent": total_email_logs},
    })

# ===================================================================
# EMAIL LOG ENDPOINTS
# ===================================================================

@app.route("/agent-api/email-logs", methods=["GET"])
@agent_api_auth
def agent_list_email_logs():
    """List email logs."""
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    total = EmailLog.query.count()
    logs = EmailLog.query.order_by(desc(EmailLog.created_at)).offset(offset).limit(limit).all()
    return jsonify({"total": total, "email_logs": [_email_log_to_dict(el) for el in logs]})

# ===================================================================
# REPORTS ENDPOINTS
# ===================================================================

@app.route("/agent-api/reports", methods=["GET"])
@agent_api_auth
def agent_list_reports():
    """List service provider reports with optional filters."""
    status = request.args.get("status")
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    q = ServiceProviderReport.query
    if status:
        q = q.filter_by(status=status)

    total = q.count()
    reports = q.order_by(desc(ServiceProviderReport.timestamp)).offset(offset).limit(limit).all()

    return jsonify({
        "total": total,
        "reports": [
            {
                "id": r.id,
                "provider_name": r.provider_name,
                "provider_phone": r.provider_phone,
                "report_reason": r.report_reason,
                "other_reason": r.other_reason,
                "status": r.status,
                "user_email": r.user_email,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "is_hidden": r.is_hidden,
            }
            for r in reports
        ],
    })


@app.route("/agent-api/reports/<int:report_id>/status", methods=["PUT"])
@agent_api_auth
def agent_update_report_status(report_id):
    """Update a report's status."""
    report = ServiceProviderReport.query.get(report_id)
    if not report:
        return jsonify({"error": "Report not found"}), 404
    data = request.get_json(silent=True) or {}
    if "status" in data:
        report.status = data["status"]
    if "is_hidden" in data:
        report.is_hidden = data["is_hidden"]
    db.session.commit()
    return jsonify({"message": "Report updated"})

# ===================================================================
# WAITING LIST ENDPOINT
# ===================================================================

@app.route("/agent-api/waiting-list", methods=["GET"])
@agent_api_auth
def agent_list_waiting_list():
    """List waiting list entries (service provider applications)."""
    status = request.args.get("status")
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    q = ServiceProviderReport.query.filter_by(report_reason="service_provider_application")
    if status:
        q = q.filter_by(status=status)

    total = q.count()
    entries = q.order_by(desc(ServiceProviderReport.timestamp)).offset(offset).limit(limit).all()

    results = []
    for e in entries:
        entry_data = {
            "id": e.id,
            "provider_name": e.provider_name,
            "provider_phone": e.provider_phone,
            "business_address": e.business_address,
            "service": e.service,
            "city": e.city,
            "province": e.province,
            "status": e.status,
            "user_email": e.user_email,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        }
        results.append(entry_data)

    return jsonify({"total": total, "waiting_list": results})

# ===================================================================
# TOOL DEFINITIONS (for external agent consumption)
# ===================================================================

@app.route("/agent-api/tools", methods=["GET"])
@agent_api_auth
def agent_tool_definitions():
    """Return tool/function definitions that external agents can use
    to understand what admin panel capabilities are available."""
    tools = [
        {
            "name": "list_providers",
            "description": "List service providers in the ConnectYou admin panel. Supports filtering by city, category, status, and search terms.",
            "endpoint": "GET /agent-api/providers",
            "parameters": {
                "city": "Filter by city name",
                "category": "Filter by service category",
                "status": "Filter by status (active/inactive/suspended/all)",
                "search": "Search by name, phone, email, or description",
                "limit": "Max results (default 50)",
                "offset": "Pagination offset",
            },
        },
        {
            "name": "get_provider",
            "description": "Get detailed information about a specific service provider by ID.",
            "endpoint": "GET /agent-api/providers/<id>",
            "parameters": {"id": "Provider ID (path parameter)"},
        },
        {
            "name": "create_provider",
            "description": "Add a new service provider to ConnectYou.",
            "endpoint": "POST /agent-api/providers",
            "required_fields": ["name", "phone", "business_address", "city", "province", "service_category"],
        },
        {
            "name": "update_provider",
            "description": "Update an existing service provider's information.",
            "endpoint": "PUT /agent-api/providers/<id>",
        },
        {
            "name": "delete_provider",
            "description": "Remove a service provider from ConnectYou.",
            "endpoint": "DELETE /agent-api/providers/<id>",
        },
        {
            "name": "list_cities",
            "description": "List all cities in the ConnectYou platform.",
            "endpoint": "GET /agent-api/cities",
            "parameters": {"status": "Filter by status (active/inactive)"},
        },
        {
            "name": "create_city",
            "description": "Add a new city to ConnectYou.",
            "endpoint": "POST /agent-api/cities",
            "required_fields": ["name", "country", "flag_emoji"],
        },
        {
            "name": "list_categories",
            "description": "List service categories, optionally filtered by city.",
            "endpoint": "GET /agent-api/categories",
            "parameters": {"city_name": "Filter by city", "status": "Filter by status"},
        },
        {
            "name": "create_category",
            "description": "Add a new service category.",
            "endpoint": "POST /agent-api/categories",
            "required_fields": ["name", "city_name"],
        },
        {
            "name": "list_advertisements",
            "description": "List all advertisements on ConnectYou.",
            "endpoint": "GET /agent-api/advertisements",
            "parameters": {"city_name": "Filter by city", "category_name": "Filter by category", "status": "Filter by status"},
        },
        {
            "name": "create_advertisement",
            "description": "Create a new advertisement.",
            "endpoint": "POST /agent-api/advertisements",
            "required_fields": ["title", "image_url", "phone_number", "city_name", "category_name"],
        },
        {
            "name": "list_interactions",
            "description": "List customer interaction logs from the admin panel.",
            "endpoint": "GET /agent-api/interactions",
            "parameters": {"status": "Filter by status", "city": "Filter by city", "search": "Search term"},
        },
        {
            "name": "create_interaction",
            "description": "Log a new customer interaction.",
            "endpoint": "POST /agent-api/interactions",
            "required_fields": ["title"],
        },
        {
            "name": "list_conversations",
            "description": "List chat conversations from the admin panel.",
            "endpoint": "GET /agent-api/chat/conversations",
            "parameters": {"status": "Filter (open/closed/archived)", "priority": "Filter by priority", "search": "Search term"},
        },
        {
            "name": "get_conversation",
            "description": "Get a conversation and all its messages.",
            "endpoint": "GET /agent-api/chat/conversations/<id>",
        },
        {
            "name": "reply_to_conversation",
            "description": "Send an admin reply to a chat conversation.",
            "endpoint": "POST /agent-api/chat/conversations/<id>/reply",
            "required_fields": ["message"],
        },
        {
            "name": "update_conversation_status",
            "description": "Update a conversation's status, priority, or admin notes.",
            "endpoint": "PUT /agent-api/chat/conversations/<id>/status",
        },
        {
            "name": "get_dashboard_analytics",
            "description": "Get a summary of all admin panel analytics: providers, cities, categories, ads, interactions, chat stats, reports, emails.",
            "endpoint": "GET /agent-api/analytics/dashboard",
        },
        {
            "name": "list_email_logs",
            "description": "List sent email logs from the admin panel.",
            "endpoint": "GET /agent-api/email-logs",
        },
        {
            "name": "list_reports",
            "description": "List service provider reports/feedback from users.",
            "endpoint": "GET /agent-api/reports",
            "parameters": {"status": "Filter (pending/reviewed/resolved)"},
        },
        {
            "name": "update_report_status",
            "description": "Update a report's status or hide it.",
            "endpoint": "PUT /agent-api/reports/<id>/status",
        },
        {
            "name": "list_waiting_list",
            "description": "List service provider applications on the waiting list.",
            "endpoint": "GET /agent-api/waiting-list",
            "parameters": {"status": "Filter (pending/approved/rejected)"},
        },
    ]
    return jsonify({"tools": tools, "auth": "Bearer token via Authorization header"})
