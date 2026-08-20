#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
import csv
from urllib.parse import urljoin

headers = {'User-Agent': 'Mozilla/5.0'}

def fetch_page(url):
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.ok:
            return r.text
    except Exception as e:
        print(f'Error fetching {url}: {e}')
    return None

def extract_restaurant_links(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text().lower()
        # Slovenian keywords
        if any(keyword in text for keyword in ['restavracija', 'gostilna', 'restaurant', 'jedilnica']):
            full = urljoin(base_url, href)
            links.append(full)
        elif any(keyword in href for keyword in ['restaurant', 'restavracija', 'gostilna']):
            full = urljoin(base_url, href)
            links.append(full)
    return list(set(links))

def extract_emails(text):
    pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
    emails = re.findall(pattern, text)
    filtered = []
    for email in emails:
        if email.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            continue
        if '..' in email:
            continue
        filtered.append(email)
    return filtered

def main():
    base = 'https://tasteslovenia.si'
    html = fetch_page(base)
    if not html:
        print('Could not fetch tasteslovenia.si')
        return
    print('Page fetched')
    # Save for inspection
    with open('/tmp/tasteslovenia.html', 'w', encoding='utf-8') as f:
        f.write(html[:50000])
    # Try to find restaurant listing page
    # Maybe there's a /restaurants
    restaurant_page = urljoin(base, '/restaurants')
    html2 = fetch_page(restaurant_page)
    if html2:
        print('Found /restaurants page')
        html = html2
    # Extract links
    links = extract_restaurant_links(html, base)
    print(f'Found {len(links)} potential restaurant links')
    # Limit
    leads = []
    for link in links[:15]:
        print(f'Processing {link}')
        detail_html = fetch_page(link)
        if not detail_html:
            continue
        soup = BeautifulSoup(detail_html, 'html.parser')
        # Extract name from title or h1
        h1 = soup.find('h1')
        name = h1.get_text().strip() if h1 else ''
        if not name:
            title = soup.title.string if soup.title else ''
            name = title.split('|')[0].strip()
        emails = extract_emails(soup.get_text())
        email = emails[0] if emails else ''
        # Try to find website link
        website = ''
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http') and 'tasteslovenia.si' not in href:
                if any(domain in href for domain in ['.si', '.com', '.hr', '.at', '.it']):
                    website = href
                    break
        leads.append({
            'name': name[:200],
            'email': email,
            'city': '',
            'country': 'Slovenia',
            'website': website,
            'owner_or_chef': '',
            'specialty': '',
            'source': 'tasteslovenia'
        })
        import time
        time.sleep(1)
    
    if leads:
        csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
        existing = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing.append(row)
        for lead in leads:
            existing.append(lead)
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing)
        print(f'Added {len(leads)} leads from tasteslovenia.si')
    else:
        print('No leads extracted')

if __name__ == '__main__':
    main()