#!/usr/bin/env python3
"""
Stealth scraper for MenuBoost leads.
Runs overnight with human-like delays to avoid bot detection.

Features:
- Rotating user agents
- Random delays (3-8 seconds between pages, 1-3 seconds between items)
- Session cookies
- Referer spoofing
- Exponential backoff on errors
- Incremental saves (won't lose progress if interrupted)
- Resumable state tracking

Usage:
  python3 tools/scraper_stealth.py              # Run all sources
  python3 tools/scraper_stealth.py --source italy    # Only Italy
  python3 tools/scraper_stealth.py --resume          # Resume from last run
  python3 tools/scraper_stealth.py --dry-run          # Test without saving
"""

import requests
import re
import csv
import json
import os
import sys
import time
import random
import signal
import argparse
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = "/home/darko/.openclaw/workspace/lead-gen/menuboost"
STATE_FILE = "/home/darko/.openclaw/workspace/tools/scraper_state.json"
LOG_FILE = "/home/darko/.openclaw/workspace/tools/scraper_log.txt"

# Delay ranges (seconds) — human-like browsing
DELAY_PAGE = (3, 8)      # Between fetching different pages
DELAY_ITEM = (1, 3)      # Between individual items on same site
DELAY_DOMAIN = (10, 20)  # Between switching to different domains
DELAY_ERROR = (5, 15)    # After an error
DELAY_RETRY_BASE = 2     # Exponential backoff base

MAX_RETRIES = 3
REQUEST_TIMEOUT = 20

# Rotating user agents (real browsers)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

# Italian referers to look more natural
REFERERS = [
    "https://www.google.it/",
    "https://www.google.com/",
    "https://www.google.hr/",
    "https://www.google.si/",
    "https://www.bing.com/",
    None,  # Sometimes no referer
]

# ============================================================
# SOURCES
# ============================================================

