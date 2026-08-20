#!/usr/bin/env python3
import csv

csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
rows = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

print('=== MENUBOOST LEAD GENERATION SUMMARY ===')
print(f'Total leads: {len(rows)}')
print()

# Count by country
from collections import Counter
countries = Counter([r['country'] for r in rows])
print('Leads by country:')
for country, count in sorted(countries.items()):
    print(f'  {country}: {count}')
print()

# Emails
emails = sum(1 for r in rows if r['email'])
print(f'Leads with email: {emails}')
print(f'Leads missing email: {len(rows) - emails}')
if len(rows) - emails:
    print('Missing email for:')
    for r in rows:
        if not r['email']:
            print(f'  - {r["name"]} ({r["country"]})')
print()

# Sources
sources = Counter([r['source'] for r in rows])
print('Sources:')
for source, count in sorted(sources.items()):
    print(f'  {source}: {count}')
print()

# Output file path
import os
print(f'CSV file: {os.path.abspath(csv_path)}')
print(f'CSV size: {os.path.getsize(csv_path)} bytes')
print()
print('Sample leads:')
for i, r in enumerate(rows[:5]):
    print(f'  {r["name"]} | {r["email"]} | {r["country"]}')