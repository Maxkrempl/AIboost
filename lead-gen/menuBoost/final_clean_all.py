#!/usr/bin/env python3
import csv
import re

def normalize(text):
    return text.lower().strip() if text else ''

def is_valid_email(email):
    if not email:
        return False
    email = email.strip()
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_website(url):
    if not url:
        return False
    url = url.lower()
    # Exclude placeholder or directory sites
    if 'facebook.com/visitistria' in url:
        return False
    if 'facebook.com' in url and 'restaurant' not in url:
        return False
    if 'istra.hr' in url:
        return False
    if 'tasteslovenia.si' in url:
        return False
    # Should contain a domain and not just path
    if '.' not in url:
        return False
    return True

csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
rows = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Step 1: Clean fields
for row in rows:
    row['name'] = row['name'].strip()
    row['email'] = row['email'].strip()
    row['city'] = row['city'].strip()
    row['country'] = row['country'].strip()
    row['website'] = row['website'].strip()
    # If city empty, infer from country
    if not row['city']:
        if row['country'] == 'Slovenia':
            row['city'] = 'Slovenia'
        elif row['country'] == 'Croatia':
            row['city'] = 'Istria'
        elif row['country'] == 'Austria':
            row['city'] = 'Tyrol'
        elif row['country'] == 'Italy':
            row['city'] = 'Alps'
    # If website missing but email domain maybe same as website? Not now.

# Step 2: Remove duplicates by email and website
seen_emails = set()
seen_websites = set()
filtered = []
for row in rows:
    email = normalize(row['email'])
    website = normalize(row['website'])
    keep = True
    if email and email in seen_emails:
        print(f'Duplicate email {email} for {row["name"]}, skipping')
        keep = False
    if website and website in seen_websites:
        print(f'Duplicate website {website} for {row["name"]}, skipping')
        keep = False
    if not keep:
        continue
    # Validate email
    if email and not is_valid_email(email):
        # Could be malformed, try to extract
        pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
        match = re.search(pattern, email)
        if match:
            row['email'] = match.group()
            email = normalize(row['email'])
        else:
            row['email'] = ''
    # Validate website
    if website and not is_valid_website(website):
        row['website'] = ''
        website = ''
    # If no email and no website, drop
    if not row['email'] and not row['website']:
        print(f'No contact info for {row["name"]}, skipping')
        continue
    # Keep
    if email:
        seen_emails.add(email)
    if website:
        seen_websites.add(website)
    filtered.append(row)

# Step 3: Sort by country, name
filtered.sort(key=lambda x: (x['country'], x['name']))

# Write final CSV
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(filtered)

print(f'Final lead count: {len(filtered)}')
print('Cleaning complete.')