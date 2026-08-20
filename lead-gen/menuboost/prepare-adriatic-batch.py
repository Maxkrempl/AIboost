#!/usr/bin/env python3
import csv

# Load suppression list
with open('/home/darko/.openclaw/workspace/shared/sent-emails.txt') as f:
    sent = set(line.strip().lower() for line in f if line.strip())

# Load Adriatic leads
leads = []
with open('/home/darko/.openclaw/workspace/lead-gen/menuboost/adriatic-coast-new.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        email = row.get('email', '').lower()
        if email and email not in sent:
            leads.append(row)

# Write batch file
with open('/home/darko/.openclaw/workspace/lead-gen/menuboost/adriatic-batch-new.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['name', 'city', 'region', 'email', 'website', 'type', 'source'])
    writer.writeheader()
    for lead in leads:
        writer.writerow(lead)

print(f'Created batch with {len(leads)} leads:')
for l in leads:
    print(f"  {l['name']} | {l['city']} | {l['email']}")
