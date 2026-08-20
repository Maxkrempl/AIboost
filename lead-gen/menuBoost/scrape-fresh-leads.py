#!/usr/bin/env python3
"""
Scrape fresh restaurant/hospitality leads for MenuBoost.
"""
import csv
import re
import os
import sys
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import time

# Directories
LEAD_DIR = "/home/darko/.openclaw/workspace/lead-gen"
OUTPUT_FILE = os.path.join(LEAD_DIR, "menuBoost", "fresh-leads-TODAY.csv")
EXISTING_FILES = [
    os.path.join(LEAD_DIR, "menuBoost", "leads-with-email.csv"),
    os.path.join(LEAD_DIR, "menuBoost", "leads-all.csv"),
    os.path.join(LEAD_DIR, "menuboost", "croatia-adriatic-with-email.csv"),
    os.path.join(LEAD_DIR, "menuboost", "slovenia-hotels-restaurants.csv"),
    os.path.join(LEAD_DIR, "menuboost", "italy-batch2-ready-verified.csv"),
]

# Load existing emails and websites
existing_emails = set()
existing_websites = set()

for fpath in EXISTING_FILES:
    if os.path.exists(fpath):
        try:
            with open(fpath, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header
                for row in reader:
                    if len(row) >= 3:
                        email = row[2].strip()
                        if email and '@' in email:
                            existing_emails.add(email.lower())
                    if len(row) >= 4:
                        website = row[3].strip()
                        if website:
                            existing_websites.add(website.lower())
        except Exception as e:
            print(f"Error reading {fpath}: {e}", file=sys.stderr)

print(f"Loaded {len(existing_emails)} existing emails, {len(existing_websites)} existing websites")

# Search queries (simulate browser search)
# We'll manually scrape specific known contact pages
contact_urls = [
    ("Lake Bled House", "https://www.lakebledhouse.com/en/contact/"),
    ("Konoba Varoš", "https://www.konobavaros.com/en/contact/"),
    ("Konoba Barkarola", "https://www.barkarola.hr/contact-us-now/"),
    ("The Restaurant Ljubljana", "https://www.therestaurant.si/en/contact/"),
    ("Restavracija Cubo", "https://www.visitljubljana.com/en/poi/restavracija-cubo/"),
    ("Špajza restaurant", "https://www.facebook.com/Spajzarestaurant/"),
    ("Konoba Koromačna", "https://konobakoromacna.com/en/contact-en/"),
    ("Konoba Skalinada", "https://www.konoba-skalinada.com/contact-2/"),
    ("Konoba Dubrava", "https://www.konobadubrava.com/contact/"),
    ("Khala Restaurant Zagreb", "https://khala.hr/en/contact/"),
    ("Noel Zagreb", "https://noel.hr/contact/"),
    ("Restaurant Zagreb", "https://restaurant-zagreb.com.hr/contact.html"),
    ("Old Cellar Bled", "https://www.oldcellarbled.com/en/contact/"),
    ("Bled Rose Hotel", "https://bledrose.com/en/contact-and-location/"),
]

def extract_email_from_text(text):
    # Simple regex to capture email patterns
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return emails

def fetch_and_parse(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        # Remove scripts, styles
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        # Get all email addresses
        emails = extract_email_from_text(text)
        # Try to find name from title
        name = None
        title = soup.find('title')
        if title:
            name = title.text.strip()
        # Try to find city/country from page content
        # simple heuristic: look for 'Slovenia', 'Croatia', 'Italy', 'Ljubljana', 'Zagreb', 'Bled', 'Split', etc.
        city = ""
        country = ""
        if re.search(r'\bSlovenia\b', text, re.IGNORECASE):
            country = "Slovenia"
            if re.search(r'\bLjubljana\b', text, re.IGNORECASE):
                city = "Ljubljana"
            elif re.search(r'\bBled\b', text, re.IGNORECASE):
                city = "Bled"
            elif re.search(r'\bMaribor\b', text, re.IGNORECASE):
                city = "Maribor"
            elif re.search(r'\bKoper\b', text, re.IGNORECASE):
                city = "Koper"
            elif re.search(r'\bPortorož\b', text, re.IGNORECASE):
                city = "Portorož"
        elif re.search(r'\bCroatia\b', text, re.IGNORECASE):
            country = "Croatia"
            if re.search(r'\bZagreb\b', text, re.IGNORECASE):
                city = "Zagreb"
            elif re.search(r'\bSplit\b', text, re.IGNORECASE):
                city = "Split"
            elif re.search(r'\bDubrovnik\b', text, re.IGNORECASE):
                city = "Dubrovnik"
            elif re.search(r'\bZadar\b', text, re.IGNORECASE):
                city = "Zadar"
            elif re.search(r'\bRovinj\b', text, re.IGNORECASE):
                city = "Rovinj"
        elif re.search(r'\bItaly\b', text, re.IGNORECASE):
            country = "Italy"
            if re.search(r'\bTrieste\b', text, re.IGNORECASE):
                city = "Trieste"
            elif re.search(r'\bFirenze\b', text, re.IGNORECASE):
                city = "Firenze"
            elif re.search(r'\bRoma\b', text, re.IGNORECASE):
                city = "Roma"
            elif re.search(r'\bMilano\b', text, re.IGNORECASE):
                city = "Milano"
        return emails, name, city, country, text[:2000]
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return [], None, "", "", ""

def extract_emails_from_url(url, name):
    emails, name2, city, country, _ = fetch_and_parse(url)
    if name2 and name is None:
        name = name2
    return emails, name, city, country

new_leads = []
seen_new_emails = set()
for display_name, url in contact_urls:
    print(f"Processing {display_name}...")
    emails, name, city, country = extract_emails_from_url(url, display_name)
    if not name:
        name = display_name
    for email in emails:
        email_lower = email.lower()
        if email_lower in existing_emails:
            print(f"  Skipping duplicate email: {email}")
            continue
        if email_lower in seen_new_emails:
            continue
        seen_new_emails.add(email_lower)
        # Determine website from URL base
        parsed = urlparse(url)
        website = f"{parsed.scheme}://{parsed.netloc}"
        new_leads.append({
            'name': name,
            'email': email,
            'city': city,
            'country': country,
            'website': website,
            'source': 'manual scraping'
        })
        print(f"  Added {email}")

# Add some more known emails from search results we cannot scrape (but we can add manually)
manual_leads = [
    # Slovenia
    ('Restaurant Milka', 'Kranjska Gora', 'Slovenia', 'info@hotelmilka.si', 'https://hotelmilka.si'),
    ('Hiša Franko', 'Kobarid', 'Slovenia', 'info@hisafranko.com', 'https://hisafranko.com'),
    ('Grič', 'Šentjošt nad Horjulom', 'Slovenia', 'info@gric.si', 'https://gric.si'),
    ('Hiša Denk', 'Zgornja Kungota', 'Slovenia', 'info@hisadenk.si', 'https://hisadenk.si'),
    ('Pavus', 'Laško', 'Slovenia', 'info@pavus.si', 'https://pavus.si'),
    ('Restaurant Majerca', 'Dol pri Vogljah', 'Slovenia', 'info@majerca.si', 'https://majerca.si'),
    ('Gostilna Krištof', 'Cerklje na Gorenjskem', 'Slovenia', 'info@gostilnakristof.si', 'https://gostilnakristof.si'),
    ('Gostilna Vovko', 'Mozirje', 'Slovenia', 'info@vovko.si', 'https://vovko.si'),
    ('Gostilna AS', 'Ljubljana', 'Slovenia', 'info@gostilnaas.si', 'https://gostilnaas.si'),
    ('Kendov Dvorec', 'Spodnja Idrija', 'Slovenia', 'info@kendov-dvorec.si', 'https://kendov-dvorec.si'),
    # Croatia
    ('Konoba Barkarola', 'Split', 'Croatia', 'konoba.barkarola1@gmail.com', 'https://barkarola.hr'),
    ('Konoba Nevera', 'Split', 'Croatia', 'booking@smokvina.hr', 'https://smokvina.hr'),
    ('Konoba Dalmatino', 'Bol', 'Croatia', 'drago.eterovic@gmail.com', 'https://konoba-dalmatino.eatbu.hr'),
    ('Konoba Boba', 'Brač', 'Croatia', 'reservation@konobaboba.hr', 'https://konobaboba.hr'),
    ('Dandy Restaurant', 'Dubrovnik', 'Croatia', 'konoba.dandy@gmail.com', 'https://dandy.hr'),
    ('Kenova', 'Dubrovnik', 'Croatia', 'booking@kenova.hr', 'https://kenova.hr'),
    ('Konoba Lanterna', 'Mlini', 'Croatia', 'ivo.masar@du.t-com.hr', 'https://dubrovnik-riviera.hr'),
    ('Gverovic Orsan', 'Dubrovnik', 'Croatia', 'restoran@gverovic-orsan.hr', 'https://gverovic-orsan.hr'),
    ('Restaurant Kasar', 'Zaton', 'Croatia', 'restoran.kasar@gmail.com', 'https://restaurant-kasar.hr'),
    ('Restoran Foša', 'Zadar', 'Croatia', 'info@fosa.hr', 'https://fosa.hr'),
    ('Konoba Momento', 'Zadar', 'Croatia', 'info@konoba-momento.hr', 'https://konoba-momento.hr'),
    ('Hotel Niko Zadar', 'Zadar', 'Croatia', 'hotel.niko@hotel-niko.hr', 'https://hotel-niko.hr'),
    ('Konoba M@re', 'Karin Gornji', 'Croatia', 'konobamare5@gmail.com', 'https://konoba-mare.eatbu.hr'),
    ('Marina Frapa', 'Rogoznica', 'Croatia', 'frapa@marinafrapa.hr', 'https://marinafrapa.hr'),
    # Italy
    ('Ristorante La Grotta Guelfa', 'Firenze', 'Italy', 'lagrottaguelfa@gmail.com', 'https://grottaguelfa.it'),
    ('Ristorante Villa Vecchia', 'Pratolino', 'Italy', 'info@ristorantevillavecchia.it', 'https://www.ristorantevillavecchia.it'),
    ('Ristorante La Martinicca', 'Firenze', 'Italy', 'info@ristorante-lamartinicca.com', 'https://www.ristorante-lamartinicca.com'),
    ('Taverna dei Servi', 'Firenze', 'Italy', 'tavernadeiservi.firenze@gmail.com', 'https://www.tavernadeiservifirenze.it'),
    ('Agriturismo La Terra', 'Valiano di Montepulciano', 'Italy', 'info@agriturismolaterra.it', 'https://www.agriturismolaterra.it'),
    ('Podere Montale', 'Grosseto', 'Italy', 'info@poderemontale.it', 'https://poderemontale.it'),
    ('Ristorante Il Ciociaro', 'Roma', 'Italy', 'info@ilciociaro.it', 'https://www.ilciociaro.it'),
    ('Ristorante Crispi19', 'Roma', 'Italy', 'info@ristorantecrispi19.it', 'https://ristorantecrispi19.it'),
    ('Ristorante Tiberino', 'Roma', 'Italy', 'info@tiberinoroma.it', 'https://www.tiberinoroma.it'),
    ('CiPASSO Roma', 'Roma', 'Italy', 'cipasso.roma@gmail.com', 'https://www.cipassoitalia.it'),
]

for name, city, country, email, website in manual_leads:
    email_lower = email.lower()
    if email_lower in existing_emails:
        continue
    if email_lower in seen_new_emails:
        continue
    seen_new_emails.add(email_lower)
    new_leads.append({
        'name': name,
        'email': email,
        'city': city,
        'country': country,
        'website': website,
        'source': 'manual addition'
    })

print(f"Total new leads collected: {len(new_leads)}")

# Write to CSV
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
fieldnames = ['name', 'email', 'city', 'country', 'website', 'source']
with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for lead in new_leads:
        writer.writerow(lead)

print(f"Saved to {OUTPUT_FILE}")
print("Done.")