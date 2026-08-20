#!/usr/bin/env python3
"""Resend email sender — replaces Gmail SMTP for outreach.

Usage:
  python3 resend_send.py --to user@example.com --subject "Hello" --html "<p>Hi</p>"
  python3 resend_send.py --to user@example.com --subject "Hello" --text "Hi"
  python3 resend_send.py --to-file recipients.csv --subject "Hello" --html "<p>Hi</p>"
  echo "user@example.com" | python3 resend_send.py --stdin --subject "Hello" --html "<p>Hi</p>"
"""

import argparse
import csv
import json
import os
import sys
import time
import requests
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────────────

ENV_FILE = Path(__file__).parent.parent / ".env"
API_URL = "https://api.resend.com/emails"

def load_env():
    """Load .env file into dict."""
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    # Also check environment variables (override .env)
    for key in ["RESEND_API_KEY", "RESEND_FROM_EMAIL", "RESEND_FROM_NAME", "RESEND_DOMAIN"]:
        if key in os.environ:
            env[key] = os.environ[key]
    return env

def send_email(api_key: str, from_email: str, from_name: str, to: str, subject: str, 
               html: str = None, text: str = None, reply_to: str = None, 
               tags: list = None) -> dict:
    """Send a single email via Resend API."""
    payload = {
        "from": f"{from_name} <{from_email}>" if from_name else from_email,
        "to": [to],
        "subject": subject,
    }
    if html:
        payload["html"] = html
    if text:
        payload["text"] = text
    if reply_to:
        payload["reply_to"] = [reply_to]
    if tags:
        payload["tags"] = [{"name": t.split(":")[0], "value": t.split(":")[1] if ":" in t else "default"} for t in tags]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "HD-Web-Design-Outreach/1.0",
    }

    resp = requests.post(API_URL, json=payload, headers=headers, timeout=15)
    return resp.json()

def main():
    parser = argparse.ArgumentParser(description="Send emails via Resend API")
    parser.add_argument("--to", help="Recipient email address")
    parser.add_argument("--to-file", help="CSV file with email column")
    parser.add_argument("--stdin", action="store_true", help="Read emails from stdin (one per line)")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--html", help="HTML body")
    parser.add_argument("--text", help="Plain text body")
    parser.add_argument("--reply-to", help="Reply-To address")
    parser.add_argument("--from-email", help="Override sender email")
    parser.add_argument("--from-name", help="Override sender name")
    parser.add_argument("--tags", nargs="*", help="Tags as key:value pairs")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be sent")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between sends (seconds)")
    parser.add_argument("--limit", type=int, help="Max emails to send")
    args = parser.parse_args()

    env = load_env()
    api_key = args.from_email or env.get("RESEND_API_KEY")
    if not api_key or api_key == "re_...":
        print("ERROR: No API key. Set RESEND_API_KEY in .env or environment.", file=sys.stderr)
        sys.exit(1)

    from_email = args.from_email or env.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    from_name = args.from_name or env.get("RESEND_FROM_NAME", "Max Herceg")

    # Collect recipients
    recipients = []
    if args.to:
        recipients.append(args.to)
    elif args.to_file:
        with open(args.to_file) as f:
            reader = csv.DictReader(f)
            # Try common column names
            for row in reader:
                email = row.get("email") or row.get("Email") or row.get("EMAIL") or row.get("e-mail") or row.get("E-mail")
                if email:
                    recipients.append(email.strip())
    elif args.stdin:
        for line in sys.stdin:
            line = line.strip()
            if line and "@" in line:
                recipients.append(line)
    else:
        print("ERROR: Specify --to, --to-file, or --stdin", file=sys.stderr)
        sys.exit(1)

    if not recipients:
        print("ERROR: No recipients found.", file=sys.stderr)
        sys.exit(1)

    if args.limit:
        recipients = recipients[:args.limit]

    if not args.html and not args.text:
        print("ERROR: Specify --html or --text", file=sys.stderr)
        sys.exit(1)

    print(f"Sending to {len(recipients)} recipients from {from_name} <{from_email}>")
    
    results = []
    for i, recipient in enumerate(recipients):
        if args.dry_run:
            print(f"  [{i+1}/{len(recipients)}] DRY RUN → {recipient}")
            continue

        result = send_email(
            api_key=api_key,
            from_email=from_email,
            from_name=from_name,
            to=recipient,
            subject=args.subject,
            html=args.html,
            text=args.text,
            reply_to=args.reply_to,
            tags=args.tags,
        )
        
        status = "✅" if "id" in result else f"❌ {result.get('message', 'unknown error')}"
        print(f"  [{i+1}/{len(recipients)}] {recipient} → {status}")
        results.append({"email": recipient, "result": result})

        if i < len(recipients) - 1:
            time.sleep(args.delay)

    # Summary
    sent = sum(1 for r in results if "id" in r["result"])
    failed = len(results) - sent
    print(f"\nDone: {sent} sent, {failed} failed")

    # Save sent log
    log_file = Path(__file__).parent.parent / "outreach" / "sent" / f"resend-{int(time.time())}.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "w") as f:
        json.dump({"timestamp": time.time(), "from": from_email, "results": results}, f, indent=2)
    print(f"Log saved: {log_file}")

if __name__ == "__main__":
    main()
