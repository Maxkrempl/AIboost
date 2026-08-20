#!/usr/bin/env python3
"""
Lead Generator — Overpass API (OpenStreetMap)
Finds businesses by type + location, extracts contacts, emails results.

Usage:
  python3 overpass_leads.py --type restaurant --location "Piran, Slovenia"
  python3 overpass_leads.py --type hotel --location "Bled" --limit 50
  python3 overpass_leads.py --type cafe --bbox 45.4,13.7,45.5,13.9
  python3 overpass_leads.py --type restaurant --location "Paris, France" --email user@example.com
  python3 overpass_leads.py --type restaurant --location "Tokyo, Japan" --limit 20 --email user@example.com
"""

import argparse
import csv
import json
import os
import re
import smtplib
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- Config ---
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "LeadGenerator/1.0 (boostsuite)"
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '***REMOVED***')
EMAIL_FROM = 'max@hd-webdesign.si'
SMTP_HOST = 'mail.hd-webdesign.si'
SMTP_PORT = 465
SMTP_USER = 'max@hd-webdesign.si'
SMTP_PASS = '***REMOVED***'

# Amenity mapping
AMENITY_MAP = {
    'restaurant': ['restaurant'],
    'cafe': ['cafe', 'coffee'],
    'bar': ['bar', 'pub'],
    'hotel': ['hotel', 'motel', 'hostel', 'guest_house'],
    'fast_food': ['fast_food'],
    'pizza_restaurant': ['restaurant'],
    'shop': ['shop'],
    'dentist': ['dentist'],
    'doctor': ['doctor'],
    'gym': ['fitness_centre'],
    'beauty': ['beauty_salon'],
    'salon': ['beauty_salon', 'hairdresser'],
    'mechanic': ['car_repair'],
    'plumber': ['plumber'],
    'electrician': ['electrician'],
}


def geocode_location(location_name):
    """Geocode ANY location name to bounding box using Nominatim."""
    url = f"{NOMINATIM_URL}?q={urllib.parse.quote(location_name)}&format=json&limit=1&addressdetails=1"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if data:
                bb = data[0].get('boundingbox', [])
                if len(bb) == 4:
                    # Nominatim returns [south, north, west, east]
                    south, north, west, east = float(bb[0]), float(bb[1]), float(bb[2]), float(bb[3])
                    # Keep bbox tight — Overpass works best with smaller areas
                    lat_range = north - south
                    lon_range = east - west
                    if lat_range > 0.2:  # Too large — shrink to city center
                        mid_lat = (south + north) / 2
                        mid_lon = (west + east) / 2
                        return (mid_lat - 0.08, mid_lon - 0.1, mid_lat + 0.08, mid_lon + 0.1)
                    return (south, west, north, east)
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return (lat - 0.05, lon - 0.05, lat + 0.05, lon + 0.05)
    except Exception as e:
        print(f"Geocoding failed for '{location_name}': {e}", file=sys.stderr)
    return None


