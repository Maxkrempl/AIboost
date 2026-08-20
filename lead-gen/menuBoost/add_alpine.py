#!/usr/bin/env python3

import re
import csv
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
headers = {'User-Agent': USER_AGENT}
TIMEOUT = 15

def extract_emails(text):
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text, re.IGNORECASE)
    filtered = []
    for email in emails:
        if email.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
            continue
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
    for a in soup.find_all('a', href=True):
        href = a['href'].lower()
        text = a.get_text().lower()
        if any(keyword in href or keyword in text for keyword in keywords):
            link = urljoin(base_url, a['href'])
            return link
    return None

def extract_owner_or_chef(soup):
    text = soup.get_text().lower()
    keywords = ['chef', 'owner', 'šef', 'lastnik', 'direktor', 'proprietor', 'head chef', 'executive chef', 'manager', 'vlasnik', 'inhaber', 'besitzer']
    lines = text.split('\n')
    for line in lines:
        for kw in keywords:
            if kw in line:
                return line.strip()[:100]
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
    
    # Try contact page
    contact_link = find_page_link(soup, homepage, ['contact', 'kontakt', 'onas', 'o-nas', 'kontakti', 'info', 'kontaktirajte', 'kontaktieren'])
    if contact_link and not emails:
        print(f"  Trying contact page: {contact_link}")
        contact_html = fetch_page(contact_link)
        if contact_html:
            contact_soup = BeautifulSoup(contact_html, 'html.parser')
            emails = extract_emails(contact_soup.get_text())
    
    # Try about page
    about_link = find_page_link(soup, homepage, ['about', 'o-nas', 'onas', 'o nama', 'team', 'chef', 'owner', 'über uns', 'unsere'])
    owner_or_chef = ''
    if about_link:
        print(f"  Trying about page: {about_link}")
        about_html = fetch_page(about_link)
        if about_html:
            about_soup = BeautifulSoup(about_html, 'html.parser')
            owner_or_chef = extract_owner_or_chef(about_soup)
    
    # Deduplicate
    unique_emails = list(set(emails))
    domain = urlparse(homepage).netloc.replace('www.', '')
    best_email = ''
    for email in unique_emails:
        if domain in email:
            best_email = email
            break
    if not best_email and unique_emails:
        best_email = unique_emails[0]
    
    # Clean email
    if best_email:
        at_pos = best_email.find('@')
        if at_pos != -1:
            left = ''
            i = at_pos - 1
            while i >= 0 and (best_email[i].isalnum() or best_email[i] in '._%+-'):
                left = best_email[i] + left
                i -= 1
            right = ''
            i = at_pos + 1
            while i < len(best_email) and (best_email[i].isalnum() or best_email[i] in '.-'):
                right = right + best_email[i]
                i += 1
            if '.' in right:
                best_email = left + '@' + right
    
    specialty = ''
    return {
        'name': name,
        'email': best_email,
        'city': city,
        'country': country,
        'website': website,
        'owner_or_chef': owner_or_chef,
        'specialty': specialty,
        'source': 'alpine_scraped'
    }

def main():
    alpine_restaurants = [
        ("Restavracija Milka", "hotelmilka.si", "Kranjska Gora", "Slovenia"),
        ("Ice Q Restaurant", "iceq.at", "Sölden", "Austria"),
        ("Hospiz Alm", "arlberghospiz.at", "St. Christoph am Arlberg", "Austria"),
        ("AlpiNN Food Space", "alpinn.it", "Kronplatz", "Italy"),
        ("Tivoli", "ristorantetivolicortina.it", "Cortina d'Ampezzo", "Italy"),
    ]
    
    results = []
    for name, website, city, country in alpine_restaurants:
        result = scrape_restaurant(name, website, city, country)
        if result:
            results.append(result)
        time.sleep(1)
    
    # Append to existing CSV
    csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
    existing_rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_rows.append(row)
    
    # Add new rows
    for row in results:
        existing_rows.append(row)
    
    # Write back
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_rows)
    
    print(f"Added {len(results)} alpine restaurants to CSV")
    return 0

if __name__ == '__main__':
    main()