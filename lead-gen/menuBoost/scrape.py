#!/usr/bin/env python3

import re
import csv
import sys
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
headers = {'User-Agent': USER_AGENT}
TIMEOUT = 10

# Email regex pattern
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

def extract_emails(text):
    return re.findall(EMAIL_PATTERN, text, re.IGNORECASE)

def fetch_page(url):
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

def find_contact_link(soup, base_url):
    # Look for links containing contact, kontak, about, o-nas, kontakt, etc.
    contact_keywords = ['contact', 'kontakt', 'onas', 'o-nas', 'about', 'kontakti', 'info']
    for a in soup.find_all('a', href=True):
        href = a['href'].lower()
        text = a.get_text().lower()
        if any(keyword in href or keyword in text for keyword in contact_keywords):
            link = urljoin(base_url, a['href'])
            return link
    return None

def extract_owner_or_chef(soup):
    # Heuristics: look for "chef", "owner", "šef", "lastnik", "direktor", "proprietor"
    # Usually in headings or strong tags
    # This is very basic; we can improve later
    text = soup.get_text().lower()
    # Search for patterns like "chef John", "owner Maria"
    # We'll just return first occurrence of a title followed by name? Hard.
    # For now, we'll return empty string and maybe manually fill later.
    return ''

def scrape_restaurant(name, website, city, country):
    print(f"Processing {name} - {website}")
    homepage = website if website.startswith('http') else f'https://{website}'
    html = fetch_page(homepage)
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    all_text = soup.get_text()
    emails = extract_emails(all_text)
    
    # If no emails found, try contact page
    contact_link = find_contact_link(soup, homepage)
    if contact_link and not emails:
        print(f"  Trying contact page: {contact_link}")
        contact_html = fetch_page(contact_link)
        if contact_html:
            contact_soup = BeautifulSoup(contact_html, 'html.parser')
            emails = extract_emails(contact_soup.get_text())
    
    # Deduplicate and filter plausible emails (exclude .png, .jpg)
    filtered_emails = []
    for email in set(emails):
        if not email.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            filtered_emails.append(email)
    
    # Choose the most likely email (prefer @restaurant domain)
    domain = urlparse(homepage).netloc.replace('www.', '')
    best_email = ''
    for email in filtered_emails:
        if domain in email:
            best_email = email
            break
    if not best_email and filtered_emails:
        best_email = filtered_emails[0]
    
    owner_or_chef = extract_owner_or_chef(soup)
    # Specialty: maybe from meta description or h1? Skip for now.
    specialty = ''
    
    return {
        'name': name,
        'email': best_email,
        'city': city,
        'country': country,
        'website': website,
        'owner_or_chef': owner_or_chef,
        'specialty': specialty,
        'source': 'scraped'
    }

def main():
    restaurants = [
        # Slovenia
        ("Restavracija Hotel Marina", "hotelmarina.si", "Izola", "Slovenia"),
        ("Restavracija COB", "cob.si", "Portorož", "Slovenia"),
        ("Restavracija Kogo", "kogo.si", "Koper", "Slovenia"),
        # Croatia (Istria)
        ("Restaurant Morgan", "morgan.hr", "Brtonigla", "Croatia"),
        ("Agli Amici", "agliamici.it", "Rovinj", "Croatia"),
        ("Monte", "monte.hr", "Rovinj", "Croatia"),
        ("Restaurant Badi", "restaurant-badi.com", "Umag", "Croatia"),
        ("Konoba Buščina", "konoba-buscina.hr", "Umag", "Croatia"),
        ("San Rocco Gourmet", "san-rocco.hr", "Brtonigla", "Croatia"),
        ("Restaurant Spinnaker", "valamar.com", "Poreč", "Croatia"),  # might need specific path
        # Croatia (Dalmatia)
        ("Pelegrini", "pelegrini.hr", "Šibenik", "Croatia"),
        ("LD Restaurant", "ldrestaurant.com", "Korčula", "Croatia"),
        ("360 Dubrovnik", "360dubrovnik.com", "Dubrovnik", "Croatia"),
    ]
    
    results = []
    for name, website, city, country in restaurants:
        result = scrape_restaurant(name, website, city, country)
        if result:
            results.append(result)
        time.sleep(1)  # be polite
    
    # Write to CSV
    csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    print(f"Saved {len(results)} leads to {csv_path}")
    return 0

if __name__ == '__main__':
    sys.exit(main())