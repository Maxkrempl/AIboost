# BoostSuite API Documentation

**Base URL:** `https://boostsuite.netlify.app/.netlify/functions`

All endpoints accept `POST` with `Content-Type: application/json`.

## Authentication

Include your API key in the `Authorization` header:

```
Authorization: Bearer bs_live_your_api_key_here
```

**Free tier:** No API key required (3 uses/day via the web UI).  
**Freelancer (€19/mo):** 200 generations/month via API.  
**Agency (€49/mo):** Unlimited API access.

---

## Endpoints

### 1. SEO Audit

**POST** `/seo-audit`

Analyzes a URL and returns an SEO score, analysis, and actionable fixes.

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "score": 72,
  "analysis": "Good title tag but missing meta description. H1 structure is solid.",
  "fixes": [
    "Add a meta description under 160 characters",
    "Add alt text to all images",
    "Improve page load speed",
    "Add structured data markup",
    "Create an XML sitemap"
  ],
  "rawData": {
    "url": "https://example.com",
    "title": "Example Domain",
    "metaDescription": "Missing",
    "h1Count": 1,
    ...
  }
}
```

---

### 2. GEO Check (AI Visibility)

**POST** `/geo-check`

Checks how visible a business is across AI assistants (ChatGPT, Gemini, Perplexity).

**Request:**
```json
{
  "business": "Joe's Pizza",
  "location": "New York, NY",
  "niche": "Italian restaurant"
}
```

**Response:**
```json
{
  "visibility": {
    "googleMaps": " Listed",
    "tripAdvisor": " Listed",
    "yelp": "Not found",
    "aiMentions": "Limited"
  },
  "score": 45,
  "recommendations": ["Claim Yelp listing", "Add photos to Google Business", ...]
}
```

---

### 3. Ad Copy Generator

**POST** `/ad-copy`

Generates platform-ready ad copy for Google, Facebook, LinkedIn, X, or Email.

**Request:**
```json
{
  "product": "Project management software",
  "audience": "Small business owners",
  "tone": "Professional",
  "cta": "Start free trial",
  "platform": "google"
}
```

**Platforms:** `google`, `facebook`, `linkedin`, `x`, `email`

**Response:**
```json
{
  "copy": {
    "headline": "Streamline Your Projects | Free Trial",
    "description": "Manage teams, deadlines, and deliverables in one place...",
    "extensions": ["14-day free trial", "No credit card required", ...]
  }
}
```

---

### 4. Listing Optimizer

**POST** `/listing-optimize`

Optimizes product listings for Etsy, Amazon, or Google Business.

**Request:**
```json
{
  "product": "Handmade ceramic mug",
  "category": "Kitchen & Dining",
  "features": ["handmade", "microwave safe", "unique design"],
  "target": "Gift buyers",
  "platform": "etsy"
}
```

**Platforms:** `etsy`, `amazon`, `google`

**Response:**
```json
{
  "optimized": {
    "title": "Handmade Ceramic Mug | Unique Gift | Microwave Safe",
    "description": "Start your morning with this beautifully handcrafted...",
    "tags": ["handmade mug", "ceramic coffee mug", "gift for her", ...],
    "tips": ["Use all 13 Etsy tags", "Add lifestyle photos", ...]
  }
}
```

---

## API Key Management

**POST** `/api-keys`

Requires `X-Admin-Token` header matching the `ADMIN_TOKEN` env var.

**Create a key:**
```json
{
  "action": "create",
  "email": "agency@example.com",
  "plan": "agency"
}
```

**List all keys:**
```json
{
  "action": "list"
}
```

---

## Rate Limits

| Plan | Monthly Generations | Notes |
|------|-------------------|-------|
| Free | 3/day (web only) | No API access |
| Freelancer | 200/month | API + web |
| Agency | Unlimited | API + web + white-label |

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad request – missing or invalid parameters |
| 401 | Invalid or missing API key |
| 403 | Admin token required for this endpoint |
| 405 | Method not allowed (use POST) |
| 500 | Server error |
