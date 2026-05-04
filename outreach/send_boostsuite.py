#!/usr/bin/env python3
"""Send BoostSuite outreach emails to agencies and freelancers."""

import csv
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import getpass
import sys
import os

# Config
SENDER = "23herceg@gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
CSV_FILE = "/home/darko/.openclaw/workspace/lead-gen/boostsuite/boostsuite-leads.csv"
SENT_LOG = "/home/darko/.openclaw/workspace/outreach/sent/boostsuite-sent.csv"
BATCH_SIZE = 25

# Email template - Agency/freelancer focused
SUBJECT = "Free SEO audit tool for your agency clients"

def make_email_agency(name):
    return f"""Hi,

Running SEO audits for clients takes time. What if you could do it in 10 seconds?

BoostSuite is an AI-powered marketing toolkit built for agencies and freelancers:

• SEO Audit — paste any URL, get instant score + top 5 fixes
• GEO Check — see how visible a business is across AI assistants (ChatGPT, Gemini, Perplexity)
• Ad Copy Generator — platform-ready copy for Google, Facebook, LinkedIn, X, Email
• Listing Optimizer — optimize Etsy, Amazon, Google Business listings

Try it free (3 audits, no signup): https://boostsuite.netlify.app

For agencies: Pro plan (€29/month) gives unlimited audits, white-label reports, and priority processing.

Use it for client pitches, monthly reports, or quick site checks. Saves hours per week.

Worth a look?

Darko
BoostSuite
https://boostsuite.netlify.app
"""

def make_email_freelancer(name):
    return f"""Hey,

Do you spend hours writing SEO reports for clients? Here's something that might help.

BoostSuite gives you instant SEO audits, AI visibility checks, ad copy generation, and listing optimization — all in one tool.

Try it free (no signup needed): https://boostsuite.netlify.app

Just paste a URL and get:
→ SEO score + top 5 actionable fixes
→ AI visibility across ChatGPT, Gemini, Perplexity
→ Ready-to-use ad copy for any platform
→ Optimized Etsy/Amazon/Google listings

Pro plan is €29/month for unlimited use + white-label reports.

Handy for freelancers who want to look professional without spending hours on reports.

Darko
BoostSuite
https://boostsuite.netlify.app
"""

def main():
    # Get Gmail App Password
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        cred_file = "/home/darko/.openclaw/workspace/outreach/credentials.sh"
        password = None
        if os.path.exists(cred_file):
            with open(cred_file) as f:
                for line in f:
                    if 'GMAIL_APP_PASSWORD' in line:
                        password = line.split('=',1)[1].strip().strip('"').strip("'")
                        break
        if not password:
            password = getpass.getpass("Gmail App Password: ")

    # Read contacts
    contacts = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('email', '').strip()
            if email and '@' in email:
                contacts.append({
                    "name": row.get('name', '').strip(),
                    "email": email,
                    "type": row.get('type', 'agency').strip(),
                })

    print(f"📋 Loaded {len(contacts)} contacts with emails")

    # Filter out already sent
    sent_emails = set()
    if os.path.exists(SENT_LOG):
        with open(SENT_LOG, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    sent_emails.add(row[2].strip().lower())

    unsent = [c for c in contacts if c['email'].lower() not in sent_emails]
    print(f"📤 {len(unsent)} unsent contacts, sending batch of {BATCH_SIZE}...")

    if not unsent:
        print("✅ All contacts already contacted!")
        return

    # Send batch
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(SENDER, password)

        sent = 0
        for contact in unsent[:BATCH_SIZE]:
            try:
                msg = MIMEMultipart()
                msg["From"] = f"Darko Herceg <{SENDER}>"
                msg["To"] = contact["email"]
                msg["Subject"] = SUBJECT

                # Choose template based on type
                if contact.get("type") == "freelancer":
                    body = make_email_freelancer(contact["name"])
                else:
                    body = make_email_agency(contact["name"])

                msg.attach(MIMEText(body, "plain", "utf-8"))
                server.sendmail(SENDER, contact["email"], msg.as_string())
                sent += 1
                print(f"  ✅ [{sent}] Sent to {contact['email']}")

                # Log
                os.makedirs(os.path.dirname(SENT_LOG), exist_ok=True)
                with open(SENT_LOG, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()},{contact['name']},{contact['email']},{contact.get('type','')}\n")

                import time, random
                time.sleep(random.uniform(3, 6))

            except Exception as e:
                print(f"  ❌ Failed {contact['email']}: {e}")

    print(f"\n📊 Sent {sent} emails. Log: {SENT_LOG}")

if __name__ == "__main__":
    main()
