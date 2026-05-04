#!/usr/bin/env python3
"""Send UPUHH partnership inquiry email."""

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
RECIPIENT = "info@upuhh.hr"

SUBJECT = "Partnerstvo za unapređenje digitalne prisutnosti hrvatskih restorana"

EMAIL_BODY = """Poštovani,

Pišemo vam u imenu MenuBoost.ai, inovativne platforme koja pomaže restoranima da poboljšaju svoju digitalnu prisutnost i povećaju promet kroz višejezične QR kod menije.

Naša usluga omogućuje restoranima da:
1. Kreiraju profesionalne digitalne menije na više jezika
2. Generišu QR kodove za bezdodirno naručivanje
3. Prikažu fotografije jela i detaljne opise
4. Prispiju međunarodnim turistima bez jezičkih barijera

Vidjeli smo da UPUHH predstavlja vodeće hotele i ugostiteljske objekte u Hrvatskoj, te bismo željeli razgovarati o mogućem partnerstvu.

Naša ideja:
- Preporučiti MenuBoost članicama UPUHH-a kao korisno rješenje za poboljšanje turističkog iskustva
- Organizirati demo prezentaciju za zainteresirane članice
- Kreirati posebne uvjete za članice UPUHH-a

MenuBoost je posebno koristan za hrvatske restorane jer:
- Podržava hrvatski, engleski, njemački, talijanski i druge jezike
- Povećava prosječnu potrošnju gostiju do 23%
- Smanjuje troškove tiskanja menija
- Poboljšava ocjene na Google i TripAdvisor

Možemo li zakazati kratki telefonski razgovor ili online sastanak kako bismo vam detaljnije predstavili našu ponudu?

S poštovanjem,

Darko Herceg
Founder, MenuBoost.ai
Email: 23herceg@gmail.com
Web: https://menuboostai.netlify.app
"""

def main():
    # Get Gmail App Password
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        # Try credentials file first
        cred_file = "/home/darko/.openclaw/workspace/outreach/credentials.sh"
        password = None
        if os.path.exists(cred_file):
            with open(cred_file) as f:
                for line in f:
                    if 'GMAIL_APP_PASSWORD' in line:
                        password = line.split('=',1)[1].strip().strip('"').strip("'")
                        break
        if not password:
            password = getpass.getpass("Gmail App Password for 23herceg@gmail.com: ")

    # Create message
    msg = MIMEMultipart()
    msg["From"] = f"Darko Herceg <{SENDER}>"
    msg["To"] = RECIPIENT
    msg["Subject"] = SUBJECT
    msg["Content-Type"] = "text/plain; charset=UTF-8"

    msg.attach(MIMEText(EMAIL_BODY, "plain", "utf-8"))

    # Send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(SENDER, password)
        server.sendmail(SENDER, RECIPIENT, msg.as_string())
        print(f"✅ UPUHH partnership email sent to {RECIPIENT}")

    # Log sent email
    log_file = "/home/darko/.openclaw/workspace/outreach/sent/upuhh-sent.csv"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()},UPUHH,{RECIPIENT},partnership\n")
    print(f"📝 Logged to {log_file}")

if __name__ == "__main__":
    main()
