#!/usr/bin/env python3
import requests
import re
import csv
from urllib.parse import urljoin

def find_emails(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.ok:
            emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', r.text)
            return list(set(emails))
    except Exception as e:
        print(f"Error {url}: {e}")
    return []

# Hospiz Alm - try http
print('Hospiz Alm:')
print('  Trying http://arlberghospiz.at')
emails = find_emails('http://arlberghospiz.at')
if emails:
    print('  Found:', emails)
else:
    # Try https with verify=False
    try:
        import ssl
        import urllib.request
        context = ssl._create_unverified_context()
        req = urllib.request.Request('https://arlberghospiz.at', headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, context=context, timeout=10)
        data = response.read().decode('utf-8')
        emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', data)
        print('  Found (no verify):', emails)
    except Exception as e:
        print('  SSL bypass failed:', e)

# Tivoli
print('\nTivoli:')
base = 'https://www.ristorantetivolicortina.it'
emails = find_emails(base)
print('  Homepage:', emails)
# Try contact page
contact = urljoin(base, '/contatti')
emails2 = find_emails(contact)
print('  Contact page:', emails2)
# Try contact-us
contact2 = urljoin(base, '/contact')
emails3 = find_emails(contact2)
print('  Contact-us:', emails3)
# Try booking page
booking = urljoin(base, '/prenota')
emails4 = find_emails(booking)
print('  Prenota:', emails4)

# Also search for email pattern with [at]
def find_at_emails(text):
    # pattern lab[at]agliamici.it
    pattern = r'(\w+)\s*\[?@\]?\s*(\w+\.\w+)'
    matches = re.findall(pattern, text)
    return [f'{local}@{domain}' for local, domain in matches]

# Fetch Tivoli page again and search
try:
    r = requests.get(base, timeout=10)
    if r.ok:
        at_emails = find_at_emails(r.text)
        print('  [at] emails:', at_emails)
except:
    pass