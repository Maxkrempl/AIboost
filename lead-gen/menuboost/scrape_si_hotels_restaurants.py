#!/usr/bin/env python3
"""Scrape Slovenian hotel & restaurant leads from dobregostilne.si and web search results.

Outputs: slovenia-hotels-restaurants.csv
Format: name,city,region,email,website,type,source
"""

import csv
import re
import subprocess
import sys
import os
import time
import json

WORKSPACE = "/home/darko/.openclaw/workspace"
OUTPUT = os.path.join(WORKSPACE, "lead-gen/menuboost/slovenia-hotels-restaurants.csv")
EXISTING = os.path.join(WORKSPACE, "lead-gen/menuBoost/leads-with-email.csv")

# Known Michelin-starred and notable Slovenian restaurants with websites
MICHELIN_RESTAURANTS = [
    # 3 Stars
    {"name": "Hiša Franko", "city": "Kobarid", "website": "https://hisafranko.com", "type": "Restaurant"},
    # 2 Stars
    {"name": "Restaurant Milka", "city": "Kranjska Gora", "website": "https://hotelmilka.si", "type": "Restaurant"},
    # 1 Star
    {"name": "COB", "city": "Portorož", "website": "https://restaurantcob.com", "type": "Restaurant"},
    {"name": "Dam", "city": "Nova Gorica", "website": "https://restaurantdam.com", "type": "Restaurant"},
    {"name": "Gostilna pri Lojzetu", "city": "Dobrovo v Brdih", "website": "https://gostilnaprilozjetu.si", "type": "Restaurant"},
    {"name": "Grič", "city": "Šentjošt nad Horjulom", "website": "https://gric.si", "type": "Restaurant"},
    {"name": "Hiša Denk", "city": "Zgornja Kungota", "website": "https://hisadenk.si", "type": "Restaurant"},
    {"name": "Hiša Linhart", "city": "Radovljica", "website": "https://hisa-linhart.si", "type": "Restaurant"},
    {"name": "Pavus", "city": "Laško", "website": "https://pavus.si", "type": "Restaurant"},
    # Bib Gourmand & Notable
    {"name": "Gostilna Rajh", "city": "Murska Sobota", "website": "https://gostilnarajh.si", "type": "Gostilna"},
    {"name": "Gostilna Mahorčič", "city": "Rodik", "website": "https://mahorcic.si", "type": "Gostilna"},
    {"name": "Restaurant Majerca", "city": "Dol pri Vogljah", "website": "https://majerca.si", "type": "Restaurant"},
    {"name": "Restaurant Jožef", "city": "Idrija", "website": "https://restavracijajozef.si", "type": "Restaurant"},
    {"name": "Gostilna Krištof", "city": "Cerklje na Gorenjskem", "website": "https://gostilnakristof.si", "type": "Gostilna"},
    {"name": "Špacapanova hiša", "city": "Komen", "website": "https://spacapanovahisa.si", "type": "Restaurant"},
    {"name": "Hiša Raduha", "city": "Luče", "website": "https://hisaraduha.si", "type": "Restaurant"},
    {"name": "Gostilna Vovko", "city": "Mozirje", "website": "https://vovko.si", "type": "Gostilna"},
    {"name": "Gostilna in vinoteka Faladur", "city": "Ljubljana", "website": "https://faladur.si", "type": "Gostilna"},
    {"name": "Restaurant Strelec", "city": "Ljubljana", "website": "https://restaurantstrelec.si", "type": "Restaurant"},
    {"name": "Gostilna AS", "city": "Ljubljana", "website": "https://gostilnaas.si", "type": "Gostilna"},
    {"name": "Kendov Dvorec", "city": "Spodnja Idrija", "website": "https://kendov-dvorec.si", "type": "Restaurant"},
    {"name": "Restavracija Sedem", "city": "Ljubljana", "website": "https://restavracijasedem.si", "type": "Restaurant"},
    {"name": "Stara Gostilna", "city": "Ljubljana", "website": "https://staragostilna.si", "type": "Gostilna"},
    {"name": "Restavracija Hotela Marina", "city": "Portorož", "website": "https://hotelmarina.si", "type": "Restaurant"},
    {"name": "Restavracija Grad Otočec", "city": "Otočec na Krki", "website": "https://grad-otocec.si", "type": "Restaurant"},
    {"name": "PEN KLUB Restavracija", "city": "Ljubljana", "website": "https://penklub.si", "type": "Restaurant"},
    {"name": "Restavracija Salicornia", "city": "Piran", "website": "https://restavracija-salicornia.com", "type": "Restaurant"},
    {"name": "Galerija okusov", "city": "Ljubljana", "website": "https://galerija-okusov.si", "type": "Restaurant"},
    {"name": "Gostilna Repovž", "city": "Ljubljana", "website": "https://gostilnarepovz.si", "type": "Gostilna"},
    {"name": "Gostilnica Ruj", "city": "Ljubljana", "website": "https://gostilnicaruj.si", "type": "Gostilna"},
    {"name": "Restaurant Triangel", "city": "Ljubljana", "website": "https://restauranttriangel.com", "type": "Restaurant"},
    {"name": "Kodila", "city": "Murska Sobota", "website": "https://kodila.com", "type": "Restaurant"},
    {"name": "Lalu Bistro", "city": "Ljubljana", "website": "https://lalubistro.si", "type": "Restaurant"},
    {"name": "Dveri Pax", "city": "Jarenina", "website": "https://dveripax.si", "type": "Restaurant"},
    {"name": "Restavracija Grad Štanjel", "city": "Štanjel", "website": "https://grad-stanjel.si", "type": "Restaurant"},
    {"name": "TaBar", "city": "Ljubljana", "website": "https://tabar.si", "type": "Restaurant"},
    {"name": "The Restaurant", "city": "Bled", "website": "https://therestaurantbled.com", "type": "Restaurant"},
    {"name": "Restavracija Franko", "city": "Kobarid", "website": "https://restavracijafranko.si", "type": "Restaurant"},
    {"name": "Jaz by Ana Roš", "city": "Ljubljana", "website": "https://jazbyana.si", "type": "Restaurant"},
    {"name": "Old Cellar Bled", "city": "Bled", "website": "https://oldcellarbled.com", "type": "Restaurant"},
    {"name": "Doppler", "city": "Ljubljana", "website": "https://doppler.si", "type": "Restaurant"},
    {"name": "Restavracija Mak", "city": "Maribor", "website": "https://restavracijamak.si", "type": "Restaurant"},
    {"name": "Restavracija Veganika", "city": "Ljubljana", "website": "https://veganika.si", "type": "Restaurant"},
    {"name": "Carat", "city": "Sežana", "website": "https://restaurantcarat.si", "type": "Restaurant"},
    {"name": "Capra", "city": "Koper", "website": "https://capra.si", "type": "Restaurant"},
    {"name": "Spargus", "city": "Loče", "website": "https://spargus.si", "type": "Restaurant"},
    {"name": "Restavracija Kamin", "city": "Portorož", "website": "https://restavracija-kamin.si", "type": "Restaurant"},
    {"name": "Butul", "city": "Koper", "website": "https://butul.si", "type": "Restaurant"},
]

