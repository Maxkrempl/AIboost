#!/usr/bin/env python3
import csv

csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
rows = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row['name'].lower()
        # Keep only rows that look like restaurant names
        # Exclude generic category names
        if name in ['craft beer', 'gourmet spots', 'istrian brandies']:
            continue
        # Also exclude if website is istra.hr (portal)
        if 'istra.hr' in row['website']:
            continue
        rows.append(row)

with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print('Removed non-restaurant entries')