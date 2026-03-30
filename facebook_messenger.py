"""
Facebook Messenger webhook handler for ConnectYou.
Automatically responds to Marketplace inquiries with relevant provider recommendations.
"""

import os
import re
import hmac
import hashlib
import logging
import json
from flask import Blueprint, request, jsonify
import requests as http_requests

logger = logging.getLogger(__name__)

messenger_bp = Blueprint('messenger', __name__)

PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
APP_SECRET = os.environ.get("FB_APP_SECRET", "")
VERIFY_TOKEN = os.environ.get("FB_VERIFY_TOKEN", "connectyou_verify_2026")

GRAPH_API = "https://graph.facebook.com/v19.0"

CATEGORY_KEYWORDS = {
    "plumber": ["plumber", "plumbing", "pipe", "leak", "drain", "faucet", "toilet", "water heater", "sewer"],
    "electrician": ["electrician", "electrical", "wiring", "outlet", "breaker", "panel", "light", "circuit"],
    "hvac": ["hvac", "heating", "cooling", "furnace", "air conditioning", "ac", "a/c", "heat pump", "duct"],
    "painter": ["painter", "painting", "paint", "stain", "drywall", "wall"],
    "roofer": ["roofer", "roofing", "roof", "shingle", "gutter", "eaves"],
    "cleaner": ["cleaner", "cleaning", "housekeeping", "maid", "janitorial", "deep clean", "house cleaning"],
    "pest control": ["pest", "exterminator", "bug", "rodent", "mouse", "rat", "ant", "cockroach", "bed bug"],
    "mover": ["mover", "moving", "relocation", "relocate", "move"],
    "handyman": ["handyman", "handy man", "general repair", "fix", "repair", "odd job"],
    "appliance repair": ["appliance", "washer", "dryer", "dishwasher", "fridge", "refrigerator", "oven", "stove"],
    "carpenter": ["carpenter", "carpentry", "cabinet", "woodwork", "deck", "fence"],
    "chimney": ["chimney", "fireplace", "chimney sweep"],
    "fence": ["fence", "fencing", "gate"],
    "garage door": ["garage door", "garage"],
    "glass": ["glass", "window repair", "mirror"],
    "insulation": ["insulation", "insulate", "attic insulation"],
    "landscaper": ["landscaper", "landscaping", "lawn", "garden", "tree", "yard"],
    "locksmith": ["locksmith", "lock", "key", "deadbolt"],
    "masonry": ["masonry", "brick", "stone", "concrete", "patio"],
    "pool": ["pool", "hot tub", "spa"],
    "siding": ["siding", "vinyl siding"],
    "tiler": ["tiler", "tile", "tiling", "backsplash", "grout"],
    "waterproofing": ["waterproofing", "waterproof", "basement leak", "foundation"],
    "window": ["window", "windows", "door", "doors"],
}

CITY_KEYWORDS = {
    "toronto": ["toronto", "gta", "north york", "scarborough", "etobicoke", "mississauga", "brampton", "markham", "vaughan", "richmond hill"],
    "barrie": ["barrie", "innisfil", "orillia", "wasaga", "collingwood", "simcoe"],
}


def detect_category(text):
    text_lower = text.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[category] = scores.get(category, 0) + 1
    if scores:
        return max(scores, key=scores.get)
    return None


def detect_city(text):
    text_lower = text.lower()
    for city, keywords in CITY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return city
    return None


def get_providers(category, city=None, limit=6):
    """Query the database for matching service providers."""
    from app import app as flask_app
    from models import ServiceProvider

    with flask_app.app_context():
        query = ServiceProvider.query.filter(
            ServiceProvider.status == 'active'
        )

        cat_map = {
            "plumber": "Plumber",
            "electrician": "Electrician",
            "hvac": "HVAC",
            "painter": "Painter",
            "roofer": "Roofer",
            "cleaner": "House Cleaning",
            "pest control": "Pest Control",
            "mover": "Moving",
            "handyman": "Handyman",
            "appliance repair": "Appliance Repair",
            "carpenter": "Carpenter",
            "chimney": "Chimney Sweep",
            "fence": "Fence & Gate Installer",
            "garage door": "Garage Door",
            "glass": "Glass & Mirror",
            "insulation": "Insulation",
            "landscaper": "Landscaper",
            "locksmith": "Locksmith",
            "masonry": "Masonry",
            "pool": "Pool & Spa",
            "siding": "Siding",
            "tiler": "Tiler",
            "waterproofing": "Waterproofing",
            "window": "Window & Door",
        }

        db_category = cat_map.get(category, category.title())
        query = query.filter(
            ServiceProvider.service_category.ilike(f"%{db_category}%")
        )

        if city:
            query = query.filter(
                ServiceProvider.city.ilike(f"%{city}%")
            )

        providers = query.order_by(
            ServiceProvider.star_rating.desc(),
            ServiceProvider.review_count.desc()
        ).limit(limit).all()

        results = []
        for p in providers:
            results.append({
                "name": p.name,
                "phone": p.formatted_phone(),
                "rating": p.star_rating,
                "reviews": p.review_count,
                "city": p.city,
            })
        return results


