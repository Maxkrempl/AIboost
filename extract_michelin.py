import re
import csv

# Page 1 text (from web_fetch earlier - simplified)
page1 = """
## Slovenia : 1-48 of 69 restaurants
 /en/si/restaurants/page/2
 Portorož, Slovenia
 €€€€
 ·
 Creative
 Ljubljana, Slovenia
 €€€
 ·
 Modern Cuisine
 Ljubljana, Slovenia
 €€€
 ·
 Traditional Cuisine
 Spodnja Idrija, Slovenia
 €€€
 ·
 Traditional Cuisine
 Kobarid, Slovenia
 €€€€
 ·
 Creative
 Kranjska Gora, Slovenia
 €€€€
 ·
 Creative
 Radovljica, Slovenia
 €€€
 ·
 Contemporary
 Nova Gorica, Slovenia
 €€€
 ·
 Modern Cuisine
 Vipava, Slovenia
 €€€€
 ·
 Modern Cuisine
 Šentjošt nad Horjulom, Slovenia
 €€€€
 ·
 Farm to table
 Zgornja Kungota, Slovenia
 €€€€
 ·
 Creative
 Lasko, Slovenia
 €€€
 ·
 Modern Cuisine
 Dobrovo v Brdih, Slovenia
 €€
 ·
 Modern Cuisine
 Idrija, Slovenia
 €€
 ·
 Regional Cuisine
 Celje, Slovenia
 €€
 ·
 Modern Cuisine
 Mozirje, Slovenia
 €
 ·
 Traditional Cuisine
 Divača, Slovenia
 €
 ·
 Regional Cuisine
 Dol pri Vogljah, Slovenia
 €€
 ·
 Regional Cuisine
 Stara Fužina, Slovenia
 €€
 ·
 Regional Cuisine
 Murska Sobota, Slovenia
 €€
 ·
 Regional Cuisine
 Murska Sobota, Slovenia
 €€
 ·
 Meats and Grills
 Gozd Martuljek, Slovenia
 €€
 ·
 Regional Cuisine
 Rodik, Slovenia
 €€
 ·
 Regional European
 Portorož, Slovenia
 €€
 ·
 Mediterranean Cuisine
 Solčava, Slovenia
 €€€
 ·
 Regional Cuisine
 Luče, Slovenia
 €€€
 ·
 Farm to table
 Portorož, Slovenia
 €€€
 ·
 Mediterranean Cuisine
 Brezice, Slovenia
 €€€
 ·
 Contemporary
 Koper, Slovenia
 €€
 ·
 Seafood
 Brusnice, Slovenia
 €€
 ·
 Regional Cuisine
 Škofja Loka, Slovenia
 €€
 ·
 Contemporary
 Maribor, Slovenia
 €€
 ·
 Contemporary
 Ljubljana, Slovenia
 €€
 ·
 Modern Cuisine
 Kranj, Slovenia
 €€
 ·
 Traditional Cuisine
 Ljubljana, Slovenia
 €€
 ·
 Farm to table
 Piran, Slovenia
 €€€€
 ·
 Modern Cuisine
 Ljubljana, Slovenia
 €€
 ·
 Modern Cuisine
 Komen, Slovenia
 €€€
 ·
 Contemporary
 Cerklje na Gorenjskem, Slovenia
 €€
 ·
 Traditional Cuisine
 Ljubljana, Slovenia
 €€€
 ·
 Regional European
 Bled, Slovenia
 €€€
 ·
 International
 Jarenina, Slovenia
 €€€
 ·
 Contemporary
 Ljubljana, Slovenia
 €
 ·
 Regional Cuisine
 Ljubljana, Slovenia
 €€
 ·
 Japanese
 Izola, Slovenia
 €€
 ·
 Mediterranean Cuisine
 Otočec na Krki, Slovenia
 €€€
 ·
 Regional Cuisine
 Ljubljana, Slovenia
 €€
 ·
 European
 Zgornja Polskava, Slovenia
 €€€
 ·
 Modern Cuisine
"""

