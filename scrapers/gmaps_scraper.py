#!/usr/bin/env python3
"""Google Maps Lead Scraper — extract businesses from Google Maps.

Uses stealth playwright to avoid detection.

Usage:
    # Search and extract businesses
    python3 scrapers/gmaps_scraper.py "restavracija Ljubljana" --limit 50

    # Search with audit
    python3 scrapers/gmaps_scraper.py "SEO agencija Slovenija" --limit 20 --audit

    # From file of search queries
    python3 scrapers/gmaps_scraper.py --queries queries.txt --limit 30

    # Export results
    python3 scrapers/gmaps_scraper.py "hotel Bled" --limit 20 --export leads.csv
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import random
from datetime import datetime
from urllib.parse import quote_plus

WORKSPACE = "/home/darko/.openclaw/workspace"
OUTPUT_DIR = os.path.join(WORKSPACE, "scrapers/output")
LEADS_DIR = os.path.join(WORKSPACE, "lead-gen")

FINGERPRINTS = [
    {"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36", "locale": "sl-SI", "timezone": "Europe/Ljubljana"},
    {"user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36", "locale": "en-US", "timezone": "America/New_York"},
    {"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0", "locale": "de-DE", "timezone": "Europe/Berlin"},
]


def extract_emails(text):
    """Extract real email addresses."""
    pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    junk = [
        "example.com", "test.com", "sentry.io", "wixpress.com",
        "w3.org", "schema.org", "googleapis.com", "cloudflare.com",
        "google.com", "gstatic.com", "youtube.com",
    ]
    # Filter out image filenames and junk
    real_emails = []
    for e in set(emails):
        e_lower = e.lower()
        if any(j in e_lower for j in junk):
            continue
        # Skip if it looks like an image filename (has common image extensions before @)
        if re.search(r'\.(png|jpg|jpeg|gif|svg|webp|bmp)@', e_lower):
            continue
        # Skip if domain has common image extensions
        if re.search(r'\.(png|jpg|jpeg|gif|svg|webp|bmp)', e_lower.split('@')[1]):
            continue
        real_emails.append(e)
    return real_emails


def scrape_gmaps(query, limit=20, headless=True):
    """Scrape Google Maps search results."""
    try:
        from playwright.sync_api import sync_playwright
        from undetected_playwright import stealth_sync
    except ImportError:
        print("❌ undetected-playwright not installed")
        return []

    fp = random.choice(FINGERPRINTS)
    search_url = f"https://www.google.com/maps/search/{quote_plus(query)}/"

    print(f"🗺️  Google Maps scraping: {query}")
    print(f"   Limit: {limit} businesses")
    print(f"   Fingerprint: {fp['locale']}")

    businesses = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )

            context = browser.new_context(
                user_agent=fp["user_agent"],
                viewport={"width": 1920, "height": 1080},
                locale=fp["locale"],
                timezone_id=fp["timezone"],
            )

            page = context.new_page()
            stealth_sync(page)

            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(3, 5))

            # Accept cookies if dialog appears
            try:
                cookie_btn = page.query_selector('button[aria-label*="Accept"], button[aria-label*="Sprejmi"], #L2AGLb, form[action*="consent"] button')
                if cookie_btn:
                    cookie_btn.click()
                    time.sleep(2)
                    print("  🍪 Accepted cookies")
            except Exception:
                pass

            # Wait for results to load
            try:
                page.wait_for_selector('[role="feed"], .Nv2PK, a[href*="/maps/place/"]', timeout=10000)
            except Exception:
                print("  ⚠️ No feed found, trying alternative selectors...")

            # Scroll to load more results
            scroll_count = 0
            max_scrolls = limit // 5 + 2

            while scroll_count < max_scrolls:
                # Try multiple scroll approaches
                feed = page.query_selector('[role="feed"]')
                if feed:
                    feed.evaluate("el => el.scrollTop = el.scrollHeight")
                else:
                    # Try scrolling the main content area
                    page.evaluate("document.querySelector('.m6QErb')?.scrollBy(0, 500) || window.scrollBy(0, 500)")

                time.sleep(random.uniform(1.5, 2.5))
                scroll_count += 1

                # Check for results with multiple selectors
                results = page.query_selector_all('a[href*="/maps/place/"], .Nv2PK a, .qBF1Pd')
                if len(results) >= limit:
                    break

            # Extract business data - try multiple selector strategies
            result_links = page.query_selector_all('a[href*="/maps/place/"]')
            if not result_links:
                result_links = page.query_selector_all('.Nv2PK a')
            if not result_links:
                result_links = page.query_selector_all('.qBF1Pd')

            for link in result_links[:limit]:
                try:
                    # Get the parent container
                    container = link.evaluate_handle("el => el.closest('[role=\"feed\"] > div')").as_element()
                    if not container:
                        container = link

                    # Extract basic info from the listing
                    name = ""
                    rating = ""
                    reviews = ""
                    address = ""
                    phone = ""
                    website = ""
                    type_info = ""

                    # Try to get name
                    name_el = container.query_selector(".fontHeadlineSmall, .qBF1Pd, [class*='fontHeadlineSmall']")
                    if name_el:
                        name = name_el.inner_text().strip()

                    # Try to get rating
                    rating_el = container.query_selector('.MW4etd, [class*="MW4etd"]')
                    if rating_el:
                        rating = rating_el.inner_text().strip()

                    # Try to get reviews count
                    reviews_el = container.query_selector('.UY7F9, [class*="UY7F9"]')
                    if reviews_el:
                        reviews = reviews_el.inner_text().strip()

                    # Try to get other info from aria-label
                    aria_label = link.get_attribute("aria-label") or ""
                    if not name and aria_label:
                        name = aria_label.split(",")[0].strip()

                    # Get the link href for later scraping
                    href = link.get_attribute("href") or ""

                    if name:
                        businesses.append({
                            "name": name,
                            "rating": rating,
                            "reviews": reviews,
                            "address": address,
                            "phone": phone,
                            "website": website,
                            "type": type_info,
                            "maps_url": href,
                            "source": f"google-maps:{query[:50]}",
                        })

                except Exception as e:
                    continue

            # Now visit each business to get detailed info
            print(f"\n  📋 Found {len(businesses)} listings, fetching details...")

            for i, biz in enumerate(businesses[:limit]):
                if biz.get("maps_url"):
                    print(f"  [{i+1}/{len(businesses)}] {biz['name'][:40]}...")
                    try:
                        page.goto(biz["maps_url"], wait_until="domcontentloaded", timeout=15000)
                        time.sleep(random.uniform(1.5, 3))

                        # Extract details from the place page
                        detail_html = page.content()

                        # Get website
                        website_el = page.query_selector('a[data-item-id="authority"]')
                        if website_el:
                            biz["website"] = website_el.get_attribute("href") or ""

                        # Get phone
                        phone_el = page.query_selector('[data-item-id*="phone"] .Io6YTe')
                        if phone_el:
                            biz["phone"] = phone_el.inner_text().strip()

                        # Get address
                        addr_el = page.query_selector('[data-item-id="address"] .Io6YTe')
                        if addr_el:
                            biz["address"] = addr_el.inner_text().strip()

                        # Get type
                        type_el = page.query_selector('.DkEaL, [role="img"][aria-label]')
                        if type_el:
                            biz["type"] = type_el.inner_text().strip() if type_el.inner_text() else type_el.get_attribute("aria-label") or ""

                        # Extract emails from page content
                        emails = extract_emails(detail_html)
                        if emails:
                            biz["email"] = emails[0]  # Primary email

                    except Exception as e:
                        print(f"    ⚠️ Error: {e}")

                    time.sleep(random.uniform(1, 2))

            browser.close()

    except Exception as e:
        print(f"❌ Error: {e}")

    return businesses


def audit_business(url):
    """Quick audit of a business website."""
    if not url:
        return None

    try:
        import httpx
        r = httpx.get(url, timeout=8, follow_redirects=True,
                     headers={"User-Agent": "Mozilla/5.0 (compatible; LeadHunter/1.0)"})
        if r.status_code != 200:
            return None

        html = r.text
        from stealth_scraper import check_schema_org, check_llm_txt, check_seo_basics

        schema = check_schema_org(html)
        llm = check_llm_txt(f"{url.split('//')[0]}//{url.split('//')[1].split('/')[0]}")
        seo = check_seo_basics(html)

        return {
            "has_schema": schema["has_json_ld"] or schema["has_microdata"],
            "has_llm_txt": llm["found"],
            "has_title": seo["has_title"],
            "has_meta_desc": seo["has_meta_description"],
            "score": sum([schema["has_json_ld"], llm["found"], seo["has_title"],
                         seo["has_meta_description"], seo["has_og_tags"]]),
        }
    except Exception:
        return None


def save_results(businesses, query, export_path=None):
    """Save results to JSON and optionally CSV."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    slug = re.sub(r'[^a-zA-Z0-9]', '-', query)[:30]

    # Save JSON
    json_path = os.path.join(OUTPUT_DIR, f"gmaps-{slug}-{timestamp}.json")
    with open(json_path, "w") as f:
        json.dump(businesses, f, indent=2, ensure_ascii=False)
    print(f"\n💾 JSON saved: {json_path}")

    # Save CSV if requested
    if export_path:
        fieldnames = ["name", "email", "phone", "website", "address", "rating",
                      "reviews", "type", "source", "has_schema", "has_llm_txt", "seo_score"]
        with open(export_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for biz in businesses:
                row = {k: biz.get(k, "") for k in fieldnames}
                writer.writerow(row)
        print(f"💾 CSV saved: {export_path}")

    return json_path


def main():
    parser = argparse.ArgumentParser(description="Google Maps Lead Scraper")
    parser.add_argument("query", nargs="?", help="Search query (e.g., 'restavracija Ljubljana')")
    parser.add_argument("--queries", "-q", help="File with search queries (one per line)")
    parser.add_argument("--limit", "-l", type=int, default=20, help="Max results per query")
    parser.add_argument("--audit", "-a", action="store_true", help="Audit each business website")
    parser.add_argument("--export", "-e", help="Export to CSV file")
    parser.add_argument("--no-headless", action="store_true", help="Show browser")

    args = parser.parse_args()

    # Get queries
    queries = []
    if args.query:
        queries.append(args.query)
    if args.queries:
        with open(args.queries) as f:
            queries.extend([line.strip() for line in f if line.strip() and not line.startswith("#")])

    if not queries:
        print("❌ Please provide a query or --queries file")
        return

    all_businesses = []

    for q in queries:
        businesses = scrape_gmaps(q, limit=args.limit, headless=not args.no_headless)

        # Audit if requested
        if args.audit:
            print(f"\n🔍 Auditing {len(businesses)} businesses...")
            for i, biz in enumerate(businesses[:10], 1):
                website = biz.get("website", "")
                if website:
                    print(f"  [{i}] {website[:50]}...")
                    audit = audit_business(website)
                    if audit:
                        biz["has_schema"] = audit["has_schema"]
                        biz["has_llm_txt"] = audit["has_llm_txt"]
                        biz["seo_score"] = audit["score"]
                    time.sleep(0.5)

        all_businesses.extend(businesses)

    # Print summary
    print(f"\n{'='*50}")
    print(f"🏆 RESULTS: {len(all_businesses)} businesses found")
    print(f"{'='*50}")

    for biz in all_businesses[:10]:
        print(f"\n  📌 {biz['name']}")
        if biz.get("website"):
            print(f"     🌐 {biz['website']}")
        if biz.get("phone"):
            print(f"     📞 {biz['phone']}")
        if biz.get("address"):
            print(f"     📍 {biz['address'][:60]}")
        if biz.get("email"):
            print(f"     📧 {biz['email']}")
        if biz.get("rating"):
            print(f"     ⭐ {biz['rating']} ({biz.get('reviews', '?')} reviews)")
        if biz.get("has_schema") is not None:
            schema_icon = "✅" if biz["has_schema"] else "❌"
            llm_icon = "✅" if biz.get("has_llm_txt") else "❌"
            print(f"     {schema_icon} Schema  {llm_icon} llm.txt  Score: {biz.get('seo_score', '?')}")

    # Save
    save_results(all_businesses, queries[0], args.export)


if __name__ == "__main__":
    main()
