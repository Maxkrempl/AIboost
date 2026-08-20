#!/usr/bin/env python3
"""
Deep audit of each website.
"""

import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def get_session():
    s = requests.Session()
    s.headers.update({'User-Agent': USER_AGENT})
    return s

def check_viewport(soup):
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    if viewport:
        return True, viewport.get('content', '')
    return False, None

def check_title(soup):
    title = soup.title
    if title and title.string:
        return title.string.strip()
    return None

def check_images(soup, base_url):
    broken = []
    images = soup.find_all('img', src=True)
    for img in images[:10]:  # limit
        src = img['src']
        if src.startswith('data:'):
            continue
        full = urljoin(base_url, src)
        try:
            resp = requests.head(full, timeout=5, verify=False)
            if resp.status_code >= 400:
                broken.append((full, resp.status_code))
        except Exception:
            broken.append((full, 'error'))
    return broken

def check_links(soup, base_url):
    broken = []
    links = soup.find_all('a', href=True)
    for a in links[:20]:  # limit
        href = a['href']
        if href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
            continue
        full = urljoin(base_url, href)
        try:
            resp = requests.head(full, timeout=5, allow_redirects=True, verify=False)
            if resp.status_code >= 400:
                broken.append((full, resp.status_code))
        except Exception:
            broken.append((full, 'error'))
    return broken

def check_gumroad(soup):
    for a in soup.find_all('a', href=True):
        if 'gumroad.com' in a['href']:
            return True, a['href']
    return False, None

def check_pricing_link(soup):
    # look for pricing, price, plan in link text or href
    for a in soup.find_all('a', href=True):
        text = a.get_text().strip().lower()
        href = a['href'].lower()
        if 'pricing' in text or 'price' in text or 'plan' in text or 'pricing' in href or 'price' in href or 'plan' in href:
            return True, a['href']
    return False, None

def check_cta(soup):
    cta_keywords = ['buy', 'start', 'get', 'try', 'sign up', 'download', 'purchase', 'order', 'go', 'learn more', 'click here']
    for tag in soup.find_all(['button', 'a', 'input']):
        text = tag.get_text().strip().lower()
        if any(keyword in text for keyword in cta_keywords):
            return True
    return False

def check_footer(soup):
    footer = soup.find('footer')
    if footer:
        return True
    return False

def audit_site(url):
    print(f"Auditing {url}")
    try:
        resp = requests.get(url, timeout=10, verify=False, headers={'User-Agent': USER_AGENT})
        resp.raise_for_status()
        html = resp.content
        final_url = resp.url
    except Exception as e:
        return {'error': str(e)}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    viewport_exists, viewport_content = check_viewport(soup)
    title = check_title(soup)
    broken_images = check_images(soup, final_url)
    broken_links = check_links(soup, final_url)
    gumroad_exists, gumroad_url = check_gumroad(soup)
    pricing_exists, pricing_url = check_pricing_link(soup)
    cta_exists = check_cta(soup)
    footer_exists = check_footer(soup)
    
    return {
        'url': final_url,
        'title': title,
        'viewport': viewport_exists,
        'viewport_content': viewport_content,
        'broken_images': broken_images,
        'broken_links': broken_links,
        'gumroad_exists': gumroad_exists,
        'gumroad_url': gumroad_url,
        'pricing_exists': pricing_exists,
        'pricing_url': pricing_url,
        'cta_exists': cta_exists,
        'footer_exists': footer_exists,
    }

def main():
    sites = [
        ("MenuBoost", "https://menuboostai.netlify.app"),
        ("BoostSuite", "https://boostsuite.netlify.app"),
        ("AdBoost", "https://adboost-mvp.netlify.app"),
        ("ListTranslate", "https://listtranslate.netlify.app"),
        ("HD WebDesign", "https://hd-webdesign.si"),
    ]
    
    results = {}
    for name, url in sites:
        print(f"\n=== {name} ===")
        results[name] = audit_site(url)
        # be polite
        import time
        time.sleep(1)
    
    # Print summary
    print("\n" + "="*60)
    print("DEEP AUDIT SUMMARY")
    print("="*60)
    for name, res in results.items():
        print(f"\n{name}:")
        if 'error' in res:
            print(f"  ERROR: {res['error']}")
            continue
        print(f"  Title: {res['title']}")
        print(f"  Viewport: {res['viewport']} ({res['viewport_content']})")
        print(f"  Gumroad link: {res['gumroad_exists']} ({res['gumroad_url']})")
        print(f"  Pricing link: {res['pricing_exists']} ({res['pricing_url']})")
        print(f"  CTA button: {res['cta_exists']}")
        print(f"  Footer: {res['footer_exists']}")
        if res['broken_images']:
            print(f"  Broken images: {len(res['broken_images'])}")
            for img, code in res['broken_images'][:3]:
                print(f"    - {img} → {code}")
        if res['broken_links']:
            print(f"  Broken links: {len(res['broken_links'])}")
            for link, code in res['broken_links'][:3]:
                print(f"    - {link} → {code}")
    
    # Write to file
    with open('/home/darko/.openclaw/workspace/deep-audit.txt', 'w') as f:
        f.write("Deep Audit Results\n")
        f.write("="*50 + "\n")
        for name, res in results.items():
            f.write(f"\n{name}:\n")
            if 'error' in res:
                f.write(f"  ERROR: {res['error']}\n")
                continue
            f.write(f"  URL: {res['url']}\n")
            f.write(f"  Title: {res['title']}\n")
            f.write(f"  Viewport: {res['viewport']} ({res['viewport_content']})\n")
            f.write(f"  Gumroad link: {res['gumroad_exists']} ({res['gumroad_url']})\n")
            f.write(f"  Pricing link: {res['pricing_exists']} ({res['pricing_url']})\n")
            f.write(f"  CTA button: {res['cta_exists']}\n")
            f.write(f"  Footer: {res['footer_exists']}\n")
            if res['broken_images']:
                f.write(f"  Broken images: {len(res['broken_images'])}\n")
                for img, code in res['broken_images']:
                    f.write(f"    - {img} → {code}\n")
            if res['broken_links']:
                f.write(f"  Broken links: {len(res['broken_links'])}\n")
                for link, code in res['broken_links']:
                    f.write(f"    - {link} → {code}\n")

if __name__ == '__main__':
    main()