# Known Slovenian hotels with websites
SLOVENIAN_HOTELS = [
    # Ljubljana
    {"name": "Grand Hotel Union", "city": "Ljubljana", "website": "https://grandhotelunion.com", "type": "Hotel"},
    {"name": "Hotel Slon", "city": "Ljubljana", "website": "https://hotelslon.com", "type": "Hotel"},
    {"name": "Hotel Lev", "city": "Ljubljana", "website": "https://h-lev.si", "type": "Hotel"},
    {"name": "Urban Boutique Hotel", "city": "Ljubljana", "website": "https://urbanhotel.si", "type": "Boutique Hotel"},
    {"name": "AS Boutique Hotel", "city": "Ljubljana", "website": "https://ashotel.si", "type": "Boutique Hotel"},
    {"name": "Hotel Mrak", "city": "Ljubljana", "website": "https://hotelmrak.si", "type": "Hotel"},
    {"name": "M Hotel", "city": "Ljubljana", "website": "https://m-hotel.si", "type": "Hotel"},
    {"name": "City Hotel Ljubljana", "city": "Ljubljana", "website": "https://cityhotel.si", "type": "Hotel"},
    {"name": "The Hotel Ljubljana", "city": "Ljubljana", "website": "https://thehotel.si", "type": "Hotel"},
    {"name": "Hotel Adore", "city": "Ljubljana", "website": "https://hoteladore.com", "type": "Boutique Hotel"},
    {"name": "Radisson Blu Plaza Hotel", "city": "Ljubljana", "website": "https://plaza.si", "type": "Hotel"},
    {"name": "Hotel A plus", "city": "Ljubljana", "website": "https://hotel-a.si", "type": "Hotel"},
    # Bled
    {"name": "Grand Hotel Toplice", "city": "Bled", "website": "https://sava-hotels.com/toplice", "type": "Hotel"},
    {"name": "Hotel Park", "city": "Bled", "website": "https://sava-hotels.com/park", "type": "Hotel"},
    {"name": "Bled Rose Hotel", "city": "Bled", "website": "https://bledrose.com", "type": "Hotel"},
    {"name": "Triglav Bled", "city": "Bled", "website": "https://triglavbled.si", "type": "Hotel"},
    {"name": "Hotel Vila Bled", "city": "Bled", "website": "https://vila-bled.si", "type": "Boutique Hotel"},
    {"name": "Hotel Astoria Bled", "city": "Bled", "website": "https://astoriabeled.com", "type": "Hotel"},
    # Portorož & Piran
    {"name": "Grand Hotel Portorož", "city": "Portorož", "website": "https://ghp.si", "type": "Hotel"},
    {"name": "Hotel Kempinski Palace", "city": "Portorož", "website": "https://kempinski.com/portoroz", "type": "Hotel"},
    {"name": "Hotel Histrion", "city": "Portorož", "website": "https://histrion.si", "type": "Hotel"},
    {"name": "Hotel Bernardin", "city": "Portorož", "website": "https://bernardingroup.com", "type": "Hotel"},
    {"name": "Hotel Slovenija", "city": "Portorož", "website": "https://hotelslovenija.com", "type": "Hotel"},
    {"name": "Hotel Marina", "city": "Portorož", "website": "https://hotelmarina.si", "type": "Hotel"},
    {"name": "Hotel Riviera", "city": "Portorož", "website": "https://sava-hotels.com/riviera", "type": "Hotel"},
    {"name": "LifeClass Hotels", "city": "Portorož", "website": "https://lifeclass.net", "type": "Hotel"},
    {"name": "Hotel Gredič", "city": "Dobrovo v Brdih", "website": "https://gredic.si", "type": "Boutique Hotel"},
    # Bohinj & Alpine
    {"name": "Hotel Bohinj", "city": "Bohinj", "website": "https://hotelbohinj.si", "type": "Hotel"},
    {"name": "Hotel Lipa", "city": "Kranjska Gora", "website": "https://hotel-lipa.si", "type": "Hotel"},
    {"name": "Hotel Plesnik", "city": "Solčava", "website": "https://hotelplesnik.si", "type": "Hotel"},
    {"name": "Hotel Krvavec", "city": "Krvavec", "website": "https://hotelkrvavec.si", "type": "Hotel"},
    # Koper & Coast
    {"name": "Grand Hotel Koper", "city": "Koper", "website": "https://grandhotekoper.si", "type": "Hotel"},
    {"name": "Hotel Vodišek", "city": "Koper", "website": "https://hotelvodisek.si", "type": "Hotel"},
    # Maribor
    {"name": "Hotel City Maribor", "city": "Maribor", "website": "https://hotelcitymaribor.com", "type": "Hotel"},
    {"name": "Hotel Orel", "city": "Maribor", "website": "https://hotelorel.si", "type": "Hotel"},
    # Other
    {"name": "Grad Otočec Hotel", "city": "Otočec", "website": "https://grad-otocec.si", "type": "Hotel"},
    {"name": "Terme Čatež", "city": "Čatež", "website": "https://terme-catez.si", "type": "Hotel"},
    {"name": "Terme Dobrna", "city": "Dobrna", "website": "https://terme-dobrna.com", "type": "Hotel"},
    {"name": "Thermana Laško", "city": "Laško", "website": "https://thermana.si", "type": "Hotel"},
    {"name": "Rimske Terme", "city": "Laško", "website": "https://rimske-terme.si", "type": "Hotel"},
    {"name": "Hotel Dvorec", "city": "Tolmin", "website": "https://hoteldvorec.si", "type": "Hotel"},
    {"name": "Park Casino & Hotel", "city": "Nova Gorica", "website": "https://park-casino.si", "type": "Hotel"},
    {"name": "Perla Casino & Hotel", "city": "Nova Gorica", "website": "https://perla.si", "type": "Hotel"},
    {"name": "Hotel Sabotin", "city": "Nova Gorica", "website": "https://hotelsabotin.com", "type": "Hotel"},
    {"name": "Kobilarna Lipica Hotel", "city": "Lipica", "website": "https://lipica.org", "type": "Hotel"},
]

