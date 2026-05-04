#!/usr/bin/env python3
"""Scrape small SEO agency websites from Clutch and extract emails."""

import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import os
import re
from datetime import datetime
from urllib.parse import urljoin

OUTPUT_DIR = "/home/darko/.openclaw/workspace/lead-gen/boostsuite"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "boostsuite-leads.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Clutch pages to scrape
CLUTCH_PAGES = [
    "https://clutch.co/seo-firms/small-business",
    "https://clutch.co/seo-firms/small-business?page=1",
    "https://clutch.co/seo-firms/small-business?page=2",
    "https://clutch.co/agencies/seo?agency_size=1-10",
    "https://clutch.co/agencies/seo?agency_size=1-10&page=1",
    "https://clutch.co/agencies/digital-marketing?agency_size=1-10",
    "https://clutch.co/agencies/digital-marketing?agency_size=1-10&page=1",
]

def extract_emails(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, text)))

def is_target_email(email):
    skip = ['noreply', 'no-reply', 'support@google', 'help@', 'security@',
            'admin@google', 'webmaster@google', 'postmaster@', 'abuse@',
            '.png', '.jpg', '.gif', 'wixpress', 'sentry.io', 'example.com',
            'test.com', 'squarespace.com', 'wix.com', 'godaddy.com',
            'wordpress.com', 'shopify.com', 'clutch.co', 'google.com',
            'facebook.com', 'twitter.com', 'linkedin.com', 'youtube.com',
            'trustpilot', 'yelp.com', 'glassdoor']
    email_lower = email.lower()
    return not any(s in email_lower for s in skip)

def get_website_emails(url, timeout=10):
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        emails = extract_emails(resp.text)
        # Check contact/about pages
        soup = BeautifulSoup(resp.text, 'html.parser')
        contact_links = []
        for link in soup.select('a[href]'):
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            if any(word in text for word in ['contact', 'about', 'team', 'impressum']):
                if href.startswith('/'):
                    href = urljoin(url, href)
                if href.startswith('http'):
                    contact_links.append(href)
        
        for cl in contact_links[:2]:  # Max 2 sub-pages
            try:
                sub_resp = requests.get(cl, headers=HEADERS, timeout=8)
                emails.extend(extract_emails(sub_resp.text))
            except:
                pass
        return list(set([e for e in emails if is_target_email(e)]))
    except:
        return []

def scrape_clutch_page(url):
    """Scrape a Clutch listing page for agency names and websites."""
    agencies = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Try multiple selectors for agency cards
        cards = soup.select('.provider-info, .company-info, [class*="company-row"], [class*="provider"]')
        if not cards:
            cards = soup.select('li[class*="provider"], li[class*="company"], div[class*="directory"]')
        
        for card in cards:
            name = ""
            website = ""
            location = ""
            
            # Get name
            name_el = card.select_one('h3, h2, h4, [class*="company-name"], [class*="provider-name"], a[class*="company"]')
            if name_el:
                name = name_el.get_text(strip=True)
            
            # Get website - look for "Visit Website" link or similar
            for link in card.select('a[href]'):
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                if 'visit' in text or 'website' in text or 'view' in text:
                    if 'clutch' not in href:
                        website = href
                        break
            
            # Get location
            loc_el = card.select_one('[class*="location"], .locality, [class*="address"]')
            if loc_el:
                location = loc_el.get_text(strip=True)
            
            if name and len(name) > 2:
                agencies.append({
                    "name": name,
                    "email": "",
                    "website": website,
                    "location": location,
                    "source": "clutch",
                    "type": "agency"
                })
    except Exception as e:
        print(f"  ❌ Error: {e}")
    return agencies

def main():
    all_leads = []
    
    for page_url in CLUTCH_PAGES:
        print(f"\n📄 Scraping: {page_url}")
        agencies = scrape_clutch_page(page_url)
        print(f"  Found {len(agencies)} agencies")
        
        # Get emails from websites
        for agency in agencies:
            if agency['website']:
                print(f"    🌐 {agency['name'][:40]} → {agency['website'][:50]}")
                emails = get_website_emails(agency['website'])
                if emails:
                    agency['email'] = emails[0]
                    print(f"    📧 {emails[0]}")
                time.sleep(random.uniform(1.5, 3))
        
        all_leads.extend(agencies)
        time.sleep(random.uniform(3, 5))
    
    # Also try Sortlist
    sortlist_pages = [
        "https://www.sortlist.com/marketing/agency",
        "https://www.sortlist.com/seo/agency",
    ]
    
    for page_url in sortlist_pages:
        print(f"\n📄 Scraping: {page_url}")
        try:
            resp = requests.get(page_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            for card in soup.select('[class*="agency"], [class*="company"], [class*="provider"]'):
                name = ""
                website = ""
                
                name_el = card.select_one('h2, h3, h4, [class*="name"]')
                if name_el:
                    name = name_el.get_text(strip=True)
                
                link = card.select_one('a[href*="http"]')
                if link and 'sortlist' not in link.get('href', ''):
                    website = link['href']
                
                if name and len(name) > 2:
                    all_leads.append({
                        "name": name,
                        "email": "",
                        "website": website,
                        "location": "",
                        "source": "sortlist",
                        "type": "agency"
                    })
        except Exception as e:
            print(f"  ❌ {e}")
    
    # Load existing
    existing_emails = set()
    existing_leads = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_emails.add(row.get('email', '').lower())
                existing_leads.append(row)
    
    # Merge
    new_count = 0
    for lead in all_leads:
        email = lead.get('email', '').lower()
        if email and email not in existing_emails:
            existing_leads.append(lead)
            existing_emails.add(email)
            new_count += 1
    
    # Save
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'email', 'website', 'location', 'source', 'type'])
        writer.writeheader()
        writer.writerows(existing_leads)
    
    print(f"\n📊 RESULTS:")
    print(f"  New leads with email: {new_count}")
    print(f"  Total leads: {len(existing_leads)}")
    print(f"  Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
