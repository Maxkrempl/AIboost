#!/usr/bin/env python3
"""Check if an email is in the shared suppression list.
Usage: python3 check_suppression.py email1@example.com email2@example.com
Returns: OK (not sent) or BLOCKED (already sent) per email."""
import sys, os

SUPPRESSION_FILE = os.path.expanduser("~/.openclaw/workspace/shared/sent-emails.txt")

def load_suppression():
    emails = set()
    if os.path.exists(SUPPRESSION_FILE):
        with open(SUPPRESSION_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    emails.add(line.lower())
    return emails

def add_to_suppression(email):
    """Add a newly sent email to the suppression list."""
    email = email.lower().strip()
    suppressed = load_suppression()
    if email not in suppressed:
        with open(SUPPRESSION_FILE, 'a') as f:
            f.write(email + '\n')
        return True  # added
    return False  # already there

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check_suppression.py <email> [email2] ...")
        print("       check_suppression.py --add <email>   (add after sending)")
        sys.exit(1)
    
    if sys.argv[1] == '--add' and len(sys.argv) >= 3:
        added = add_to_suppression(sys.argv[2])
        print(f"{'ADDED' if added else 'ALREADY_EXISTS'}: {sys.argv[2]}")
        sys.exit(0)
    
    suppressed = load_suppression()
    for email in sys.argv[1:]:
        email_lower = email.lower()
        if email_lower in suppressed:
            print(f"BLOCKED: {email} (already sent)")
        else:
            print(f"OK: {email} (safe to send)")