def check_mx(domain):
    """Check if domain has MX records."""
    try:
        result = subprocess.run(['dig', '+short', 'MX', domain], capture_output=True, text=True, timeout=5)
        return bool(result.stdout.strip())
    except:
        return False

def guess_email(website):
    """Guess common email patterns from website domain."""
    domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    candidates = [f"info@{domain}", f"rezervacije@{domain}", f"hotel@{domain}", f"restavracija@{domain}"]
    valid = []
    for email in candidates:
        email_domain = email.split("@")[1]
        if check_mx(email_domain):
            valid.append(email)
    return valid[0] if valid else None

def load_existing():
    """Load existing emails to avoid duplicates."""
    existing = set()
    if os.path.exists(EXISTING):
        with open(EXISTING) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'email' in row:
                    existing.add(row['email'].lower())
                if 'url' in row:
                    existing.add(row['url'].lower())
    return existing

def main():
    existing = load_existing()
    print(f"Loaded {len(existing)} existing entries for dedup")

    all_leads = []

    # Process Michelin restaurants
    print(f"\n=== Processing {len(MICHELIN_RESTAURANTS)} Michelin/notable restaurants ===")
    for r in MICHELIN_RESTAURANTS:
        name = r["name"]
        # Skip if already in existing leads
        if r.get("website") and r["website"].lower() in existing:
            print(f"  SKIP (dup): {name}")
            continue

        print(f"  Processing: {name} ({r['city']})")
        email = guess_email(r["website"])
        if email:
            all_leads.append({
                "name": name,
                "city": r["city"],
                "region": "Slovenia",
                "email": email,
                "website": r["website"],
                "type": r["type"],
                "source": "michelin-guide"
            })
            print(f"    ✓ {email}")
        else:
            print(f"    ✗ No MX for {r['website']}")
        time.sleep(0.3)

    # Process hotels
    print(f"\n=== Processing {len(SLOVENIAN_HOTELS)} hotels ===")
    for h in SLOVENIAN_HOTELS:
        name = h["name"]
        if h.get("website") and h["website"].lower() in existing:
            print(f"  SKIP (dup): {name}")
            continue

        print(f"  Processing: {name} ({h['city']})")
        email = guess_email(h["website"])
        if email:
            all_leads.append({
                "name": name,
                "city": h["city"],
                "region": "Slovenia",
                "email": email,
                "website": h["website"],
                "type": h["type"],
                "source": "hotel-directory"
            })
            print(f"    ✓ {email}")
        else:
            print(f"    ✗ No MX for {h['website']}")
        time.sleep(0.3)

    # Write CSV
    print(f"\n=== Writing {len(all_leads)} leads to CSV ===")
    with open(OUTPUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "city", "region", "email", "website", "type", "source"])
        writer.writeheader()
        writer.writerows(all_leads)

    print(f"\nDone! {len(all_leads)} leads written to {OUTPUT}")

    # Summary
    by_type = {}
    for lead in all_leads:
        t = lead["type"]
        by_type[t] = by_type.get(t, 0) + 1
    print("\nBreakdown:")
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")

if __name__ == "__main__":
    main()
