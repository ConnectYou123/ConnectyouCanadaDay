"""
Versioned public API for AI agents to discover ConnectYou providers and submit inquiries.
"""

import logging
import os
from functools import wraps

from flask import Blueprint, jsonify, request, url_for
from sqlalchemy import func

from app import db
from models import Category, City, Inquiry, ServiceProvider

agent_api_bp = Blueprint("agent_api", __name__, url_prefix="/api/v1")

DEFAULT_PROVIDER_LIMIT = 6
HUB_ONLY_FANOUT_REASON = "provider_phones_hub_only"


def _get_agent_api_key():
    return os.environ.get("CONNECTYOU_AGENT_API_KEY")


def require_agent_auth(view):
    """Require Bearer token when CONNECTYOU_AGENT_API_KEY is configured."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        api_key = _get_agent_api_key()
        if not api_key:
            logging.warning(
                "CONNECTYOU_AGENT_API_KEY is not set; allowing unauthenticated /api/v1 access"
            )
            return view(*args, **kwargs)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header[7:].strip()
        if token != api_key:
            return jsonify({"error": "Unauthorized"}), 401

        return view(*args, **kwargs)

    return wrapped


@agent_api_bp.after_request
def add_cors_headers(response):
    """Allow simple cross-origin access for agent clients."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@agent_api_bp.route("/<path:path>", methods=["OPTIONS"])
@agent_api_bp.route("/", methods=["OPTIONS"])
def handle_options(**kwargs):
    return "", 204


def query_ranked_providers(city, category, limit=DEFAULT_PROVIDER_LIMIT):
    """Return active providers sorted by star_rating then review_count."""
    return (
        ServiceProvider.query.filter(
            func.lower(ServiceProvider.service_category) == category.lower(),
            func.lower(ServiceProvider.city) == city.lower(),
            ServiceProvider.status == "active",
        )
        .order_by(
            ServiceProvider.star_rating.desc(),
            ServiceProvider.review_count.desc(),
        )
        .limit(limit)
        .all()
    )


def serialize_provider(provider):
    """Agent-safe provider payload without raw phone numbers."""
    return {
        "id": provider.id,
        "name": provider.name,
        "city": provider.city,
        "category": provider.service_category,
        "star_rating": provider.star_rating,
        "review_count": provider.review_count,
        "status": provider.status,
        "contact_via": "connectyou",
        "contact": {
            "call_endpoint": url_for("call_provider", _external=True),
            "text_endpoint": url_for("text_provider", _external=True),
            "provider_id": provider.id,
            "provider_name": provider.name,
            "service_category": provider.service_category,
        },
    }


@agent_api_bp.route("/cities", methods=["GET"])
@require_agent_auth
def list_cities():
    cities = City.query.filter_by(status="active").order_by(City.name).all()
    return jsonify(
        {
            "cities": [
                {
                    "id": city.id,
                    "name": city.name,
                    "country": city.country,
                    "flag_emoji": city.flag_emoji,
                    "status": city.status,
                }
                for city in cities
            ],
            "count": len(cities),
        }
    )


@agent_api_bp.route("/categories", methods=["GET"])
@require_agent_auth
def list_categories():
    city_name = request.args.get("city")
    if not city_name:
        return jsonify({"error": "city query parameter is required"}), 400

    city = City.query.filter(func.lower(City.name) == city_name.lower()).first()
    if not city:
        return jsonify({"error": f"City '{city_name}' not found"}), 404

    categories = (
        Category.query.filter_by(city_name=city.name, status="active")
        .order_by(Category.name)
        .all()
    )

    return jsonify(
        {
            "city": city.name,
            "categories": [
                {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "icon": category.icon,
                    "status": category.status,
                }
                for category in categories
            ],
            "count": len(categories),
        }
    )


@agent_api_bp.route("/find_providers", methods=["POST"])
@require_agent_auth
def find_providers():
    data = request.get_json(silent=True) or {}
    city = (data.get("city") or "").strip()
    category = (data.get("category") or "").strip()
    need = (data.get("need") or "").strip() or None

    if not city or not category:
        return jsonify({"error": "city and category are required"}), 400

    limit = data.get("limit", DEFAULT_PROVIDER_LIMIT)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return jsonify({"error": "limit must be an integer"}), 400

    if limit < 1:
        return jsonify({"error": "limit must be at least 1"}), 400

    city_row = City.query.filter(func.lower(City.name) == city.lower()).first()
    if not city_row:
        return jsonify({"error": f"City '{city}' not found"}), 404

    providers = query_ranked_providers(city_row.name, category, limit=limit)

    return jsonify(
        {
            "city": city_row.name,
            "category": category,
            "need": need,
            "limit": limit,
            "providers": [serialize_provider(provider) for provider in providers],
            "count": len(providers),
        }
    )


@agent_api_bp.route("/inquiries", methods=["POST"])
@require_agent_auth
def create_inquiry():
    data = request.get_json(silent=True) or {}
    city = (data.get("city") or "").strip()
    category = (data.get("category") or "").strip()
    need = (data.get("need") or "").strip()

    if not city or not category or not need:
        return jsonify({"error": "city, category, and need are required"}), 400

    fanout = bool(data.get("fanout", False))

    inquiry = Inquiry(
        city=city,
        category=category,
        customer_name=(data.get("customer_name") or "").strip() or None,
        customer_contact=(data.get("customer_contact") or "").strip() or None,
        need=need,
        fanout_requested=fanout,
        status="recorded",
        source="agent_api",
    )

    response = {
        "status": "recorded",
        "inquiry_id": None,
    }

    if fanout:
        providers = query_ranked_providers(city, category, limit=DEFAULT_PROVIDER_LIMIT)
        inquiry.fanout_status = "deferred"
        inquiry.fanout_reason = HUB_ONLY_FANOUT_REASON
        inquiry.fanout_provider_count = len(providers)
        response["fanout"] = "deferred"
        response["reason"] = HUB_ONLY_FANOUT_REASON
        response["providers_matched"] = len(providers)

    db.session.add(inquiry)
    db.session.commit()

    response["inquiry_id"] = inquiry.id
    return jsonify(response), 201
