#!/usr/bin/env python3
import requests
import re
import csv
import ssl
import urllib.request
from urllib.parse import urljoin

def fetch_without_ssl(url):
    context = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urllib.request.urlopen(req, context=context, timeout=10)
        data = response.read().decode('utf-8')
        return data
    except Exception as e:
        print(f'  SSL bypass error: {e}')
        return None

def find_email(text):
    emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', text)
    for email in emails:
        if email.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            continue
        if '..' in email:
            continue
        return email
    return None

csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
rows = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

updated = False
for row in rows:
    if row['email']:
        continue
    name = row['name']
    website = row['website']
    if not website:
        continue
    print(f'Searching email for {name} ({website})')
    # Ensure URL scheme
    if not website.startswith('http'):
        website = f'https://{website}'
    # Try normal request
    try:
        r = requests.get(website, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.ok:
            email = find_email(r.text)
            if email:
                row['email'] = email
                updated = True
                print(f'  Found: {email}')
                continue
    except Exception as e:
        print(f'  Request failed: {e}')
    # Try SSL bypass for Hospiz Alm
    if name == 'Hospiz Alm':
        print('  Trying SSL bypass...')
        html = fetch_without_ssl(website)
        if html:
            email = find_email(html)
            if email:
                row['email'] = email
                updated = True
                print(f'  Found via bypass: {email}')
    # Try contact page
    contact_url = urljoin(website, '/contact')
    try:
        r = requests.get(contact_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.ok:
            email = find_email(r.text)
            if email:
                row['email'] = email
                updated = True
                print(f'  Found via contact page: {email}')
    except:
        pass

if updated:
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print('Updated CSV with missing emails')
else:
    print('No new emails found')