#!/usr/bin/env python3
import csv, os

BASE = "/home/darko/.openclaw/media/inbound/kmetije_kontakti---59898630-c3eb-41e1-bf22-241f4dcebdc4.csv"
DIR = "/home/darko/.openclaw/workspace/lead-gen/menuBoost"
os.makedirs(DIR, exist_ok=True)

ALL_FILE = os.path.join(DIR, "leads-all.csv")
WITH_EMAIL = os.path.join(DIR, "leads-with-email.csv")
NO_EMAIL = os.path.join(DIR, "leads-no-email.csv")

def norm_key(k: str) -> str:
    return (k or "").strip().lstrip("\ufeff")

with open(BASE, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    # Normalize keys to avoid BOM / whitespace issues
    rows = [{norm_key(k): (v.strip() if isinstance(v, str) else v) for k, v in r.items()} for r in reader]

# All leads
with open(ALL_FILE, "w", newline="", encoding="utf-8") as out:
    w = csv.writer(out)
    w.writerow(["ime", "naslov", "email", "url"])
    for r in rows:
        w.writerow([r["ime"], r["naslov"], r["email"], r["url"]])

# With email (deduplicated)
seen = set()
email_rows = []
for r in rows:
    e = r["email"].strip()
    if e and e not in seen:
        seen.add(e)
        email_rows.append(r)

with open(WITH_EMAIL, "w", newline="", encoding="utf-8") as out:
    w = csv.writer(out)
    w.writerow(["ime", "naslov", "email", "url"])
    for r in email_rows:
        w.writerow([r["ime"], r["naslov"], r["email"], r["url"]])

# Without email
no_email_rows = [r for r in rows if not r["email"].strip()]
with open(NO_EMAIL, "w", newline="", encoding="utf-8") as out:
    w = csv.writer(out)
    w.writerow(["ime", "naslov", "email", "url"])
    for r in no_email_rows:
        w.writerow([r["ime"], r["naslov"], r["email"], r["url"]])

print(f"Total leads: {len(rows)}")
print(f"With email (unique): {len(email_rows)}")
print(f"Without email: {len(no_email_rows)}")
print(f"Files saved to: {DIR}")
