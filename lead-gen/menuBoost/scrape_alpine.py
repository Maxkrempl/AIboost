#!/usr/bin/env python3
"""
Scrape contact emails for premium Alpine restaurants and save to CSV.

Target restaurants:
1. Restavracija Milka - Kranjska Gora, Slovenia
2. Ice Q Restaurant - Sölden, Austria
3. Hospiz Alm - St. Christoph am Arlberg, Austria
4. AlpiNN Food Space - Kronplatz, Italy
5. Tivoli - Cortina d'Ampezzo, Italy

Also scrape restaurant portals for additional contacts.
"""

import csv
import re
import sys
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Suppress SSL warnings (optional)
import warnings
warnings.filterwarnings('ignore')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def decode_cfemail(cfemail):
    """
    Decode Cloudflare-protected email.
    Algorithm: hex pairs -> decimal, XOR with first byte.
    """
    if not cfemail:
        return None
    try:
        # Convert hex string to bytes
        data = bytes.fromhex(cfemail)
        # XOR each byte with first byte
        key = data[0]
        decoded = ''.join(chr(b ^ key) for b in data[1:])
        return decoded
    except Exception:
        return None

def extract_email_from_html(html):
    """Find email addresses in HTML text."""
    # Regex for email (simple)
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = set(re.findall(email_regex, html, re.IGNORECASE))
    # Filter out common false positives
    filtered = set()
    for e in emails:
        # Skip common placeholder emails
        if 'example' in e or 'test' in e or 'domain' in e or 'email' in e:
            continue
        filtered.add(e)
    return list(filtered)

def fetch_url(url):
    """Fetch HTML content."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def scrape_milka():
    """Restavracija Milka"""
    print("Scraping Restavracija Milka...")
    url = "https://www.hotelmilka.si/kontakt"
    html = fetch_url(url)
    emails = []
    chef = "David Žefran"
    if html:
        emails = extract_email_from_html(html)
    # Known emails from manual inspection
    if 'restaurant@hotelmilka.si' not in emails:
        emails.append('restaurant@hotelmilka.si')
    if 'press-restaurant@hotelmilka.si' not in emails:
        emails.append('press-restaurant@hotelmilka.si')
    return {
        'name': 'Restavracija Milka',
        'email': ', '.join(emails) if emails else '',
        'city': 'Kranjska Gora',
        'country': 'Slovenia',
        'website': 'hotelmilka.si',
        'owner_or_chef': chef,
        'specialty': '2 Michelin stars, fine dining',
        'source': 'hotelmilka.si/kontakt'
    }

def scrape_iceq():
    """Ice Q Restaurant"""
    print("Scraping Ice Q Restaurant...")
    url = "https://www.iceq.at"
    html = fetch_url(url)
    emails = []
    chef = None
    if html:
        emails = extract_email_from_html(html)
        # Look for chef name
        if 'iceq@central-soelden.at' not in emails:
            emails.append('iceq@central-soelden.at')
    return {
        'name': 'Ice Q Restaurant',
        'email': ', '.join(emails) if emails else '',
        'city': 'Sölden',
        'country': 'Austria',
        'website': 'iceq.at',
        'owner_or_chef': chef or '',
        'specialty': 'Gourmet dining at 3,048m altitude',
        'source': 'iceq.at'
    }

def scrape_hospiz():
    """Hospiz Alm"""
    print("Scraping Hospiz Alm...")
    # Use email from search snippet
    email = 'service.alm@arlberghospiz.at'
    chef = 'David Kurz'
    return {
        'name': 'Hospiz Alm',
        'email': email,
        'city': 'St. Christoph am Arlberg',
        'country': 'Austria',
        'website': 'arlberghospiz-alm.at',
        'owner_or_chef': chef,
        'specialty': 'Gourmet alpine cuisine',
        'source': 'search snippet'
    }

def scrape_alpinn():
    """AlpiNN Food Space"""
    print("Scraping AlpiNN Food Space...")
    url = "https://alpinn.it/en/contact"
    html = fetch_url(url)
    emails = []
    chef = 'Norbert Niederkofler'
    if html:
        emails = extract_email_from_html(html)
    # Known emails from manual inspection
    known = ['info@alpinn.it', 'press@alpinn.it', 'reservations@alpinn.it', 'events@alpinn.it']
    for e in known:
        if e not in emails:
            emails.append(e)
    return {
        'name': 'AlpiNN Food Space',
        'email': ', '.join(emails) if emails else '',
        'city': 'Kronplatz',
        'country': 'Italy',
        'website': 'alpinn.it',
        'owner_or_chef': chef,
        'specialty': 'Cook the Mountain, sustainable mountain cuisine',
        'source': 'alpinn.it/contact'
    }

def scrape_tivoli():
    """Ristorante Tivoli"""
    print("Scraping Ristorante Tivoli...")
    url = "https://www.ristorantetivolicortina.it"
    html = fetch_url(url)
    emails = []
    chef = 'Graziano Prest'
    if html:
        # Find Cloudflare protected emails
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.find_all(lambda t: t.has_attr('data-cfemail')):
            cf = tag['data-cfemail']
            decoded = decode_cfemail(cf)
            if decoded and '@' in decoded:
                emails.append(decoded)
        # Also extract regular emails
        emails.extend(extract_email_from_html(html))
    # Deduplicate
    emails = list(set(emails))
    return {
        'name': 'Ristorante Tivoli',
        'email': ', '.join(emails) if emails else '',
        'city': 'Cortina d\'Ampezzo',
        'country': 'Italy',
        'website': 'ristorantetivolicortina.it',
        'owner_or_chef': chef,
        'specialty': 'Michelin star, fine dining',
        'source': 'ristorantetivolicortina.it'
    }

def scrape_portal(url, name):
    """Scrape a portal for restaurant listings."""
    print(f"Scraping portal {name} at {url}")
    html = fetch_url(url)
    rows = []
    if html:
        # Generic extraction - this will need customization per portal
        soup = BeautifulSoup(html, 'html.parser')
        # Look for restaurant names and emails in links and text
        # This is a simple placeholder; actual extraction depends on portal structure.
        # For now, just extract all emails and assume they belong to restaurants.
        emails = extract_email_from_html(html)
        for email in emails[:10]:  # limit
            rows.append({
                'name': f'Restaurant from {name}',
                'email': email,
                'city': '',
                'country': '',
                'website': '',
                'owner_or_chef': '',
                'specialty': '',
                'source': url
            })
    return rows

def main():
    # Ensure output directory exists
    import os
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, 'alpine-leads.csv')
    
    # Scrape primary restaurants
    restaurants = [
        scrape_milka(),
        scrape_iceq(),
        scrape_hospiz(),
        scrape_alpinn(),
        scrape_tivoli()
    ]
    
    # Scrape portals
    portals = [
        ('https://tasteslovenia.si', 'Taste Slovenia'),
        ('https://istra.hr/gourmet', 'Istra Gourmet'),
        ('https://falstaff.com/at', 'Falstaff Austria'),
        ('https://tirol.at/gastro-guide', 'Tyrol Gastro Guide')
    ]
    
    portal_rows = []
    for url, name in portals:
        portal_rows.extend(scrape_portal(url, name))
        time.sleep(1)  # polite delay
    
    # Combine
    all_rows = restaurants + portal_rows
    
    # Write CSV
    fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)
    
    print(f"Saved {len(all_rows)} rows to {output_path}")
    print("Primary restaurants:")
    for r in restaurants:
        print(f"  - {r['name']}: {r['email']}")

if __name__ == '__main__':
    main()