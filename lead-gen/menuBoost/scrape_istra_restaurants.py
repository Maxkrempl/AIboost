#!/usr/bin/env python3
import re
import csv
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time

headers = {'User-Agent': 'Mozilla/5.0'}

def get_restaurant_links(url):
    resp = requests.get(url, headers=headers)
    if not resp.ok:
        return []
    soup = BeautifulSoup(resp.text, 'html.parser')
    links = []
    # Find all links that contain '/where-to-eat/' and have a restaurant name
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/where-to-eat/' in href and href.count('/') >= 5:
            # Skip pagination links
            if 'page=' in href:
                continue
            full = urljoin(url, href)
            if full not in links:
                links.append(full)
    return links

def extract_restaurant_info(detail_url):
    try:
        resp = requests.get(detail_url, headers=headers, timeout=10)
        if not resp.ok:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Name from h1 or title
        h1 = soup.find('h1')
        name = h1.get_text().strip() if h1 else ''
        if not name:
            title = soup.title.string if soup.title else ''
            name = title.split('|')[0].strip()
        # Find website link
        website = ''
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'http' in href and ('restaurant' in href or 'www' in href):
                # Maybe external website
                if 'istra.hr' not in href:
                    website = href
                    break
        # If not found, look for link with domain .hr or .com
        if not website:
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('http') and ('.hr' in href or '.com' in href or '.si' in href):
                    if 'istra.hr' not in href:
                        website = href
                        break
        # Extract emails from page
        emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', soup.get_text())
        email = ''
        for em in emails:
            if em.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                continue
            if '..' in em:
                continue
            email = em
            break
        # City and country hardcoded
        city = ''
        country = 'Croatia'
        # Try to find city from breadcrumbs or location meta
        # Not implemented
        return {
            'name': name[:200],
            'email': email,
            'city': city,
            'country': country,
            'website': website,
            'owner_or_chef': '',
            'specialty': '',
            'source': 'istra_directory'
        }
    except Exception as e:
        print(f'Error scraping {detail_url}: {e}')
        return None

def load_existing_leads(csv_path):
    names = set()
    websites = set()
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            names.add(row['name'].lower().strip())
            if row['website']:
                websites.add(row['website'].lower().strip())
    return names, websites

def main():
    base_url = 'https://www.istra.hr/en/gourmet/where-to-eat'
    print('Fetching restaurant list...')
    links = get_restaurant_links(base_url)
    print(f'Found {len(links)} restaurant detail pages')
    
    csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
    existing_names, existing_websites = load_existing_leads(csv_path)
    
    new_leads = []
    for link in links[:25]:  # limit to first 25
        print(f'Processing {link}')
        info = extract_restaurant_info(link)
        if not info:
            continue
        # Check if already in CSV
        if info['name'].lower().strip() in existing_names:
            print(f'  Skipping duplicate name: {info["name"]}')
            continue
        if info['website'] and info['website'].lower().strip() in existing_websites:
            print(f'  Skipping duplicate website: {info["website"]}')
            continue
        # If no website, maybe skip
        if not info['website']:
            print(f'  No website found for {info["name"]}')
            # Still maybe keep with email?
            if info['email']:
                pass
            else:
                continue
        new_leads.append(info)
        time.sleep(1)
    
    if new_leads:
        # Append to CSV
        existing_rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_rows.append(row)
        for lead in new_leads:
            existing_rows.append(lead)
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_rows)
        print(f'Added {len(new_leads)} new restaurant leads from Istria directory')
    else:
        print('No new leads added')
    return 0

if __name__ == '__main__':
    main()