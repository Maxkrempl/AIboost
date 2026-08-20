#!/usr/bin/env python3
import csv
import re

def clean_email(raw):
    if not raw:
        return ''
    # Find email pattern
    pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
    matches = re.findall(pattern, raw)
    if matches:
        email = matches[0]
        # Remove any trailing non-email characters (letters/digits allowed in local part?)
        # Keep only email characters up to the end of the match
        return email
    return raw

csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
rows = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        row['email'] = clean_email(row['email'])
        rows.append(row)

# Manual fixes
for row in rows:
    if row['name'] == 'Ice Q Restaurant':
        # Known email
        row['email'] = 'iceq@central-soelden.at'
    if row['name'] == 'AlpiNN Food Space':
        row['email'] = 'reservations@alpinn.it'
    if row['name'] == 'Restavracija Milka':
        # Already correct
        pass

with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print('Cleaned emails')