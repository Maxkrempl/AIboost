#!/usr/bin/env python3
"""
Reddit Signal Monitor — finds people asking about:
- Menu translation tools
- SEO audit alternatives
- GEO optimization
- Ad copy generators
"""
import json
import os
import re
from datetime import datetime

SEARCH_QUERIES = [
    "translate restaurant menu",
    "menu translation tool",
    "SEOptimer alternative",
    "SEO audit tool free",
    "how to rank in ChatGPT",
    "GEO optimization",
    "ad copy generator",
    "AI marketing tools",
    "restaurant menu multilingual",
    "freelancer SEO tools",
]

SUBREDDITS = [
    "SaaS", "microsaas", "localbusinesses", "marketing",
    "SEO", "restaurants", "smallbusiness", "Entrepreneur",
    "webdev", "saas", "indiehackers",
]

OUTPUT_FILE = "/home/darko/.openclaw/workspace/shared/reddit-signals.json"

def load_seen():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            return json.load(f)
    return {"seen": [], "last_check": None}

def save_seen(data):
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

def check_signals():
    """Placeholder — in production, use Reddit API or web scraping."""
    data = load_seen()
    data["last_check"] = datetime.now().isoformat()
    data["queries"] = SEARCH_QUERIES
    data["subreddits"] = SUBREDDITS
    save_seen(data)
    print(f"Monitor configured. Queries: {len(SEARCH_QUERIES)}, Subreddits: {len(SUBREDDITS)}")
    print("To activate: add Reddit API credentials to config.")

if __name__ == "__main__":
    check_signals()
