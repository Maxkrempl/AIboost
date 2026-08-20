#!/usr/bin/env python3
"""Stealth Scraper — invisible scraping that avoids detection.

Two modes:
  1. Firecrawl (cloud) — reliable, handles anti-bot, costs credits
  2. Local stealth (undetected-playwright) — free, fingerprint rotation

Usage:
    # Firecrawl scrape (recommended for most sites)
    python3 scrapers/stealth_scraper.py firecrawl "https://example.com"

    # Local stealth scrape (free, undetected)
    python3 scrapers/stealth_scraper.py stealth "https://example.com"

    # Search + scrape (find and extract)
    python3 scrapers/stealth_scraper.py search "restavracija email kontakt"

    # Auto mode: tries Firecrawl first, falls back to stealth
    python3 scrapers/stealth_scraper.py auto "https://example.com"

    # Site audit: check schema.org, llm.txt, robots.txt, sitemap
    python3 scrapers/stealth_scraper.py audit "https://example.com"

    # Batch URLs from file (with optional audit)
    python3 scrapers/stealth_scraper.py batch urls.txt --mode auto --audit
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
from pathlib import Path
from urllib.parse import quote_plus, urlparse

WORKSPACE = "/home/darko/.openclaw/workspace"
OUTPUT_DIR = os.path.join(WORKSPACE, "scrapers/output")
FIRECRAWL_CACHE = os.path.join(WORKSPACE, ".firecrawl")

# Browser fingerprints for rotation
FINGERPRINTS = [
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "locale": "sl-SI",
        "timezone": "Europe/Ljubljana",
    },
    {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1440, "height": 900},
        "locale": "en-US",
        "timezone": "America/New_York",
    },
    {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
        "viewport": {"width": 1366, "height": 768},
        "locale": "de-DE",
        "timezone": "Europe/Berlin",
    },
    {
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 2560, "height": 1440},
        "locale": "hr-HR",
        "timezone": "Europe/Zagreb",
    },
    {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
        "viewport": {"width": 1280, "height": 800},
        "locale": "en-GB",
        "timezone": "Europe/London",
    },
]


def get_random_fingerprint():
    """Get a random browser fingerprint."""
    return random.choice(FINGERPRINTS)


def ensure_output_dir():
    """Create output directory if needed."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(FIRECRAWL_CACHE, exist_ok=True)


def extract_emails(text):
    """Extract email addresses from text."""
    pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    # Filter junk
    junk = ["example.com", "test.com", "sentry.io", "wixpress.com",
            "w3.org", "schema.org", "googleapis.com", "cloudflare.com"]
    return [e for e in set(emails) if not any(j in e for j in junk)]


# =============================================================================
# SITE AUDIT — schema.org, llm.txt, robots.txt, sitemap
# =============================================================================

def check_url(url, timeout=10):
    """Quick HEAD/GET check if a URL exists. Returns (status_code, content_type)."""
    try:
        import httpx
        r = httpx.head(url, timeout=timeout, follow_redirects=True,
                       headers={"User-Agent": "Mozilla/5.0 (compatible; StealthScraper/1.0)"})
        return r.status_code, r.headers.get("content-type", "")
    except Exception:
        try:
            r = httpx.get(url, timeout=timeout, follow_redirects=True, max_redirects=3,
                          headers={"User-Agent": "Mozilla/5.0 (compatible; StealthScraper/1.0)"})
            return r.status_code, r.headers.get("content-type", "")
        except Exception:
            return 0, ""


