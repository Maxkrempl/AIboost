#!/usr/bin/env python3
"""Fast PDF email extraction using pdftotext (if available)."""

import subprocess
import re
import csv
import os

PDF_PATH = "/home/darko/.openclaw/workspace/lead-gen/menuboost/gastronaut_restaurants.pdf"
OUTPUT_CSV = "/home/darko/.openclaw/workspace/lead-gen/menuboost/croatia-gastronaut-emails.csv"
TEMP_TEXT = "/tmp/gastronaut_text.txt"

def extract_with_pdftotext():
    """Extract text using pdftotext command."""
    print("Extracting text from PDF using pdftotext...")
    
    try:
        # Use pdftotext if available
        result = subprocess.run(
            ["pdftotext", PDF_PATH, "-"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            print("pdftotext failed, trying alternative...")
            return None
            
    except FileNotFoundError:
        print("pdftotext not installed, trying Python fallback...")
        return None
    except Exception as e:
        print(f"Error with pdftotext: {e}")
        return None

def extract_with_python():
    """Extract text using Python PDF library."""
    print("Extracting text with Python...")
    
    try:
        import pdfplumber
        
        full_text = ""
        with pdfplumber.open(PDF_PATH) as pdf:
            print(f"Processing {len(pdf.pages)} pages...")
            
            for i, page in enumerate(pdf.pages):
                if i % 20 == 0:
                    print(f"  Page {i+1}/{len(pdf.pages)}")
                
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        
        return full_text
        
    except Exception as e:
        print(f"Error with Python extraction: {e}")
        return None

def extract_emails_from_text(text):
    """Extract emails from text."""
    print("Searching for email addresses...")
    
    # Find all email addresses
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    
    # Clean and deduplicate
    unique_emails = []
    for email in emails:
        email = email.lower().strip()
        if email not in unique_emails:
            unique_emails.append(email)
    
    return unique_emails

def save_results(emails):
    """Save emails to CSV."""
    print(f"Saving {len(emails)} emails to CSV...")
    
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'restaurant_name', 'region', 'source', 'notes'])
        
        for i, email in enumerate(emails):
            # Try to extract domain for naming
            domain = email.split('@')[1] if '@' in email else 'unknown'
            restaurant_name = f"Restaurant from {domain}"
            
            writer.writerow([email, restaurant_name, 'Croatia', 'Gastronaut.hr PDF', 'Extracted via PDF parsing'])
    
    print(f"Saved to: {OUTPUT_CSV}")

def main():
    print("=== Gastronaut.hr PDF Email Extractor ===\n")
    
    # Try pdftotext first (faster)
    text = extract_with_pdftotext()
    
    # Fall back to Python
    if not text:
        text = extract_with_python()
    
    if not text:
        print("Failed to extract text from PDF.")
        return
    
    # Save text for debugging
    with open(TEMP_TEXT, 'w', encoding='utf-8') as f:
        f.write(text[:10000])  # First 10k chars
    print(f"Sample text saved to: {TEMP_TEXT}")
    
    # Extract emails
    emails = extract_emails_from_text(text)
    
    if emails:
        print(f"\n🎉 Found {len(emails)} unique email addresses!")
        print("\nFirst 20 emails:")
        for i, email in enumerate(emails[:20]):
            print(f"  {i+1:2d}. {email}")
        
        save_results(emails)
        
        # Show statistics
        domains = {}
        for email in emails:
            domain = email.split('@')[1] if '@' in email else 'unknown'
            domains[domain] = domains.get(domain, 0) + 1
        
        print("\nTop domains:")
        sorted_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)
        for domain, count in sorted_domains[:10]:
            print(f"  {domain}: {count} emails")
            
    else:
        print("No email addresses found in PDF.")

if __name__ == "__main__":
    main()