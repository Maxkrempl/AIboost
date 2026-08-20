#!/usr/bin/env python3
"""Lead Hunter — finds leads for ALL hd-webdesign.si services.

Services:
  1. MenuBoost → restaurants, hotels, cafés, tourist farms
  2. BoostSuite → SEO agencies, freelancers, digital marketing
  3. ListTranslate → cross-border e-commerce, Chinese sellers
  4. Subvencije → EU grant applicants, Slovenian businesses
  5. HD Web Design → businesses needing websites

Usage:
    # Hunt for specific service
    python3 scrapers/lead_hunter.py --service menuboost --region si

    # Hunt for all services
    python3 scrapers/lead_hunter.py --service all --region si,hr,it

    # With audit (check schema.org, llm.txt, etc.)
    python3 scrapers/lead_hunter.py --service menuboost --region si --audit

    # Export to CSV
    python3 scrapers/lead_hunter.py --service all --region si --export leads.csv
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
import random
from datetime import datetime
from urllib.parse import quote_plus, urlparse

WORKSPACE = "/home/darko/.openclaw/workspace"
OUTPUT_DIR = os.path.join(WORKSPACE, "scrapers/output")
LEADS_DIR = os.path.join(WORKSPACE, "lead-gen")

# =============================================================================
# SERVICE DEFINITIONS — who we're looking for
# =============================================================================

SERVICES = {
    "menuboost": {
        "name": "MenuBoost",
        "description": "AI menu descriptions for restaurants",
        "target_businesses": [
            "restavracija", "restaurant", "restoran", "gostilna", "gostinski lokal",
            "turistična kmetija", "tourist farm", "turistično kmetijo",
            "hoteli", "hotel", "hostel", "apartma", "apartment",
            "bar", "café", "kavarna", "pivnica", " gostilna",
            "konoba", "trattoria", "ristorante", "pizzeria",
            "penzion", "pension", "bb", "bed and breakfast",
        ],
        "search_queries": {
            "si": [
                '"turistična kmetija" email kontakt Slovenija',
                '"gostilna" email naslov Slovenija',
                'site:bizi.si "gostinska dejavnost" email',
                'site:si.traisi.si "restavracija" kontakt',
                '"restavracija" email "prijavite se"',
                '"hotel" email kontakt Slovenija obala',
                '"kavarna" email naslov Ljubljana',
            ],
            "hr": [
                '"restoran" email kontakt Istra',
                '"konoba" email adresa Hrvatska',
                'site:gastronaut.hr "restoran" email',
                'site:booking.com "hotel" "restoran" email Istria',
                '"apartman" email kontakt Hrvatska',
                '"pizzeria" email adresa Zagreb',
            ],
            "it": [
                '"ristorante" email contatto Trieste',
                '"trattoria" email contatto Friuli',
                'site:tripadvisor.it "ristorante" "contatti" Trieste',
                '"agriturismo" email contatto Veneto',
                '"bar" email contatto Milano',
            ],
            "de": [
                '"Gasthof" email kontakt Kärnten',
                '"Berghütte" email Tirol',
                '"Restaurant" email kontakt München',
            ],
        },
        "overpass_categories": [
            "amenity=restaurant",
            "amenity=cafe",
            "amenity=bar",
            "amenity=pub",
            "tourism=hotel",
            "tourism=hostel",
            "tourism=motel",
            "tourism=apartment",
        ],
    },
    "boostsuite": {
        "name": "BoostSuite",
        "description": "SEO audit, GEO, ad copy, listing optimize",
        "target_businesses": [
            "SEO agency", "digital marketing agency", "marketing agency",
            "SEO freelancer", "web agency", "creative agency",
            "ppc agency", "content marketing agency", "social media agency",
        ],
        "search_queries": {
            "si": [
                '"SEO agencija" email kontakt',
                '"digitalna marketing agencija" Slovenija',
                'site:clutch.co "SEO agency" Slovenia email',
                '"spletno oglaševanje" agencija email',
            ],
            "hr": [
                '"SEO agencija" email kontakt Hrvatska',
                '"digitalna agencija" Zagreb email',
                'site:clutch.co "SEO agency" Croatia email',
            ],
            "it": [
                '"agenzia SEO" email contatto Italia',
                '"agenzia digitale" Milano email',
                'site:clutch.co "SEO agency" Italy email',
            ],
            "global": [
                'SEO agency email contact',
                '"SEO freelancer" email contact',
                'site:clutch.co "SEO agency" email',
                '"digital marketing agency" SEO services email',
                '"link building" agency email contact',
                '"GEO optimization" agency contact',
                '"AI SEO" agency email',
            ],
        },
    },
    "listtranslate": {
        "name": "AI Authority",
        "description": "GEO optimization — make websites visible to AI models (ChatGPT, Gemini, Perplexity)",
        "target_businesses": [
            "business with outdated SEO", "company needing AI visibility",
            "SME needing GEO", "startup needing schema.org",
            "business without llm.txt", "business not in AI recommendations",
            "restaurant needing AI visibility", "hotel needing AI visibility",
            "agency needing GEO services",
        ],
        "search_queries": {
            "si": [
                '"GEO optimizacija" kontakt',
                '"AI vidljivost" podjetje email',
                '"schema.org" implementacija Slovenija',
                '"llm.txt" nastavitev',
                '"AI priporočilo" podjetje',
                '"ChatGPT priporočilo" gostilna',
            ],
            "hr": [
                '"GEO optimizacija" kontakt Hrvatska',
                '"AI vidljivost" tvrtka email',
                '"schema.org" implementacija Hrvatska',
                '"ChatGPT preporuka" restoran',
            ],
            "it": [
                '"GEO optimization" contatto Italia',
                '"AI visibility" business email',
                '"schema.org" implementazione Italia',
                '"ChatGPT raccomandazione" ristorante',
            ],
            "global": [
                '"GEO optimization" agency contact',
                '"AI visibility" service email',
                '"schema.org" implementation service',
                '"llm.txt" creation service',
                '"AI SEO" agency email contact',
                '"generative engine optimization" service',
                '"ChatGPT recommend" business service',
            ],
        },
    },
    "subvencije": {
        "name": "Subvencije",
        "description": "EU grants documentation service",
        "target_businesses": [
            "SME", "small business", "startup", "podjetje",
            "EU grant applicant", "razpis", "subvencija",
            "podjetništvo", "entrepreneurship",
        ],
        "search_queries": {
            "si": [
                '"subvencija" "razpis" email kontakt',
                '"EU sredstva" podjetje email',
                '"javni razpis" podjetje kontakt',
                'site:spi.si "subvencija" email',
                '"spodbujevalni ukrepi" podjetje',
            ],
        },
    },
    "webdesign": {
        "name": "HD Web Design",
        "description": "Web design & development",
        "target_businesses": [
            "business without website", "outdated website",
            "company needing website", "startup needing website",
        ],
        "search_queries": {
            "si": [
                '"podjetje" "brez spletne strani"',
                '"posodobitev spletne strani" kontakt',
                '"izdelava spletne strani" email',
                'site:123reg.si "nova stran"',
            ],
        },
    },
}

# =============================================================================
# OVERPASS API — bulk restaurant/hotel extraction
# =============================================================================

# Bounding boxes for regions
REGION_BBOX = {
    "si": (13.37, 45.42, 16.60, 46.88),      # Slovenia
    "si-coast": (13.50, 45.48, 16.30, 45.70),  # Slovenian coast
    "si-ljubljana": (14.45, 46.00, 14.60, 46.10),  # Ljubljana area
    "hr": (13.48, 42.38, 19.43, 46.55),        # Croatia
    "hr-istra": (13.60, 44.80, 14.10, 45.50),  # Istria
    "it": (6.63, 36.65, 18.52, 47.09),         # Italy
    "it-trieste": (13.70, 45.63, 13.85, 45.72),  # Trieste area
    "de": (5.87, 47.27, 15.04, 55.06),         # Germany
    "at": (9.53, 46.37, 17.16, 48.47),         # Austria
}


OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]


def overpass_query(bbox, category, limit=500):
    """Query Overpass API for businesses (tries multiple endpoints)."""
    south, west, north, east = bbox
    query = f"""
    [out:json][timeout:30];
    (
      node["{category.split('=')[0]}"="{category.split('=')[1]}"]({south},{west},{north},{east});
      way["{category.split('=')[0]}"="{category.split('=')[1]}"]({south},{west},{north},{east});
    );
    out center body {limit};
    """

    for endpoint in OVERPASS_ENDPOINTS:
        try:
            import httpx
            r = httpx.post(
                endpoint,
                content=f"data={query}",
                headers={"User-Agent": "Mozilla/5.0 (compatible; LeadHunter/1.0)",
                         "Content-Type": "application/x-www-form-urlencoded"},
                timeout=60,
            )
            if r.status_code == 200:
                data = r.json()
                return data.get("elements", [])
        except Exception:
            continue

    print(f"  ❌ All Overpass endpoints failed for {category}")
    return []


def parse_overpass_results(elements):
    """Parse Overpass API results into leads."""
    leads = []

    for el in elements:
        tags = el.get("tags", {})

        name = tags.get("name", "")
        if not name:
            continue

        email = tags.get("email", "")
        phone = tags.get("phone", tags.get("contact:phone", ""))
        website = tags.get("website", tags.get("contact:website", ""))
        addr = tags.get("addr:street", "")
        city = tags.get("addr:city", tags.get("addr:town", tags.get("addr:village", "")))
        cuisine = tags.get("cuisine", "")

        lead = {
            "name": name,
            "email": email,
            "phone": phone,
            "website": website,
            "address": addr,
            "city": city,
            "cuisine": cuisine,
            "type": tags.get("amenity", tags.get("tourism", "")),
            "source": "overpass-api",
            "lat": el.get("lat", el.get("center", {}).get("lat")),
            "lon": el.get("lon", el.get("center", {}).get("lon")),
        }
        leads.append(lead)

    return leads


def hunt_overpass(region, categories, limit=200):
    """Hunt leads using Overpass API."""
    bbox = REGION_BBOX.get(region)
    if not bbox:
        print(f"  ❌ Unknown region: {region}")
        return []

    all_leads = []
    for cat in categories:
        print(f"  🗺️  Overpass: {cat} in {region}...")
        elements = overpass_query(bbox, cat, limit)
        leads = parse_overpass_results(elements)
        print(f"     Found {len(leads)} businesses")
        all_leads.extend(leads)
        time.sleep(1)  # Be nice to the API

    return all_leads


# =============================================================================
# WEB SEARCH HUNTING
# =============================================================================

def web_search_hunt(queries, service_name):
    """Hunt leads using web search."""
    all_leads = []

    for query in queries:
        print(f"  🔍 Searching: {query[:60]}...")

        # Use firecrawl search
        try:
            output_path = os.path.join(OUTPUT_DIR, f"hunt-{int(time.time())}.json")
            cmd = [
                "firecrawl", "search", query,
                "--limit", "10",
                "--scrape",
                "--json",
                "-o", output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0 and os.path.exists(output_path):
                with open(output_path) as f:
                    data = json.load(f)

                for item in data.get("data", {}).get("web", []):
                    content = item.get("markdown", "") or item.get("content", "")
                    emails = extract_emails(content)

                    for email in emails:
                        all_leads.append({
                            "name": item.get("title", "")[:80],
                            "email": email,
                            "website": item.get("url", ""),
                            "type": service_name,
                            "source": f"web-search:{query[:50]}",
                        })

                os.remove(output_path)  # Cleanup

        except Exception as e:
            print(f"  ⚠️ Search error: {e}")

        time.sleep(2)  # Rate limit

    return all_leads


# =============================================================================
# SITE AUDIT (reuse from stealth_scraper)
# =============================================================================

def quick_audit(url):
    """Quick audit of a website — schema, llm.txt, SEO."""
    from stealth_scraper import check_schema_org, check_llm_txt, check_seo_basics, fetch_text

    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    html = fetch_text(url)
    if not html:
        return None

    schema = check_schema_org(html)
    llm = check_llm_txt(base_url)
    seo = check_seo_basics(html)

    return {
        "has_schema": schema["has_json_ld"] or schema["has_microdata"],
        "schema_types": schema["json_ld_types"],
        "has_llm_txt": llm["found"],
        "has_title": seo["has_title"],
        "has_meta_desc": seo["has_meta_description"],
        "has_og_tags": seo["has_og_tags"],
        "score": sum([
            schema["has_json_ld"],
            llm["found"],
            seo["has_title"],
            seo["has_meta_description"],
            seo["has_og_tags"],
            seo["has_canonical"],
            seo["has_h1"],
        ]),
    }


# =============================================================================
# EMAIL EXTRACTION
# =============================================================================

def extract_emails(text):
    """Extract email addresses from text."""
    pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    junk = [
        "example.com", "test.com", "sentry.io", "wixpress.com",
        "w3.org", "schema.org", "googleapis.com", "cloudflare.com",
        "wordpress.org", "wordpress.com", "google.com", "googleapis.com",
    ]
    return [e for e in set(emails) if not any(j in e for j in junk)]


# =============================================================================
# LEAD DEDUPLICATION
# =============================================================================

def load_existing_leads():
    """Load all existing leads for dedup."""
    emails = set()
    websites = set()

    for root, dirs, files in os.walk(LEADS_DIR):
        for f in files:
            if not f.endswith(".csv"):
                continue
            try:
                with open(os.path.join(root, f), newline="", errors="replace") as fh:
                    reader = csv.DictReader(fh)
                    for row in reader:
                        e = (row.get("email") or "").strip().lower()
                        w = (row.get("website") or "").strip().lower()
                        if e:
                            emails.add(e)
                        if w:
                            websites.add(w)
            except Exception:
                pass

    return emails, websites


def dedup_leads(leads, existing_emails, existing_websites):
    """Remove duplicates."""
    unique = []
    seen_emails = set()
    seen_websites = set()

    for lead in leads:
        email = lead.get("email", "").lower().strip()
        website = lead.get("website", "").lower().strip()

        # Skip generic emails
        if email and any(x in email for x in [
            "info@", "contact@", "hello@", "admin@", "noreply@",
            "support@", "office@", "sekretariat@",
        ]):
            continue

        # Skip if already exists
        if email and (email in existing_emails or email in seen_emails):
            continue
        if website and (website in existing_websites or website in seen_websites):
            continue

        if email:
            seen_emails.add(email)
        if website:
            seen_websites.add(website)

        unique.append(lead)

    return unique


# =============================================================================
# SAVE RESULTS
# =============================================================================

def save_leads_csv(leads, service, region="all"):
    """Save leads to CSV."""
    if not leads:
        return None

    os.makedirs(os.path.join(LEADS_DIR, service), exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    filename = f"hunter-{region}-{timestamp}.csv"
    filepath = os.path.join(LEADS_DIR, service, filename)

    fieldnames = ["name", "email", "phone", "website", "city", "type", "cuisine",
                  "source", "has_schema", "has_llm_txt", "seo_score"]

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lead in leads:
            row = {k: lead.get(k, "") for k in fieldnames}
            writer.writerow(row)

    return filepath


# =============================================================================
# MAIN HUNTER
# =============================================================================

def hunt_leads(service, regions, do_audit=False):
    """Main lead hunting function."""
    config = SERVICES.get(service)
    if not config:
        print(f"❌ Unknown service: {service}")
        print(f"   Available: {', '.join(SERVICES.keys())}")
        return []

    print(f"\n{'='*60}")
    print(f"🎯 HUNTING LEADS FOR: {config['name']}")
    print(f"   {config['description']}")
    print(f"   Regions: {', '.join(regions)}")
    print(f"{'='*60}\n")

    all_leads = []

    # 1. Overpass API (for restaurants/hotels)
    if "overpass_categories" in config:
        for region in regions:
            leads = hunt_overpass(region, config["overpass_categories"])
            all_leads.extend(leads)

    # 2. Web search
    for region in regions:
        queries = config.get("search_queries", {}).get(region, [])
        if not queries:
            # Try global queries
            queries = config.get("search_queries", {}).get("global", [])
        if queries:
            leads = web_search_hunt(queries, service)
            all_leads.extend(leads)

    # Also try global queries if we have region-specific ones
    global_queries = config.get("search_queries", {}).get("global", [])
    if global_queries:
        leads = web_search_hunt(global_queries, service)
        all_leads.extend(leads)

    # 3. Dedup
    existing_emails, existing_websites = load_existing_leads()
    unique_leads = dedup_leads(all_leads, existing_emails, existing_websites)

    print(f"\n📊 Results:")
    print(f"   Total found: {len(all_leads)}")
    print(f"   After dedup: {len(unique_leads)}")
    print(f"   Existing: {len(existing_emails)} emails, {len(existing_websites)} websites")

    # 4. Audit (optional)
    if do_audit and unique_leads:
        print(f"\n🔍 Auditing {len(unique_leads)} leads...")
        for i, lead in enumerate(unique_leads[:20], 1):  # Limit to 20 audits
            website = lead.get("website", "")
            if website:
                print(f"  [{i}/{min(len(unique_leads), 20)}] {website[:50]}...")
                audit = quick_audit(website)
                if audit:
                    lead["has_schema"] = audit["has_schema"]
                    lead["has_llm_txt"] = audit["has_llm_txt"]
                    lead["seo_score"] = audit["score"]
                time.sleep(1)

    # 5. Save
    filepath = save_leads_csv(unique_leads, service, "-".join(regions))
    if filepath:
        print(f"\n💾 Saved: {filepath}")

    return unique_leads


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Lead Hunter — finds leads for all hd-webdesign.si services",
    )

    parser.add_argument(
        "--service", "-s",
        choices=list(SERVICES.keys()) + ["all"],
        default="all",
        help="Service to hunt leads for",
    )
    parser.add_argument(
        "--region", "-r",
        default="si",
        help="Comma-separated regions (si,hr,it,de,at,global)",
    )
    parser.add_argument(
        "--audit", "-a",
        action="store_true",
        help="Audit each lead's website",
    )
    parser.add_argument(
        "--export", "-e",
        help="Export all results to a single CSV",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=200,
        help="Max leads per Overpass query",
    )

    args = parser.parse_args()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    regions = [r.strip() for r in args.region.split(",")]

    if args.service == "all":
        services = list(SERVICES.keys())
    else:
        services = [args.service]

    all_results = []
    for svc in services:
        leads = hunt_leads(svc, regions, do_audit=args.audit)
        all_results.extend([(svc, lead) for lead in leads])

    # Export to single CSV if requested
    if args.export and all_results:
        with open(args.export, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["service", "name", "email", "phone", "website",
                           "city", "type", "source", "has_schema", "has_llm_txt", "seo_score"])
            for svc, lead in all_results:
                writer.writerow([
                    svc,
                    lead.get("name", ""),
                    lead.get("email", ""),
                    lead.get("phone", ""),
                    lead.get("website", ""),
                    lead.get("city", ""),
                    lead.get("type", ""),
                    lead.get("source", ""),
                    lead.get("has_schema", ""),
                    lead.get("has_llm_txt", ""),
                    lead.get("seo_score", ""),
                ])
        print(f"\n📦 Exported {len(all_results)} leads to {args.export}")

    # Summary
    print(f"\n{'='*60}")
    print(f"🏆 HUNTING COMPLETE")
    print(f"{'='*60}")
    for svc in services:
        count = sum(1 for s, _ in all_results if s == svc)
        print(f"  {SERVICES[svc]['name']}: {count} leads")
    print(f"  TOTAL: {len(all_results)} leads")


if __name__ == "__main__":
    main()
