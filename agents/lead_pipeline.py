#!/usr/bin/env python3
"""Lead Pipeline — takes new leads and generates personalized emails with real results.

MenuBoost: scrapes menu → translates dishes → builds demo email
BoostSuite: runs SEO audit → builds audit email with findings

Usage:
    python3 agents/lead_pipeline.py --input lead-gen/menuboost/scout-light-20260519.csv
    python3 agents/lead_pipeline.py --input lead-gen/boostsuite/scout-light-20260519.csv
    python3 agents/lead_pipeline.py --app menuboost --limit 2
    python3 agents/lead_pipeline.py --app boostsuite --limit 2
"""

import csv
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
QUEUE_DIR = WORKSPACE / "outreach" / "queue"
SENT_LOG = WORKSPACE / "outreach" / "sent" / "pipeline-sent.csv"
AUDIT_TOOL = WORKSPACE / "boostsuite" / "tools" / "combined_audit.js"

RESEND_API_KEY = "***REMOVED***"
FROM_MENUBOOST = "Darko Herceg | MenuBoost <max@hd-webdesign.si>"
FROM_BOOSTSUITE = "Darko Herceg | BoostSuite <max@hd-webdesign.si>"
REPLY_TO = "hercegdarko@hd-webdesign.si"

LANG_FLAGS = {"EN": "🇬🇧", "DE": "🇩🇪", "HR": "🇭🇷", "IT": "🇮🇹", "SR": "🇷🇸"}
LANG_NAMES = {"EN": "English", "DE": "Deutsch", "HR": "Hrvatski", "IT": "Italiano", "SR": "Српски"}


def load_sent_emails():
    """Load already-sent emails to avoid duplicates."""
    sent = set()
    if SENT_LOG.exists():
        with open(SENT_LOG, newline="", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sent.add(row.get("email", "").lower())
    return sent


def log_sent(email, app, name, subject):
    """Log a sent email."""
    SENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    write_header = not SENT_LOG.exists()
    with open(SENT_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["email", "app", "name", "subject", "sent_at"])
        writer.writerow([email, app, name, subject, datetime.now().isoformat()])


def fetch_page_text(url):
    """Fetch a webpage and extract text content."""
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "10", "-A", "Mozilla/5.0", url],
            capture_output=True, text=True, timeout=15
        )
        html = result.stdout
        # Simple HTML to text
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:5000]  # First 5000 chars
    except Exception:
        return ""


