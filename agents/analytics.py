#!/usr/bin/env python3
"""Analytics Agent — pulls metrics from all 4 SaaS apps and generates daily summary.

Currently reads from:
- Netlify deploy info (via file checks)
- Outreach tracking (sent/replied/bounced)
- Lead pipeline status
- Gumroad sales data (via Gumroad API)

Future: Netlify Analytics API

Run: python3 agents/analytics.py
"""

import csv
import json
import os
from datetime import datetime, timedelta
from collections import Counter

WORKSPACE = "/home/darko/.openclaw/workspace"


def count_sent_emails():
    """Count sent emails per app from sent CSVs."""
    sent_dir = os.path.join(WORKSPACE, "outreach/sent")
    results = {}

    if not os.path.exists(sent_dir):
        return results

    for filename in os.listdir(sent_dir):
        if not filename.endswith(".csv"):
            continue
        filepath = os.path.join(sent_dir, filename)
        try:
            with open(filepath) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                count = len(rows)
                # Determine app from filename
                if "menuboost" in filename.lower() or "sent.csv" in filename.lower():
                    app = "MenuBoost"
                elif "boostsuite" in filename.lower():
                    app = "BoostSuite"
                else:
                    app = "Other"

                if app not in results:
                    results[app] = {"sent": 0, "files": []}
                results[app]["sent"] += count
                results[app]["files"].append(filename)
        except Exception as e:
            print(f"  Error reading {filename}: {e}")

    return results


def count_leads():
    """Count leads in pipeline per app."""
    lead_dirs = [
        os.path.join(WORKSPACE, "lead-gen/menuBoost"),
        os.path.join(WORKSPACE, "lead-gen/menuboost"),
        os.path.join(WORKSPACE, "lead-gen/boostsuite"),
    ]

    results = {}

    for lead_dir in lead_dirs:
        if not os.path.exists(lead_dir):
            continue
        for filename in os.listdir(lead_dir):
            if not filename.endswith(".csv"):
                continue
            filepath = os.path.join(lead_dir, filename)
            try:
                with open(filepath) as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    count = len(rows)

                    if "menuboost" in lead_dir.lower() or "menuBoost" in lead_dir:
                        app = "MenuBoost"
                    elif "boostsuite" in lead_dir.lower():
                        app = "BoostSuite"
                    else:
                        app = "Other"

                    if app not in results:
                        results[app] = {"leads": 0, "files": []}
                    results[app]["leads"] += count
                    results[app]["files"].append(filename)
            except Exception:
                pass

    return results


def count_replies():
    """Count replies by sentiment."""
    state_file = os.path.join(WORKSPACE, "outreach/replies-state.json")
    if not os.path.exists(state_file):
        return {}

    with open(state_file) as f:
        state = json.load(f)

    replies = state.get("replies", [])
    sentiments = Counter(r.get("sentiment", "unknown") for r in replies)
    return dict(sentiments)


def count_suppression():
    """Count suppression list entries."""
    supp_file = os.path.join(WORKSPACE, "outreach/suppression.txt")
    if not os.path.exists(supp_file):
        return 0
    with open(supp_file) as f:
        return sum(1 for line in f if line.strip())


def get_recent_sent(days=7):
    """Count emails sent in last N days."""
    sent_dir = os.path.join(WORKSPACE, "outreach/sent")
    cutoff = datetime.now() - timedelta(days=days)
    recent = 0

    if not os.path.exists(sent_dir):
        return 0

    for filename in os.listdir(sent_dir):
        if not filename.endswith(".csv"):
            continue
        filepath = os.path.join(sent_dir, filename)
        try:
            with open(filepath) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sent_at = row.get("sent_at", row.get("timestamp", ""))
                    if sent_at:
                        try:
                            dt = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
                            if dt.replace(tzinfo=None) > cutoff:
                                recent += 1
                        except (ValueError, TypeError):
                            pass
        except Exception:
            pass

    return recent


