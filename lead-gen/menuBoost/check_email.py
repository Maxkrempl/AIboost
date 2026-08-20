#!/usr/bin/env python3
import requests
import re

def fetch(url):
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    return r.text

# Hotel Marina
text = fetch('https://hotelmarina.si/kontakt')
emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', text)
print('Hotel Marina emails:', emails)
# Kogo
text = fetch('https://kogo.si/kontakt')
emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', text)
print('Kogo emails:', emails)
# Monte
text = fetch('https://monte.hr/kontakt')
emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', text)
print('Monte emails:', emails)
# Pelegrini
text = fetch('https://pelegrini.hr/kontakt')
emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', text)
print('Pelegrini emails:', emails)