def build_reply(sender_text):
    """Build an auto-reply based on the user's message."""
    category = detect_category(sender_text)
    city = detect_city(sender_text)

    if not category:
        return (
            "Hi there! Thanks for reaching out to ConnectYou.\n\n"
            "We help homeowners in Toronto and Barrie find trusted, top-rated home service providers.\n\n"
            "What service are you looking for? For example:\n"
            "- Plumber\n- Electrician\n- HVAC\n- Roofer\n- House Cleaning\n- Handyman\n- Painter\n- Mover\n- Appliance Repair\n\n"
            "Just let us know and we'll match you with the best providers in your area!"
        )

    providers = get_providers(category, city)
    city_label = city.title() if city else "Toronto & Barrie"
    cat_label = category.title()

    if not providers:
        return (
            f"Thanks for your interest in {cat_label} services!\n\n"
            f"We're currently expanding our {cat_label} providers in {city_label}. "
            f"Please visit https://connectyou.pro to browse all available providers, "
            f"or let us know your specific area and we'll help you find someone."
        )

    reply = f"Great news! Here are our top-rated {cat_label} providers"
    if city:
        reply += f" in {city_label}"
    reply += ":\n\n"

    for i, p in enumerate(providers, 1):
        reply += f"{i}. {p['name']}\n"
        reply += f"   Rating: {p['rating']}/5 ({p['reviews']} reviews)\n"
        reply += f"   Call/Text: {p['phone']}\n"
        reply += f"   Area: {p['city']}\n\n"

    reply += (
        "You can also visit https://connectyou.pro for more options, reviews, "
        "and to contact providers directly.\n\n"
        "Need a different service or area? Just let us know!"
    )
    return reply


def verify_signature(payload, signature):
    """Verify that the webhook payload is from Facebook."""
    if not APP_SECRET or not signature:
        return True
    expected = hmac.new(
        APP_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def send_message(recipient_id, text):
    """Send a message to a user via the Messenger Send API."""
    url = f"{GRAPH_API}/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}

    for chunk in _split_message(text, 2000):
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": chunk},
            "messaging_type": "RESPONSE",
        }
        try:
            resp = http_requests.post(url, params=params, json=payload, timeout=10)
            if resp.status_code != 200:
                logger.error("Messenger send failed: %s %s", resp.status_code, resp.text)
        except Exception as e:
            logger.error("Messenger send error: %s", e)


def _split_message(text, max_len):
    """Split a long message into chunks that fit the Messenger limit."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


@messenger_bp.route("/webhook/messenger", methods=["GET"])
def webhook_verify():
    """Handle Facebook webhook verification challenge."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Messenger webhook verified")
        return challenge, 200
    logger.warning("Messenger webhook verification failed (token mismatch)")
    return "Forbidden", 403


@messenger_bp.route("/webhook/messenger", methods=["POST"])
def webhook_receive():
    """Handle incoming Messenger messages."""
    sig = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(request.get_data(), sig):
        logger.warning("Invalid signature on Messenger webhook")
        return "Invalid signature", 403

    data = request.get_json(silent=True)
    if not data:
        return "OK", 200

    if data.get("object") != "page":
        return "OK", 200

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):
            sender_id = event.get("sender", {}).get("id")
            message = event.get("message", {})
            text = message.get("text", "")

            if not sender_id or not text:
                continue

            if message.get("is_echo"):
                continue

            logger.info("Messenger message from %s: %s", sender_id, text[:100])

            reply = build_reply(text)
            send_message(sender_id, reply)

    return "OK", 200
