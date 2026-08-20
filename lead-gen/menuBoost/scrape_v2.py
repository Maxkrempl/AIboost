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
TIMEOUT = 15

def extract_emails(text):
    # Pattern with word boundaries
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text, re.IGNORECASE)
    # Additional filter: if email ends with image extension, discard
    filtered = []
    for email in emails:
        if email.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
            continue
        # If email contains '..' or consecutive dots, skip
        if '..' in email:
            continue
        filtered.append(email)
    return filtered

def fetch_page(url):
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

def find_page_link(soup, base_url, keywords):
    # Look for links containing any of the keywords
    for a in soup.find_all('a', href=True):
        href = a['href'].lower()
        text = a.get_text().lower()
        if any(keyword in href or keyword in text for keyword in keywords):
            link = urljoin(base_url, a['href'])
            return link
    return None

def extract_owner_or_chef(soup):
    # Search for chef/owner keywords in text
    text = soup.get_text().lower()
    # Define keywords in multiple languages
    keywords = ['chef', 'owner', 'šef', 'lastnik', 'direktor', 'proprietor', 'head chef', 'executive chef', 'manager', 'vlasnik']
    # Look for lines containing keywords
    lines = text.split('\n')
    for line in lines:
        for kw in keywords:
            if kw in line:
                # Extract the line, maybe we can parse a name
                # Simple heuristic: take the next word after keyword as name? Too noisy.
                # Return the line trimmed
                return line.strip()[:100]  # limit length
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
    
    # Try contact page if no emails
    contact_link = find_page_link(soup, homepage, ['contact', 'kontakt', 'onas', 'o-nas', 'kontakti', 'info', 'kontaktirajte'])
    if contact_link and not emails:
        print(f"  Trying contact page: {contact_link}")
        contact_html = fetch_page(contact_link)
        if contact_html:
            contact_soup = BeautifulSoup(contact_html, 'html.parser')
            emails = extract_emails(contact_soup.get_text())
    
    # Try about page for owner/chef info
    about_link = find_page_link(soup, homepage, ['about', 'o-nas', 'onas', 'o nama', 'team', 'chef', 'owner'])
    owner_or_chef = ''
    if about_link:
        print(f"  Trying about page: {about_link}")
        about_html = fetch_page(about_link)
        if about_html:
            about_soup = BeautifulSoup(about_html, 'html.parser')
            owner_or_chef = extract_owner_or_chef(about_soup)
    
    # Deduplicate emails
    unique_emails = list(set(emails))
    
    # Choose the most likely email (prefer @restaurant domain)
    domain = urlparse(homepage).netloc.replace('www.', '')
    best_email = ''
    for email in unique_emails:
        if domain in email:
            best_email = email
            break
    if not best_email and unique_emails:
        best_email = unique_emails[0]
    
    # If still no email, maybe there's a reservation email in meta
    if not best_email:
        # Look for meta tags with email
        for meta in soup.find_all('meta'):
            content = meta.get('content', '')
            if '@' in content:
                emails_meta = extract_emails(content)
                if emails_meta:
                    best_email = emails_meta[0]
                    break
    
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
        'source': 'scraped_v2'
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
    
    # Write to CSV (overwrite)
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