def fetch_text(url, timeout=10):
    """Fetch URL and return text content."""
    try:
        import httpx
        r = httpx.get(url, timeout=timeout, follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0 (compatible; StealthScraper/1.0)"})
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return None


def check_schema_org(html_content):
    """Check for schema.org structured data in HTML."""
    results = {
        "has_json_ld": False,
        "json_ld_types": [],
        "has_microdata": False,
        "microdata_types": [],
        "raw_schemas": [],
    }

    if not html_content:
        return results

    # Check JSON-LD
    json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    json_ld_matches = re.findall(json_ld_pattern, html_content, re.DOTALL | re.IGNORECASE)

    if json_ld_matches:
        results["has_json_ld"] = True
        for match in json_ld_matches:
            try:
                data = json.loads(match.strip())
                if isinstance(data, list):
                    for item in data:
                        if "@type" in item:
                            results["json_ld_types"].append(item["@type"])
                            results["raw_schemas"].append(item)
                elif isinstance(data, dict):
                    if "@type" in data:
                        results["json_ld_types"].append(data["@type"])
                        results["raw_schemas"].append(data)
                    # Check @graph
                    if "@graph" in data:
                        for item in data["@graph"]:
                            if "@type" in item:
                                results["json_ld_types"].append(item["@type"])
                                results["raw_schemas"].append(item)
            except json.JSONDecodeError:
                pass

    # Check Microdata
    microdata_pattern = r'itemtype=["\']([^"\']+)["\']'
    microdata_matches = re.findall(microdata_pattern, html_content, re.IGNORECASE)
    if microdata_matches:
        results["has_microdata"] = True
        results["microdata_types"] = list(set(microdata_matches))

    # Deduplicate
    results["json_ld_types"] = list(set(str(t) for t in results["json_ld_types"]))
    results["microdata_types"] = list(set(results["microdata_types"]))

    return results


def check_robots_txt(base_url):
    """Check robots.txt for sitemap and rules."""
    url = base_url.rstrip("/") + "/robots.txt"
    content = fetch_text(url)

    result = {
        "exists": content is not None,
        "url": url,
        "sitemaps": [],
        "has_user_agent": False,
        "allows_ai_crawlers": None,
    }

    if content:
        result["has_user_agent"] = bool(re.search(r'user-agent', content, re.IGNORECASE))
        sitemap_matches = re.findall(r'Sitemap:\s*(\S+)', content, re.IGNORECASE)
        result["sitemaps"] = sitemap_matches

        # Check if AI crawlers are allowed
        ai_bots = ["GPTBot", "ChatGPT-User", "Google-Extended", "ClaudeBot", "anthropic-ai"]
        for bot in ai_bots:
            if re.search(rf'(disallow.*{bot}|user-agent:\s*{bot})', content, re.IGNORECASE):
                result["allows_ai_crawlers"] = False
                break
            if re.search(rf'(allow.*{bot}|user-agent:\s*\*)', content, re.IGNORECASE):
                result["allows_ai_crawlers"] = True

    return result


def check_llm_txt(base_url):
    """Check for llm.txt and .well-known/llm.txt."""
    checks = [
        ("/llm.txt", "llm.txt"),
        ("/.well-known/llm.txt", ".well-known/llm.txt"),
        ("/llms.txt", "llms.txt"),
        ("/.well-known/llms.txt", ".well-known/llms.txt"),
    ]

    results = {
        "found": False,
        "files": {},
    }

    for path, name in checks:
        url = base_url.rstrip("/") + path
        content = fetch_text(url)
        if content and len(content.strip()) > 10:
            results["found"] = True
            results["files"][name] = {
                "url": url,
                "length": len(content),
                "preview": content[:500],
            }

    return results


def check_sitemap(base_url, robots_sitemaps=None):
    """Check sitemap.xml."""
    sitemap_urls = []

    # From robots.txt
    if robots_sitemaps:
        sitemap_urls.extend(robots_sitemaps)

    # Default locations
    default_paths = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"]
    for path in default_paths:
        url = base_url.rstrip("/") + path
        if url not in sitemap_urls:
            sitemap_urls.append(url)

    results = {
        "exists": False,
        "urls": [],
        "url_count": 0,
    }

    for url in sitemap_urls[:3]:  # Check max 3
        content = fetch_text(url)
        if content and ("<urlset" in content.lower() or "<sitemapindex" in content.lower()):
            results["exists"] = True
            results["urls"].append(url)
            # Count URLs
            url_count = len(re.findall(r'<loc>', content, re.IGNORECASE))
            results["url_count"] += url_count
            break

    return results


def check_seo_basics(html_content):
    """Check basic SEO elements."""
    results = {
        "has_title": False,
        "title": "",
        "has_meta_description": False,
        "meta_description": "",
        "has_og_tags": False,
        "og_tags": {},
        "has_canonical": False,
        "canonical": "",
        "has_h1": False,
        "h1_count": 0,
        "has_viewport_meta": False,
    }

    if not html_content:
        return results

    # Title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.DOTALL | re.IGNORECASE)
    if title_match:
        results["has_title"] = True
        results["title"] = title_match.group(1).strip()[:100]

    # Meta description
    desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
    if not desc_match:
        desc_match = re.search(r'<meta[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']description["\']', html_content, re.IGNORECASE)
    if desc_match:
        results["has_meta_description"] = True
        results["meta_description"] = desc_match.group(1).strip()[:200]

    # Open Graph
    og_pattern = r'<meta[^>]*property=["\']og:(\w+)["\'][^>]*content=["\']([^"\']*)["\']'
    og_matches = re.findall(og_pattern, html_content, re.IGNORECASE)
    if og_matches:
        results["has_og_tags"] = True
        results["og_tags"] = {k: v for k, v in og_matches}

    # Canonical
    canonical_match = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
    if canonical_match:
        results["has_canonical"] = True
        results["canonical"] = canonical_match.group(1)

    # H1
    h1_count = len(re.findall(r'<h1[\s>]', html_content, re.IGNORECASE))
    results["has_h1"] = h1_count > 0
    results["h1_count"] = h1_count

    # Viewport
    results["has_viewport_meta"] = bool(re.search(r'<meta[^>]*name=["\']viewport["\']', html_content, re.IGNORECASE))

    return results


def check_json_files(html_content, base_url):
    """Find and analyze JSON files on the site."""
    results = {
        "found_files": [],
        "json_ld": [],
        "manifest": None,
        "package_json": None,
        "api_endpoints": [],
        "other_json": [],
        "total_size": 0,
    }

    if not html_content:
        return results

    # 1. Find JSON files linked in HTML
    # script src="*.json"
    script_json = re.findall(r'<script[^>]*src=["\']([^"\']*\.json[^"\']*)["\']', html_content, re.IGNORECASE)
    # link href="*.json"
    link_json = re.findall(r'<link[^>]*href=["\']([^"\']*\.json[^"\']*)["\']', html_content, re.IGNORECASE)
    # a href="*.json"
    a_json = re.findall(r'<a[^>]*href=["\']([^"\']*\.json[^"\']*)["\']', html_content, re.IGNORECASE)
    # Any other src/href with .json
    all_json_refs = re.findall(r'(?:src|href|url)=["\']([^"\']*/[^"\']*/[^"\']*\.json[^"\']*)["\']', html_content, re.IGNORECASE)

    json_urls_raw = set(script_json + link_json + a_json + all_json_refs)

    # 2. Check common well-known JSON files
    common_json = [
        "/manifest.json",
        "/site.webmanifest",
        "/.well-known/assetlinks.json",
        "/.well-known/apple-app-site-association",
        "/package.json",
        "/_next/data/",
        "/wp-json/",
        "/api/",
        "/feed.json",
        "/atom.json",
    ]

    # 3. Find JSON-LD (already in schema but let's get raw)
    json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    json_ld_matches = re.findall(json_ld_pattern, html_content, re.DOTALL | re.IGNORECASE)
    for match in json_ld_matches:
        try:
            data = json.loads(match.strip())
            results["json_ld"].append(data)
        except json.JSONDecodeError:
            pass

    # 4. Find API-like patterns in HTML
    api_patterns = re.findall(r'["\']/(api|v[0-9]|graphql|rest)/[^"\']*["\']', html_content, re.IGNORECASE)
    results["api_endpoints"] = list(set(api_patterns))

    # 5. Fetch and analyze found JSON files
    checked = set()

    for json_url in json_urls_raw:
        # Normalize URL
        if json_url.startswith("//"):
            json_url = "https:" + json_url
        elif json_url.startswith("/"):
            json_url = base_url + json_url
        elif not json_url.startswith("http"):
            json_url = base_url + "/" + json_url

        if json_url in checked:
            continue
        checked.add(json_url)

        try:
            import httpx
            r = httpx.get(json_url, timeout=8, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; StealthScraper/1.0)"})
            if r.status_code == 200:
                content_type = r.headers.get("content-type", "")
                if "json" in content_type or r.text.strip().startswith(("{", "[")):
                    try:
                        data = json.loads(r.text)
                        size = len(r.text)
                        results["total_size"] += size

                        file_info = {
                            "url": json_url,
                            "size": size,
                            "type": type(data).__name__,
                            "keys": list(data.keys())[:20] if isinstance(data, dict) else None,
                            "length": len(data) if isinstance(data, list) else None,
                        }

                        # Categorize
                        if "manifest" in json_url.lower() or "webmanifest" in json_url.lower():
                            results["manifest"] = file_info
                        elif "package" in json_url.lower():
                            results["package_json"] = file_info
                        else:
                            results["other_json"].append(file_info)

                        results["found_files"].append(json_url)
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass

    # 6. Check common paths
    for path in common_json:
        if path.startswith("/"):
            check_url = base_url.rstrip("/") + path
        else:
            continue

        if check_url in checked:
            continue
        checked.add(check_url)

        try:
            import httpx
            r = httpx.get(check_url, timeout=5, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; StealthScraper/1.0)"})
            if r.status_code == 200:
                content_type = r.headers.get("content-type", "")
                if "json" in content_type or r.text.strip().startswith(("{", "[")):
                    try:
                        data = json.loads(r.text)
                        size = len(r.text)
                        results["total_size"] += size

                        file_info = {
                            "url": check_url,
                            "size": size,
                            "type": type(data).__name__,
                            "keys": list(data.keys())[:20] if isinstance(data, dict) else None,
                            "length": len(data) if isinstance(data, list) else None,
                        }

                        if "manifest" in path.lower():
                            results["manifest"] = file_info
                        elif "package" in path.lower():
                            results["package_json"] = file_info
                        elif "wp-json" in path.lower():
                            results["api_endpoints"].append("wp-json")
                        elif "/api/" in path.lower():
                            results["api_endpoints"].append(path)
                        else:
                            results["other_json"].append(file_info)

                        results["found_files"].append(check_url)
                    except json.JSONDecodeError:
                        pass
        except Exception:
            pass

    results["found_files"] = list(set(results["found_files"]))
    results["api_endpoints"] = list(set(results["api_endpoints"]))

    return results


def audit_site(url):
    """Full site audit: schema.org, llm.txt, robots.txt, sitemap, SEO basics."""
    # Normalize URL
    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    print(f"🔍 Auditing: {base_url}")
    print("=" * 50)

    # Fetch main page HTML
    html_content = fetch_text(url)

    # Run all checks
    schema = check_schema_org(html_content)
    robots = check_robots_txt(base_url)
    llm = check_llm_txt(base_url)
    sitemap = check_sitemap(base_url, robots.get("sitemaps", []))
    seo = check_seo_basics(html_content)
    json_files = check_json_files(html_content, base_url)

    # Build report
    report = {
        "url": base_url,
        "timestamp": datetime.now().isoformat(),
        "schema_org": schema,
        "robots_txt": robots,
        "llm_txt": llm,
        "sitemap": sitemap,
        "seo_basics": seo,
        "json_files": json_files,
        "emails": extract_emails(html_content) if html_content else [],
    }

    # Print summary
    print(f"\n📊 AUDIT RESULTS: {base_url}")
    print("=" * 50)

    # Schema.org
    print(f"\n🏗️  Schema.org:")
    if schema["has_json_ld"]:
        print(f"  ✅ JSON-LD: {', '.join(schema['json_ld_types'])}")
    else:
        print(f"  ❌ No JSON-LD structured data")
    if schema["has_microdata"]:
        print(f"  ✅ Microdata: {', '.join(schema['microdata_types'][:5])}")
    else:
        print(f"  ❌ No Microdata")

    # llm.txt
    print(f"\n🤖 llm.txt:")
    if llm["found"]:
        for name, info in llm["files"].items():
            print(f"  ✅ {name} ({info['length']} bytes)")
    else:
        print(f"  ❌ No llm.txt found")

    # robots.txt
    print(f"\n🤖 robots.txt:")
    if robots["exists"]:
        print(f"  ✅ Exists")
        if robots["sitemaps"]:
            print(f"  📍 Sitemaps: {len(robots['sitemaps'])}")
        if robots["allows_ai_crawlers"] is False:
            print(f"  ⚠️  AI crawlers BLOCKED")
        elif robots["allows_ai_crawlers"] is True:
            print(f"  ✅ AI crawlers allowed")
    else:
        print(f"  ❌ No robots.txt")

    # Sitemap
    print(f"\n🗺️  Sitemap:")
    if sitemap["exists"]:
        print(f"  ✅ Found ({sitemap['url_count']} URLs)")
    else:
        print(f"  ❌ No sitemap found")

    # SEO basics
    print(f"\n📈 SEO Basics:")
    print(f"  {'✅' if seo['has_title'] else '❌'} Title: {seo['title'][:60] if seo['title'] else 'MISSING'}")
    print(f"  {'✅' if seo['has_meta_description'] else '❌'} Meta Description: {'OK' if seo['has_meta_description'] else 'MISSING'}")
    print(f"  {'✅' if seo['has_og_tags'] else '❌'} Open Graph: {len(seo['og_tags'])} tags")
    print(f"  {'✅' if seo['has_canonical'] else '❌'} Canonical: {'OK' if seo['has_canonical'] else 'MISSING'}")
    print(f"  {'✅' if seo['has_h1'] else '❌'} H1: {seo['h1_count']} found")
    print(f"  {'✅' if seo['has_viewport_meta'] else '❌'} Viewport Meta")

    # JSON Files
    print(f"\n📄 JSON Files:")
    if json_files["found_files"]:
        print(f"  ✅ Found {len(json_files['found_files'])} JSON files ({json_files['total_size']:,} bytes total)")
        for f in json_files["found_files"][:10]:
            print(f"    📎 {f}")
    else:
        print(f"  ❌ No JSON files found")

    if json_files["json_ld"]:
        print(f"  📋 JSON-LD: {len(json_files['json_ld'])} blocks")

    if json_files["manifest"]:
        print(f"  📱 Manifest: {json_files['manifest']['url']}")
        if json_files["manifest"].get("keys"):
            print(f"     Keys: {', '.join(json_files['manifest']['keys'][:10])}")

    if json_files["package_json"]:
        print(f"  📦 package.json: {json_files['package_json']['url']}")
        if json_files["package_json"].get("keys"):
            print(f"     Keys: {', '.join(json_files['package_json']['keys'][:10])}")

    if json_files["api_endpoints"]:
        print(f"  🔌 API endpoints: {', '.join(json_files['api_endpoints'][:5])}")

    if json_files["other_json"]:
        print(f"  📁 Other JSON: {len(json_files['other_json'])} files")
        for f in json_files["other_json"][:5]:
            print(f"    📎 {f['url']} ({f['size']:,} bytes, {f['type']})")

    # Emails
    if report["emails"]:
        print(f"\n📧 Emails found: {', '.join(report['emails'])}")

    # Save report
    slug = parsed.netloc.replace(".", "-")
    report_path = os.path.join(OUTPUT_DIR, f"audit-{slug}-{int(time.time())}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Report saved: {report_path}")

    return report


# =============================================================================
# SCRAPING MODES
# =============================================================================

def firecrawl_scrape(url, output_path=None, wait_for=3000, query=None):
    """Scrape a URL using Firecrawl (cloud-based, anti-bot)."""
    cmd = ["firecrawl", "scrape", url, "--wait-for", str(wait_for)]

    if query:
        cmd.extend(["--query", query])

    if output_path:
        cmd.extend(["-o", output_path])
    else:
        slug = urlparse(url).netloc.replace(".", "-")
        output_path = os.path.join(OUTPUT_DIR, f"{slug}-{int(time.time())}.md")
        cmd.extend(["-o", output_path])

    cmd.extend(["--format", "markdown"])

    print(f"🔥 Firecrawl scraping: {url}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"❌ Firecrawl error: {result.stderr}")
        return None

    if os.path.exists(output_path):
        with open(output_path) as f:
            content = f.read()
        emails = extract_emails(content)
        return {
            "url": url,
            "content": content,
            "emails": emails,
            "output_path": output_path,
            "method": "firecrawl",
        }

    return None


def firecrawl_search(query, limit=10, scrape=True):
    """Search using Firecrawl and optionally scrape results."""
    output_path = os.path.join(OUTPUT_DIR, f"search-{int(time.time())}.json")
    cmd = ["firecrawl", "search", query, "--limit", str(limit), "--json", "-o", output_path]

    if scrape:
        cmd.append("--scrape")

    print(f"🔍 Firecrawl searching: {query}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"❌ Firecrawl search error: {result.stderr}")
        return None

    if os.path.exists(output_path):
        with open(output_path) as f:
            data = json.load(f)

        all_emails = []
        if "data" in data:
            for item in data["data"].get("web", []):
                content = item.get("markdown", "") or item.get("content", "")
                emails = extract_emails(content)
                for email in emails:
                    all_emails.append({
                        "email": email,
                        "url": item.get("url", ""),
                        "title": item.get("title", ""),
                    })

        return {
            "query": query,
            "results": data,
            "emails_found": all_emails,
            "output_path": output_path,
            "method": "firecrawl-search",
        }

    return None


def stealth_scrape(url, output_path=None, headless=True):
    """Scrape using local undetected-playwright (free, stealth)."""
    try:
        from playwright.sync_api import sync_playwright
        from undetected_playwright import stealth_sync
    except ImportError:
        print("❌ undetected-playwright not installed. Run: pip install undetected-playwright")
        return None

    fp = get_random_fingerprint()

    if not output_path:
        slug = urlparse(url).netloc.replace(".", "-")
        output_path = os.path.join(OUTPUT_DIR, f"{slug}-stealth-{int(time.time())}.md")

    print(f"🥷 Stealth scraping: {url}")
    print(f"   Fingerprint: {fp['locale']} / {fp['timezone']}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--no-sandbox",
                ],
            )

            context = browser.new_context(
                user_agent=fp["user_agent"],
                viewport=fp["viewport"],
                locale=fp["locale"],
                timezone_id=fp["timezone"],
                java_script_enabled=True,
                ignore_https_errors=True,
            )

            page = context.new_page()
            stealth_sync(page)

            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(1.5, 3.5))

            page.mouse.wheel(0, random.randint(100, 400))
            time.sleep(random.uniform(0.5, 1.5))

            content = page.content()

            try:
                main = page.query_selector("main, article, .content, #content, .main")
                if main:
                    content = main.inner_text()
            except Exception:
                content = page.inner_text("body")

            browser.close()

            with open(output_path, "w") as f:
                f.write(content)

            emails = extract_emails(content)

            return {
                "url": url,
                "content": content,
                "emails": emails,
                "output_path": output_path,
                "method": "stealth-playwright",
                "fingerprint": fp["locale"],
            }

    except Exception as e:
        print(f"❌ Stealth error: {e}")
        return None


def stealth_search(query, limit=5):
    """Search Google with stealth browser and extract results."""
    try:
        from playwright.sync_api import sync_playwright
        from undetected_playwright import stealth_sync
    except ImportError:
        print("❌ undetected-playwright not installed")
        return None

    fp = get_random_fingerprint()
    search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={limit}"

    print(f"🥷 Stealth searching: {query}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )

            context = browser.new_context(
                user_agent=fp["user_agent"],
                viewport=fp["viewport"],
                locale=fp["locale"],
                timezone_id=fp["timezone"],
            )

            page = context.new_page()
            stealth_sync(page)

            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(2, 4))

            results = []
            for el in page.query_selector_all("div.g"):
                try:
                    title_el = el.query_selector("h3")
                    link_el = el.query_selector("a")
                    snippet_el = el.query_selector(".VwiC3b, .st, .s")

                    if title_el and link_el:
                        results.append({
                            "title": title_el.inner_text(),
                            "url": link_el.get_attribute("href"),
                            "snippet": snippet_el.inner_text() if snippet_el else "",
                        })
                except Exception:
                    continue

            browser.close()

            all_emails = []
            for r in results:
                text = f"{r['title']} {r['snippet']}"
                emails = extract_emails(text)
                for email in emails:
                    all_emails.append({
                        "email": email,
                        "url": r["url"],
                        "title": r["title"],
                    })

            return {
                "query": query,
                "results": results,
                "emails_found": all_emails,
                "method": "stealth-search",
            }

    except Exception as e:
        print(f"❌ Stealth search error: {e}")
        return None


def auto_scrape(url, output_path=None):
    """Try Firecrawl first, fall back to stealth if it fails."""
    result = firecrawl_scrape(url, output_path)
    if result:
        return result

    print("⚠️ Firecrawl failed, trying stealth mode...")
    return stealth_scrape(url, output_path)


def batch_scrape(urls_file, mode="auto", do_audit=False):
    """Scrape multiple URLs from a file."""
    with open(urls_file) as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    results = []
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] {url}")

        if mode == "firecrawl":
            result = firecrawl_scrape(url)
        elif mode == "stealth":
            result = stealth_scrape(url)
        else:
            result = auto_scrape(url)

        if result:
            # Run audit if requested
            if do_audit:
                print(f"  🔍 Running audit...")
                audit = audit_site(url)
                result["audit"] = audit

            results.append(result)
            print(f"  ✅ Found {len(result['emails'])} emails")
        else:
            print(f"  ❌ Failed")

        if i < len(urls):
            delay = random.uniform(2, 5)
            print(f"  ⏳ Waiting {delay:.1f}s...")
            time.sleep(delay)

    return results


def save_results(results, prefix="scrape"):
    """Save all results to a summary file."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    output_file = os.path.join(OUTPUT_DIR, f"{prefix}-results-{timestamp}.json")

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_urls": len(results),
        "total_emails": sum(len(r.get("emails", [])) for r in results),
        "results": [],
    }

    for r in results:
        entry = {
            "url": r.get("url", ""),
            "method": r.get("method", ""),
            "emails": r.get("emails", []),
            "output_path": r.get("output_path", ""),
        }
        if "audit" in r:
            entry["audit"] = r["audit"]
        summary["results"].append(entry)

    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n📊 Summary saved: {output_file}")
    print(f"   URLs scraped: {summary['total_urls']}")
    print(f"   Emails found: {summary['total_emails']}")

    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Stealth Scraper — invisible scraping with site audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s firecrawl "https://example.com"           # Cloud scrape
  %(prog)s stealth "https://example.com"              # Local stealth
  %(prog)s search "restavracija email kontakt"        # Search + extract
  %(prog)s auto "https://example.com"                 # Auto (firecrawl → stealth)
  %(prog)s audit "https://example.com"                # Full site audit
  %(prog)s batch urls.txt --mode auto --audit         # Batch with audit
        """,
    )

    parser.add_argument(
        "mode",
        choices=["firecrawl", "stealth", "search", "auto", "audit", "batch"],
        help="Scraping mode",
    )
    parser.add_argument("target", help="URL to scrape, search query, or urls file (for batch)")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--mode", dest="fallback_mode", default="auto",
                        help="Fallback mode for batch: auto, firecrawl, stealth")
    parser.add_argument("--query", "-q", help="Query for firecrawl scrape")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Result limit for search")
    parser.add_argument("--audit", action="store_true",
                        help="Also run site audit (schema.org, llm.txt, etc.)")
    parser.add_argument("--headless", action="store_true", default=True,
                        help="Run browser in headless mode (default: True)")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window")

    args = parser.parse_args()
    ensure_output_dir()

    headless = not args.no_headless

    if args.mode == "firecrawl":
        result = firecrawl_scrape(args.target, args.output, query=args.query)
        if result:
            print(f"\n✅ Found {len(result['emails'])} emails")
            for email in result["emails"]:
                print(f"  📧 {email}")
            if args.audit:
                audit_site(args.target)

    elif args.mode == "stealth":
        result = stealth_scrape(args.target, args.output, headless=headless)
        if result:
            print(f"\n✅ Found {len(result['emails'])} emails")
            for email in result["emails"]:
                print(f"  📧 {email}")
            if args.audit:
                audit_site(args.target)

    elif args.mode == "search":
        result = firecrawl_search(args.target, limit=args.limit)
        if not result:
            result = stealth_search(args.target, limit=args.limit)

        if result:
            print(f"\n✅ Found {len(result['emails_found'])} emails")
            for item in result["emails_found"]:
                print(f"  📧 {item['email']} ({item['url'][:50]}...)")

    elif args.mode == "audit":
        audit_site(args.target)

    elif args.mode == "auto":
        result = auto_scrape(args.target, args.output)
        if result:
            print(f"\n✅ Found {len(result['emails'])} emails via {result['method']}")
            for email in result["emails"]:
                print(f"  📧 {email}")
            if args.audit:
                audit_site(args.target)

    elif args.mode == "batch":
        results = batch_scrape(args.target, mode=args.fallback_mode, do_audit=args.audit)
        if results:
            save_results(results, prefix="batch")


if __name__ == "__main__":
    main()
