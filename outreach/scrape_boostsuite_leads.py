#!/usr/bin/env python3
"""Scrape SEO/digital marketing freelancer and small agency leads for BoostSuite."""

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

# Sources to scrape
SOURCES = [
    # Clutch.co - SEO agencies directory
    {"url": "https://clutch.co/agencies/seo?agency_size=1-10&page={page}", "name": "clutch-seo-small", "pages": 5},
    {"url": "https://clutch.co/agencies/digital-marketing?agency_size=1-10&page={page}", "name": "clutch-digital-small", "pages": 5},
    # Sortlist - European agencies
    {"url": "https://www.sortlist.com/marketing/agency?page={page}", "name": "sortlist-marketing", "pages": 3},
    # GoodFirms
    {"url": "https://www.goodfirms.co/digital-marketing-agencies?page={page}", "name": "goodfirms-digital", "pages": 3},
    # Upwork SEO freelancers (directory pages)
    {"url": "https://www.upwork.com/freelance-jobs/seo/?page={page}", "name": "upwork-seo", "pages": 3},
]

def extract_emails(text):
    """Extract email addresses from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, text)))

def is_target_email(email):
    """Filter out generic/robot emails."""
    skip = ['noreply', 'no-reply', 'support@', 'help@', 'info@google', 'info@facebook',
            'security@', 'admin@', 'webmaster@', 'postmaster@', 'abuse@', 'contact@trustpilot',
            'noreply@clutch', 'noreply@goodfirms', 'noreply@sortlist']
    email_lower = email.lower()
    return not any(s in email_lower for s in skip)

def scrape_clutch(url, name, max_pages):
    """Scrape Clutch.co agency listings."""
    leads = []
    for page in range(1, max_pages + 1):
        try:
            page_url = url.format(page=page)
            print(f"  📄 Scraping {page_url}")
            resp = requests.get(page_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Find agency cards
            for card in soup.select('.company-info, .provider-info, [class*="company"]'):
                name_el = card.select_one('h3, h2, .company-name, [class*="name"]')
                agency_name = name_el.get_text(strip=True) if name_el else ""
                
                # Look for website link
                link = card.select_one('a[href*="http"]')
                website = link['href'] if link else ""
                
                # Look for location
                loc_el = card.select_one('[class*="location"], .locality')
                location = loc_el.get_text(strip=True) if loc_el else ""
                
                if agency_name:
                    leads.append({
                        "name": agency_name,
                        "email": "",  # Will be filled by visiting website
                        "website": website,
                        "location": location,
                        "source": name,
                        "type": "agency"
                    })
            
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"  ❌ Error on page {page}: {e}")
    return leads

def scrape_generic(url, name, max_pages):
    """Generic scraper that extracts any emails and links found."""
    leads = []
    for page in range(1, max_pages + 1):
        try:
            page_url = url.format(page=page)
            print(f"  📄 Scraping {page_url}")
            resp = requests.get(page_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Extract all emails from page
            emails = extract_emails(resp.text)
            for email in emails:
                if is_target_email(email):
                    leads.append({
                        "name": email.split('@')[0],
                        "email": email,
                        "website": "",
                        "location": "",
                        "source": name,
                        "type": "freelancer"
                    })
            
            # Extract links to individual profiles/pages
            for link in soup.select('a[href]'):
                href = link.get('href', '')
                if '/agency/' in href or '/freelancer/' in href or '/profile/' in href:
                    # Visit individual page for email
                    try:
                        if href.startswith('/'):
                            from urllib.parse import urljoin
                            href = urljoin(page_url, href)
                        time.sleep(random.uniform(1, 2))
                        sub_resp = requests.get(href, headers=HEADERS, timeout=10)
                        sub_emails = extract_emails(sub_resp.text)
                        for email in sub_emails:
                            if is_target_email(email):
                                leads.append({
                                    "name": link.get_text(strip=True)[:100],
                                    "email": email,
                                    "website": href,
                                    "location": "",
                                    "source": f"{name}-profile",
                                    "type": "freelancer"
                                })
                    except:
                        pass
            
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"  ❌ Error on page {page}: {e}")
    return leads

def get_website_email(url):
    """Visit a website and extract email addresses."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        emails = extract_emails(resp.text)
        return [e for e in emails if is_target_email(e)]
    except:
        return []

def main():
    all_leads = []
    
    for source in SOURCES:
        print(f"\n🔍 Processing: {source['name']}")
        
        if 'clutch' in source['name']:
            leads = scrape_clutch(source['url'], source['name'], source['pages'])
        else:
            leads = scrape_generic(source['url'], source['name'], source['pages'])
        
        all_leads.extend(leads)
        print(f"  ✅ Found {len(leads)} leads from {source['name']}")
    
    # Try to get emails for leads that have websites but no emails
    print(f"\n📧 Enriching {len([l for l in all_leads if l['website'] and not l['email']])} leads with website emails...")
    for lead in all_leads:
        if lead['website'] and not lead['email']:
            emails = get_website_email(lead['website'])
            if emails:
                lead['email'] = emails[0]
            time.sleep(random.uniform(1, 2))
    
    # Deduplicate by email
    seen_emails = set()
    unique_leads = []
    for lead in all_leads:
        email = lead['email'].lower().strip()
        if email and email not in seen_emails:
            seen_emails.add(email)
            unique_leads.append(lead)
        elif not email:
            unique_leads.append(lead)
    
    # Save to CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'email', 'website', 'location', 'source', 'type'])
        writer.writeheader()
        writer.writerows(unique_leads)
    
    print(f"\n📊 RESULTS:")
    print(f"  Total leads: {len(unique_leads)}")
    print(f"  With email: {len([l for l in unique_leads if l['email']])}")
    print(f"  Without email: {len([l for l in unique_leads if not l['email']])}")
    print(f"  Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
