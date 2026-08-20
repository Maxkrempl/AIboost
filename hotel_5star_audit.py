#!/usr/bin/env python3
"""
5★ Hotel AI Visibility Audit — slow batch
Processes one hotel at a time with delays.
"""
import json
import subprocess
import time
import sys
import os
import re

WORKSPACE = "/home/darko/.openclaw/workspace"
IZKAZNICA_URL = "https://hd-webdesign.si/ai-izkaznica/"

HOTELS_5STAR = [
    {"name": "Atlantida Boutique Hotel", "website": "atlantida-rogaska.si", "stars": "5"},
    {"name": "Grand Hotel Bernardin", "website": "hoteli-bernardin.si", "stars": "5"},
    {"name": "Grand Hotel Toplice", "website": "sava-hotels-resorts.com", "stars": "5"},
    {"name": "Grand Plaza Hotel & Congress Center", "website": "grandplazahotel.si", "stars": "5"},
    {"name": "Hotel Grad Otocec", "website": "grad-otocec.com", "stars": "5"},
    {"name": "Hotel Livada Prestige", "website": "sava-hotels-resorts.com", "stars": "5"},
    {"name": "Hotel Slovenija", "website": "lifeclass.net", "stars": "5"},
    {"name": "Hotel Vivat", "website": "vivat.si", "stars": "5"},
    {"name": "InterContinental Ljubljana", "website": "ljubljana.intercontinental.com", "stars": "5"},
    {"name": "Palace Portorož", "website": "anantara.com", "stars": "5"},
    {"name": "Remisens Hotel Metropol", "website": "remisens.com", "stars": "5"},
    {"name": "Vila Planinka", "website": "vilaplaninka.com", "stars": "5"},
]

def check_website(domain):
    """Check if website exists and is reachable."""
    try:
        result = subprocess.run(
            ["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}", f"https://{domain}", "--max-time", "10"],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout.strip()
    except:
        return "error"

def check_ai_visibility(domain):
    """Check basic AI visibility indicators."""
    checks = {
        "has_robots": False,
        "has_llms_txt": False,
        "has_schema": False,
        "has_meta_desc": False,
        "response_code": None,
    }
    
    try:
        # Check robots.txt
        result = subprocess.run(
            ["curl", "-s", f"https://{domain}/robots.txt", "--max-time", "10"],
            capture_output=True, text=True, timeout=15
        )
        if "llms.txt" in result.stdout.lower() or "llm" in result.stdout.lower():
            checks["has_llms_txt"] = True
        if result.stdout.strip():
            checks["has_robots"] = True
    except:
        pass
    
    try:
        # Check llms.txt directly
        result = subprocess.run(
            ["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}", f"https://{domain}/llms.txt", "--max-time", "10"],
            capture_output=True, text=True, timeout=15
        )
        if result.stdout.strip() == "200":
            checks["has_llms_txt"] = True
    except:
        pass
    
    try:
        # Check homepage for schema/meta
        result = subprocess.run(
            ["curl", "-s", f"https://{domain}", "--max-time", "15"],
            capture_output=True, text=True, timeout=20
        )
        html = result.stdout
        if "application/ld+json" in html:
            checks["has_schema"] = True
        if '<meta name="description"' in html:
            checks["has_meta_desc"] = True
    except:
        pass
    
    return checks

def calculate_score(checks):
    """Calculate AI visibility score (A-F)."""
    score = 0
    if checks["has_robots"]: score += 1
    if checks["has_llms_txt"]: score += 3
    if checks["has_schema"]: score += 3
    if checks["has_meta_desc"]: score += 1
    
    if score >= 7: return "A"
    if score >= 5: return "B"
    if score >= 3: return "C"
    if score >= 1: return "D"
    return "F"

def main():
    results = []
    
    for i, hotel in enumerate(HOTELS_5STAR):
        print(f"\n{'='*60}")
        print(f"[{i+1}/12] {hotel['name']}")
        print(f"  Website: {hotel['website']}")
        
        # Check website
        status = check_website(hotel['website'])
        print(f"  HTTP Status: {status}")
        
        if status in ["200", "301", "302"]:
            # Check AI visibility
            print(f"  Checking AI visibility...")
            checks = check_ai_visibility(hotel['website'])
            score = calculate_score(checks)
            print(f"  AI Score: {score}")
            print(f"  Robots.txt: {'✅' if checks['has_robots'] else '❌'}")
            print(f"  LLMs.txt: {'✅' if checks['has_llms_txt'] else '❌'}")
            print(f"  Schema.org: {'✅' if checks['has_schema'] else '❌'}")
            print(f"  Meta desc: {'✅' if checks['has_meta_desc'] else '❌'}")
            
            results.append({
                "name": hotel["name"],
                "website": hotel["website"],
                "stars": hotel["stars"],
                "status": status,
                "score": score,
                "checks": checks,
            })
        else:
            print(f"  ⚠️ Website not reachable")
            results.append({
                "name": hotel["name"],
                "website": hotel["website"],
                "stars": hotel["stars"],
                "status": status,
                "score": "N/A",
                "checks": {},
            })
        
        # Save progress
        with open(f"{WORKSPACE}/outreach/hotel_5star_audit.json", "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Delay between hotels (5 seconds)
        if i < len(HOTELS_5STAR) - 1:
            print(f"  ⏳ Waiting 5s before next hotel...")
            time.sleep(5)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY — 5★ Hotels AI Visibility")
    print(f"{'='*60}")
    
    scores = {}
    for r in results:
        s = r["score"]
        scores[s] = scores.get(s, 0) + 1
    
    for grade in ["A", "B", "C", "D", "F", "N/A"]:
        if grade in scores:
            print(f"  {grade}: {scores[grade]} hotelov")
    
    print(f"\nPoslano v {WORKSPACE}/outreach/hotel_5star_audit.json")

if __name__ == "__main__":
    main()
