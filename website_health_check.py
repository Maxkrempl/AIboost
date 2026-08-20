#!/usr/bin/env python3
"""
Automated website health check for 5 sites.
Checks HTTP status, broken links, images, CTA, pricing, Gumroad, viewport, footer, mobile.
"""

import requests
import sys
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def get_session():
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    return session

def check_url(session, url, timeout=10):
    """Return status code and final URL after redirects."""
    try:
        resp = session.get(url, timeout=timeout, verify=False, allow_redirects=True)
        return resp.status_code, resp.url, resp.content
    except Exception as e:
        return None, str(e), None

def extract_links(soup, base_url):
    """Extract all internal and external links."""
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
            continue
        full_url = urljoin(base_url, href)
        links.append(full_url)
    return links

def extract_images(soup, base_url):
    """Extract all image src."""
    images = []
    for img in soup.find_all('img', src=True):
        src = img['src']
        if src.startswith('data:'):
            continue
        full_url = urljoin(base_url, src)
        images.append(full_url)
    return images

def check_viewport(soup):
    """Check for viewport meta tag."""
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    return viewport is not None

def check_gumroad_link(soup):
    """Check for any link containing gumroad.com."""
    for a in soup.find_all('a', href=True):
        if 'gumroad.com' in a['href']:
            return True, a['href']
    return False, None

def check_pricing_link(soup):
    """Look for pricing, price, plan in link text or href."""
    for a in soup.find_all('a', href=True):
        text = a.get_text().strip().lower()
        href = a['href'].lower()
        if 'pricing' in text or 'price' in text or 'plan' in text or 'pricing' in href or 'price' in href or 'plan' in href:
            return True, a['href']
    return False, None

def check_cta(soup):
    """Look for CTA buttons."""
    cta_keywords = ['buy', 'start', 'get', 'try', 'sign up', 'download', 'purchase', 'order', 'go', 'learn more', 'click here']
    for tag in soup.find_all(['button', 'a', 'input']):
        text = tag.get_text().strip().lower()
        if any(keyword in text for keyword in cta_keywords):
            return True
    return False

def check_footer(soup):
    """Check for footer element."""
    footer = soup.find('footer')
    if footer:
        return True
    return False

def check_title(soup):
    """Get page title."""
    title = soup.title
    if title and title.string:
        return title.string.strip()
    return None

def audit_site(url, session):
    """Perform audit on a single site."""
    results = {
        'url': url,
        'http_status': None,
        'final_url': None,
        'title': None,
        'viewport': False,
        'broken_images': [],
        'broken_links': [],
        'gumroad_exists': False,
        'gumroad_url': None,
        'gumroad_works': None,
        'pricing_exists': False,
        'pricing_url': None,
        'cta_exists': False,
        'footer_exists': False,
        'error': None
    }
    
    # 1. Does it load?
    status, final_url, content = check_url(session, url)
    if status is None:
        results['error'] = f"Failed to load: {final_url}"
        return results
    results['http_status'] = status
    results['final_url'] = final_url
    
    if content is None:
        results['error'] = "No content retrieved"
        return results
    
    # Parse HTML
    try:
        soup = BeautifulSoup(content, 'html.parser')
    except Exception as e:
        results['error'] = f"Failed to parse HTML: {e}"
        return results
    
    # 2. Title
    results['title'] = check_title(soup)
    
    # 3. Viewport
    results['viewport'] = check_viewport(soup)
    
    # 4. Broken links (limit to 10 for speed)
    links = extract_links(soup, final_url)
    for link in links[:10]:
        try:
            resp = session.head(link, timeout=5, allow_redirects=True, verify=False)
            if resp.status_code >= 400:
                results['broken_links'].append((link, resp.status_code))
        except Exception:
            results['broken_links'].append((link, 'connection error'))
    
    # 5. Broken images (limit to 5)
    images = extract_images(soup, final_url)
    for img in images[:5]:
        try:
            resp = session.head(img, timeout=5, verify=False)
            if resp.status_code >= 400:
                results['broken_images'].append((img, resp.status_code))
        except Exception:
            results['broken_images'].append((img, 'connection error'))
    
    # 6. Gumroad link
    gumroad_exists, gumroad_url = check_gumroad_link(soup)
    results['gumroad_exists'] = gumroad_exists
    results['gumroad_url'] = gumroad_url
    if gumroad_exists:
        try:
            resp = session.head(gumroad_url, timeout=5, allow_redirects=True, verify=False)
            results['gumroad_works'] = resp.status_code < 400
        except Exception:
            results['gumroad_works'] = False
    
    # 7. Pricing link
    pricing_exists, pricing_url = check_pricing_link(soup)
    results['pricing_exists'] = pricing_exists
    results['pricing_url'] = pricing_url
    
    # 8. CTA button
    results['cta_exists'] = check_cta(soup)
    
    # 9. Footer
    results['footer_exists'] = check_footer(soup)
    
    return results

def main():
    sites = [
        ("MenuBoost", "https://menuboostai.netlify.app"),
        ("BoostSuite", "https://boostsuite.netlify.app"),
        ("AdBoost", "https://adboost-mvp.netlify.app"),
        ("ListTranslate", "https://listtranslate.netlify.app"),
        ("HD WebDesign", "https://hd-webdesign.si"),
    ]
    
    session = get_session()
    
    print("Website Health Check")
    print("="*60)
    
    all_results = []
    for name, url in sites:
        print(f"\nChecking {name}...")
        results = audit_site(url, session)
        all_results.append((name, results))
        time.sleep(1)  # be polite
    
    # Print summary
    print("\n" + "="*60)
    print("HEALTH CHECK SUMMARY")
    print("="*60)
    
    for name, res in all_results:
        print(f"\n{name} ({res['url']}):")
        if res['error']:
            print(f"  ERROR: {res['error']}")
            continue
        print(f"  HTTP Status: {res['http_status']}")
        print(f"  Title: {res['title']}")
        print(f"  Viewport: {res['viewport']}")
        print(f"  Gumroad: {res['gumroad_exists']} ({res['gumroad_url']}) - Works: {res['gumroad_works']}")
        print(f"  Pricing link: {res['pricing_exists']} ({res['pricing_url']})")
        print(f"  CTA button: {res['cta_exists']}")
        print(f"  Footer: {res['footer_exists']}")
        if res['broken_images']:
            print(f"  Broken images: {len(res['broken_images'])}")
            for img, code in res['broken_images']:
                print(f"    - {img} → {code}")
        if res['broken_links']:
            print(f"  Broken links: {len(res['broken_links'])}")
            for link, code in res['broken_links']:
                print(f"    - {link} → {code}")
    
    # Write to file
    with open('/home/darko/.openclaw/workspace/health-check.txt', 'w') as f:
        f.write("Website Health Check Results\n")
        f.write("="*50 + "\n")
        for name, res in all_results:
            f.write(f"\n{name} ({res['url']}):\n")
            if res['error']:
                f.write(f"  ERROR: {res['error']}\n")
                continue
            f.write(f"  HTTP Status: {res['http_status']}\n")
            f.write(f"  Title: {res['title']}\n")
            f.write(f"  Viewport: {res['viewport']}\n")
            f.write(f"  Gumroad: {res['gumroad_exists']} ({res['gumroad_url']}) - Works: {res['gumroad_works']}\n")
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
    
    print("\nDetailed results saved to health-check.txt")

if __name__ == '__main__':
    main()