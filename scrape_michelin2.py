import requests
from bs4 import BeautifulSoup
import csv
import re
import time

def extract_restaurants_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    restaurants = []
    
    # Look for restaurant cards - inspecting the page shows cards with data-restaurant-id
    cards = soup.find_all('div', {'data-restaurant-id': True})
    print(f"Found {len(cards)} cards with data-restaurant-id")
    
    if not cards:
        # Try alternative: look for h3 tags with restaurant names
        for h3 in soup.find_all('h3'):
            text = h3.get_text(strip=True)
            if text and len(text) > 2 and not text.isdigit():
                # Find next city information
                parent = h3.parent
                # Look for city in parent or siblings
                city_elem = parent.find('span', class_=lambda c: c and ('locality' in c or 'city' in c))
                if not city_elem:
                    # Try to find text with "Slovenia"
                    for elem in parent.find_all(text=True):
                        if 'Slovenia' in elem:
                            city = elem.split(',')[0].strip()
                            restaurants.append((text, city))
                            break
    
    # If still nothing, try regex on the whole text
    if not restaurants:
        text = soup.get_text('\n')
        # Pattern for restaurant name (looks like it might be in h3 tags)
        # Actually let's look for the structure: name, city, price, cuisine
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line.endswith(", Slovenia") and not line.startswith("##"):
                city = line.replace(", Slovenia", "").strip()
                # Go backwards to find restaurant name
                for j in range(max(0, i-5), i):
                    if lines[j].strip() and len(lines[j].strip()) > 2:
                        # Check if it's not a price or other metadata
                        if not any(marker in lines[j] for marker in ['€', '$', '·', 'Slovenia', 'of', 'restaurants']):
                            name = lines[j].strip()
                            restaurants.append((name, city))
                            break
    
    return restaurants

def main():
    # Fetch page 1
    url1 = "https://guide.michelin.com/en/si/restaurants"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        print(f"Fetching {url1}")
        r1 = requests.get(url1, headers=headers, timeout=10)
        r1.raise_for_status()
        restaurants1 = extract_restaurants_from_html(r1.text)
        print(f"Page 1: {len(restaurants1)} restaurants")
        
        # Fetch page 2
        url2 = url1 + "/page/2"
        print(f"Fetching {url2}")
        r2 = requests.get(url2, headers=headers, timeout=10)
        r2.raise_for_status()
        restaurants2 = extract_restaurants_from_html(r2.text)
        print(f"Page 2: {len(restaurants2)} restaurants")
        
        all_restaurants = restaurants1 + restaurants2
        
        # Write to CSV
        with open('michelin_extracted.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'city', 'type', 'source'])
            for name, city in all_restaurants:
                writer.writerow([name, city, 'Restaurant', 'michelin-guide'])
        
        print(f"Total restaurants extracted: {len(all_restaurants)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()