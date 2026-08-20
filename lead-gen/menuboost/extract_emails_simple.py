#!/usr/bin/env python3
"""Simple script to extract emails from Gastronaut.hr PDF."""

import pdfplumber
import re
import csv

PDF_PATH = "/home/darko/.openclaw/workspace/lead-gen/menuboost/gastronaut_restaurants.pdf"
OUTPUT_CSV = "/home/darko/.openclaw/workspace/lead-gen/menuboost/croatia-gastronaut-emails.csv"

def extract_emails_from_pdf():
    """Extract all email addresses from PDF."""
    print(f"Opening PDF: {PDF_PATH}")
    
    emails_found = []
    
    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            print(f"PDF has {len(pdf.pages)} pages")
            
            for page_num, page in enumerate(pdf.pages):
                if page_num % 10 == 0:
                    print(f"Processing page {page_num + 1}/{len(pdf.pages)}...")
                
                text = page.extract_text()
                if text:
                    # Find all email addresses in the text
                    page_emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
                    
                    for email in page_emails:
                        # Clean and validate email
                        email = email.lower().strip()
                        if email not in emails_found:
                            emails_found.append(email)
                            
                            # Try to find restaurant name near the email
                            email_pos = text.find(email)
                            if email_pos > 0:
                                # Look back 100 characters for potential name
                                start = max(0, email_pos - 100)
                                context = text[start:email_pos]
                                lines = context.split('\n')
                                
                                # Find the last non-empty line before the email
                                name = "Unknown Restaurant"
                                for line in reversed(lines):
                                    line = line.strip()
                                    if line and len(line) > 2 and len(line) < 100:
                                        if not any(x in line.lower() for x in ['http', '@', 'tel:', 'fax:', 'phone:']):
                                            name = line
                                            break
                                
                                print(f"  Found: {name} - {email}")
    
    except Exception as e:
        print(f"Error: {e}")
        return []
    
    return emails_found

def save_emails(emails):
    """Save emails to CSV."""
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'name', 'region', 'notes'])
        
        for i, email in enumerate(emails):
            writer.writerow([email, f"Restaurant {i+1} from Gastronaut.hr", "Croatia", "Extracted from Gastronaut.hr PDF"])
    
    print(f"\nSaved {len(emails)} emails to {OUTPUT_CSV}")

def main():
    print("Extracting emails from Gastronaut.hr PDF...")
    emails = extract_emails_from_pdf()
    
    if emails:
        print(f"\n🎉 Found {len(emails)} unique email addresses!")
        print("\nSample emails:")
        for i, email in enumerate(emails[:10]):
            print(f"  {i+1}. {email}")
        
        save_emails(emails)
    else:
        print("No emails found in PDF.")

if __name__ == "__main__":
    main()