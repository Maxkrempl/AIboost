#!/usr/bin/env python3
import csv

csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
rows = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Email mapping
email_map = {
    'Restavracija Hotel Marina': 'recepcija@hotelmarina.si',
    'Restavracija Kogo': 'info@kogo.si',
    'Monte': 'restaurant@monte.hr',
    'Pelegrini': 'reservations@pelegrini.hr',
    'Restaurant Spinnaker': 'reservations@valamar.com',
    'Agli Amici': 'lab@agliamici.it',
}

for row in rows:
    if row['name'] in email_map:
        row['email'] = email_map[row['name']]
    # Clean owner_or_chef column: trim whitespace and limit length
    if row['owner_or_chef']:
        row['owner_or_chef'] = row['owner_or_chef'].strip()[:100]

# Write final CSV (overwrite)
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print("Updated CSV with corrected emails")