#!/usr/bin/env python3
import csv
import re

def normalize(text):
    return text.lower().strip()

def is_valid_website(url):
    if not url:
        return False
    url = url.lower()
    # Exclude facebook placeholder links
    if 'facebook.com/visitistria' in url:
        return False
    if 'facebook.com' in url and 'restaurant' not in url:
        return False
    # Exclude generic istra.hr
    if 'istra.hr' in url:
        return False
    return True

csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
rows = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Deduplication by email and website
seen_emails = set()
seen_websites = set()
deduped = []
for row in rows:
    email = normalize(row['email'])
    website = normalize(row['website'])
    # If email already seen, skip (keep first)
    if email and email in seen_emails:
        print(f'Duplicate email {email} for {row["name"]}, skipping')
        continue
    # If website already seen, skip
    if website and website in seen_websites:
        print(f'Duplicate website {website} for {row["name"]}, skipping')
        continue
    # If website invalid, maybe still keep if email present
    if not is_valid_website(row['website']):
        # Replace with empty string
        row['website'] = ''
        # If also no email, skip
        if not row['email']:
            print(f'Invalid website and no email for {row["name"]}, skipping')
            continue
    # Add
    if email:
        seen_emails.add(email)
    if website:
        seen_websites.add(website)
    deduped.append(row)

# Fill missing city with region based on country
for row in deduped:
    if not row['city']:
        if row['country'] == 'Croatia':
            row['city'] = 'Istria'
        elif row['country'] == 'Slovenia':
            row['city'] = 'Slovenia'
        elif row['country'] == 'Austria':
            row['city'] = 'Tyrol'
        elif row['country'] == 'Italy':
            row['city'] = 'Alps'

# Write back
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(deduped)

print(f'Deduplicated: {len(rows)} -> {len(deduped)} rows')