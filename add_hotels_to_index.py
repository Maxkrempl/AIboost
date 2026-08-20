#!/usr/bin/env python3
"""
Add all hotels to the AI Visibility Index.
Uses POST to hd-webdesign.si/indeks-ai-vidljivosti/api/index.php
"""
import json
import subprocess
import time

API_URL = "https://hd-webdesign.si/indeks-ai-vidljivosti/api/index.php"

def add_to_index(entry):
    """Add single entry to index via API."""
    data = json.dumps(entry, ensure_ascii=False)
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", API_URL,
         "-H", "Content-Type: application/json",
         "-d", data],
        capture_output=True, text=True, timeout=15
    )
    return result.stdout

def grade_to_score(grade):
    """Convert letter grade to numeric score."""
    return {"A": 90, "B": 70, "C": 50, "D": 30, "F": 10, "N/A": 0}.get(grade, 0)

def main():
    # Load 5-star hotels
    with open("/home/darko/.openclaw/workspace/outreach/hotel_5star_audit.json") as f:
        hotels_5star = json.load(f)
    
    # Load other hotels
    with open("/home/darko/.openclaw/workspace/outreach/hotel_search_results.json") as f:
        hotels_other = json.load(f)
    
    # Combine and filter (only with websites)
    all_hotels = hotels_5star + hotels_other
    hotels = [h for h in all_hotels if h.get("website")]
    
    print(f"🏨 Skupaj hotelov z spletnimi stranmi: {len(hotels)}")
    print(f"{'='*60}")
    
    added = 0
    errors = 0
    
    for i, hotel in enumerate(hotels):
        name = hotel["name"]
        website = hotel["website"]
        grade = hotel.get("score", "N/A")
        stars = hotel.get("stars", "")
        checks = hotel.get("checks", {})
        
        # Build entry
        entry = {
            "domain": website,
            "podjetje": name,
            "score": grade_to_score(grade),
            "grade": grade,
            "sector": "Turizem in gostinstvo",
            "checks": {
                "main": {"pass": True},
                "llms": {"pass": checks.get("llms", False)},
                "schema": {"pass": checks.get("schema", False)},
                "meta": {"pass": checks.get("meta", False)},
                "og": {"pass": False},
                "sitemap": {"pass": False},
                "robots": {"pass": checks.get("robots", False)}
            },
            "visible": True,
            "category": f"{stars} hotel" if stars else "Hotel"
        }
        
        # Add to index
        result = add_to_index(entry)
        try:
            resp = json.loads(result)
            if "id" in resp:
                added += 1
                print(f"[{i+1}/{len(hotels)}] ✅ {name} → {grade}")
            else:
                errors += 1
                print(f"[{i+1}/{len(hotels)}] ❌ {name} → {resp.get('error', 'unknown')}")
        except:
            errors += 1
            print(f"[{i+1}/{len(hotels)}] ❌ {name} → napaka pri odzivu")
        
        time.sleep(0.5)  # Rate limit
    
    print(f"\n{'='*60}")
    print(f"✅ Dodanih: {added}")
    print(f"❌ Napake: {errors}")

if __name__ == "__main__":
    main()
