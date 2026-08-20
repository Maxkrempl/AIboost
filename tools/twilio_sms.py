#!/usr/bin/env python3
"""
Twilio SMS sender for ListTranslate outreach.
Usage: python3 twilio_sms.py --to "+86..." --body "你好，我是Max..."
       python3 twilio_sms.py --csv leads.csv --body-file message.txt
"""

import os
import sys
import csv
import json
import time
import argparse
from pathlib import Path

CRED_FILE = Path.home() / ".openclaw" / "workspace" / "tools" / "twilio.json"

def load_credentials():
    if not CRED_FILE.exists():
        print(f"❌ No Twilio credentials found at {CRED_FILE}")
        print("Run: python3 twilio_sms.py --setup")
        sys.exit(1)
    with open(CRED_FILE) as f:
        return json.load(f)

def save_credentials(account_sid, auth_token, from_number):
    CRED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CRED_FILE, "w") as f:
        json.dump({
            "account_sid": account_sid,
            "auth_token": auth_token,
            "from_number": from_number
        }, f, indent=2)
    os.chmod(CRED_FILE, 0o600)
    print(f"✅ Credentials saved to {CRED_FILE}")

def send_sms(to_number, body, creds=None):
    """Send a single SMS via Twilio REST API (no SDK needed)."""
    import urllib.request
    import urllib.parse
    import base64

    if creds is None:
        creds = load_credentials()

    account_sid = creds["account_sid"]
    auth_token = creds["auth_token"]
    from_number = creds["from_number"]

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

    data = urllib.parse.urlencode({
        "From": from_number,
        "To": to_number,
        "Body": body
    }).encode("ascii")

    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            print(f"✅ SMS sent to {to_number} | SID: {result['sid']} | Status: {result['status']}")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ Failed to send to {to_number}: {e.code} {error_body}")
        return None

def send_batch(csv_file, body, delay=1.0):
    """Send SMS to all numbers in a CSV file."""
    creds = load_credentials()
    results = []

    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Expect column: phone (or phone_number, mobile, etc.)
        phone_field = None
        for col in reader.fieldnames:
            if col.lower().strip() in ("phone", "phone_number", "mobile", "tel", "sms"):
                phone_field = col
                break
        if not phone_field:
            print(f"❌ No phone column found in CSV. Columns: {reader.fieldnames}")
            sys.exit(1)

        for i, row in enumerate(reader):
            phone = row[phone_field].strip()
            if not phone or not phone.startswith("+"):
                print(f"⚠️  Skipping invalid phone: {phone}")
                continue

            print(f"[{i+1}] Sending to {phone}...")
            result = send_sms(phone, body, creds)
            results.append({"phone": phone, "success": result is not None, "result": result})

            if i < len(list(reader)) - 1:
                time.sleep(delay)  # Rate limiting

    sent = sum(1 for r in results if r["success"])
    print(f"\n📊 Batch complete: {sent}/{len(results)} sent successfully")
    return results

def buy_number(creds=None):
    """Search for and buy a Twilio phone number."""
    import urllib.request
    import urllib.parse
    import base64

    if creds is None:
        creds = load_credentials()

    account_sid = creds["account_sid"]
    auth_token = creds["auth_token"]

    # Search for available numbers (US)
    url = "https://api.twilio.com/2010-04-01/Accounts/" + account_sid + "/AvailablePhoneNumbers/US.json?Limit=5"
    auth = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {auth}")

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            numbers = result.get("available_phone_numbers", [])
            if not numbers:
                print("❌ No available numbers")
                return None

            print("📱 Available numbers:")
            for i, n in enumerate(numbers):
                print(f"  [{i+1}] {n['phone_number']} ({n.get('locality', 'US')})")

            # Buy the first one
            chosen = numbers[0]
            buy_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/IncomingPhoneNumbers.json"
            buy_data = urllib.parse.urlencode({"PhoneNumber": chosen["phone_number"]}).encode()
            buy_req = urllib.request.Request(buy_url, data=buy_data, method="POST")
            buy_req.add_header("Authorization", f"Basic {auth}")
            buy_req.add_header("Content-Type", "application/x-www-form-urlencoded")

            with urllib.request.urlopen(buy_req) as buy_resp:
                bought = json.loads(buy_resp.read())
                print(f"✅ Bought number: {bought['phone_number']}")
                return bought["phone_number"]
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Twilio SMS Sender")
    parser.add_argument("--setup", action="store_true", help="Save Twilio credentials")
    parser.add_argument("--to", help="Recipient phone number (E.164 format: +1...)")
    parser.add_argument("--body", help="SMS message text")
    parser.add_argument("--body-file", help="Read SMS body from file")
    parser.add_argument("--csv", help="CSV file with phone numbers for batch send")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between sends (seconds)")
    parser.add_argument("--buy-number", action="store_true", help="Buy a Twilio phone number")
    parser.add_argument("--sid", help="Account SID (for --setup)")
    parser.add_argument("--token", help="Auth Token (for --setup)")
    parser.add_argument("--from-number", help="Twilio number (for --setup)")

    args = parser.parse_args()

    if args.setup:
        if not args.sid or not args.token or not args.from_number:
            print("Usage: python3 twilio_sms.py --setup --sid ACxxx --token xxx --from-number +1xxx")
            sys.exit(1)
        save_credentials(args.sid, args.token, args.from_number)
        return

    if args.buy_number:
        creds = load_credentials()
        buy_number(creds)
        return

    if args.csv and (args.body or args.body_file):
        body = args.body
        if args.body_file:
            with open(args.body_file, encoding="utf-8") as f:
                body = f.read()
        send_batch(args.csv, body, args.delay)
        return

    if args.to and (args.body or args.body_file):
        body = args.body
        if args.body_file:
            with open(args.body_file, encoding="utf-8") as f:
                body = f.read()
        send_sms(args.to, body)
        return

    parser.print_help()

if __name__ == "__main__":
    main()