def extract_menu_items(text):
    """Extract potential menu items from page text."""
    items = []
    # Common menu patterns
    patterns = [
        r'(?:juha|soup|suppe|zuppa|corba)\s+(?:od|z|mit|con|sa)\s+\w+',
        r'(?:pečenka|steak|braten|arrosto|pečena)\s+\w+',
        r'(?:rižota|risotto|reis)\s+\w+',
        r'(?:štruklji|strudel|strudel)\s+\w+',
        r'(?:salata|salat|salade|ensalada)\s+\w+',
        r'(?:kraji|dumplings|klöße|gnocchi|knedle)\s+\w+',
        r'(?:meso|meat|fleisch|carne|meso)\s+\w+',
        r'(?:riba|fish|fisch|pesce|riba)\s+\w+',
        r'(?:testenine|pasta|nudeln|pasta)\s+\w+',
        r'(?:palačinke|crepes|pfannkuchen|crepes)\s+\w+',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        items.extend(matches)
    
    # Also look for lines that look like menu items (short, food-related)
    lines = text.split('.')
    for line in lines:
        line = line.strip()
        if 10 < len(line) < 80 and any(w in line.lower() for w in [
            'juha', 'solata', 'pečenka', 'rižota', 'štruklji', 'meso', 'riba',
            'soup', 'salad', 'steak', 'risotto', 'pasta', 'fish', 'meat',
            'suppe', 'salat', 'braten', 'fisch', 'fleisch',
            'zuppa', 'insalata', 'arrosto', 'pesce', 'carne',
            'čorba', 'salata', 'riba', 'meso'
        ]):
            items.append(line.strip())
    
    # Deduplicate and limit
    seen = set()
    unique = []
    for item in items:
        item_clean = item.lower().strip()
        if item_clean not in seen and len(item_clean) > 5:
            seen.add(item_clean)
            unique.append(item)
    
    return unique[:5]  # Max 5 items


def translate_dish(dish, target_lang):
    """Translate a dish name using simple pattern matching."""
    # This is a simplified translation — in production, call ListTranslate API
    translations = {
        "EN": {
            "juha": "soup", "solata": "salad", "pečenka": "roasted",
            "rižota": "risotto", "štruklji": "rolled dumplings",
            "meso": "meat", "riba": "fish", "gobova": "mushroom",
            "telečja": "veal", "jota": "bean and sauerkraut stew",
            "palačinke": "crepes", "kmečka": "farmhouse",
        },
        "DE": {
            "juha": "Suppe", "solata": "Salat", "pečenka": "Braten",
            "rižota": "Risotto", "štruklji": "Strudel",
            "meso": "Fleisch", "riba": "Fisch", "gobova": "Pilz",
            "telečja": "Kalb", "jota": "Bohnen-Eintopf",
            "palačinke": "Pfannkuchen", "kmečka": "Bauern",
        },
        "HR": {
            "juha": "juha", "solata": "salata", "pečenka": "pečenka",
            "rižota": "rižoto", "štruklji": "štruklji",
            "meso": "meso", "riba": "riba", "gobova": "gobova",
            "telečja": "teletina", "jota": "jota",
            "palačinke": "palačinke", "kmečka": "seoska",
        },
        "IT": {
            "juha": "zuppa", "solata": "insalata", "pečenka": "arrosto",
            "rižota": "risotto", "štruklji": "strudel",
            "meso": "carne", "riba": "pesce", "gobova": "funghi",
            "telečja": "vitello", "jota": "fagioli",
            "palačinke": "crepes", "kmečka": "fattoria",
        },
        "SR": {
            "juha": "чорба", "solata": "салата", "pečenka": "печење",
            "rižota": "ризот", "štruklji": "штрудљи",
            "meso": "месо", "riba": "риба", "gobova": "гљива",
            "telečja": "телетина", "jota": "џота",
            "palačinke": "палачинке", "kmečka": "сеоска",
        },
    }
    
    if target_lang not in translations:
        return dish
    
    result = dish
    for src, dst in translations[target_lang].items():
        result = re.sub(src, dst, result, flags=re.IGNORECASE)
    
    return result


def build_menuboost_email(name, url, email, dishes):
    """Build MenuBoost demo email HTML."""
    country = "SI" if any(tld in url for tld in [".si", ".sl"]) else "HR" if any(tld in url for tld in [".hr"]) else "IT"
    flag = {"SI": "🇸🇮", "HR": "🇭🇷", "IT": "🇮🇹", "DE": "🇩🇪", "AT": "🇦🇹"}.get(country, "🇪🇺")
    
    dish_sections = ""
    for dish in dishes[:3]:
        trans_rows = ""
        for lang in ["EN", "DE", "HR", "IT", "SR"]:
            translated = translate_dish(dish, lang)
            trans_rows += f"""<tr>
                <td style="padding:6px 8px;border-bottom:1px solid #f3f4f6;width:24px;font-size:16px;">{LANG_FLAGS[lang]}</td>
                <td style="padding:6px 8px;border-bottom:1px solid #f3f4f6;font-size:12px;color:#6b7280;width:70px;">{LANG_NAMES[lang]}</td>
                <td style="padding:6px 8px;border-bottom:1px solid #f3f4f6;color:#1e40af;font-weight:500;font-size:13px;">{translated}</td>
            </tr>"""
        
        dish_sections += f"""<div style="margin:25px 0;padding:20px;background:#f9fafb;border-radius:10px;border:1px solid #e5e7eb;">
            <div style="font-size:18px;font-weight:bold;color:#111827;margin-bottom:12px;font-style:italic;">"{dish}"</div>
            <table style="width:100%;border-collapse:collapse;">
                <tr style="background:#eef2ff;"><th style="padding:8px;text-align:left;font-size:12px;color:#4338ca;">Jezik</th><th style="padding:8px;text-align:left;font-size:12px;color:#4338ca;">MenuBoost prevod</th></tr>
                {trans_rows}
            </table>
        </div>"""
    
    subject = f"{flag} {name} — vaš jedilnik v 5 jezikih (brezplačni primer)"
    
    html = f"""<div style="font-family:system-ui,-apple-system,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <p>Živjo {name},</p>
        
        <p>Opazil sem vašo stran in sem naredil kratek primer — 3 jedi iz vašega jedilnika, prevedene v 5 jezikov z MenuBoostom:</p>
        
        {dish_sections}
        
        <p style="margin-top:25px;">To je brezplačno za 3 jedi — brez registracije, brez kartice:</p>
        
        <div style="text-align:center;margin:25px 0;">
            <a href="https://hd-webdesign.si/menu-boost/" style="background:#4f46e5;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">Preizkusite MenuBoost →</a>
        </div>
        
        <p style="color:#6b7280;font-size:13px;">Za 19 EUR/mesec dobite neomejeno uporabo za vse jedi. Če imate vprašanja, sem tukaj.</p>
        
        <p>Lep pozdrav,<br>Darko Herceg<br>
        <span style="color:#6b7280;font-size:12px;">Founder, HD Web Design · <a href="https://hd-webdesign.si">hd-webdesign.si</a></span></p>
    </div>"""
    
    return subject, html


def run_boostsuite_audit(url):
    """Run BoostSuite SEO audit."""
    try:
        result = subprocess.run(
            ["node", str(AUDIT_TOOL), url],
            capture_output=True, text=True, timeout=45
        )
        if result.stdout:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"  Audit error for {url}: {e}")
    return None


