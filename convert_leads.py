import csv
import sys
from datetime import datetime, timedelta

# Read OSINT CSV
osint_rows = []
with open('OSINT_leads_2026Q2.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        osint_rows.append(row)

# Transform to LeadSheet format
leadsheet_rows = []
for i, row in enumerate(osint_rows):
    # Extract contact from LinkedIn URL if available
    contact = ""
    linkedin = row.get('LinkedIn', '')
    if linkedin and linkedin != 'N/A':
        # Try to extract name from LinkedIn URL
        if '/in/' in linkedin:
            # Example: https://www.linkedin.com/in/john-ozuysal/
            parts = linkedin.split('/in/')
            if len(parts) > 1:
                name_part = parts[1].strip('/')
                name = name_part.replace('-', ' ').title()
                contact = name
    
    # Determine ICP based on Industry
    industry = row.get('Industry', '')
    icp = ""
    if 'SEO' in industry or 'Digital Marketing' in industry:
        icp = "SEO/Digital Marketing Agency"
    elif 'E-commerce' in industry:
        icp = "E-commerce Store"
    elif 'Hospitality' in industry:
        icp = "Restaurant/Hospitality"
    else:
        icp = industry
    
    # Extract email from ContactPage if it looks like an email
    contact_page = row.get('ContactPage', '')
    email = ""
    if '@' in contact_page and '.' in contact_page and ' ' not in contact_page:
        email = contact_page
    elif 'hello@' in contact_page:
        email = contact_page
    
    # Create LeadSheet row
    leadsheet_row = {
        'Company': row.get('Company', ''),
        'Contact': contact,
        'Title': 'Founder/Manager' if contact else '',
        'Email': email,
        'Website': row.get('Website', ''),
        'Country': row.get('Country', ''),
        'ICP': icp,
        'Channel': 'Outreach',
        'Stage': 'Lead',
        'Wave': '1',
        'MessageVariant': 'A',
        'FollowUpDate': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
        'MilestoneDate': (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
        'Notes': row.get('WhyFit', '')[:200]  # Truncate if too long
    }
    leadsheet_rows.append(leadsheet_row)

# Write LeadSheet CSV
fieldnames = ['Company', 'Contact', 'Title', 'Email', 'Website', 'Country', 'ICP', 'Channel', 'Stage', 'Wave', 'MessageVariant', 'FollowUpDate', 'MilestoneDate', 'Notes']

with open('leads/LeadSheet.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(leadsheet_rows)

print(f"Converted {len(leadsheet_rows)} leads to LeadSheet.csv")