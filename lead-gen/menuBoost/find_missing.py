#!/usr/bin/env python3
import requests
import re

def find_emails(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.ok:
            emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', r.text)
            return list(set(emails))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return []

# Pelegrini
print('Pelegrini emails:', find_emails('https://pelegrini.hr'))
print('Pelegrini contact page:', find_emails('https://pelegrini.hr/contact'))
print('Pelegrini kontakt:', find_emails('https://pelegrini.hr/kontakt'))
# Valamar (Spinnaker)
print('Valamar emails:', find_emails('https://valamar.com'))
print('Valamar contact:', find_emails('https://valamar.com/contact'))
# Maybe restaurant-specific page: spinnaker
print('Spinnaker page:', find_emails('https://www.valamar.com/en/restaurants/spinnaker'))
# Monte (already have)
print('Monte emails:', find_emails('https://monte.hr'))
# Kogo
print('Kogo emails:', find_emails('https://kogo.si'))
# Hotel Marina
print('Hotel Marina emails:', find_emails('https://hotelmarina.si'))