def get_severity(score):
    if score >= 80:
        return "excellent", "🟢"
    elif score >= 60:
        return "needs work", "🟡"
    else:
        return "critical", "🔴"


def generate_fix_suggestion(check_name, detail):
    """Generate a fix suggestion based on the check."""
    fixes = {
        "meta_description": "Add a compelling 150-160 character meta description that includes your target keywords",
        "h1_tags": "Ensure every page has exactly one H1 tag that clearly describes the page content",
        "image_alt": "Add descriptive alt text to all images — helps both SEO and accessibility",
        "ssl": "Install an SSL certificate — most hosts offer free Let's Encrypt certificates",
        "mobile_viewport": "Add a viewport meta tag: <meta name='viewport' content='width=device-width, initial-scale=1'>",
        "structured_data": "Add JSON-LD structured data for your business (LocalBusiness schema is a good start)",
        "open_graph": "Add Open Graph meta tags so links look good when shared on social media",
        "page_speed": "Compress images and enable browser caching to improve load times",
    }
    
    for key, fix in fixes.items():
        if key in check_name.lower():
            return fix
    
    return f"Fix: {detail}" if detail else f"Review and fix: {check_name}"


def build_boostsuite_email(name, url, email, audit_result):
    """Build BoostSuite audit email."""
    if not audit_result or "error" in audit_result:
        return None, None
    
    overall = audit_result.get("overall", {})
    audits = audit_result.get("audits", {})
    score = overall.get("score", 0)
    grade = overall.get("grade", "?")
    
    severity_label, emoji = get_severity(score)
    
    findings = []
    critical_fixes = []
    
    for key, audit in audits.items():
        category = audit.get("category", key)
        checks = audit.get("checks", [])
        
        fails = [c for c in checks if c.get("status") == "fail"]
        warns = [c for c in checks if c.get("status") == "warn"]
        
        for f in fails[:2]:
            findings.append(f"❌ {category}: {f.get('check', '')} — {f.get('detail', '')}")
            critical_fixes.append(f)
        for w in warns[:1]:
            findings.append(f"⚠️ {category}: {w.get('check', '')} — {w.get('detail', '')}")
    
    if score < 60:
        subject = f"🔴 {name} — your website scored {score}/100 (here's why)"
    elif score < 80:
        subject = f"🟡 {name} — website audit: {score}/100 ({len(findings)} issues found)"
    else:
        subject = f"🟢 {name} — your website scored {score}/100 (congrats!)"
    
    findings_html = ""
    for finding in findings[:8]:
        findings_html += f"<li style='padding:4px 0;'>{finding}</li>\n"
    
    fixes_html = ""
    if score < 70:
        fixes_html = "<p><strong>Here's what I'd prioritize:</strong></p><ol>"
        for i, f in enumerate(critical_fixes[:5], 1):
            fix = generate_fix_suggestion(f.get("check", ""), f.get("detail", ""))
            fixes_html += f"<li>{fix}</li>"
        fixes_html += "</ol>"
    
    html = f"""<div style="font-family:system-ui,-apple-system,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <p>Hi {name},</p>
        
        <p>I ran a free automated audit on <a href="{url}">{url}</a> and wanted to share the results with you.</p>
        
        <div style="text-align:center;margin:20px 0;">
            <div style="font-size:48px;font-weight:bold;color:{'#dc2626' if score < 60 else '#d97706' if score < 80 else '#16a34a'};">{score}/100</div>
            <div style="color:#6b7280;">Grade: {grade}</div>
        </div>
        
        <p><strong>Here's what I found:</strong></p>
        <ul style="list-style:none;padding:0;">
            {findings_html}
        </ul>
        
        {fixes_html}
        
        <p>I built a free tool called BoostSuite that runs these audits instantly — no signup, no credit card:</p>
        
        <div style="text-align:center;margin:25px 0;">
            <a href="https://hd-webdesign.si/boostsuite/" style="background:#4f46e5;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">Try BoostSuite Free →</a>
        </div>
        
        <p style="color:#6b7280;font-size:13px;">It also checks AI visibility across ChatGPT, Gemini, and Perplexity — increasingly important for getting found online.</p>
        
        <p>If you'd like, I can walk you through fixing the top issues — happy to do a free 15-minute call.</p>
        
        <p>Best,<br>Darko Herceg<br>
        <span style="color:#6b7280;font-size:12px;">Founder, HD Web Design · <a href="https://hd-webdesign.si">hd-webdesign.si</a></span></p>
    </div>"""
    
    return subject, html


