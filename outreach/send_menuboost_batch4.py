#!/usr/bin/env python3
"""Send MenuBoost outreach emails to tourist farms via Gmail SMTP - Batch 4 (61-80)."""

import csv
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import getpass
import sys

# Config
SENDER = "23herceg@gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
CSV_FILE = "/home/darko/.openclaw/workspace/lead-gen/menuBoost/leads-with-email.csv"
SENT_LOG = "/home/darko/.openclaw/workspace/outreach/sent/menuboost-sent.csv"
BATCH_START = 60  # 0-indexed, so 40 means starting from the 41st item
BATCH_SIZE = 20

# Slovenian email template
def make_email(name, address, url):
    return f"""Živjo,

Koliko tujih gostov imate na turistični kmetiji {name}? Koliko časa porabite za prevajanje jedilnika v nemščino ali angleščino?

MenuBoost v 10 sekundah ustvari apetiten opis vaše jedi v 6 jezikih: slovensko, hrvaško, angleško, nemško, italjansko, srbsko.

Kaj dobite:
• Poetične opise jedi za jedilnik
• Opise za Wolt/Bolt Food dostavo
• Opise za družbena omrežja (Instagram, Facebook)
• Prevode v nemščino za nemške in avstrijske goste

3 opisi brezplačno — brez registracije: https://menuboostai.netlify.app

Za neomejeno uporabo: 19 EUR/mesec.

Idealno za turistične kmetije, ki želijo privabiti več tujih gostov z lepimi opisi jedi.

Lep pozdrav,
Darko
MenuBoost
https://menuboostai.netlify.app
"""

SUBJECT = "MenuBoost — vaš digitalni meni za turistično kmetijo"

def main():
    # Get Gmail App Password
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = getpass.getpass("Gmail App Password for 23herceg@gmail.com: ")

    # Read contacts
    contacts = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            contacts.append({
                "name": row["ime"],
                "address": row["naslov"],
                "email": row["email"],
                "url": row["url"]
            })

    print(f"📋 Loaded {len(contacts)} contacts")
    print(f"📤 Sending batch {BATCH_START+1} to {BATCH_START+BATCH_SIZE}...\n")

    # Connect to Gmail
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(SENDER, password)

        sent = 0
        for contact in contacts[BATCH_START:BATCH_START+BATCH_SIZE]:
            try:
                msg = MIMEMultipart()
                msg["From"] = f"Darko <{SENDER}>"
                msg["To"] = contact["email"]
                msg["Subject"] = SUBJECT
                msg["Content-Type"] = "text/plain; charset=UTF-8"

                body = make_email(contact["name"], contact["address"], contact["url"])
                msg.attach(MIMEText(body, "plain", "utf-8"))

                server.sendmail(SENDER, contact["email"], msg.as_string())
                sent += 1
                print(f"  ✅ {sent}. {contact['name']} → {contact['email']}")
            except Exception as e:
                print(f"  ❌ {contact['name']} → {contact['email']}: {e}")

    print(f"\n🎉 Sent {sent}/{BATCH_SIZE} emails!")

    # Log sent emails
    with open(SENT_LOG, "a", encoding="utf-8") as f:
        for contact in contacts[BATCH_START:BATCH_START+BATCH_SIZE]:
            f.write(f"{datetime.now().isoformat()},{contact['name']},{contact['email']},{contact['url']}\n")
    print(f"📝 Logged to {SENT_LOG}")

if __name__ == "__main__":
    main()