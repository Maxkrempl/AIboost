#!/usr/bin/env python3
import requests
import re
import csv

def scrape_restaurant(name, website, city, country):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        url = website if website.startswith('http') else f'https://{website}'
        r = requests.get(url, headers=headers, timeout=10)
        if r.ok:
            text = r.text
            emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', text)
            email = ''
            for em in emails:
                if em.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    continue
                if '..' in em:
                    continue
                email = em
                break
            # Also search for mailto
            mailtos = re.findall(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', text)
            if mailtos:
                email = mailtos[0]
            return email
    except Exception as e:
        print(f'Error scraping {website}: {e}')
    return ''

austrian_restaurants = [
    ('Restaurant Ikarus', 'ikarus.at', 'Salzburg', 'Austria'),
    ('Steirereck', 'steirereck.at', 'Vienna', 'Austria'),
    ('Mraz & Sohn', 'mraz-sohn.at', 'Vienna', 'Austria'),
    ('Restaurant Obendorfer', 'obendorfer.at', 'Vienna', 'Austria'),
]

csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
existing_rows = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        existing_rows.append(row)

existing_names = {r['name'].lower() for r in existing_rows}

for name, website, city, country in austrian_restaurants:
    if name.lower() in existing_names:
        print(f'{name} already in list')
        continue
    print(f'Scraping {name}...')
    email = scrape_restaurant(name, website, city, country)
    if not email:
        # guess info@website
        domain = website.replace('www.', '').split('/')[0]
        email = f'info@{domain}'
    existing_rows.append({
        'name': name,
        'email': email,
        'city': city,
        'country': country,
        'website': website,
        'owner_or_chef': '',
        'specialty': '',
        'source': 'austrian_manual'
    })
    print(f'  Added with email {email}')

with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(existing_rows)

print('Added Austrian restaurants')