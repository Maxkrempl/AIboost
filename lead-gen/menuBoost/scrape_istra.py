#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
import csv
from urllib.parse import urljoin

headers = {'User-Agent': 'Mozilla/5.0'}

def get_restaurant_links(url):
    resp = requests.get(url, headers=headers)
    if not resp.ok:
        print(f'Failed to fetch {url}')
        return []
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Look for restaurant links - guess based on class or href
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text().strip()
        # Heuristic: link containing 'restaurant' or 'gourmet' or 'dining'
        if re.search(r'restaurant|gourmet|dining|tavern|konoba', href, re.I) or \
           re.search(r'restaurant|gourmet|dining|tavern|konoba', text, re.I):
            full = urljoin(url, href)
            links.append(full)
    return list(set(links))

def extract_emails(text):
    pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
    emails = re.findall(pattern, text)
    filtered = []
    for email in emails:
        if email.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
            continue
        if '..' in email:
            continue
        filtered.append(email)
    return filtered

def scrape_restaurant_page(url):
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if not resp.ok:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Try to find name (maybe in title or h1)
        title = soup.title.string if soup.title else ''
        h1 = soup.find('h1')
        name = h1.get_text().strip() if h1 else title.split('|')[0].strip()
        # Find emails
        emails = extract_emails(soup.get_text())
        email = emails[0] if emails else ''
        # Guess city/country (hard)
        city = ''
        country = 'Croatia'
        # Website is the url
        website = url.split('//')[-1].split('/')[0]
        return {
            'name': name[:200],
            'email': email,
            'city': city,
            'country': country,
            'website': website,
            'owner_or_chef': '',
            'specialty': '',
            'source': 'istra_portal'
        }
    except Exception as e:
        print(f'Error scraping {url}: {e}')
        return None

def main():
    base = 'https://www.istra.hr/en/gourmet'
    print('Fetching restaurant links...')
    links = get_restaurant_links(base)
    print(f'Found {len(links)} potential restaurant links')
    # Limit to first 10 for now
    leads = []
    for link in links[:10]:
        print(f'Processing {link}')
        lead = scrape_restaurant_page(link)
        if lead and lead['email']:
            leads.append(lead)
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
        print(f'Added {len(leads)} new leads from Istria portal')
    else:
        print('No leads extracted')

if __name__ == '__main__':
    main()