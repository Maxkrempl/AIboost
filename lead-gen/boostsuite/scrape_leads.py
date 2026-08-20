#!/usr/bin/env python3
"""
Scrape SEO/marketing agency leads from various sources and save to CSV.
Uses web_search and web_fetch via OpenClaw agent tools (if run within agent).
Alternatively uses requests and BeautifulSoup for direct website scraping.
"""

import csv
import re
import requests
from bs4 import BeautifulSoup
import time
import sys

def search_web(query):
    """Simulate web search - returns list of URLs (mock)."""
    # In actual implementation, use OpenClaw web_search tool.
    # For standalone script, we might use Google Custom Search API.
    # This is a placeholder.
    print(f"Searching: {query}")
    return []

def fetch_url(url):
    """Fetch URL content using requests."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.text
        else:
            print(f"Failed to fetch {url}: {resp.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_email(text):
    """Extract email addresses from text."""
    # Simple regex pattern for email addresses
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    return emails

def scrape_agency_website(url):
    """Visit agency website and find contact email."""
    html = fetch_url(url)
    if html is None:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    # Look for contact page links
    contact_links = soup.find_all('a', href=True, text=re.compile(r'contact|kontakt', re.I))
    contact_urls = [link['href'] for link in contact_links]
    # Ensure absolute URLs
    for contact_url in contact_urls:
        if contact_url.startswith('/'):
            contact_url = url.rstrip('/') + contact_url
        html2 = fetch_url(contact_url)
        if html2:
            emails = extract_email(html2)
            if emails:
                return emails
    # Fallback: extract emails from whole page
    emails = extract_email(html)
    return emails

def main():
    sources = [
        ("SEO agency Slovenia email contact", "Slovenia"),
        ("digital marketing agency Croatia contact email", "Croatia"),
        ("SEO freelancer Italy email", "Italy"),
        ("AEO GEO agency contact", "Global"),
    ]
    
    leads = []
    
    for query, country in sources:
        # Simulate search results
        search_results = search_web(query)
        # For demonstration, we'll use pre-known websites
        # In real scenario, parse search results
        pass
    
    # Example manual leads we already collected
    manual_leads = [
        {
            'name': 'Proelium Media',
            'email': 'office@proeliummedia.com',
            'company': 'Proelium Media',
            'city': 'Bibinje',
            'country': 'Croatia',
            'website': 'https://www.proeliummedia.com/',
            'specialty': 'Digital marketing agency',
            'source': 'web_search',
        },
        {
            'name': 'Experience TEN',
            'email': 'digital@ten.marketing',
            'company': 'Experience TEN d.o.o.',
            'city': 'Zagreb',
            'country': 'Croatia',
            'website': 'https://ten.marketing/',
            'specialty': 'Digital marketing',
            'source': 'web_search',
        },
        {
            'name': 'AI Agency DX',
            'email': 'info@aiagencydx.com',
            'company': 'AI Agency DX',
            'city': 'Sisak',
            'country': 'Croatia',
            'website': 'https://aiagencydx.com/',
            'specialty': 'AI integration automation digital marketing',
            'source': 'web_search',
        },
        {
            'name': 'Livmark Agency',
            'email': 'agency@livmark.hr',
            'company': 'Livmark Agency',
            'city': 'Čakovec',
            'country': 'Croatia',
            'website': 'https://livmark.agency/',
            'specialty': 'Marketing strategy UI/UX SEO',
            'source': 'web_search',
        },
        {
            'name': 'Jonathan SEO',
            'email': 'jon@thnx.it',
            'company': 'Freelancer',
            'city': 'Unknown',
            'country': 'Italy',
            'website': 'https://jonathanseo.com/',
            'specialty': 'SEO freelancer',
            'source': 'web_search',
        },
        {
            'name': 'AEO Agency US',
            'email': 'info@aeoagency.us',
            'company': 'AEO Agency US',
            'city': 'Sheridan Wyoming',
            'country': 'USA',
            'website': 'https://aeoagency.us/',
            'specialty': 'AEO/GEO optimization',
            'source': 'web_search',
        },
        {
            'name': 'Act Local',
            'email': 'info@actlocal.si',
            'company': 'Act Local',
            'city': 'Ljubljana',
            'country': 'Slovenia',
            'website': 'https://actlocal.si/',
            'specialty': 'Local SEO digital marketing',
            'source': 'web_search',
        },
        {
            'name': 'SEO Consult',
            'email': 'info@seo-consult.info',
            'company': 'SEO Consult',
            'city': 'Dubrovnik',
            'country': 'Croatia',
            'website': 'https://www.seo-consult.info/',
            'specialty': 'SEO consulting',
            'source': 'web_search',
        },
    ]
    
    # Write CSV
    output_path = 'fresh-leads-2026-05-15.csv'
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'email', 'company', 'city', 'country', 'website', 'specialty', 'source'])
        writer.writeheader()
        writer.writerows(manual_leads)
    
    print(f"Saved {len(manual_leads)} leads to {output_path}")
    
    # Optionally, compare with existing leads to avoid duplicates
    existing_path = 'boostsuite-leads-europe-fresh.csv'
    if len(sys.argv) > 1 and sys.argv[1] == '--check-duplicates':
        try:
            with open(existing_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                existing_emails = [row['email'].strip().lower() for row in reader if row['email']]
            new_emails = [lead['email'].strip().lower() for lead in manual_leads]
            duplicates = [email for email in new_emails if email in existing_emails]
            print(f"Duplicate emails: {duplicates}")
        except FileNotFoundError:
            print(f"Existing file {existing_path} not found.")

if __name__ == '__main__':
    main()