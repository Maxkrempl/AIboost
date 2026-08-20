#!/usr/bin/env python3
"""
Website audit script for 5 sites.
Checks HTTP status, broken links, images, CTA, pricing, Gumroad, UX, footer, mobile.
"""

import requests
import sys
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Suppress SSL warnings for self-signed certs
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
        if href.startswith('#'):
            continue
        if href.startswith('mailto:'):
            continue
        if href.startswith('tel:'):
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

def audit_site(url, session):
    """Perform audit on a single site."""
    print(f"Auditing {url}...")
    issues = []
    
    # 1. Does it load?
    status, final_url, content = check_url(session, url)
    if status is None:
        issues.append(f"Failed to load: {final_url}")
        return issues
    if status != 200:
        issues.append(f"HTTP status {status} (final URL: {final_url})")
    
    if content is None:
        issues.append("No content retrieved")
        return issues
    
    # Parse HTML
    try:
        soup = BeautifulSoup(content, 'html.parser')
    except Exception as e:
        issues.append(f"Failed to parse HTML: {e}")
        return issues
    
    # 2. Broken links
    links = extract_links(soup, final_url)
    broken = []
    for link in links[:10]:  # Limit to first 10 for speed
        try:
            resp = session.head(link, timeout=5, allow_redirects=True, verify=False)
            if resp.status_code >= 400:
                broken.append(f"{link} → {resp.status_code}")
        except Exception:
            broken.append(f"{link} → connection error")
    if broken:
        issues.append(f"Broken links: {broken}")
    
    # 3. Images loading
    images = extract_images(soup, final_url)
    broken_images = []
    for img in images[:5]:  # Limit
        try:
            resp = session.head(img, timeout=5, verify=False)
            if resp.status_code >= 400:
                broken_images.append(f"{img} → {resp.status_code}")
        except Exception:
            broken_images.append(f"{img} → connection error")
    if broken_images:
        issues.append(f"Broken images: {broken_images}")
    
    # 4. CTA (call to action) - check for buttons with common CTA text
    cta_keywords = ['buy', 'start', 'get', 'try', 'sign up', 'download', 'purchase', 'order']
    cta_found = False
    for button in soup.find_all(['button', 'a']):
        text = button.get_text().strip().lower()
        if any(keyword in text for keyword in cta_keywords):
            cta_found = True
            break
    if not cta_found:
        issues.append("No obvious CTA button found")
    
    # 5. Pricing page visible and clear
    pricing_links = []
    for a in soup.find_all('a', href=True):
        text = a.get_text().strip().lower()
        if 'pricing' in text or 'price' in text or 'plan' in text:
            pricing_links.append(a['href'])
    if not pricing_links:
        issues.append("No pricing page link found")
    
    # 6. Gumroad payment link
    gumroad_exists, gumroad_url = check_gumroad_link(soup)
    if not gumroad_exists:
        issues.append("No Gumroad payment link found")
    else:
        # Check if Gumroad link works
        try:
            resp = session.head(gumroad_url, timeout=5, allow_redirects=True, verify=False)
            if resp.status_code >= 400:
                issues.append(f"Gumroad link may be broken: {gumroad_url} → {resp.status_code}")
        except Exception:
            issues.append(f"Gumroad link connection error: {gumroad_url}")
    
    # 7. Footer working - check footer element
    footer = soup.find('footer')
    if not footer:
        issues.append("No <footer> element found")
    else:
        # Check if footer has content
        if len(footer.get_text().strip()) < 10:
            issues.append("Footer appears empty")
    
    # 8. Mobile responsiveness (viewport meta tag)
    if not check_viewport(soup):
        issues.append("Missing viewport meta tag (mobile responsiveness)")
    
    # 9. Title tag
    title = soup.title
    if not title or not title.string or len(title.string.strip()) < 2:
        issues.append("Missing or empty <title> tag")
    
    return issues

def main():
    sites = [
        ("MenuBoost", "https://menuboostai.netlify.app"),
        ("BoostSuite", "https://boostsuite.netlify.app"),
        ("AdBoost", "https://adboost-mvp.netlify.app"),
        ("ListTranslate", "https://listtranslate.netlify.app"),
        ("HD WebDesign", "https://hd-webdesign.si"),
    ]
    
    session = get_session()
    
    results = {}
    for name, url in sites:
        issues = audit_site(url, session)
        results[name] = (url, issues)
        time.sleep(1)  # Be polite
    
    # Print summary
    print("\n" + "="*60)
    print("AUDIT SUMMARY")
    print("="*60)
    for name, (url, issues) in results.items():
        print(f"\n{name} ({url}):")
        if issues:
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("  No issues found.")
    
    # Write to file
    with open('/home/darko/.openclaw/workspace/audit-results.txt', 'w') as f:
        f.write("Website Audit Results\n")
        f.write("="*50 + "\n")
        for name, (url, issues) in results.items():
            f.write(f"\n{name} ({url}):\n")
            if issues:
                for issue in issues:
                    f.write(f"  - {issue}\n")
            else:
                f.write("  No issues found.\n")
    
    print("\nDetailed results saved to audit-results.txt")

if __name__ == '__main__':
    main()