def count_gumroad_sales():
    """Pull sales data from Gumroad API."""
    import subprocess
    token = os.environ.get("GUMROAD_TOKEN", "")
    if not token:
        # Try loading from credentials file
        creds = os.path.join(WORKSPACE, "agents/credentials.sh")
        if os.path.exists(creds):
            with open(creds) as f:
                for line in f:
                    if "GUMROAD_TOKEN" in line:
                        token = line.split('"')[1] if '"' in line else ""
                        break

    if not token:
        return {"error": "No Gumroad token found"}

    try:
        import urllib.request
        url = f"https://api.gumroad.com/v2/products?access_token={token}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        if not data.get("success"):
            return {"error": "API request failed"}

        products = []
        total_sales = 0
        total_revenue = 0.0

        # Only track MenuBoost and BoostSuite
        tracked = ["menuboost", "boostsuite"]

        for p in data.get("products", []):
            name = p["name"].strip()
            if not any(t in name.lower() for t in tracked):
                continue
            products.append({
                "name": p["name"].strip(),
                "price": p.get("formatted_price", "?"),
                "sales": p.get("sales_count", 0),
                "revenue_usd": p.get("sales_usd_cents", 0) / 100,
                "published": p.get("published", False),
                "url": p.get("short_url", "")
            })
            total_sales += p.get("sales_count", 0)
            total_revenue += p.get("sales_usd_cents", 0) / 100

        return {
            "products": products,
            "total_sales": total_sales,
            "total_revenue": total_revenue
        }
    except Exception as e:
        return {"error": str(e)}


def generate_report():
    """Generate full analytics report."""
    report = []
    report.append(f"📊 MenuBoost Daily Analytics — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("=" * 50)

    # Gumroad sales
    gumroad = count_gumroad_sales()
    report.append("\n💰 GUMROAD SALES")
    if gumroad.get("error"):
        report.append(f"  ⚠️ {gumroad['error']}")
    else:
        report.append(f"  Total sales: {gumroad['total_sales']}")
        report.append(f"  Total revenue: ${gumroad['total_revenue']:.2f}")
        for p in gumroad["products"]:
            report.append(f"  {p['name']}: {p['sales']} sales ({p['price']})")

    # Outreach stats
    sent = count_sent_emails()
    report.append("\n📧 OUTREACH")
    for app, data in sent.items():
        report.append(f"  {app}: {data['sent']} emails sent (from {len(data['files'])} files)")

    # Recent activity
    recent_7d = get_recent_sent(7)
    recent_1d = get_recent_sent(1)
    report.append(f"\n  Last 24h: {recent_1d} sent")
    report.append(f"  Last 7d: {recent_7d} sent")

    # Reply stats
    replies = count_replies()
    report.append(f"\n📩 REPLIES")
    total_replies = sum(replies.values())
    report.append(f"  Total: {total_replies}")
    for sentiment, count in sorted(replies.items()):
        emoji = {"positive": "🟢", "negative": "🔴", "bounce": "⚪", "neutral": "🟡"}.get(sentiment, "❓")
        report.append(f"  {emoji} {sentiment}: {count}")

    # Lead pipeline
    leads = count_leads()
    report.append(f"\n📋 LEAD PIPELINE")
    for app, data in leads.items():
        report.append(f"  {app}: {data['leads']} leads (from {len(data['files'])} files)")

    # Suppression
    suppressed = count_suppression()
    report.append(f"\n🚫 SUPPRESSION LIST: {blocked} entries" if (blocked := suppressed) else "")

    report_text = "\n".join(report)
    return report_text


if __name__ == "__main__":
    report = generate_report()
    print(report)

    # Save to file
    report_dir = os.path.join(WORKSPACE, "agents/reports")
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, f"analytics-{datetime.now().strftime('%Y-%m-%d')}.txt")
    with open(report_file, "w") as f:
        f.write(report)
    print(f"\n📁 Saved to {report_file}")