SOURCES = {
    "italy": [
        # Open Tourism — real restaurant listings with emails
        {"name": "OpenTourism Rimini", "type": "directory",
         "urls": [f"https://www.opentourism.it/it/servizi/ristorante?page={p}" for p in range(1, 4)],
         "region": "Emilia-Romagna", "country": "it"},
        # Accademia — individual restaurant pages have emails
        {"name": "Accademia Rimini", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=99&comune=&ragione-sociale="],
         "region": "Emilia-Romagna", "country": "it"},
        {"name": "Accademia Venezia", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=27&comune=&ragione-sociale="],
         "region": "Veneto", "country": "it"},
        {"name": "Accademia Udine", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=30&comune=&ragione-sociale="],
         "region": "Friuli-Venezia Giulia", "country": "it"},
        {"name": "Accademia Pisa", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=50&comune=&ragione-sociale="],
         "region": "Toscana", "country": "it"},
        {"name": "Accademia Roma", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=58&comune=&ragione-sociale="],
         "region": "Lazio", "country": "it"},
        {"name": "Accademia Napoli", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=63&comune=&ragione-sociale="],
         "region": "Campania", "country": "it"},
        {"name": "Accademia Bari", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=72&comune=&ragione-sociale="],
         "region": "Puglia", "country": "it"},
        {"name": "Accademia Palermo", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=82&comune=&ragione-sociale="],
         "region": "Sicily", "country": "it"},
        {"name": "Accademia Cagliari", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=92&comune=&ragione-sociale="],
         "region": "Sardegna", "country": "it"},
        # Additional Italian Accademia provinces
        {"name": "Accademia Firenze", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=48&comune=&ragione-sociale="],
         "region": "Toscana", "country": "it"},
        {"name": "Accademia Bologna", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=37&comune=&ragione-sociale="],
         "region": "Emilia-Romagna", "country": "it"},
        {"name": "Accademia Milano", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=15&comune=&ragione-sociale="],
         "region": "Lombardia", "country": "it"},
        {"name": "Accademia Torino", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=96&comune=&ragione-sociale="],
         "region": "Piemonte", "country": "it"},
        {"name": "Accademia Genova", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=54&comune=&ragione-sociale="],
         "region": "Liguria", "country": "it"},
        {"name": "Accademia Catania", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=87&comune=&ragione-sociale="],
         "region": "Sicily", "country": "it"},
        {"name": "Accademia Brescia", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=17&comune=&ragione-sociale="],
         "region": "Lombardia", "country": "it"},
        {"name": "Accademia Bergamo", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=16&comune=&ragione-sociale="],
         "region": "Lombardia", "country": "it"},
        {"name": "Accademia Verona", "type": "directory",
         "urls": ["https://www.accademiaitalianadellacucina.it/it/ristoranti?provincia=23&comune=&ragione-sociale="],
         "region": "Veneto", "country": "it"},
        # Italian restaurant directories
        {"name": "Tried and Tested Italy", "type": "directory",
         "urls": ["https://www.triedandtested.it/ristoranti-italia"],
         "region": "Italy", "country": "it"},
        {"name": "Wine-Searcher Restaurants Italy", "type": "directory",
         "urls": ["https://www.wine-searcher.com/restaurant-italy"],
         "region": "Italy", "country": "it"},
        {"name": "Restaurant Guru Italy", "type": "directory",
         "urls": ["https://restaurantguru.com/Italy"],
         "region": "Italy", "country": "it"},
    ],
    "croatia": [
        {"name": "Istra Gastro", "type": "directory",
         "urls": [f"https://www.istra.hr/en/gourmet/where-to-eat?page={p}" for p in range(1, 6)],
         "region": "Istra", "country": "hr"},
        {"name": "Split Restaurants", "type": "directory",
         "urls": [f"https://www.visitsplit.com/en/56/restaurants?page={p}" for p in range(1, 6)],
         "region": "Split-Dalmatia", "country": "hr"},
        {"name": "Dubrovnik Restaurants", "type": "directory",
         "urls": [f"https://www.visitdubrovnik.hr/restaurants?page={p}" for p in range(1, 6)],
         "region": "Dubrovnik-Neretva", "country": "hr"},
        {"name": "Zadar Gastronomy", "type": "directory",
         "urls": [f"https://www.zadar.travel/en/gastronomy?page={p}" for p in range(1, 6)],
         "region": "Zadar", "country": "hr"},
        {"name": "Kvarner Gastro", "type": "directory",
         "urls": [f"https://www.kvarner.hr/en/gastro?page={p}" for p in range(1, 6)],
         "region": "Primorje-Gorski", "country": "hr"},
        # Additional Croatian tourism sites
        {"name": "Split-Dalmatia County Tourism", "type": "directory",
         "urls": ["https://www.dalmatia.hr/en/gastro"],
         "region": "Split-Dalmatia", "country": "hr"},
        {"name": "Rab Island Tourism", "type": "directory",
         "urls": ["https://www.rab-visit.com/en/restaurants"],
         "region": "Primorje-Gorski", "country": "hr"},
        {"name": "Pag Island Tourism", "type": "directory",
         "urls": ["https://www.pag-tourism.hr/en/gastronomy"],
         "region": "Zadar", "country": "hr"},
        {"name": "Makarska Tourism", "type": "directory",
         "urls": ["https://www.makarska.com/en/restaurants"],
         "region": "Split-Dalmatia", "country": "hr"},
        {"name": "Opatija Tourism", "type": "directory",
         "urls": ["https://www.opatija.com/en/gastronomy"],
         "region": "Primorje-Gorski", "country": "hr"},
    ],
    "slovenia": [
        {"name": "Visit Ljubljana Restaurants", "type": "directory",
         "urls": [f"https://www.visitljubljana.com/en/visitors/see-do/cuisine/restaurants/?page={p}" for p in range(1, 4)],
         "region": "Ljubljana", "country": "si"},
        {"name": "Slovenia Info Gastronomy", "type": "directory",
         "urls": ["https://www.slovenia.info/en/gastronomy", "https://www.slovenia.info/en/experiences/gastronomy"],
         "region": "Slovenia", "country": "si"},
        # Additional Slovenian directories
        {"name": "Gostilna.si Restaurant Directory", "type": "directory",
         "urls": ["https://www.gostilna.si/"],
         "region": "Slovenia", "country": "si"},
        {"name": "Restaurant Slovenia Directory", "type": "directory",
         "urls": ["https://www.restaurant.slovenia.si/"],
         "region": "Slovenia", "country": "si"},
    ],
}

