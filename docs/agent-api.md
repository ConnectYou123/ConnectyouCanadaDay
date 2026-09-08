# ConnectYou Agent API

Versioned HTTP API for AI assistants to discover curated service providers and submit customer inquiries.

**Base path:** `/api/v1`

## Authentication

Set `CONNECTYOU_AGENT_API_KEY` in the server environment. When configured, every `/api/v1/*` request must include:

```http
Authorization: Bearer <CONNECTYOU_AGENT_API_KEY>
```

When the key is **not** set, endpoints remain open and the server logs a warning (intended for local development).

### Example (production)

```bash
export CONNECTYOU_AGENT_API_KEY="your-long-random-secret"
```

```http
POST /api/v1/find_providers HTTP/1.1
Authorization: Bearer your-long-random-secret
Content-Type: application/json
```

## CORS

Cross-origin `GET`, `POST`, and `OPTIONS` are allowed for `/api/v1/*` with `Authorization` and `Content-Type` headers.

---

## Endpoints

### `GET /api/v1/cities`

Returns active cities.

**Response**

```json
{
  "cities": [
    {
      "id": 1,
      "name": "Toronto",
      "country": "Canada",
      "flag_emoji": "🇨🇦",
      "status": "active"
    }
  ],
  "count": 1
}
```

---

### `GET /api/v1/categories?city=<name>`

Returns active categories for a city.

**Query parameters**

| Name | Required | Description |
|------|----------|-------------|
| `city` | yes | City name (case-insensitive) |

**Response**

```json
{
  "city": "Toronto",
  "categories": [
    {
      "id": 10,
      "name": "Plumber",
      "description": "Licensed plumbing services",
      "icon": "fas fa-wrench",
      "status": "active"
    }
  ],
  "count": 1
}
```

---

### `POST /api/v1/find_providers`

Returns active providers for a city and category, sorted by `star_rating` (desc) then `review_count` (desc).

Provider phone numbers are **not** exposed. Contact is routed through ConnectYou call/text endpoints.

**Request body**

```json
{
  "city": "Toronto",
  "category": "Plumber",
  "need": "Kitchen sink leak",
  "limit": 6
}
```

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `city` | yes | — | City name |
| `category` | yes | — | Service category name |
| `need` | no | `null` | Customer need (echoed in response; does not filter results) |
| `limit` | no | `6` | Maximum providers to return |

**Response**

```json
{
  "city": "Toronto",
  "category": "Plumber",
  "need": "Kitchen sink leak",
  "limit": 6,
  "count": 2,
  "providers": [
    {
      "id": 42,
      "name": "Ace Plumbing",
      "city": "Toronto",
      "category": "Plumber",
      "star_rating": 4.9,
      "review_count": 210,
      "status": "active",
      "contact_via": "connectyou",
      "contact": {
        "call_endpoint": "https://example.com/call_provider",
        "text_endpoint": "https://example.com/text_provider",
        "provider_id": 42,
        "provider_name": "Ace Plumbing",
        "service_category": "Plumber"
      }
    }
  ]
}
```

To initiate contact, POST to the existing ConnectYou endpoints with `provider_id`, `provider_name`, and `service_category` (calls/texts are handled by the platform, not direct provider numbers).

---

### `POST /api/v1/inquiries`

Records a customer inquiry. Optionally requests provider fan-out.

**Request body**

```json
{
  "city": "Toronto",
  "category": "Plumber",
  "customer_name": "Jane Doe",
  "customer_contact": "+14165551234",
  "need": "Emergency pipe burst in basement",
  "fanout": true
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `city` | yes | City name |
| `category` | yes | Service category |
| `need` | yes | Description of the customer's need |
| `customer_name` | no | Customer display name |
| `customer_contact` | no | Phone or email for follow-up |
| `fanout` | no | When `true`, match up to 6 providers (see below) |

**Response (fanout deferred)**

When `fanout` is `true`, the inquiry is saved. Provider SMS/call fan-out is deferred because outbound Twilio traffic is routed through the ConnectYou hub line rather than individual provider numbers:

```json
{
  "status": "recorded",
  "inquiry_id": 7,
  "fanout": "deferred",
  "reason": "provider_phones_hub_only",
  "providers_matched": 6
}
```

**Response (no fanout)**

```json
{
  "status": "recorded",
  "inquiry_id": 7
}
```

---

## Error responses

| Status | Meaning |
|--------|---------|
| `400` | Missing or invalid parameters |
| `401` | Missing or invalid `Authorization` bearer token |
| `404` | City not found |

Errors use `{ "error": "message" }`.

---

## Quick start for agents

1. `GET /api/v1/cities` — pick a city
2. `GET /api/v1/categories?city=Toronto` — list services
3. `POST /api/v1/find_providers` — get top-rated providers
4. `POST /api/v1/inquiries` — record the customer's need (set `fanout: true` to queue provider matching)
