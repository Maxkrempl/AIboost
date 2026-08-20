#!/usr/bin/env python3
import csv

csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
rows = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

filtered = []
for row in rows:
    email = row['email'].lower()
    # Remove generic portal emails
    if 'slovenia.info' in email or 'tasteslovenia.si' in email:
        print(f'Removing generic email: {row["name"]} - {row["email"]}')
        continue
    filtered.append(row)

with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(filtered)

print(f'Remaining leads: {len(filtered)}')