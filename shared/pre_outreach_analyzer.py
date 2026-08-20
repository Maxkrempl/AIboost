#!/usr/bin/env python3
"""
Pre-outreach website analyzer for Rose.
Analyzes a restaurant/agency website BEFORE sending email.
Generates personalized talking points for outreach.

Usage:
  python3 pre_outreach_analyzer.py https://www.restavracija.si
  python3 pre_outreach_analyzer.py https://www.agencija.hr --type agency
"""

import sys
import urllib.request
import urllib.parse
import json
import re
import ssl

def fetch_page(url, timeout=15):
    """Fetch webpage content."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' not in content_type and 'text/plain' not in content_type:
                return None
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def analyze_restaurant(html, url):
    """Analyze restaurant website for outreach signals."""
    signals = {
        'url': url,
        'issues': [],
        'strengths': [],
        'personalization': [],
        'outreach_angle': ''
    }
    
    if not html:
        signals['issues'].append('Could not fetch website')
        signals['outreach_angle'] = 'Website may be down or unreachable'
        return signals
    
    html_lower = html.lower()
    
    # Check for languages
    languages_found = []
    lang_markers = {
        'si': ['sloven', 'slovenšč', 'slovensc'],
        'en': ['english', 'angleš'],
        'hr': ['hrvat', 'hrvatsk'],
        'it': ['italian', 'italij'],
        'de': ['deutsch', 'nemsc', 'german'],
        'fr': ['franç', 'francos'],
        'es': ['español', 'špans'],
    }
    for lang, markers in lang_markers.items():
        for marker in markers:
            if marker in html_lower:
                languages_found.append(lang)
                break
    
    if len(languages_found) <= 1:
        signals['issues'].append(f'Website only in {len(languages_found)} language(s) - missing international tourists')
        signals['outreach_angle'] = 'multilingual gap'
    
    # Check for menu/jedilnik
    menu_keywords = ['jedilnik', 'meni', 'menu', 'carta', 'speisekarte', 'karta jela']
    has_menu = any(kw in html_lower for kw in menu_keywords)
    if not has_menu:
        signals['issues'].append('No online menu found')
        signals['outreach_angle'] = 'missing online menu'
    
    # Check for QR code
    has_qr = 'qr' in html_lower or 'qrcode' in html_lower
    if not has_qr:
        signals['issues'].append('No QR code for menu')
    
    # Check for allergens
    allergen_keywords = ['alergen', 'allergen', 'alergi', 'nutritional', 'hranilna']
    has_allergens = any(kw in html_lower for kw in allergen_keywords)
    if not has_allergens:
        signals['issues'].append('No allergen information visible')
    
    # Check for meta tags
    has_meta_desc = 'meta name="description"' in html_lower or "meta name='description'" in html_lower
    if not has_meta_desc:
        signals['issues'].append('Missing meta description')
    
    has_og_tags = 'og:title' in html_lower or 'og:description' in html_lower
    if not has_og_tags:
        signals['issues'].append('Missing Open Graph tags (social media previews broken)')
    
    # Check for schema markup
    has_schema = 'application/ld+json' in html_lower or 'itemscope' in html_lower
    if not has_schema:
        signals['issues'].append('No structured data (schema markup)')
    
    # Check for mobile responsiveness
    has_viewport = 'viewport' in html_lower
    if not has_viewport:
        signals['issues'].append('Missing mobile viewport tag')
    
    # Check for HTTPS
    if url.startswith('http://'):
        signals['issues'].append('Site uses HTTP instead of HTTPS')
    
    # Check for images without alt text
    img_count = len(re.findall(r'<img[^>]*>', html, re.IGNORECASE))
    img_with_alt = len(re.findall(r'<img[^>]*alt=["\'][^"\']+["\']', html, re.IGNORECASE))
    if img_count > 0 and img_with_alt < img_count * 0.5:
        signals['issues'].append(f'Most images ({img_count - img_with_alt}/{img_count}) missing alt text')
    
    # Check for TripAdvisor/booking mentions
    booking_platforms = ['tripadvisor', 'booking.com', 'google.com/maps']
    has_booking = any(p in html_lower for p in booking_platforms)
    if has_booking:
        signals['strengths'].append('Connected to booking platforms')
    
    # Check for social media
    social_platforms = ['facebook', 'instagram', 'twitter', 'linkedin']
    has_social = any(p in html_lower for p in social_platforms)
    if has_social:
        signals['strengths'].append('Active on social media')
    
    # Generate personalization points
    if signals['issues']:
        signals['personalization'].append(f"I noticed your website has {len(signals['issues'])} areas for improvement")
    
    if 'multilingual gap' in signals.get('outreach_angle', ''):
        signals['personalization'].append("Your menu is only available in one language, but tourists from multiple countries visit your area")
    
    if not has_qr:
        signals['personalization'].append("Adding a QR code would let customers access your menu instantly on their phones")
    
    # Generate outreach angle summary
    if not signals['outreach_angle']:
        if len(signals['issues']) > 3:
            signals['outreach_angle'] = 'multiple SEO/usability issues'
        elif len(signals['issues']) > 0:
            signals['outreach_angle'] = 'minor improvements available'
        else:
            signals['outreach_angle'] = 'well-optimized site (soft approach)'
    
    return signals

def analyze_agency(html, url):
    """Analyze agency website for BoostSuite outreach."""
    signals = {
        'url': url,
        'issues': [],
        'strengths': [],
        'personalization': [],
        'outreach_angle': ''
    }
    
    if not html:
        signals['issues'].append('Could not fetch website')
        return signals
    
    html_lower = html.lower()
    
    # Check for services list
    services = ['seo', 'web design', 'marketing', 'social media', 'ppc', 'ads']
    found_services = [s for s in services if s in html_lower]
    if found_services:
        signals['strengths'].append(f"Services found: {', '.join(found_services)}")
    
    # Check for client portfolio
    has_portfolio = 'portfolio' in html_lower or 'case study' in html_lower or 'our work' in html_lower
    if has_portfolio:
        signals['strengths'].append('Has portfolio/case studies')
    
    # Check for blog
    has_blog = '/blog' in html_lower or 'blog' in html_lower.split('/')[-1]
    if has_blog:
        signals['strengths'].append('Has blog (content marketing active)')
    
    # Check for GEO awareness
    geo_keywords = ['geo', 'ai optimization', 'chatgpt', 'generative engine', 'ai visibility']
    has_geo = any(kw in html_lower for kw in geo_keywords)
    if not has_geo:
        signals['issues'].append('No GEO/AI optimization mentioned - opportunity to introduce BoostSuite')
        signals['outreach_angle'] = 'GEO gap'
    
    # Check for SEO claims
    seo_keywords = ['seo', 'search engine', 'google ranking', 'organic']
    claims_seo = any(kw in html_lower for kw in seo_keywords)
    if claims_seo and not has_geo:
        signals['issues'].append('Claims SEO expertise but no GEO - gap in their offering')
        signals['outreach_angle'] = 'SEO without GEO'
    
    # Check for pricing
    has_pricing = 'price' in html_lower or 'pricing' in html_lower or '€' in html or '$' in html
    if has_pricing:
        signals['strengths'].append('Transparent pricing')
    
    if not signals['outreach_angle']:
        signals['outreach_angle'] = 'tool partnership opportunity'
    
    return signals

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 pre_outreach_analyzer.py <url> [--type restaurant|agency]")
        sys.exit(1)
    
    url = sys.argv[1]
    analysis_type = 'restaurant'
    
    if '--type' in sys.argv:
        idx = sys.argv.index('--type')
        if idx + 1 < len(sys.argv):
            analysis_type = sys.argv[idx + 1]
    
    # Ensure URL has protocol
    if not url.startswith('http'):
        url = 'https://' + url
    
    print(f"🔍 Analyzing: {url}")
    print(f"📋 Type: {analysis_type}")
    print("=" * 50)
    
    html = fetch_page(url)
    
    if analysis_type == 'agency':
        signals = analyze_agency(html, url)
    else:
        signals = analyze_restaurant(html, url)
    
    # Print results
    if signals['issues']:
        print("\n❌ ISSUES FOUND:")
        for issue in signals['issues']:
            print(f"  • {issue}")
    
    if signals['strengths']:
        print("\n✅ STRENGTHS:")
        for strength in signals['strengths']:
            print(f"  • {strength}")
    
    if signals['personalization']:
        print("\n🎯 PERSONALIZATION POINTS:")
        for point in signals['personalization']:
            print(f"  • {point}")
    
    print(f"\n📧 OUTREACH ANGLE: {signals['outreach_angle']}")
    
    # Generate email subject line
    domain = urllib.parse.urlparse(url).netloc.replace('www.', '')
    if signals['outreach_angle'] == 'multilingual gap':
        subject = f"{domain} — tourists can't read your menu"
    elif signals['outreach_angle'] == 'GEO gap':
        subject = f"{domain} — your clients aren't visible in ChatGPT"
    elif signals['outreach_angle'] == 'SEO without GEO':
        subject = f"{domain} — SEO is only half the story"
    else:
        subject = f"{domain} — quick question"
    
    print(f"\n📝 SUGGESTED SUBJECT: {subject}")
    
    # Output JSON for programmatic use
    print(f"\n📊 JSON OUTPUT:")
    print(json.dumps(signals, indent=2))

if __name__ == '__main__':
    main()
