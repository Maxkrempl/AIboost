#!/usr/bin/env python3
"""Verify Adriatic leads: email MX, website menu check, MenuBoost personalization."""
import csv, subprocess, json, urllib.request, re, ssl

# Disable SSL verification for some sites
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

leads = []
with open('/home/darko/.openclaw/workspace/lead-gen/menuboost/adriatic-batch-new.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        leads.append(row)

def check_mx(email):
    """Check if email domain has MX record."""
    domain = email.split('@')[-1]
    try:
        r = subprocess.run(['dig', '+short', 'MX', domain], capture_output=True, text=True, timeout=5)
        return len(r.stdout.strip()) > 0
    except:
        return None

def check_menu(url):
    """Check if website has a menu page."""
    if not url:
        return {"has_menu": False, "menu_url": None, "reason": "no_url"}
    
    # Normalize URL
    if not url.startswith('http'):
        url = 'https://' + url
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        html = resp.read().decode('utf-8', errors='ignore').lower()
        
        # Check for menu links
        menu_patterns = [
            r'href=["\']([^"\']*menu[^"\']*)["\']',
            r'href=["\']([^"\']*jelovnik[^"\']*)["\']',
            r'href=["\']([^"\']*meni[^"\']*)["\']',
            r'href=["\']([^"\']*carta[^"\']*)["\']',
            r'href=["\']([^"\']*karta[^"\']*)["\']',
            r'href=["\']([^"\']*speisekarte[^"\']*)["\']',
            r'href=["\']([^"\']*piatto[^"\']*)["\']',
            r'href=["\']([^"\']*jedilni[^"\']*)["\']',
        ]
        
        menu_urls = []
        for pattern in menu_patterns:
            matches = re.findall(pattern, html)
            menu_urls.extend(matches)
        
        # Check for PDF menus
        pdf_menus = re.findall(r'href=["\']([^"\']*\.pdf[^"\']*)["\']', html)
        
        # Check for menu section on page
        has_menu_section = any(word in html for word in ['jelovnik', 'meni', 'menu', 'carta dei piatti', 'speisekarte'])
        
        if menu_urls:
            return {"has_menu": True, "menu_url": menu_urls[0], "all_menus": menu_urls[:3]}
        elif pdf_menus:
            return {"has_menu": True, "menu_url": pdf_menus[0], "type": "pdf"}
        elif has_menu_section:
            return {"has_menu": True, "menu_url": url, "type": "section_on_page"}
        else:
            return {"has_menu": False, "reason": "no_menu_found"}
            
    except Exception as e:
        return {"has_menu": False, "reason": f"fetch_error: {str(e)[:50]}"}

# Process each lead
results = []
for lead in leads:
    email = lead.get('email', '')
    name = lead.get('name', '')
    url = lead.get('website', '')
    city = lead.get('city', '')
    
    print(f"\n{'='*50}")
    print(f"Checking: {name} ({city})")
    print(f"  Email: {email}")
    
    # Check MX
    mx = check_mx(email)
    print(f"  MX valid: {'✅' if mx else '❌' if mx is False else '⚠️ unknown'}")
    
    # Check website for menu
    menu = check_menu(url)
    if menu['has_menu']:
        print(f"  Menu: ✅ Found ({menu.get('type', 'link')})")
        if menu.get('menu_url'):
            print(f"  Menu URL: {menu['menu_url']}")
    else:
        print(f"  Menu: ❌ {menu.get('reason', 'unknown')}")
    
    results.append({
        'name': name,
        'city': city,
        'email': email,
        'website': url,
        'mx_valid': mx,
        'has_menu': menu['has_menu'],
        'menu_info': menu
    })

# Save results
with open('/home/darko/.openclaw/workspace/lead-gen/menuboost/adriatic-verified.json', 'w') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n{'='*50}")
print(f"SUMMARY: {len(results)} leads checked")
print(f"  MX valid: {sum(1 for r in results if r['mx_valid'])}")
print(f"  Has menu: {sum(1 for r in results if r['has_menu'])}")
print(f"  No menu: {sum(1 for r in results if not r['has_menu'])}")
