#!/usr/bin/env python3
"""Lead Scout Agent — finds new leads from web sources and enriches existing ones.

Scources:
- Michelin Guide (restaurants)
- Tourism board directories
- Google search for hotels/restaurants
- Business directories (Bizi.si, GFR.si)

Run: python3 agents/lead_scout.py [--app menuboost|boostsuite] [--country si|hr|it]
"""

import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime

WORKSPACE = "/home/darko/.openclaw/workspace"
LEAD_DIR = os.path.join(WORKSPACE, "lead-gen")
REPORT_FILE = os.path.join(WORKSPACE, "agents/reports/lead-scout-report.txt")


def load_existing_leads():
    """Load all existing leads for deduplication."""
    existing = {"emails": set(), "names": set(), "websites": set()}

    for root, dirs, files in os.walk(LEAD_DIR):
        for filename in files:
            if not filename.endswith(".csv"):
                continue
            filepath = os.path.join(root, filename)
            try:
                with open(filepath) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("email"):
                            existing["emails"].add(row["email"].lower())
                        if row.get("name"):
                            existing["names"].add(row["name"].lower())
                        if row.get("website"):
                            existing["websites"].add(row["website"].lower())
            except Exception:
                pass

    return existing


def check_mx(domain):
    """Check if domain has MX records."""
    try:
        result = subprocess.run(
            ['dig', '+short', 'MX', domain],
            capture_output=True, text=True, timeout=5
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def verify_lead(lead):
    """Verify a lead has valid email."""
    email = lead.get("email", "")
    if not email or "@" not in email:
        return False
    domain = email.split("@")[1]
    return check_mx(domain)


def save_leads(leads, app="menuboost", source="scout"):
    """Save new leads to a timestamped CSV."""
    if not leads:
        return None

    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{source}-{timestamp}.csv"
    filepath = os.path.join(LEAD_DIR, app, filename)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "city", "region", "email", "website", "type", "source"])
        writer.writeheader()
        writer.writerows(leads)

    return filepath


def generate_report(new_leads, verified, rejected, source):
    """Generate scout report."""
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)

    report = []
    report.append(f"🔍 Lead Scout Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"   Source: {source}")
    report.append(f"   Found: {len(new_leads)} leads")
    report.append(f"   Verified: {verified}")
    report.append(f"   Rejected (dup/invalid): {rejected}")

    # Breakdown by type
    types = {}
    for lead in new_leads:
        t = lead.get("type", "unknown")
        types[t] = types.get(t, 0) + 1

    report.append("\n   By type:")
    for t, count in sorted(types.items()):
        report.append(f"     {t}: {count}")

    report_text = "\n".join(report)
    print(report_text)

    with open(REPORT_FILE, "w") as f:
        f.write(report_text)

    return report_text


if __name__ == "__main__":
    print("🔍 Lead Scout Agent")
    print("   This agent is a framework — actual scraping is done by")
    print("   specialized scripts in lead-gen/menuboost/scrape_*.py")
    print()
    print("   Run the hotel/restaurant scraper:")
    print("   python3 lead-gen/menuboost/scrape_si_hotels_restaurants.py")
    print()
    print("   Or trigger via cron for automated weekly runs.")
