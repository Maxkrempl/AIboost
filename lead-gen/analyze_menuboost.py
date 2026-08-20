#!/usr/bin/env python3
"""Analyze MenuBoost leads: stats + tourist restaurants without AI markup."""
import csv, os, glob

TOURIST_AREAS = {
    'dubrovnik', 'split', 'rovinj', 'pula', 'umag', 'istria', 'zadar', 'hvar',
    'korčula', 'kotor', 'piran', 'novigrad', 'brtonigla', 'vrsar', 'poreč',
    'rabac', 'lopud', 'cavtat', 'trogir', 'šibenik', 'makarska', 'omis',
    'krk', 'rab', 'pag', 'nin', 'primošten', 'biograd', 'vodice',
    'hrvatska', 'priobalje', 'dalmacija',
    'bled', 'bohinj', 'kranjska gora', 'portorož', 'koper', 'izola', 'postojna',
    'roma', 'firenze', 'venezia', 'milano', 'napoli', 'positano', 'amalfi',
    'rimini', 'cortina', 'dolomiti', 'belluno', 'treviso', 'padova', 'verona',
    'riccione', 'cattolica', 'pesaro', 'fano',
    'salzburg', 'innsbruck', 'vienna', 'kitzbühel', 'sölden', 'ischgl',
    'lech', 'zell am see', 'hallstatt',
    'val gardena', 'alpe di siusi', 'madonna di campiglio', 'livigno', 'bormio',
}

TOURIST_KEYWORDS = [
    'turist', 'tourist', 'beach', 'plaža', 'sea', 'morje', 'mountain', 'gora',
    'ski', 'smučišče', 'harbour', 'luka', 'old town', 'stari grad', 'riva',
    'waterfront', 'promenade', 'rivijera', 'riviera', 'resort', 'spa',
    'wellness', 'hotel', 'agriturizmo', 'konoba', 'taverna',
]

all_files = glob.glob('/home/darko/.openclaw/workspace/lead-gen/**/*.csv', recursive=True) + \
            glob.glob('/home/darko/.openclaw/workspace/outreach/sent/menuboost*.csv') + \
            glob.glob('/home/darko/.openclaw/workspace/outreach/sent/scraped*.csv') + \
            ['/home/darko/.openclaw/workspace/outreach/tracker.csv', '/home/darko/.openclaw/workspace/OSINT_leads_2026Q2.csv']

all_rows = []
for f in all_files:
    if not os.path.exists(f): continue
    try:
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                row['_source'] = f
                all_rows.append(row)
    except: pass

seen = set()
unique = []
for r in all_rows:
    name = (r.get('name','') or r.get('Company','')).strip().lower()
    email = (r.get('email','') or r.get('Email','')).strip().lower()
    website = (r.get('website','') or r.get('Website','')).strip().lower()
    key = (name, email, website)
    if key not in seen and (name or email or website):
        seen.add(key)
        unique.append(r)

for r in unique:
    r['name_clean'] = (r.get('name','') or r.get('Company','')).strip()
    r['email_clean'] = (r.get('email','') or r.get('Email','')).strip()
    r['website_clean'] = (r.get('website','') or r.get('Website','')).strip()
    r['city_clean'] = (r.get('city','') or r.get('location','')).strip()
    r['country_clean'] = (r.get('country','') or r.get('Country','')).strip()

total = len(unique)
has_website = [r for r in unique if r['website_clean']]
has_email = [r for r in unique if r['email_clean']]

print(f"{'='*60}")
print(f"📊 MENUBOOST LEAD DATABASE ANALYSIS")
print(f"{'='*60}")
print(f"\n📋 TOTAL UNIQUE CONTACTS: {total}")
print(f"   ✅ With website: {len(has_website)} ({len(has_website)*100//total}%)")
print(f"   ✅ With email: {len(has_email)} ({len(has_email)*100//total}%)")
print(f"   ❌ No website: {total - len(has_website)}")
print(f"   ❌ No email: {total - len(has_email)}")

countries = {}
for r in unique:
    co = r['country_clean']
    if co:
        countries[co] = countries.get(co, 0) + 1

print(f"\n🌍 BY COUNTRY:")
for k,v in sorted(countries.items(), key=lambda x: -x[1])[:15]:
    print(f"   {k}: {v}")

def is_tourist_area(r):
    city = r['city_clean'].lower()
    name = r['name_clean'].lower()
    notes = (r.get('notes','') or '').lower()
    specialty = (r.get('specialty','') or '').lower()
    combined = f"{city} {name} {notes} {specialty}"
    for area in TOURIST_AREAS:
        if area in city:
            return True
    for kw in TOURIST_KEYWORDS:
        if kw in combined:
            return True
    return False

tourist_restaurants = [r for r in unique if is_tourist_area(r)]

print(f"\n🏖️  TOURIST AREA RESTAURANTS: {len(tourist_restaurants)}")

tourist_countries = {}
for r in tourist_restaurants:
    co = r['country_clean']
    tourist_countries[co] = tourist_countries.get(co, 0) + 1

print(f"   By country:")
for k,v in sorted(tourist_countries.items(), key=lambda x: -x[1]):
    print(f"     {k}: {v}")

def has_ai_mention(r):
    combined = f"{r.get('notes','')} {r.get('specialty','')} {r.get('source','')} {r.get('notes','')} {r.get('type','')}".lower()
    return any(p in combined for p in ['ai', 'schema', 'llm', 'markup', 'seo boost', 'ai authority'])

with_ai = [r for r in tourist_restaurants if has_ai_mention(r)]
without_ai = [r for r in tourist_restaurants if not has_ai_mention(r)]

print(f"\n🤖 AI MARKUP STATUS (tourist subset):")
print(f"   With AI mention in data: {len(with_ai)}")
print(f"   Without AI mention: {len(without_ai)}")

candidates = [r for r in tourist_restaurants 
              if r['website_clean'] 
              and r['email_clean']
              and not has_ai_mention(r)
              and 'booking.com' not in r['website_clean']
              and 'tripadvisor' not in r['website_clean']
              and 'facebook.com' not in r['website_clean']
              and 'instagram.com' not in r['website_clean']]

print(f"\n🎯 BEST CANDIDATES (tourist + website + email + no AI + own domain): {len(candidates)}")

output = candidates[:100]

with open('/home/darko/.openclaw/workspace/lead-gen/menuboost-tourist-100.csv', 'w', newline='') as fh:
    writer = csv.writer(fh)
    writer.writerow(['name', 'email', 'website', 'city', 'country', 'source'])
    for r in output:
        writer.writerow([
            r['name_clean'],
            r['email_clean'],
            r['website_clean'],
            r['city_clean'],
            r['country_clean'],
            os.path.basename(r.get('_source','')),
        ])

print(f"\n✅ Written to: lead-gen/menuboost-tourist-100.csv ({len(output)} records)")

out_countries = {}
for r in output:
    co = r['country_clean']
    out_countries[co] = out_countries.get(co, 0) + 1

print(f"\n   Distribution in output:")
for k,v in sorted(out_countries.items(), key=lambda x: -x[1]):
    print(f"     {k}: {v}")

print(f"\n{'='*60}")
print(f"📋 FIRST 15 FROM SUB-DATABASE:")
print(f"{'='*60}")
for i, r in enumerate(output[:15], 1):
    print(f"  {i}. {r['name_clean']}")
    print(f"     📧 {r['email_clean']}")
    print(f"     🌐 {r['website_clean']}")
    print(f"     📍 {r['city_clean']}, {r['country_clean']}")
    print()
