"""Tests for the versioned ConnectYou agent API."""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock

# Configure test environment before importing the Flask app.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SESSION_SECRET"] = "test-secret"
os.environ.pop("CONNECTYOU_AGENT_API_KEY", None)

# Stub optional integrations so the full app can import in CI.
sys.modules.setdefault("mailersend", MagicMock())
sys.modules.setdefault("mailersend.emails", MagicMock())

from app import app, db
from models import Category, City, Inquiry, ServiceProvider


def _auth_headers(api_key="test-agent-key"):
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


class AgentApiTestCase(unittest.TestCase):
    """Agent API integration tests using an in-memory database."""

    def setUp(self):
        self._prior_api_key = os.environ.get("CONNECTYOU_AGENT_API_KEY")
        os.environ.pop("CONNECTYOU_AGENT_API_KEY", None)

        self.client = app.test_client()
        self.client.testing = True

        with app.app_context():
            db.drop_all()
            db.create_all()
            self._seed_data()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

        if self._prior_api_key is None:
            os.environ.pop("CONNECTYOU_AGENT_API_KEY", None)
        else:
            os.environ["CONNECTYOU_AGENT_API_KEY"] = self._prior_api_key

    def _seed_data(self):
        city = City(
            name="Testville",
            country="Canada",
            flag_emoji="CA",
            status="active",
        )
        db.session.add(city)
        db.session.flush()

        category = Category(
            name="Plumber",
            description="Plumbing services",
            icon="fas fa-wrench",
            status="active",
            city_name="Testville",
        )
        db.session.add(category)

        providers = [
            ("Alpha Plumbing", 4.5, 50),
            ("Beta Plumbing", 5.0, 10),
            ("Gamma Plumbing", 5.0, 200),
            ("Delta Plumbing", 4.9, 100),
            ("Epsilon Plumbing", 4.8, 300),
            ("Zeta Plumbing", 4.7, 400),
            ("Eta Plumbing", 4.6, 500),
            ("Theta Plumbing", 4.0, 999),
        ]
        for index, (name, rating, reviews) in enumerate(providers, start=1):
            db.session.add(
                ServiceProvider(
                    name=name,
                    phone=f"+1416555{index:04d}",
                    business_address=f"{index} Main St",
                    city="Testville",
                    province="ON",
                    service_category="Plumber",
                    star_rating=rating,
                    review_count=reviews,
                    status="active" if index <= 7 else "inactive",
                )
            )

        db.session.commit()

    def test_find_providers_returns_top_six_sorted_by_rating_then_reviews(self):
        response = self.client.post(
            "/api/v1/find_providers",
            data=json.dumps(
                {"city": "Testville", "category": "Plumber", "limit": 6}
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["count"], 6)
        self.assertEqual(payload["limit"], 6)

        names = [provider["name"] for provider in payload["providers"]]
        self.assertEqual(
            names,
            [
                "Gamma Plumbing",
                "Beta Plumbing",
                "Delta Plumbing",
                "Epsilon Plumbing",
                "Zeta Plumbing",
                "Eta Plumbing",
            ],
        )

        for provider in payload["providers"]:
            self.assertEqual(provider["contact_via"], "connectyou")
            self.assertNotIn("phone", provider)
            self.assertIn("call_endpoint", provider["contact"])
            self.assertIn("text_endpoint", provider["contact"])

    def test_find_providers_excludes_inactive_providers(self):
        response = self.client.post(
            "/api/v1/find_providers",
            data=json.dumps(
                {"city": "Testville", "category": "Plumber", "limit": 10}
            ),
            content_type="application/json",
        )

        payload = response.get_json()
        names = {provider["name"] for provider in payload["providers"]}
        self.assertNotIn("Theta Plumbing", names)
        self.assertEqual(payload["count"], 7)

    def test_auth_required_when_api_key_set(self):
        os.environ["CONNECTYOU_AGENT_API_KEY"] = "test-agent-key"

        unauthenticated = self.client.post(
            "/api/v1/find_providers",
            data=json.dumps({"city": "Testville", "category": "Plumber"}),
            content_type="application/json",
        )
        self.assertEqual(unauthenticated.status_code, 401)

        wrong_token = self.client.post(
            "/api/v1/find_providers",
            data=json.dumps({"city": "Testville", "category": "Plumber"}),
            headers=_auth_headers("wrong-key"),
        )
        self.assertEqual(wrong_token.status_code, 401)

        authenticated = self.client.post(
            "/api/v1/find_providers",
            data=json.dumps({"city": "Testville", "category": "Plumber", "limit": 1}),
            headers=_auth_headers("test-agent-key"),
        )
        self.assertEqual(authenticated.status_code, 200)
        self.assertEqual(authenticated.get_json()["count"], 1)

    def test_cities_and_categories_endpoints(self):
        cities_response = self.client.get("/api/v1/cities")
        self.assertEqual(cities_response.status_code, 200)
        cities_payload = cities_response.get_json()
        self.assertEqual(cities_payload["count"], 1)
        self.assertEqual(cities_payload["cities"][0]["name"], "Testville")

        categories_response = self.client.get("/api/v1/categories?city=Testville")
        self.assertEqual(categories_response.status_code, 200)
        categories_payload = categories_response.get_json()
        self.assertEqual(categories_payload["count"], 1)
        self.assertEqual(categories_payload["categories"][0]["name"], "Plumber")

    def test_create_inquiry_with_deferred_fanout(self):
        response = self.client.post(
            "/api/v1/inquiries",
            data=json.dumps(
                {
                    "city": "Testville",
                    "category": "Plumber",
                    "customer_name": "Jane Doe",
                    "customer_contact": "+14165550100",
                    "need": "Leaky faucet",
                    "fanout": True,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["status"], "recorded")
        self.assertEqual(payload["fanout"], "deferred")
        self.assertEqual(payload["reason"], "provider_phones_hub_only")
        self.assertEqual(payload["providers_matched"], 6)

        with app.app_context():
            inquiry = Inquiry.query.get(payload["inquiry_id"])
            self.assertIsNotNone(inquiry)
            self.assertEqual(inquiry.need, "Leaky faucet")
            self.assertTrue(inquiry.fanout_requested)
            self.assertEqual(inquiry.fanout_status, "deferred")


if __name__ == "__main__":
    unittest.main()
