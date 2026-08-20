#!/usr/bin/env python3
"""Quick search for emails in first few pages of PDF."""

import pdfplumber
import re

PDF_PATH = "/home/darko/.openclaw/workspace/lead-gen/menuboost/gastronaut_restaurants.pdf"

def quick_search():
    """Search first 20 pages for emails."""
    print("Searching first 20 pages for emails...")
    
    emails = []
    
    try:
        with pdfplumber.open(PDF_PATH) as pdf:
            total_pages = len(pdf.pages)
            print(f"PDF has {total_pages} pages total")
            
            # Only check first 20 pages to save time
            pages_to_check = min(20, total_pages)
            
            for page_num in range(pages_to_check):
                page = pdf.pages[page_num]
                text = page.extract_text()
                
                if text:
                    page_emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
                    
                    for email in page_emails:
                        email = email.lower().strip()
                        if email not in emails:
                            emails.append(email)
                            print(f"Page {page_num+1}: {email}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    return emails

def main():
    emails = quick_search()
    
    print(f"\nFound {len(emails)} emails in first 20 pages:")
    for i, email in enumerate(emails):
        print(f"{i+1:2d}. {email}")
    
    # Save to file
    if emails:
        with open("/tmp/gastronaut_emails.txt", "w") as f:
            for email in emails:
                f.write(f"{email}\n")
        print(f"\nEmails saved to /tmp/gastronaut_emails.txt")

if __name__ == "__main__":
    main()