def query_overpass(amenities, bbox, limit=100):
    """Query Overpass API for businesses in bounding box."""
    south, west, north, east = bbox
    
    # Hotels use tourism=hotel, not amenity
    tourism_types = {'hotel', 'motel', 'hostel', 'guest_house'}
    amenity_types = [a for a in amenities if a not in tourism_types]
    tourism_filters = [a for a in amenities if a in tourism_types]
    
    queries = []
    if amenity_types:
        amenity_filter = '|'.join(amenity_types)
        queries.append(f'node["amenity"~"{amenity_filter}"]({south},{west},{north},{east})')
        queries.append(f'way["amenity"~"{amenity_filter}"]({south},{west},{north},{east})')
    if tourism_filters:
        tourism_filter = '|'.join(tourism_filters)
        queries.append(f'node["tourism"~"{tourism_filter}"]({south},{west},{north},{east})')
        queries.append(f'way["tourism"~"{tourism_filter}"]({south},{west},{north},{east})')
    
    query_lines = ['[out:json][timeout:60];', '(']
    for q in queries:
        query_lines.append(f'  {q};')
    query_lines.append(');')
    query_lines.append('out center body;')
    query = chr(10).join(query_lines)
    
    data = urllib.parse.urlencode({'data': query}).encode()
    req = urllib.request.Request(OVERPASS_URL, data=data, headers={
        'User-Agent': USER_AGENT,
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            elements = result.get('elements', [])
            print(f"Overpass returned {len(elements)} results")
            return elements[:limit]
    except Exception as e:
        print(f"Overpass query failed: {e}", file=sys.stderr)
        return []


def extract_email_from_url(url, timeout=10):
    """Try to extract email from a website."""
    if not url:
        return None
    if not url.startswith('http'):
        url = 'https://' + url
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            
            emails = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', html)
            junk = ['example.com', 'test.com', 'sentry.io', 'wixpress.com', 
                    'wordpress.com', 'schema.org', 'w3.org', 'googleapis.com',
                    'facebook.com', 'twitter.com', 'instagram.com', 'tiktok.com']
            
            for email in emails:
                if not any(j in email.lower() for j in junk):
                    return email
            
            mailtos = re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', html)
            for email in mailtos:
                if not any(j in email.lower() for j in junk):
                    return email
    except Exception:
        pass
    return None


def parse_element(el):
    """Parse an Overpass element into a lead dict."""
    tags = el.get('tags', {})
    
    if el['type'] == 'node':
        lat, lon = el.get('lat'), el.get('lon')
    else:
        center = el.get('center', {})
        lat, lon = center.get('lat'), center.get('lon')
    
    website = tags.get('website', tags.get('contact:website', ''))
    if website and not website.startswith('http'):
        website = 'https://' + website
    
    return {
        'osm_id': el.get('id'),
        'name': tags.get('name', tags.get('name:en', 'Unknown')),
        'name_local': tags.get('name:sl', tags.get('name:hr', tags.get('name:it', ''))),
        'type': tags.get('amenity', ''),
        'cuisine': tags.get('cuisine', ''),
        'addr_street': tags.get('addr:street', ''),
        'addr_housenumber': tags.get('addr:housenumber', ''),
        'addr_city': tags.get('addr:city', ''),
        'addr_postcode': tags.get('addr:postcode', ''),
        'phone': tags.get('phone', tags.get('contact:phone', '')),
        'website': website,
        'email': tags.get('email', tags.get('contact:email', '')),
        'opening_hours': tags.get('opening_hours', ''),
        'outdoor_seating': tags.get('outdoor_seating', ''),
        'delivery': tags.get('delivery', ''),
        'takeaway': tags.get('takeaway', ''),
        'wheelchair': tags.get('wheelchair', ''),
        'stars': tags.get('stars', tags.get('tourism:stars', '')),
        'lat': lat, 'lon': lon,
    }


def save_to_csv(leads, location_name, lead_type):
    """Save leads to CSV, return filepath."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d-%H%M')
    safe_name = re.sub(r'[^a-z0-9]', '-', location_name.lower())[:30]
    filename = f"leads-{lead_type}-{safe_name}-{timestamp}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    fieldnames = [
        'name', 'name_local', 'type', 'cuisine', 'phone', 'email', 'website',
        'addr_street', 'addr_housenumber', 'addr_city', 'addr_postcode',
        'opening_hours', 'outdoor_seating', 'delivery', 'takeaway',
        'wheelchair', 'stars', 'lat', 'lon', 'osm_id'
    ]
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lead in leads:
            writer.writerow({k: lead.get(k, '') for k in fieldnames})
    
    print(f"✅ Saved {len(leads)} leads to {filepath}")
    return filepath


def enrich_leads(leads):
    """Enrich leads with emails from websites."""
    enriched = 0
    total = len(leads)
    
    for i, lead in enumerate(leads):
        if lead.get('email'):
            continue
        website = lead.get('website', '')
        if not website:
            continue
        
        sys.stdout.write(f"\r  Enriching {i+1}/{total}: {lead['name'][:40]}...")
        sys.stdout.flush()
        
        email = extract_email_from_url(website)
        if email:
            lead['email'] = email
            enriched += 1
        time.sleep(0.5)
    
    print(f"\n  Found {enriched} new emails from {total} leads")
    return leads


def send_email_with_csv(recipient, filepath, location, lead_type, stats):
    """Send CSV as email attachment via Resend API."""
    subject = f"🎯 {stats['total']} {lead_type} leads — {location}"
    
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1a1a2e;">🎯 Your leads are ready!</h2>
        <p>Here are <strong>{stats['total']} {lead_type} leads</strong> from <strong>{location}</strong>.</p>
        
        <div style="background: #f8f9fa; border-radius: 8px; padding: 16px; margin: 20px 0;">
            <h3 style="margin-top: 0;">📊 Summary</h3>
            <ul style="list-style: none; padding: 0;">
                <li>✅ Total leads: <strong>{stats['total']}</strong></li>
                <li>📧 With email: <strong>{stats['with_email']}</strong></li>
                <li>📞 With phone: <strong>{stats['with_phone']}</strong></li>
                <li>🌐 With website: <strong>{stats['with_website']}</strong></li>
            </ul>
        </div>
        
        <p>The CSV file is attached. You can import it into your CRM, spreadsheet, or outreach tool.</p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #666; font-size: 12px;">
            Generated by <a href="https://hd-webdesign.si/boostsuite/">BoostSuite Lead Generator</a><br>
            Need more leads? <a href="https://hd-webdesign.si/boostsuite/">Upgrade to Pro →</a>
        </p>
    </div>
    """
    
    # Read CSV as attachment
    with open(filepath, 'rb') as f:
        csv_data = f.read()
    csv_b64 = __import__('base64').b64encode(csv_data).decode()
    filename = os.path.basename(filepath)
    
    # Build email with attachment
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    
    part = MIMEBase('text', 'csv')
    part.set_payload(csv_data)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
    msg.attach(part)
    
    # Send via SMTP
    try:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {recipient}")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description='Lead Generator — any location worldwide')
    parser.add_argument('--type', '-t', default='restaurant',
                       choices=list(AMENITY_MAP.keys()),
                       help='Type of business to find')
    parser.add_argument('--location', '-l', required=True,
                       help='Location name — ANY place worldwide (e.g. "Paris, France", "Tokyo", "New York")')
    parser.add_argument('--bbox', help='Bounding box: south,west,north,east')
    parser.add_argument('--limit', type=int, default=50, help='Max leads to return')
    parser.add_argument('--no-enrich', action='store_true', help='Skip email extraction from websites')
    parser.add_argument('--email', '-e', help='Send results to this email address')
    parser.add_argument('--output', '-o', help='Custom output filename')
    
    args = parser.parse_args()
    
    # Determine bounding box
    bbox = None
    if args.bbox:
        parts = [float(x.strip()) for x in args.bbox.split(',')]
        if len(parts) == 4:
            bbox = tuple(parts)
    else:
        print(f"📍 Geocoding '{args.location}'...")
        bbox = geocode_location(args.location)
    
    if not bbox:
        print("Error: Could not find location. Try a more specific name.", file=sys.stderr)
        sys.exit(1)
    
    print(f"📍 Search area: {bbox[0]:.4f},{bbox[1]:.4f} → {bbox[2]:.4f},{bbox[3]:.4f}")
    
    amenities = AMENITY_MAP.get(args.type, [args.type])
    
    print(f"🔍 Searching for {args.type}...")
    elements = query_overpass(amenities, bbox, args.limit)
    
    if not elements:
        print("No results found.")
        sys.exit(0)
    
    leads = [parse_element(el) for el in elements]
    
    if not args.no_enrich:
        print("📧 Extracting emails from websites...")
        leads = enrich_leads(leads)
    
    with_email = sum(1 for l in leads if l.get('email'))
    with_phone = sum(1 for l in leads if l.get('phone'))
    with_website = sum(1 for l in leads if l.get('website'))
    
    stats = {
        'total': len(leads),
        'with_email': with_email,
        'with_phone': with_phone,
        'with_website': with_website,
    }
    
    print(f"\n📊 Results:")
    print(f"  Total: {stats['total']}")
    print(f"  With email: {stats['with_email']}")
    print(f"  With phone: {stats['with_phone']}")
    print(f"  With website: {stats['with_website']}")
    
    # Save CSV
    filepath = save_to_csv(leads, args.location, args.type)
    
    # Send email if requested
    if args.email:
        print(f"\n📧 Sending results to {args.email}...")
        send_email_with_csv(args.email, filepath, args.location, args.type, stats)
    
    # Print sample
    print(f"\n📋 Sample leads:")
    for lead in leads[:5]:
        email_str = f" | {lead['email']}" if lead.get('email') else ""
        phone_str = f" | {lead['phone']}" if lead.get('phone') else ""
        print(f"  • {lead['name']}{phone_str}{email_str}")


if __name__ == '__main__':
    main()
