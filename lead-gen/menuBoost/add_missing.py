#!/usr/bin/env python3
import csv
import requests
import re

def find_email_via_mailto(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.ok:
            # Find mailto links
            mailtos = re.findall(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', r.text)
            if mailtos:
                return mailtos[0]
            # Search for email pattern in whole page
            emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', r.text)
            # Filter out false positives
            for email in emails:
                if email.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    continue
                if '..' in email:
                    continue
                # Prefer email with domain matching url
                if url.split('//')[-1].split('/')[0].replace('www.', '') in email:
                    return email
            if emails:
                return emails[0]
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return ''

csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
rows = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Check if Hospiz Alm already present
hospiz_present = any(r['name'] == 'Hospiz Alm' for r in rows)
if not hospiz_present:
    # Try to find email
    email = find_email_via_mailto('https://arlberghospiz.at')
    if not email:
        email = find_email_via_mailto('http://arlberghospiz.at')
    rows.append({
        'name': 'Hospiz Alm',
        'email': email,
        'city': 'St. Christoph am Arlberg',
        'country': 'Austria',
        'website': 'arlberghospiz.at',
        'owner_or_chef': '',
        'specialty': '',
        'source': 'alpine_manual'
    })

# Tivoli - try to find email
tivoli_rows = [r for r in rows if r['name'] == 'Tivoli']
if tivoli_rows and not tivoli_rows[0]['email']:
    # Update existing Tivoli row
    for row in rows:
        if row['name'] == 'Tivoli':
            email = find_email_via_mailto('https://www.ristorantetivolicortina.it')
            if not email:
                # Try contact page
                email = find_email_via_mailto('https://www.ristorantetivolicortina.it/contatti')
            if not email:
                # Guess common email
                email = 'info@ristorantetivolicortina.it'
            row['email'] = email
            break

# Write back
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print('Added missing restaurants')