#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
import csv
import time
import sys

def scrape_michelin_page(url):
    """Scrape a single Michelin page for restaurant names and locations."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    restaurants = []
    
    # Look for restaurant cards - this is a heuristic; adjust as needed
    # The page seems to list items with structure: city, price, cuisine
    # Actually let's try a simpler approach: extract all text and parse lines
    text = soup.get_text('\n')
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Look for patterns: "City, Slovenia" followed by price and cuisine
    # But the page structure is complex. Let's try to find restaurant names
    # by looking for h2/h3 tags with links
    
    # Another approach: look for data attributes or classes
    # Let's search for any element with "restaurant" in class
    cards = soup.find_all('div', class_=lambda c: c and ('card' in c or 'restaurant' in c))
    if not cards:
        # Try looking for list items
        cards = soup.find_all('li')
    
    # Fallback: extract all text and manually parse
    # The Michelin page shows "City, Slovenia" then price then cuisine
    # We'll implement a simple regex pattern
    pattern = r'([A-Za-zčšžĆŠŽ\s\-\']+),\s+Slovenia\s+[€$£¥]+\s+·\s+([A-Za-z\s]+)'
    matches = re.findall(pattern, text)
    
    # Also look for restaurant names in h2/h3 tags
    for tag in soup.find_all(['h2', 'h3', 'h4']):
        text = tag.get_text(strip=True)
        if text and len(text) > 3 and not text.isdigit():
            # Check if it might be a restaurant name
            if any(word in text.lower() for word in ['restaurant', 'gostilna', 'hiša', 'pri', 'tavern']):
                print(f"Potential restaurant: {text}")
    
    return matches

def main():
    base_url = "https://guide.michelin.com/en/si/restaurants"
    all_restaurants = []
    
    # Try first page
    print(f"Fetching {base_url}")
    matches = scrape_michelin_page(base_url)
    print(f"Found {len(matches)} matches")
    print(matches[:10])
    
    # Try page 2
    url2 = base_url + "/page/2"
    print(f"Fetching {url2}")
    matches2 = scrape_michelin_page(url2)
    print(f"Found {len(matches2)} more matches")
    
    all_matches = matches + matches2
    
    # Write to CSV
    with open('michelin_temp.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'city', 'cuisine'])
        for city, cuisine in all_matches:
            writer.writerow(['', city, cuisine])
    
    print(f"Total matches: {len(all_matches)}")

if __name__ == '__main__':
    main()