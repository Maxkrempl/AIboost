#!/usr/bin/env python3
"""Content Agent — generates blog posts, social media content, and translations.

Generates drafts for MenuBoost marketing content in all target languages.

Run: python3 agents/content_agent.py [--topic blog|social|email] [--lang si|hr|it|en]
"""

import os
import json
from datetime import datetime

WORKSPACE = "/home/darko/.openclaw/workspace"
DRAFTS_DIR = os.path.join(WORKSPACE, "content/drafts")

# Content calendar topics
CONTENT_CALENDAR = {
    "blog": [
        {
            "title": "Kako prevesti jedilnik za tuje goste v 10 sekundah",
            "title_en": "How to translate your menu for foreign guests in 10 seconds",
            "keywords": ["meni prevod", "jedilnik tujci", "restavracija turisti"],
            "target": "restaurants"
        },
        {
            "title": "Zakaj turistične kmetije potrebujejo večjezični meni",
            "title_en": "Why tourist farms need multilingual menus",
            "keywords": ["turistična kmetija", "večjezični meni", "tuji gosti"],
            "target": "tourist_farms"
        },
        {
            "title": "5 najpogostejših napak pri prevajanju jedilnikov",
            "title_en": "5 most common menu translation mistakes",
            "keywords": ["napake prevajanje", "jedilnik napake", "menu translation errors"],
            "target": "all"
        },
        {
            "title": "Kako hoteli privabijo več tujih gostov z boljšim menijem",
            "title_en": "How hotels attract more foreign guests with better menus",
            "keywords": ["hotel meni", "tuji gosti hotel", "hotel menu translation"],
            "target": "hotels"
        },
    ],
    "social": [
        {
            "platform": "facebook",
            "topic": "Customer success story",
            "target_groups": ["Slovenian restaurants", "Croatian tourism", "Italian agriturismos"]
        },
        {
            "platform": "linkedin",
            "topic": "MenuBoost product update",
            "target": "SaaS community, restaurant owners"
        },
        {
            "platform": "instagram",
            "topic": "Before/after menu translation visual",
            "target": "Food lovers, restaurant owners"
        },
    ]
}


def get_next_content(content_type="blog"):
    """Get the next content piece to create based on calendar."""
    if content_type == "blog":
        return CONTENT_CALENDAR["blog"]
    elif content_type == "social":
        return CONTENT_CALENDAR["social"]
    return []


def generate_blog_draft(topic):
    """Generate a blog post draft structure."""
    draft = {
        "type": "blog",
        "topic": topic,
        "generated_at": datetime.now().isoformat(),
        "status": "draft",
        "structure": {
            "title": topic["title"],
            "meta_description": f"Odkrijte {topic['title'].lower()}. MenuBoost vam pomaga prevesti jedilnik v 10 sekundah.",
            "sections": [
                {"heading": "Uvod", "content": "[Draft needed]"},
                {"heading": "Problem", "content": "[Draft needed]"},
                {"heading": "Rešitev", "content": "[Draft needed]"},
                {"heading": "Kako deluje", "content": "[Draft needed]"},
                {"heading": "Zaključek", "content": "[Draft needed]"},
            ],
            "cta": "Preizkusite MenuBoost brezplačno na menuboost.com",
            "keywords": topic["keywords"],
            "target_audience": topic["target"]
        }
    }
    return draft


def generate_social_draft(topic):
    """Generate a social media post draft structure."""
    draft = {
        "type": "social",
        "platform": topic["platform"],
        "generated_at": datetime.now().isoformat(),
        "status": "draft",
        "content": {
            "hook": "[Hook needed]",
            "body": "[Body needed]",
            "cta": "[CTA needed]",
            "hashtags": ["#MenuBoost", "#restavracija", "#turizem", "#gostinstvo"],
            "image_suggestion": "[Image concept needed]"
        }
    }
    return draft


def run_content_agent(content_type="blog"):
    """Run the content agent for a given type."""
    os.makedirs(DRAFTS_DIR, exist_ok=True)

    topics = get_next_content(content_type)
    drafts = []

    for topic in topics:
        if content_type == "blog":
            draft = generate_blog_draft(topic)
        elif content_type == "social":
            draft = generate_social_draft(topic)
        else:
            continue

        # Save draft
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        filename = f"{content_type}-{timestamp}.json"
        filepath = os.path.join(DRAFTS_DIR, filename)

        with open(filepath, "w") as f:
            json.dump(draft, f, indent=2, ensure_ascii=False)

        drafts.append(draft)

    print(f"🎨 Content Agent generated {len(drafts)} {content_type} drafts")
    for d in drafts:
        if content_type == "blog":
            print(f"   📝 {d['topic']['title']}")
        else:
            print(f"   📱 {d['platform']}: {d['content']['hook'][:50]}...")

    return drafts


if __name__ == "__main__":
    import sys
    content_type = sys.argv[1] if len(sys.argv) > 1 else "blog"
    run_content_agent(content_type)
