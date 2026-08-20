import re
import csv
import requests
from bs4 import BeautifulSoup

# The article text from web_fetch
article_text = """
Hiša Franko maintains Three MICHELIN Stars
Offering culinary creations that stand at the pinnacle of global gastronomy, [Hiša Franko](https://guide.michelin.com/si/en/gorizia/kobarid/restaurant/hisa-franko) has maintained its Three MICHELIN Stars and MICHELIN Green Star for another year. A true culinary landmark in Slovenia, Hiša Franko takes guests on a singular journey through the country’s local produce and terroirs — masterfully interpreted by the extroverted and inventive Chef Ana Roš.
At the Two Star level, [Milka](https://guide.michelin.com/si/en/upper-carniola/kranjska-gora/restaurant/milka)(Kranjska Gora) also maintains its distinction, demonstrating impressive consistency in offering "excellent cuisine, worth a detour." Here, Chef David Žefran and his team present a refined gastronomic synthesis of the region — skillfully interpreted and prepared, with a deep emphasis on local ingredients.
Finally, seven restaurants across the country have once again impressed the MICHELIN Inspectors and have retained their One MICHELIN Star: [Grič](https://guide.michelin.com/si/en/lower-carniola/sentjost-nad-horjulom/restaurant/gostisce-gric), [Hiša Linhart](https://guide.michelin.com/si/en/upper-carniola/radovljica/restaurant/hisa-linhart), [Dam](https://guide.michelin.com/si/en/gorizia/nova-gorica/restaurant/dam), [Gostilna Pri Lojzetu](https://guide.michelin.com/si/en/gorizia/vipava/restaurant/pri-lojzetu), [COB](https://guide.michelin.com/si/en/coastal%E2%80%93karst/portoroz/restaurant/cob), [Hiša Denk](https://guide.michelin.com/si/en/drava/zgornja-kungota/restaurant/hisa-denk), and [Pavus](https://guide.michelin.com/si/en/savinja/lasko/restaurant/pavus).
Across all categories, Slovenia boasts nine MICHELIN-Starred restaurants — confirming its status as a noteworthy gastronomic destination in Europe.

## Plesnik sees its inspiring commitments to a more eco-friendly gastronomy rewarded the MICHELIN Green Star
The MICHELIN Green Star rewards the initiatives of groundbreaking restaurants that fully commit to rethinking their impact and encouraging a strong gastronomic transition. One restaurant is newly awarded the MICHELIN Green Star for its remarkable philosophy and commitment toward a more eco-friendly approach to gastronomy.
[Plesnik](https://guide.michelin.com/si/en/savinja/solcava_2575166/restaurant/plesnik), newly entering the main selection this year, stands out with its holistic 360° approach dedicated to respecting nature and the local environment. Located in the heart of the Logar Valley, its cuisine embodies two distinct yet harmonious souls: on one hand, it honors the historic recipes of Marija Plesnik, who cooked here in the 1940s; on the other, it offers a refined tasting menu oriented toward fine dining. Throughout, there is meticulous attention to local ingredients, many of which — especially meat and vegetables — come directly from the restaurant’s own farm.
With this new awarded restaurant, and together with the 8 eateries which retain their distinction this year, Slovenia now boasts 9 MICHELIN Green Star establishments, whose commitment to reshaping gastronomy is a source of inspiration.

## Three restaurants newly awarded a Bib Gourmand
Within the MICHELIN Guide's restaurant selection, the Bib Gourmand distinction highlights establishments that stand out for their excellent value for money and offer a complete meal at an affordable price.
A new entry to the selection with a Bib Gourmand, [Lesnika](https://guide.michelin.com/si/en/savinja/mozirje_2579692/restaurant/lesnika)is a charming restaurant located in Mozirije, a small town along the Savinja River. Also functioning as a bar and a social hub for the local community, it offers an generous and well-crafted traditional cuisine.
Two previously selected restaurants have been promoted to the Bib Gourmand category, reflecting the continued rise in their culinary standards while maintaining accessible pricing: [Gredič](https://guide.michelin.com/si/en/gorizia/dobrovo-v-brdih/restaurant/gredic)(Dobrovo v Brdih), whose cuisine blends Mediterranean and Central Europe influences, and [Etna](https://guide.michelin.com/si/en/coastal%E2%80%93karst/divaca/restaurant/etna)(Divača), which offers fresh Mediterranean-inspired dishes.
Together with the nine restaurants that have retained their Bib Gourmand distinction from last year, these three new additions bring the total number of establishments recognized for outstanding value for money in Slovenia to 12.

## Nine restaurants newly recommended for their high-quality cuisine join the main selection
In addition to Starred and Bib Gourmand restaurants, the MICHELIN Guide inspectors also recommend restaurants that impress with their high-quality cuisine.
Nine new restaurants, discovered during the Inspectors’ annual explorations, have been added to the main selection — bringing the total number of Selected restaurants in Slovenia to 51.
Among them is Jaz by Ana Roš, located in the heart of the capital. This welcoming contemporary bistro offers a lively atmosphere where gourmets can enjoy easygoing and playful cuisine. Salicornia, in Koper, features excellent seafood dishes inspired by the daily market. Grad Štanjel Restaurant & Lounge Bar is an outstanding gourmet bistro situated in the historic village of Štanjel.
Other new entries to the main selection are:
-	[Old Cellar Bled (Bled)](https://guide.michelin.com/si/en/upper-carniola/bled/restaurant/old-cellar-bled)
-	[Hiša Raduha (Luče)](https://guide.michelin.com/si/en/savinja/luce_2579382/restaurant/hisa-raduha)
0   [Dveri Pax (Jarenina)](https://guide.michelin.com/si/en/drava/jarenina_7770421/restaurant/dveri-pax)
"""

# Parse markdown links
pattern = r'\[([^\]]+)\]\([^\)]+\)(?:\(([^\)]+)\))?'
matches = re.findall(pattern, article_text)

restaurants = []
for name, city in matches:
    if city:
        restaurants.append((name.strip(), city.strip()))
    else:
        # Try to extract city from context
        restaurants.append((name.strip(), ""))

# Also extract named restaurants without links
# Look for "restaurant names (city)" pattern
pattern2 = r'([A-Za-zčšžĆŠŽ\s\-\'\.]+) \(([^\)]+)\)'
matches2 = re.findall(pattern2, article_text)
for name, city in matches2:
    restaurants.append((name.strip(), city.strip()))

# Deduplicate
restaurants = list(dict.fromkeys(restaurants))

print(f"Found {len(restaurants)} restaurants")
for name, city in restaurants:
    print(f"{name} - {city}")

# Write to CSV
with open('michelin_from_article.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['name', 'city', 'type', 'source'])
    for name, city in restaurants:
        writer.writerow([name, city, 'Restaurant', 'michelin-guide-2025'])

print("Wrote michelin_from_article.csv")

# Now fetch the list of all 72 restaurants from the Michelin website
# We'll search for the full list
# For now, we have a good start