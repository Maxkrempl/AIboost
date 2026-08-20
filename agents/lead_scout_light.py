#!/usr/bin/env python3
"""Lightweight Lead Scout — 1-2 searches per run, saves results to CSV.

Designed for heartbeat integration: quick, non-overwhelming, cumulative.

Usage:
    python3 agents/lead_scout_light.py --app menuboost --limit 2
    python3 agents/lead_scout_light.py --app boostsuite --limit 1
    python3 agents/lead_scout_light.py --app both --limit 1
"""

import csv
import json
import os
import re
import subprocess
import sys
import hashlib
from datetime import datetime
from urllib.parse import quote_plus

WORKSPACE = "/home/darko/.openclaw/workspace"
LEAD_DIR = os.path.join(WORKSPACE, "lead-gen")
STATE_FILE = os.path.join(WORKSPACE, "agents/lead-scout-state.json")
REPORT_DIR = os.path.join(WORKSPACE, "agents/reports")

# Search templates per app
SEARCH_QUERIES = {
    "menuboost": [
        # Slovenia
        '"turistična kmetija" email kontakt',
        '"gostilna" email naslov Slovenija',
        'site:bizi.si "gostinska dejavnost" email',
        'site:si.traisi.si "restavracija" kontakt',
        # Croatia
        '"restoran" email kontakt Istra',
        '"konoba" email adresa Hrvatska',
        'site:gastronaut.hr "restoran" email',
        'site:booking.com "hotel" "restoran" email Istria',
        # Italy
        '"ristorante" email contatto Trieste',
        '"trattoria" email contatto Friuli',
        'site:tripadvisor.it "ristorante" "contatti" Trieste',
        # Alps
        '"Gasthof" email kontakt Kärnten',
        '"Berghütte" email Tirol',
    ],
    "boostsuite": [
        'SEO agency email contact',
        '"SEO freelancer" email contact',
        'site:clutch.co "SEO agency" email',
        '"digital marketing agency" SEO services email',
        '"GEO optimization" agency contact',
        '"AI SEO" agency email',
        'site:upwork.com "SEO consultant" profile',
        '"link building" agency email contact',
    ],
}

# File to track which queries have been used
USED_QUERIES_FILE = os.path.join(WORKSPACE, "agents/used-queries.json")


def load_state():
    """Load scout state (last run, stats)."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_run": None, "total_found": 0, "total_verified": 0, "runs": 0}


def save_state(state):
    """Save scout state."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_used_queries():
    """Load list of already-used search queries."""
    if os.path.exists(USED_QUERIES_FILE):
        with open(USED_QUERIES_FILE) as f:
            return json.load(f)
    return []


def save_used_queries(used):
    """Save used queries list (keep last 50)."""
    with open(USED_QUERIES_FILE, "w") as f:
        json.dump(used[-50:], f, indent=2)


def load_existing_emails():
    """Load all existing lead emails for deduplication."""
    emails = set()
    for root, dirs, files in os.walk(LEAD_DIR):
        for filename in files:
            if not filename.endswith(".csv"):
                continue
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, newline="", errors="replace") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        email = (row.get("email") or "").strip().lower()
                        if email and "@" in email:
                            emails.add(email)
            except Exception:
                pass
    return emails


def web_search(query, count=5):
    """Run web_search via openclaw CLI and return results."""
    # We'll use subprocess to call the openclaw web search
    # Actually, we output the query and let the calling agent do the search
    return query


def extract_emails_from_text(text):
    """Extract email addresses from text."""
    pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, text)))


def extract_leads_from_search(query, search_results, existing_emails):
    """Parse search results into leads."""
    leads = []
    
    if not search_results:
        return leads
    
    for result in search_results:
        title = result.get("title", "")
        url = result.get("url", "")
        snippet = result.get("snippet", "")
        
        # Extract emails from snippet
        emails = extract_emails_from_text(snippet)
        
        # Also try to extract from title
        emails.extend(extract_emails_from_text(title))
        
        for email in emails:
            email = email.lower().strip()
            if email in existing_emails:
                continue
            if any(x in email for x in ["example.com", "test.com", "sentry.io", "wixpress.com", "w3.org"]):
                continue
            
            lead = {
                "name": title[:80],
                "city": "",
                "region": "",
                "email": email,
                "website": url,
                "type": "restaurant" if "menuboost" in query.lower() or "restoran" in query.lower() or "gostilna" in query.lower() or "restaurant" in query.lower() else "agency",
                "source": f"web-search:{query[:50]}",
            }
            leads.append(lead)
            existing_emails.add(email)  # Dedup within this run
    
    return leads


def save_leads(leads, app, source="scout-light"):
    """Save leads to CSV."""
    if not leads:
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    filename = f"{source}-{timestamp}.csv"
    filepath = os.path.join(LEAD_DIR, app, filename)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    fieldnames = ["name", "city", "region", "email", "website", "type", "source"]
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads)
    
    return filepath


def pick_next_queries(app, limit, used_queries):
    """Pick unused queries for this run."""
    all_queries = SEARCH_QUERIES.get(app, [])
    available = [q for q in all_queries if q not in used_queries]
    
    if not available:
        # Reset — all queries used, start over
        available = all_queries
    
    # Pick up to `limit` queries
    return available[:limit]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Lightweight Lead Scout")
    parser.add_argument("--app", choices=["menuboost", "boostsuite", "both"], default="menuboost")
    parser.add_argument("--limit", type=int, default=2, help="Max searches per run (1-2)")
    parser.add_argument("--dry-run", action="store_true", help="Print queries without searching")
    args = parser.parse_args()
    
    args.limit = min(args.limit, 2)  # Hard cap at 2
    
    state = load_state()
    used_queries = load_used_queries()
    existing_emails = load_existing_emails()
    
    apps = ["menuboost", "boostsuite"] if args.app == "both" else [args.app]
    
    results = []
    remaining = args.limit
    
    for app in apps:
        if remaining <= 0:
            break
        queries = pick_next_queries(app, remaining, used_queries)
        remaining -= len(queries)
        
        for query in queries:
            used_queries.append(query)
            results.append({
                "app": app,
                "query": query,
                "action": "search" if not args.dry_run else "dry-run",
            })
    
    # Save state
    state["last_run"] = datetime.now().isoformat()
    state["runs"] += 1
    save_state(state)
    save_used_queries(used_queries)
    
    # Output for the calling agent
    output = {
        "status": "ready",
        "queries": results,
        "existing_leads_count": len(existing_emails),
        "runs_completed": state["runs"],
    }
    
    print(json.dumps(output, indent=2))
    
    return results


if __name__ == "__main__":
    main()