# ============================================================
# LOGGING & STATE
# ============================================================

def log(msg):
    """Append to log file and print."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_state():
    """Load scraper state for resuming."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "completed_urls": [],
        "completed_sources": [],
        "contacts_found": 0,
        "started_at": None,
        "last_url": None
    }

def save_state(state):
    """Save scraper state."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def load_existing_emails():
    """Load all existing emails to avoid duplicates."""
    emails = set()
    for f in os.listdir(BASE_DIR):
        if f.endswith(".csv"):
            try:
                with open(os.path.join(BASE_DIR, f), encoding="utf-8", errors="replace") as fh:
                    reader = csv.DictReader(fh)
                    for row in reader:
                        for key in ["email", "Email"]:
                            if key in row and row[key]:
                                emails.add(row[key].strip().lower())
            except: pass
    
    # Also check sent
    sent_dir = "/home/darko/.openclaw/workspace/outreach/sent"
    if os.path.exists(sent_dir):
        for f in os.listdir(sent_dir):
            if f.endswith(".csv"):
                try:
                    with open(os.path.join(sent_dir, f), encoding="utf-8", errors="replace") as fh:
                        for line in fh:
                            parts = line.strip().split(",")
                            if len(parts) >= 3:
                                email = parts[2].strip().lower()
                                if "@" in email:
                                    emails.add(email)
                except: pass
    
    return emails

# ============================================================
# HTTP HELPERS
# ============================================================

class StealthSession:
    """HTTP session with human-like behavior."""
    
    def __init__(self):
        self.session = requests.Session()
        self.request_count = 0
        self.last_domain = None
    
    def _get_headers(self, url):
        """Generate realistic headers."""
        domain = urlparse(url).netloc
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": random.choice([
                "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "en-US,en;q=0.9,it;q=0.8",
                "hr-HR,hr;q=0.9,en;q=0.8",
                "sl-SI,sl;q=0.9,en;q=0.8",
            ]),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": random.choice(["none", "same-origin", "cross-site"]),
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        
        # Add referer
        referer = random.choice(REFERERS)
        if referer:
            headers["Referer"] = referer
        
        # Add DNT sometimes
        if random.random() > 0.5:
            headers["DNT"] = "1"
        
        return headers
    
    def _smart_delay(self, url, is_error=False):
        """Wait with appropriate delay based on context."""
        domain = urlparse(url).netloc
        
        if is_error:
            delay = random.uniform(*DELAY_ERROR)
        elif domain != self.last_domain and self.last_domain is not None:
            delay = random.uniform(*DELAY_DOMAIN)
        elif self.request_count % 10 == 0:
            # Every 10 requests, take a longer break (like a human pausing)
            delay = random.uniform(15, 30)
            log(f"  ☕ Taking a coffee break ({delay:.0f}s)...")
        else:
            delay = random.uniform(*DELAY_PAGE)
        
        # Add small jitter
        delay += random.uniform(-0.5, 0.5)
        delay = max(1, delay)
        
        time.sleep(delay)
        self.last_domain = domain
        self.request_count += 1
    
    def get(self, url, retries=MAX_RETRIES):
        """GET with retries and smart delays."""
        for attempt in range(retries):
            try:
                self._smart_delay(url, is_error=(attempt > 0))
                
                headers = self._get_headers(url)
                resp = self.session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                
                if resp.status_code == 429:
                    # Rate limited — wait longer
                    wait = random.uniform(30, 60) * (attempt + 1)
                    log(f"  ⏳ Rate limited, waiting {wait:.0f}s...")
                    time.sleep(wait)
                    continue
                
                if resp.status_code == 403:
                    log(f"  🚫 Forbidden: {url}")
                    return None
                
                resp.raise_for_status()
                return resp.text
                
            except requests.exceptions.Timeout:
                log(f"  ⏱️ Timeout (attempt {attempt+1}/{retries}): {url}")
                time.sleep(DELAY_RETRY_BASE ** attempt + random.uniform(1, 5))
                
            except requests.exceptions.HTTPError as e:
                log(f"  ❌ HTTP {resp.status_code}: {url}")
                if resp.status_code in [404, 410]:
                    return None  # Don't retry 404s
                time.sleep(DELAY_RETRY_BASE ** attempt + random.uniform(1, 5))
                
            except Exception as e:
                log(f"  ❌ Error (attempt {attempt+1}/{retries}): {e}")
                time.sleep(DELAY_RETRY_BASE ** attempt + random.uniform(1, 5))
        
        return None

# ============================================================
# EMAIL EXTRACTION
# ============================================================

def extract_emails(text):
    """Extract emails from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    
    # Filter junk
    skip = ['noreply', 'no-reply', 'donotreply', 'mailer-daemon', 
            'abuse@', 'postmaster@', 'hostmaster@', 'webmaster@',
            'example.com', 'test.com', 'placeholder', 'email@',
            'your@', 'user@', 'name@', 'screenshot', '.png', '.jpg', '.gif']
    
    return list(set(
        e.lower() for e in emails 
        if not any(s in e.lower() for s in skip)
        and len(e) > 6
    ))

