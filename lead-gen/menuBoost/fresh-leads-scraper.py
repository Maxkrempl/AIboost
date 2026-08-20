#!/usr/bin/env python3
"""
Scrape new restaurant/tourist farm leads for MenuBoost.
"""
import csv
import os
import re
import requests
from bs4 import BeautifulSoup
import time
import sys

# Paths
EXISTING_DIR = "/home/darko/.openclaw/workspace/lead-gen"
OUTPUT_FILE = "/home/darko/.openclaw/workspace/lead-gen/menuBoost/fresh-leads-TODAY.csv"

# Load existing emails and websites to avoid duplicates
existing_emails = set()
existing_websites = set()

def load_existing():
    for root, dirs, files in os.walk(EXISTING_DIR):
        for file in files:
            if file.endswith(".csv"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
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
                    print(f"Error reading {path}: {e}")

load_existing()
print(f"Loaded {len(existing_emails)} existing emails, {len(existing_websites)} existing websites")

# Search queries for target regions
queries = [
    "restaurant Ljubljana email",
    "restaurant Bled email",
    "turistična kmetija Slovenia email",
    "restaurant Zagreb email",
    "restaurant Dubrovnik email",
    "konoba Croatia email",
    "restaurant Trieste email",
    "agriturismo Friuli Venezia Giulia email",
    "restaurant Istria email",
]

# Function to search via Tavily API? We'll use web_fetch manually.
# For now, we'll manually collect URLs from search results.

# List of known directories
directory_urls = [
    "https://www.turisticnekmetije.si/kmetije",
    "https://gastronaut.hr/restaurants",
    "https://www.tripadvisor.com/Restaurants-g274881-Ljubljana.html",
    "https://www.tripadvisor.com/Restaurants-g295371-Zagreb.html",
]

def scrape_turisticnekmetije():
    """Scrape tourist farms from turisticnekmetije.si"""
    url = "https://www.turisticnekmetije.si/kmetije"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        # Find all farm links
        farms = []
        # The page structure unknown; we'll need to inspect.
        # For now, we'll skip due to complexity.
        print("Scraping turisticnekmetije.si - need to inspect HTML")
        return farms
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

def extract_email_from_page(url):
    """Fetch page and extract email addresses"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        # Regex for email
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(?:com|net|org|si|hr|it|[a-zA-Z]{2})', text)
        return emails
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def main():
    new_leads = []
    # We'll manually add some leads from web search results
    # For now, we'll demonstrate with a few test URLs
    test_urls = [
        "https://www.turisticna-kmetija-weiss.si/kontakt/",
        "https://www.kmetija-podobnik.si/en/contact-us/",
        "https://kotrle.si/contact/",
    ]
    for url in test_urls:
        emails = extract_email_from_page(url)
        if emails:
            # Determine name from page
            # For simplicity, we'll just use domain name
            name = url.split('/')[2]
            new_leads.append({
                'name': name,
                'email': emails[0],
                'city': '',
                'country': 'Slovenia',
                'website': url,
                'source': 'web scrape'
            })
    
    # Write CSV
    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'email', 'city', 'country', 'website', 'source'])
        writer.writeheader()
        for lead in new_leads:
            writer.writerow(lead)
    
    print(f"Saved {len(new_leads)} leads to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()