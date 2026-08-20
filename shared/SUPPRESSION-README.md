# Shared Email Suppression List

## What
`sent-emails.txt` contains ALL email addresses that have been sent outreach from either Rose (Hermes) or Max (OpenClaw).

## Why
Prevent duplicate outreach — same lead getting the same (or different) product email twice.

## How to check before sending
```bash
python3 ~/.openclaw/workspace/shared/check_suppression.py email@example.com
# Returns: OK (safe) or BLOCKED (already sent)
```

## How to add after sending
```bash
python3 ~/.openclaw/workspace/shared/check_suppression.py --add email@example.com
```

## Who updates this
- **Rose (Hermes)** — after any email send via Resend
- **Max (OpenClaw)** — after any email send via send_queue.py

## Rules
1. ALWAYS check suppression list BEFORE sending any email
2. ALWAYS add to suppression list AFTER sending
3. Both MenuBoost AND BoostSuite emails are tracked (same list)
4. If BLOCKED: skip the lead, do not send any follow-up
