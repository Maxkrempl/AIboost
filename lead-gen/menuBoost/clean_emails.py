#!/usr/bin/env python3
import csv
import re

def clean_email(email):
    if not email:
        return ''
    # Remove trailing non-email characters (letters, digits, dots, hyphens allowed after @?)
    # Use regex to find email pattern within the string
    # Standard email pattern
    pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    matches = re.findall(pattern, email)
    if matches:
        return matches[0]
    # If no match, try to strip anything after .si, .hr, .com etc
    # For now return original
    return email

csv_path = '/home/darko/.openclaw/workspace/lead-gen/menuBoost/premium-leads.csv'
rows = []
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        row['email'] = clean_email(row['email'])
        rows.append(row)

# Write back
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['name', 'email', 'city', 'country', 'website', 'owner_or_chef', 'specialty', 'source']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print("Cleaned emails")