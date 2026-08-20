#!/usr/bin/env python3
"""Reply Monitor Agent — checks for new email replies, classifies sentiment properly.

Fixes the broken sentiment detection that marks bounces as positive.

Run: python3 agents/reply_monitor.py
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime

WORKSPACE = "/home/darko/.openclaw/workspace"
STATE_FILE = os.path.join(WORKSPACE, "outreach/replies-state.json")
ALERT_FILE = os.path.join(WORKSPACE, "agents/alerts.json")

# Patterns that indicate bounce/failure (NOT positive replies)
BOUNCE_PATTERNS = [
    r"delivery status notification",
    r"undeliverable",
    r"address not found",
    r"message blocked",
    r"mail delivery subsystem",
    r"failure notice",
    r"returned mail",
    r"could not be delivered",
    r"permanent error",
    r"550 ",
    r"552 ",
    r"421 ",
    r"451 ",
    r"mailer-daemon",
    r"postmaster@",
    r"no-reply@",
    r"noreply@",
    r"automatic reply",
    r"out of office",
    r"vacation",
]

# Patterns that indicate genuine interest
POSITIVE_PATTERNS = [
    r"zainteresir",       # interested (SI/HR)
    r"interesir",         # interested
    r"rad bi",            # I would like (SI)
    r"žel",               # want/wish (SI)
    r"prosim",            # please (SI)
    r"kako",              # how (SI/HR)
    r"kaj pa",            # what about (SI)
    r"lahko",             # can you (SI)
    r"pošlji",            # send (SI)
    r"želim",             # I want (SI)
    r"contact",           # contact
    r"interested",        # interested
    r"tell me more",      # interested
    r"pricing",           # buying signal
    r"price",             # buying signal
    r"demo",              # buying signal
    r"trial",             # buying signal
    r"free",              # buying signal
    r"yes",               # affirmative
    r"da",                # yes (SI/HR)
    r"ok",                # ok
]

# Patterns that indicate rejection
NEGATIVE_PATTERNS = [
    r"nismo zainteresirani",  # not interested (HR)
    r"ne zanima",             # not interested (SI)
    r"hvala.*ne",             # thanks but no
    r"trenutno ne",           # currently no
    r"odjavi",                # unsubscribe
    r"unsubscribe",
    r"opt out",
    r"remove me",
    r"stop",
    r"ne želim",              # don't want
]


def classify_reply(subject, preview):
    """Classify reply sentiment properly."""
    text = f"{subject} {preview}".lower()

    # Check bounce first (most common false positive)
    for pattern in BOUNCE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return "bounce"

    # Check negative
    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return "negative"

    # Check positive
    positive_score = 0
    for pattern in POSITIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            positive_score += 1

    if positive_score >= 1:
        return "positive"

    return "neutral"


def load_state():
    """Load reply state."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"replies": [], "lastCheck": None}


def save_state(state):
    """Save reply state."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def check_replies():
    """Run the reply checker and reclassify."""
    state = load_state()
    replies = state.get("replies", [])

    # Reclassify all existing replies
    fixed = 0
    for reply in replies:
        subject = reply.get("subject", "")
        preview = reply.get("preview", "")
        old_sentiment = reply.get("sentiment", "unknown")
        new_sentiment = classify_reply(subject, preview)

        if old_sentiment != new_sentiment:
            reply["sentiment"] = new_sentiment
            reply["sentiment_fixed"] = True
            fixed += 1

    # Count by sentiment
    counts = {}
    for reply in replies:
        s = reply.get("sentiment", "unknown")
        counts[s] = counts.get(s, 0) + 1

    # Find genuine positive replies
    positives = [r for r in replies if r.get("sentiment") == "positive"]

    # Generate alert if there are new positive replies
    alerts = []
    for pos in positives:
        if not pos.get("alerted"):
            alerts.append({
                "type": "positive_reply",
                "from": pos.get("from", "unknown"),
                "subject": pos.get("subject", ""),
                "preview": pos.get("preview", "")[:200],
                "timestamp": datetime.now().isoformat()
            })
            pos["alerted"] = True

    save_state(state)

    # Output summary
    print(f"📊 Reply Monitor Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Total replies: {len(replies)}")
    print(f"   Fixed sentiment: {fixed}")
    print()
    for sentiment, count in sorted(counts.items()):
        emoji = {"positive": "🟢", "negative": "🔴", "bounce": "⚪", "neutral": "🟡"}.get(sentiment, "❓")
        print(f"   {emoji} {sentiment}: {count}")

    if alerts:
        print(f"\n🚨 {len(alerts)} NEW positive replies need attention!")
        for alert in alerts:
            print(f"   📩 {alert['from']}: {alert['subject']}")
            print(f"      {alert['preview'][:150]}")

    # Save alerts
    if alerts:
        existing_alerts = []
        if os.path.exists(ALERT_FILE):
            with open(ALERT_FILE) as f:
                existing_alerts = json.load(f)
        existing_alerts.extend(alerts)
        with open(ALERT_FILE, "w") as f:
            json.dump(existing_alerts, f, indent=2)

    return {
        "total": len(replies),
        "fixed": fixed,
        "counts": counts,
        "new_alerts": len(alerts),
        "positives": len([r for r in replies if r.get("sentiment") == "positive"])
    }


if __name__ == "__main__":
    result = check_replies()
    print(f"\n✅ Done. {result['new_alerts']} new alerts generated.")
