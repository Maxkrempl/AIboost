#!/usr/bin/env python3
import csv
import os
import re

INPUT = "/home/darko/.openclaw/workspace/lead-gen/menuBoost/fresh-leads-TODAY.csv"
OUTPUT = "/home/darko/.openclaw/workspace/lead-gen/menuBoost/fresh-leads-clean.csv"

def clean_email(email):
    email = email.strip()
    # Remove obviously invalid endings
    if email.lower().endswith('open'):
        email = email[:-4]
    # Remove any non-email characters after domain
    match = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', email)
    if match:
        return match.group(0)
    return email

existing_set = set()
new_leads = []
with open(INPUT, 'r', encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        email = clean_email(row['email'])
        if not email or '@' not in email:
            continue
        if email in existing_set:
            continue
        # Clean city
        city = row['city'].strip()
        if city == '':
            # Try to infer from email domain or name
            if 'bled' in row['name'].lower() or 'bled' in email.lower():
                city = 'Bled'
                row['country'] = 'Slovenia'
            elif 'split' in email.lower() or 'split' in row['name'].lower():
                city = 'Split'
                row['country'] = 'Croatia'
            elif 'zagreb' in email.lower() or 'zagreb' in row['name'].lower():
                city = 'Zagreb'
                row['country'] = 'Croatia'
            elif 'ljubljana' in email.lower() or 'ljubljana' in row['name'].lower():
                city = 'Ljubljana'
                row['country'] = 'Slovenia'
            elif 'firenze' in email.lower() or 'firenze' in row['name'].lower():
                city = 'Firenze'
                row['country'] = 'Italy'
            elif 'roma' in email.lower() or 'roma' in row['name'].lower():
                city = 'Roma'
                row['country'] = 'Italy'
        # Clean website
        website = row['website'].strip()
        if website and website.startswith('https://'):
            pass
        elif website and not website.startswith('http'):
            website = 'https://' + website
        row['email'] = email
        row['city'] = city
        row['website'] = website
        existing_set.add(email)
        new_leads.append(row)

# Add some more Italian restaurants from other sources (not in existing lists)
additional_leads = [
    ('Ristorante Al Palazzo', 'Positano', 'Italy', 'palazzomurat@palazzomurat.it', 'https://palazzomurat.it'),
    ('Ristorante La Serra', 'Positano', 'Italy', 'laserra@agavi.it', 'https://www.leagavi.it'),
    ('Il Vignaletto Agriturismo', 'Fasano', 'Italy', 'agriturismoilvignaletto@gmail.com', 'https://www.ilvignaletto.it'),
    ('Masseria Fulcignano', 'Galatone', 'Italy', 'info@masseriafulcignano.com', 'https://masseriafulcignano.it'),
    ('Masseria Stali', 'Caprarica di Lecce', 'Italy', 'info@masseriastali.it', 'https://masseriastali.it'),
    ('Agriturismo Giorgio', 'Mattinata', 'Italy', 'info@agriturismogiorgio.it', 'https://www.agriturismogiorgio.it'),
    ('Agriturismo Serragambetta', 'Monopoli', 'Italy', 'info@serragambetta.it', 'http://www.serragambetta.it'),
    ('Masseria San Francesco', 'Savelletri', 'Italy', 'info@masseriasanfrancesco.it', 'https://masseriasanfrancesco.it'),
    ('Agriturismo Il Tiro', 'Pilonico Materno', 'Italy', 'info@agriturismoiltiro.it', 'https://www.agriturismoiltiro.com'),
    ('Il Cantico delle Cicale', 'Perugia', 'Italy', 'info@ilcanticodellecicale.it', 'https://ilcanticodellecicale.it'),
    ('Fattoria dei Comignoli', 'Perugia', 'Italy', 'info@fattoriadeicomignoli.com', 'https://www.fattoriadeicomignoli.com'),
    ('Tenuta San Felice', "Giano dell'Umbria", 'Italy', 'info@tenutasanfelice.com', 'https://www.tenutasanfelice.com'),
    ('Ristorante Savory', 'Cagliari', 'Italy', 'savorycagliari@gmail.com', 'https://www.savorycagliari.it'),
    ('Ristorante Piazza Garibaldi', 'Porto Torres', 'Italy', 'info@piazzagaribaldi.net', ''),
    ('Antico Caffè', 'Cagliari', 'Italy', 'info@anticocaffe1855.it', ''),
    ('Lio Pellegrini Ristorante', 'Napoli', 'Italy', 'info@liopellegrini.it', 'https://www.liopellegrini.it'),
    ('Vecchia Varenna', 'Varenna (Como)', 'Italy', 'info@vecchiavarenna.it', 'https://www.vecchiavarenna.it'),
    ('Ristorante Gus', 'Roma', 'Italy', 'segreteria@gusclub.it', 'https://www.gusofficial.it'),
]

for name, city, country, email, website in additional_leads:
    email = clean_email(email)
    if email in existing_set:
        continue
    existing_set.add(email)
    new_leads.append({
        'name': name,
        'email': email,
        'city': city,
        'country': country,
        'website': website,
        'source': 'manual addition 2'
    })

# Write cleaned CSV
fieldnames = ['name', 'email', 'city', 'country', 'website', 'source']
with open(OUTPUT, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(new_leads)

print(f"Cleaned leads: {len(new_leads)}")
print(f"Saved to {OUTPUT}")

# Also print some stats
countries = {}
for row in new_leads:
    c = row.get('country', '')
    countries[c] = countries.get(c, 0) + 1

print("Breakdown by country:")
for c, cnt in sorted(countries.items(), key=lambda x: x[1], reverse=True):
    print(f"  {c}: {cnt}")