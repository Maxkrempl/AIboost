#!/usr/bin/env python3
"""BoostSuite lead gen via web search + email extraction."""

import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import os
import re
from datetime import datetime

OUTPUT_DIR = "/home/darko/.openclaw/workspace/lead-gen/boostsuite"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "boostsuite-leads.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def extract_emails(text):
    """Extract email addresses from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, text)))

def is_target_email(email):
    """Filter out generic/robot emails."""
    skip = ['noreply', 'no-reply', 'support@google', 'support@facebook', 'help@',
            'security@', 'admin@google', 'webmaster@google', 'postmaster@',
            'abuse@', 'contact@trustpilot', '.png', '.jpg', '.gif', 'wixpress',
            'sentry.io', 'example.com', 'test.com', 'squarespace', 'wix.com',
            'godaddy', 'wordpress', 'shopify']
    email_lower = email.lower()
    return not any(s in email_lower for s in skip)

def get_website_emails(url, timeout=10):
    """Visit a website and extract email addresses."""
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        emails = extract_emails(resp.text)
        # Also check contact page
        soup = BeautifulSoup(resp.text, 'html.parser')
        for link in soup.select('a[href*="contact"], a[href*="about"]'):
            try:
                href = link.get('href', '')
                if href.startswith('/'):
                    from urllib.parse import urljoin
                    href = urljoin(url, href)
                if href.startswith('http'):
                    sub_resp = requests.get(href, headers=HEADERS, timeout=8)
                    emails.extend(extract_emails(sub_resp.text))
            except:
                pass
        return list(set([e for e in emails if is_target_email(e)]))
    except:
        return []

# Target searches - small agencies and freelancers
SEARCH_QUERIES = [
    # English-speaking markets
    "seo freelancer contact email",
    "small seo agency contact",
    "digital marketing freelancer email",
    "seo consultant contact email",
    "seo expert website contact",
    # European markets
    "seo agentur kontakt email",
    "seo freiberufler email",
    "agence seo contact email",
    "freelance seo email",
    "consulente seo contatto email",
    # Niche
    "local seo agency small business",
    "ecommerce seo freelancer",
    "wordpress seo consultant",
    "shopify seo expert",
]

def search_and_extract(query, max_sites=10):
    """Search for sites and extract emails."""
    leads = []
    try:
        # Use DuckDuckGo HTML search
        url = f"https://html.duckduckgo.com/html/?q={query}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        results = soup.select('.result__a, .result__url, a.result__a')
        sites = []
        for r in results[:max_sites]:
            href = r.get('href', '')
            if href.startswith('http') and 'duckduckgo' not in href and 'google' not in href:
                sites.append(href)
        
        for site in sites:
            print(f"    🌐 {site[:60]}...")
            emails = get_website_emails(site)
            for email in emails:
                leads.append({
                    "name": email.split('@')[0].replace('.', ' ').title(),
                    "email": email,
                    "website": site,
                    "location": "",
                    "source": f"search:{query[:30]}",
                    "type": "agency"
                })
            time.sleep(random.uniform(2, 4))
    except Exception as e:
        print(f"    ❌ Search error: {e}")
    return leads

def main():
    all_leads = []
    
    for query in SEARCH_QUERIES:
        print(f"\n🔍 Searching: {query}")
        leads = search_and_extract(query, max_sites=8)
        all_leads.extend(leads)
        print(f"  ✅ Found {len(leads)} emails")
        time.sleep(random.uniform(3, 5))
    
    # Load existing leads
    existing_emails = set()
    existing_leads = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_emails.add(row.get('email', '').lower())
                existing_leads.append(row)
    
    # Merge with new leads
    new_count = 0
    for lead in all_leads:
        if lead['email'].lower() not in existing_emails:
            existing_leads.append(lead)
            existing_emails.add(lead['email'].lower())
            new_count += 1
    
    # Save
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'email', 'website', 'location', 'source', 'type'])
        writer.writeheader()
        writer.writerows(existing_leads)
    
    print(f"\n📊 RESULTS:")
    print(f"  New leads: {new_count}")
    print(f"  Total leads: {len(existing_leads)}")
    print(f"  With email: {len([l for l in existing_leads if l.get('email')])}")
    print(f"  Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