def extract_restaurant_name(html, url):
    """Try to extract restaurant name from page."""
    patterns = [
        r'<title>([^<]+)</title>',
        r'<h1[^>]*>([^<]+)</h1>',
        r'og:title"\s*content="([^"]+)"',
    ]
    for p in patterns:
        match = re.search(p, html, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up
            name = re.sub(r'\s*[-–|].*', '', name)  # Remove suffix
            name = name.strip()
            if len(name) > 3 and len(name) < 100:
                return name
    return ""

# ============================================================
# SCRAPING LOGIC
# ============================================================

def scrape_directory_page(session, url, source, existing_emails, dry_run=False):
    """Scrape a directory page for restaurant links and emails."""
    html = session.get(url)
    if not html:
        return []
    
    contacts = []
    emails_found = extract_emails(html)
    
    # Extract restaurant detail links
    detail_links = re.findall(r'href="(/it/ristoranti/[^"]+)"', html)
    detail_links += re.findall(r'href="(https?://[^"]*(?:restaurant|ristorante|konoba|trattoria)[^"]*)"', html, re.IGNORECASE)
    detail_links = list(set(detail_links))[:15]  # Limit per page
    
    # If emails found on directory page directly
    for email in emails_found:
        if email not in existing_emails:
            contact = {
                "name": extract_restaurant_name(html, url) or f"Restaurant ({source['region']})",
                "city": "",
                "region": source["region"],
                "email": email,
                "website": url,
                "type": "Ristorante",
                "source": source["name"],
                "country": source["country"]
            }
            contacts.append(contact)
            existing_emails.add(email)
            if not dry_run:
                log(f"  ✅ {contact['name']} → {email}")
    
    # Visit detail pages for more emails
    for link in detail_links[:8]:  # Max 8 detail pages per directory page
        if link.startswith("/"):
            full_url = urljoin(url, link)
        else:
            full_url = link
        
        detail_html = session.get(full_url)
        if not detail_html:
            continue
        
        detail_emails = extract_emails(detail_html)
        name = extract_restaurant_name(detail_html, full_url) or source["region"]
        
        for email in detail_emails:
            if email not in existing_emails and not any(c["email"] == email for c in contacts):
                contact = {
                    "name": name,
                    "city": "",
                    "region": source["region"],
                    "email": email,
                    "website": full_url,
                    "type": "Ristorante",
                    "source": source["name"],
                    "country": source["country"]
                }
                contacts.append(contact)
                existing_emails.add(email)
                if not dry_run:
                    log(f"  ✅ {name} → {email}")
        
        # Small delay between detail pages
        time.sleep(random.uniform(*DELAY_ITEM))
    
    return contacts

def save_contacts_incremental(contacts, source_name):
    """Save contacts to a source-specific CSV."""
    filename = source_name.lower().replace(" ", "-") + ".csv"
    filepath = os.path.join(BASE_DIR, f"scraped-{filename}")
    
    fieldnames = ["name", "city", "region", "email", "website", "type", "source", "country"]
    
    # Append mode — incremental saves
    file_exists = os.path.exists(filepath)
    
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for contact in contacts:
            row = {k: contact.get(k, "") for k in fieldnames}
            writer.writerow(row)

# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Stealth scraper for MenuBoost leads")
    parser.add_argument("--source", choices=["italy", "croatia", "slovenia", "all"], default="all")
    parser.add_argument("--resume", action="store_true", help="Resume from last run")
    parser.add_argument("--dry-run", action="store_true", help="Test without saving")
    parser.add_argument("--max-pages", type=int, default=100, help="Max pages to scrape")
    args = parser.parse_args()
    
    # Graceful shutdown
    def signal_handler(sig, frame):
        log("\n🛑 Interrupted! Saving state...")
        save_state(state)
        log(f"💾 State saved. Found {state['contacts_found']} contacts so far.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    log("=" * 50)
    log("🕵️ MenuBoost Stealth Scraper")
    log("=" * 50)
    
    # Load state
    state = load_state() if args.resume else {
        "completed_urls": [],
        "completed_sources": [],
        "contacts_found": 0,
        "started_at": datetime.now().isoformat(),
        "last_url": None
    }
    
    existing_emails = load_existing_emails()
    log(f"📋 {len(existing_emails)} existing emails loaded for dedup")
    
    session = StealthSession()
    total_contacts = []
    pages_scraped = 0
    
    # Select sources
    if args.source == "all":
        sources = SOURCES
    else:
        sources = {args.source: SOURCES.get(args.source, [])}
    
    for country, source_list in sources.items():
        log(f"\n{'=' * 40}")
        log(f"🌍 {country.upper()}")
        log(f"{'=' * 40}")
        
        for source in source_list:
            if source["name"] in state.get("completed_sources", []):
                log(f"  ⏭️ Skipping {source['name']} (already done)")
                continue
            
            log(f"\n📡 {source['name']} ({source['region']})")
            source_contacts = []
            
            for url in source["urls"]:
                if url in state.get("completed_urls", []):
                    log(f"  ⏭️ Skipping {url}")
                    continue
                
                if pages_scraped >= args.max_pages:
                    log(f"  🛑 Max pages ({args.max_pages}) reached")
                    break
                
                log(f"  🔍 {url[:80]}...")
                contacts = scrape_directory_page(session, url, source, existing_emails, args.dry_run)
                source_contacts.extend(contacts)
                pages_scraped += 1
                
                # Incremental save
                if contacts and not args.dry_run:
                    save_contacts_incremental(contacts, source["name"])
                
                # Update state
                state["completed_urls"].append(url)
                state["contacts_found"] += len(contacts)
                state["last_url"] = url
                save_state(state)
            
            if source_contacts:
                total_contacts.extend(source_contacts)
                log(f"  📊 {source['name']}: {len(source_contacts)} new contacts")
            
            state["completed_sources"].append(source["name"])
            save_state(state)
    
    # Final summary
    log(f"\n{'=' * 50}")
    log(f"🎉 SCRAPING COMPLETE")
    log(f"{'=' * 50}")
    log(f"  Pages scraped: {pages_scraped}")
    log(f"  New contacts: {len(total_contacts)}")
    log(f"  Total contacts found this run: {state['contacts_found']}")
    
    if not args.dry_run and total_contacts:
        # Also save a combined batch file
        combined_file = os.path.join(BASE_DIR, "scraped-combined-batch.csv")
        fieldnames = ["name", "city", "region", "email", "website", "type", "source", "country"]
        with open(combined_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for contact in total_contacts:
                row = {k: contact.get(k, "") for k in fieldnames}
                writer.writerow(row)
        log(f"  💾 Combined batch: {combined_file}")
    
    log(f"\n✅ Done at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
