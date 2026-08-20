#!/usr/bin/env python3
"""Parse Gastronaut.hr PDF to extract restaurant contact information."""

import pdfplumber
import csv
import re
from pathlib import Path

PDF_PATH = "/home/darko/.openclaw/workspace/lead-gen/menuboost/gastronaut_restaurants.pdf"
OUTPUT_CSV = "/home/darko/.openclaw/workspace/lead-gen/menuboost/croatia-gastronaut-top100.csv"

# Try to download PDF if not exists
import requests

def download_pdf():
    """Download Gastronaut.hr PDF if not already downloaded."""
    url = "https://100.gastronaut.hr/knjiga/Restorani2024EN.pdf"
    
    if Path(PDF_PATH).exists():
        print(f"PDF already exists: {PDF_PATH}")
        return True
    
    print(f"Downloading PDF from {url}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(PDF_PATH, "wb") as f:
            f.write(response.content)
        
        print(f"PDF downloaded successfully: {PDF_PATH} ({len(response.content)} bytes)")
        return True
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        # Try alternative URL
        alt_url = "https://100.gastronaut.hr/knjiga/Restorani2023EN.pdf"
        try:
            print(f"Trying alternative URL: {alt_url}")
            response = requests.get(alt_url, timeout=30)
            response.raise_for_status()
            
            with open(PDF_PATH, "wb") as f:
                f.write(response.content)
            
            print(f"PDF downloaded from alternative URL: {PDF_PATH}")
            return True
        except Exception as e2:
            print(f"Error downloading from alternative URL: {e2}")
            return False

def extract_restaurants_from_pdf():
    """Extract restaurant information from PDF."""
    restaurants = []
    
    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            print(f"Processing PDF with {len(pdf.pages)} pages...")
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                # Look for restaurant patterns
                # Common patterns in restaurant guides:
                # 1. Restaurant name followed by city/region
                # 2. Contact information (email, phone, website)
                # 3. Address information
                
                lines = text.split('\n')
                
                # Try to find restaurant entries
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    # Skip empty lines and page numbers
                    if not line or line.isdigit() or '~' in line:
                        continue
                    
                    # Look for potential restaurant names (often in all caps or title case)
                    if (len(line) > 3 and len(line) < 100 and 
                        not line.startswith('http') and
                        not any(x in line.lower() for x in ['page', 'tel:', 'fax:', 'email:', '@', '.com', '.hr'])):
                        
                        # This might be a restaurant name
                        restaurant_name = line
                        
                        # Look ahead for contact info
                        email = None
                        phone = None
                        website = None
                        address = None
                        
                        # Check next few lines for contact info
                        for j in range(i+1, min(i+10, len(lines))):
                            next_line = lines[j].strip()
                            
                            if not next_line:
                                continue
                            
                            # Extract email
                            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', next_line)
                            if email_match and not email:
                                email = email_match.group(0)
                            
                            # Extract website
                            website_match = re.search(r'(https?://[^\s]+|www\.[^\s]+)', next_line)
                            if website_match and not website:
                                website = website_match.group(0)
                                if not website.startswith('http'):
                                    website = 'http://' + website
                            
                            # Extract phone
                            phone_match = re.search(r'[\+\d\s\-\(\)]{8,}', next_line)
                            if phone_match and not phone:
                                phone = phone_match.group(0).strip()
                        
                        # Only add if we have at least an email or website
                        if email or website:
                            restaurants.append({
                                'name': restaurant_name,
                                'email': email or '',
                                'website': website or '',
                                'phone': phone or '',
                                'source_page': page_num + 1
                            })
                            print(f"Found: {restaurant_name} - Email: {email}, Website: {website}")
    
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        # Try alternative extraction method
        return extract_with_simple_method()
    
    return restaurants

def extract_with_simple_method():
    """Simple text extraction for testing."""
    restaurants = []
    
    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # Save text for manual review
            text_file = PDF_PATH.replace('.pdf', '_extracted.txt')
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            print(f"Full text extracted to: {text_file}")
            
            # Try to find emails in the text
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', full_text)
            websites = re.findall(r'(https?://[^\s]+|www\.[^\s]+\.[a-z]{2,})', full_text)
            
            print(f"Found {len(emails)} emails and {len(websites)} websites in PDF")
            
            # For now, create a simple list from found emails
            for i, email in enumerate(emails[:50]):  # Limit to 50 for now
                # Try to find restaurant name near the email
                email_idx = full_text.find(email)
                if email_idx > 0:
                    # Look back 200 characters for potential name
                    prev_text = full_text[max(0, email_idx-200):email_idx]
                    lines = prev_text.split('\n')
                    # Take the last non-empty line as potential name
                    name = "Restaurant from Gastronaut.hr"
                    for line in reversed(lines):
                        line = line.strip()
                        if line and len(line) > 2 and len(line) < 100:
                            name = line
                            break
                    
                    restaurants.append({
                        'name': name,
                        'email': email,
                        'website': '',
                        'phone': '',
                        'source_page': 0
                    })
    
    except Exception as e:
        print(f"Error in simple extraction: {e}")
    
    return restaurants

def save_to_csv(restaurants):
    """Save extracted restaurants to CSV."""
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'email', 'website', 'phone', 'region', 'city', 'type', 'notes'])
        writer.writeheader()
        
        for r in restaurants:
            # Try to guess region from name or other info
            region = 'Croatia'
            city = ''
            r_type = 'Restaurant'
            
            writer.writerow({
                'name': r['name'],
                'email': r['email'],
                'website': r['website'],
                'phone': r['phone'],
                'region': region,
                'city': city,
                'type': r_type,
                'notes': f"Extracted from Gastronaut.hr PDF, page {r['source_page']}"
            })
    
    print(f"Saved {len(restaurants)} restaurants to {OUTPUT_CSV}")

def main():
    # Download PDF first
    if not download_pdf():
        print("Could not download PDF. Please check the URL or download manually.")
        return
    
    # Extract restaurants
    print("Extracting restaurant information from PDF...")
    restaurants = extract_restaurants_from_pdf()
    
    if not restaurants:
        print("No restaurants extracted. Trying simple method...")
        restaurants = extract_with_simple_method()
    
    if restaurants:
        save_to_csv(restaurants)
        print(f"\n🎉 Successfully extracted {len(restaurants)} restaurants!")
        print(f"CSV saved to: {OUTPUT_CSV}")
        
        # Show sample
        print("\nSample restaurants:")
        for i, r in enumerate(restaurants[:5]):
            print(f"  {i+1}. {r['name']} - {r['email']}")
    else:
        print("No restaurants could be extracted from the PDF.")
        print("Please check the PDF structure or extract manually.")

if __name__ == "__main__":
    main()