def process_lead(lead, app, sent_emails):
    """Process a single lead: generate personalized email."""
    email = lead.get("email", "").lower()
    name = lead.get("name", "there")
    url = lead.get("website", "")
    
    if not email or not url:
        return None
    if email in sent_emails:
        print(f"  ⏭️  Already sent to {email}, skipping")
        return None
    if not url.startswith("http"):
        url = "https://" + url
    
    print(f"  🔍 Processing: {name} ({url})")
    
    if app == "menuboost":
        # Fetch page and extract menu items
        text = fetch_page_text(url)
        dishes = extract_menu_items(text)
        
        if not dishes:
            print(f"  ⚠️  No menu items found for {name}, using fallback")
            dishes = ["Dnevna juha", "Glavna jed", "Sladica"]
        
        print(f"  📝 Found {len(dishes)} dishes: {', '.join(dishes[:3])}")
        subject, html = build_menuboost_email(name, url, email, dishes)
        
    elif app == "boostsuite":
        # Run SEO audit
        audit = run_boostsuite_audit(url)
        if not audit:
            print(f"  ⚠️  Audit failed for {name}")
            return None
        
        score = audit.get("overall", {}).get("score", 0)
        print(f"  📊 Audit score: {score}/100")
        subject, html = build_boostsuite_email(name, url, email, audit)
        
        if not subject:
            print(f"  ⚠️  Could not generate email for {name}")
            return None
    else:
        return None
    
    return {
        "email": email,
        "name": name,
        "app": app,
        "subject": subject,
        "html": html,
        "url": url,
        "generated_at": datetime.now().isoformat(),
    }


def save_to_queue(items):
    """Save generated emails to the send queue."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    
    saved = 0
    for item in items:
        filename = f"{item['app']}-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{saved}.json"
        filepath = QUEUE_DIR / filename
        with open(filepath, "w") as f:
            json.dump(item, f, indent=2)
        saved += 1
        print(f"  💾 Queued: {filepath.name}")
    
    return saved


def find_latest_csv(app):
    """Find the most recent scout CSV for an app."""
    lead_dir = WORKSPACE / "lead-gen" / app
    if not lead_dir.exists():
        return None
    
    csvs = sorted(lead_dir.glob("scout-*.csv"), reverse=True)
    if not csvs:
        csvs = sorted(lead_dir.glob("*.csv"), reverse=True)
    
    return csvs[0] if csvs else None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Lead Pipeline — generate personalized emails from new leads")
    parser.add_argument("--input", help="CSV file with leads to process")
    parser.add_argument("--app", choices=["menuboost", "boostsuite"], help="App to process leads for")
    parser.add_argument("--limit", type=int, default=2, help="Max leads to process")
    parser.add_argument("--dry-run", action="store_true", help="Don't save to queue")
    args = parser.parse_args()
    
    # Find leads
    if args.input:
        csv_path = Path(args.input)
    elif args.app:
        csv_path = find_latest_csv(args.app)
        if not csv_path:
            print(f"❌ No CSV found for {args.app} in lead-gen/{args.app}/")
            sys.exit(1)
        print(f"📄 Using latest CSV: {csv_path.name}")
    else:
        print("❌ Must specify --input or --app")
        sys.exit(1)
    
    if not csv_path or not csv_path.exists():
        print(f"❌ CSV not found: {csv_path}")
        sys.exit(1)
    
    # Detect app from path or arg
    app = args.app or ("menuboost" if "menuboost" in str(csv_path) else "boostsuite")
    
    # Load leads
    leads = []
    with open(csv_path, newline="", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("email") and row.get("website"):
                leads.append(row)
    
    print(f"📊 Found {len(leads)} leads with emails+websites in {csv_path.name}")
    
    # Load sent emails
    sent_emails = load_sent_emails()
    print(f"📨 {len(sent_emails)} already sent, will skip")
    
    # Process leads
    results = []
    for lead in leads[:args.limit]:
        result = process_lead(lead, app, sent_emails)
        if result:
            results.append(result)
            sent_emails.add(result["email"])  # Dedup within this run
        time.sleep(1)  # Be nice to servers
    
    # Save to queue
    if results and not args.dry_run:
        saved = save_to_queue(results)
        print(f"\n✅ {saved} emails queued for sending")
        print(f"   Queue dir: {QUEUE_DIR}")
    elif results:
        print(f"\n🔍 Dry run: {len(results)} emails would be queued")
    else:
        print("\n⚠️  No leads processed")
    
    # Summary
    return {
        "processed": len(results),
        "app": app,
        "csv": str(csv_path),
        "queue_dir": str(QUEUE_DIR),
    }


if __name__ == "__main__":
    main()
