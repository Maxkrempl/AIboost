#!/usr/bin/env python3
import csv
import re

def extract_core_email(raw):
    if not raw:
        return ''
    # Remove any leading/trailing whitespace
    raw = raw.strip()
    # Common pattern: email with possible attached letters/digits
    # We'll find the @ and then extend left and right to capture the email
    at_pos = raw.find('@')
    if at_pos == -1:
        return ''
    # Left side: local-part: alphanumeric, dots, underscores, hyphens
    left = ''
    i = at_pos - 1
    while i >= 0 and (raw[i].isalnum() or raw[i] in '._%+-'):
        left = raw[i] + left
        i -= 1
    # Right side: domain and TLD
    right = ''
    i = at_pos + 1
    while i < len(raw) and (raw[i].isalnum() or raw[i] in '.-'):
        right = right + raw[i]
        i += 1
    # Ensure right part contains a dot
    if '.' not in right:
        return ''
    # Construct email
    email = left + '@' + right
    # Validate with regex
    if re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$', email):
        return email
    else:
        return ''

def clean_email(raw):
    core = extract_core_email(raw)
    if core:
        return core
    # Fallback to regex search
    pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
    matches = re.findall(pattern, raw)
    if matches:
        return matches[0]
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
    if row['name'] == 'Agli Amici' and not row['email']:
        row['email'] = 'lab@agliamici.it'
    if row['name'] == 'Restaurant Spinnaker' and row['email'] == 'skiing@valamar.com':
        # This seems generic, maybe there's a restaurant-specific email
        # Keep for now
        pass

# Write back
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print("Cleaned emails and added missing")