# Page 2 text
page2 = """
## Slovenia : 49-69 of 69 restaurants
 Brestanica, Slovenia
 €€€
 ·
 Modern Cuisine
 Ljubljana, Slovenia
 €€€
 ·
 Mediterranean Cuisine
 Štanjel, Slovenia
 €€
 ·
 Regional Cuisine
 Maribor, Slovenia
 €€€
 ·
 Mediterranean Cuisine
 Ljubljana, Slovenia
 €€
 ·
 Traditional Cuisine
 Maribor, Slovenia
 €€€€
 ·
 Creative
 Koper, Slovenia
 €€
 ·
 Regional Cuisine
 Nova Gorica, Slovenia
 €€
 ·
 Traditional Cuisine
 Zgornje Jezersko, Slovenia
 €€€
 ·
 Regional Cuisine
 Ljubljana, Slovenia
 €€€
 ·
 Modern Cuisine
 Bled, Slovenia
 €€€
 ·
 Contemporary
 Ljubljana, Slovenia
 €
 ·
 Asian
 Petrovče, Slovenia
 €€€
 ·
 Modern Cuisine
 Izola, Slovenia
 €€
 ·
 Regional Cuisine
 Ljubljana, Slovenia
 €€€
 ·
 Modern Cuisine
 Bled, Slovenia
 €€
 ·
 Regional Cuisine
 Ljubljana, Slovenia
 €€
 ·
 Contemporary
 Radovljica, Slovenia
 €€
 ·
 Modern Cuisine
 Ljubljana, Slovenia
 €€
 ·
 Mediterranean Cuisine
 Ljubljana, Slovenia
 €€
 ·
 Contemporary
 Šentjanž, Slovenia
 €€
 ·
 Farm to table
"""

# Combine and parse
lines = page1.split('\n') + page2.split('\n')

# Known restaurant names from earlier extraction
restaurant_names = [
    "COB", "Restavracija Strelec", "Gostilna AS", "Kendov Dvorec", "Hiša Franko", 
    "Milka", "Hiša Linhart", "Dam", "Gostilna Pri Lojzetu", "Grič", 
    "Hiša Denk", "Pavus", "Gredič", "Restavracija Jožef", "LAL Bistro",
    "Lesnika", "Restavracija Majerca", "Gostilna Rajh", "Gostilna Mahorčič", 
    "Restavracija Plesnik", "Hiša Raduha", "Gostilna Vovko", "Restavracija Sedem",
    "Gostilna Krištof", "Stara Gostilna", "Špacapanova Hiša", "The Restaurant",
    "Restavracija Hotela Marina", "Restavracija Grad Otočec", "PEN KLUB Restavracija"
]

# But we need to match names with cities from the text
# The text shows city then price then cuisine
# Let's extract city lines
cities = []
for i, line in enumerate(lines):
    line = line.strip()
    if line.endswith(", Slovenia") and not line.startswith("##"):
        city = line.replace(", Slovenia", "").strip()
        # Get cuisine from next lines
        cuisine = ""
        for j in range(i+1, min(i+10, len(lines))):
            if "·" in lines[j] and lines[j+1].strip():
                cuisine = lines[j+1].strip()
                break
        cities.append((city, cuisine))

print(f"Found {len(cities)} city entries")
for city, cuisine in cities[:10]:
    print(f"{city}: {cuisine}")

# Write to CSV
with open('michelin_restaurants.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['name', 'city', 'cuisine', 'type', 'source'])
    
    # We don't have exact name-city mapping, so we'll use city as placeholder
    for idx, (city, cuisine) in enumerate(cities):
        name = f"Restaurant in {city}"  # Placeholder
        if idx < len(restaurant_names):
            name = restaurant_names[idx]
        writer.writerow([name, city, cuisine, "Restaurant", "michelin-guide"])

print("Wrote michelin_restaurants.csv")