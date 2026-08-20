#!/usr/bin/env python3
"""
Hotel AI Visibility Audit
Finds websites and checks AI visibility indicators for Slovenian hotels.
"""
import json
import subprocess
import re
import time
import sys
import os

WORKSPACE = "/home/darko/.openclaw/workspace"

def load_hotels():
    """Parse hotels from raw text file."""
    hotels = []
    current_cat = ""
    with open(f"{WORKSPACE}/hotels_raw.txt", "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line in ["5 zvezdic", "4 zvezdic", "3 zvezdic", "2 zvezdic", "Neocenjeno"]:
                current_cat = line
                continue
            hotels.append({"name": line, "stars": current_cat, "website": ""})
    return hotels

def find_website_hotelname(name):
    """Try common website patterns for a hotel name."""
    # Clean name for URL
    clean = name.lower()
    clean = re.sub(r'[^a-z0-9\s-]', '', clean)
    clean = re.sub(r'\s+', '', clean)
    
    # Common patterns
    patterns = [
        f"https://www.{clean}.si",
        f"https://www.{clean}.com",
        f"https://{clean}.si",
        f"https://{clean}.com",
        f"https://www.{clean}.eu",
    ]
    
    for url in patterns:
        try:
            result = subprocess.run(
                ["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}", 
                 "--connect-timeout", "3", "--max-time", "5", url],
                capture_output=True, text=True, timeout=8
            )
            code = result.stdout.strip()
            if code in ["200", "301", "302"]:
                # Get final URL after redirects
                result2 = subprocess.run(
                    ["curl", "-sI", "-o", "/dev/null", "-w", "%{redirect_url}",
                     "--connect-timeout", "3", "--max-time", "5", url],
                    capture_output=True, text=True, timeout=8
                )
                final = result2.stdout.strip()
                if final and final.startswith("http"):
                    return final
                return url
        except:
            continue
    return ""

def check_ai_visibility(url):
    """Check a website for AI visibility indicators."""
    if not url:
        return {"score": 0, "checks": {}}
    
    checks = {
        "has_llm_txt": False,
        "has_schema_org": False,
        "has_meta_description": False,
        "has_og_tags": False,
        "has_structured_data": False,
        "has_robots_txt": False,
        "https": url.startswith("https"),
    }
    
    try:
        # Check llm.txt
        base = url.rstrip("/")
        result = subprocess.run(
            ["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}",
             "--connect-timeout", "3", "--max-time", "5", f"{base}/llm.txt"],
            capture_output=True, text=True, timeout=8
        )
        if result.stdout.strip() == "200":
            checks["has_llm_txt"] = True
        
        # Check robots.txt
        result = subprocess.run(
            ["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}",
             "--connect-timeout", "3", "--max-time", "5", f"{base}/robots.txt"],
            capture_output=True, text=True, timeout=8
        )
        if result.stdout.strip() == "200":
            checks["has_robots_txt"] = True
        
        # Get page content for meta/schema check
        result = subprocess.run(
            ["curl", "-sL", "--connect-timeout", "5", "--max-time", "10", 
             "-A", "Mozilla/5.0", base],
            capture_output=True, text=True, timeout=15
        )
        html = result.stdout[:50000]  # First 50KB
        
        if 'schema.org' in html or 'itemtype' in html:
            checks["has_schema_org"] = True
        if 'application/ld+json' in html:
            checks["has_structured_data"] = True
        if 'meta name="description"' in html or 'name="description"' in html:
            checks["has_meta_description"] = True
        if 'og:title' in html or 'og:description' in html:
            checks["has_og_tags"] = True
            
    except Exception as e:
        pass
    
    # Calculate score (0-100)
    score = 0
    if checks["has_llm_txt"]: score += 25
    if checks["has_schema_org"]: score += 20
    if checks["has_structured_data"]: score += 15
    if checks["has_meta_description"]: score += 15
    if checks["has_og_tags"]: score += 10
    if checks["has_robots_txt"]: score += 5
    if checks["https"]: score += 10
    
    return {"score": score, "checks": checks}

def generate_izkaznica(hotel, ai_result):
    """Generate AI visibility izkaznica for a hotel."""
    checks = ai_result["checks"]
    score = ai_result["score"]
    
    # Grade
    if score >= 80: grade = "A"
    elif score >= 60: grade = "B"
    elif score >= 40: grade = "C"
    elif score >= 20: grade = "D"
    else: grade = "F"
    
    # Recommendations
    recs = []
    if not checks["has_llm_txt"]:
        recs.append("Dodajte llm.txt za boljšo vidljivost v AI iskalnikih")
    if not checks["has_schema_org"] and not checks["has_structured_data"]:
        recs.append("Implementirajte Schema.org strukturirane podatke (Hotel, LocalBusiness)")
    if not checks["has_meta_description"]:
        recs.append("Dodajte meta description oznake na vse strani")
    if not checks["has_og_tags"]:
        recs.append("Dodajte Open Graph (OG) meta tag za boljše deljenje")
    if not checks["https"]:
        recs.append("Preklopite na HTTPS")
    
    return {
        "name": hotel["name"],
        "stars": hotel["stars"],
        "website": hotel["website"],
        "score": score,
        "grade": grade,
        "checks": checks,
        "recommendations": recs
    }

def main():
    hotels = load_hotels()
    print(f"Loaded {len(hotels)} hotels")
    
    # Load existing results if any
    results_file = f"{WORKSPACE}/hotel_audit_results.json"
    existing = {}
    if os.path.exists(results_file):
        with open(results_file, "r") as f:
            for r in json.load(f):
                existing[r["name"]] = r
    
    # Process hotels that don't have results yet
    processed = 0
    for i, hotel in enumerate(hotels):
        if hotel["name"] in existing:
            continue
        
        print(f"[{i+1}/{len(hotels)}] {hotel['name']}...", end=" ", flush=True)
        
        # Find website
        website = find_website_hotelname(hotel["name"])
        hotel["website"] = website
        
        if website:
            # Check AI visibility
            ai_result = check_ai_visibility(website)
            izkaznica = generate_izkaznica(hotel, ai_result)
            existing[hotel["name"]] = izkaznica
            print(f"✓ {website} → {izkaznica['grade']} ({izkaznica['score']}%)")
        else:
            existing[hotel["name"]] = {
                "name": hotel["name"],
                "stars": hotel["stars"],
                "website": "",
                "score": 0,
                "grade": "X",
                "checks": {},
                "recommendations": ["Ni najdene spletne strani"]
            }
            print("✗ ni strani")
        
        processed += 1
        
        # Save every 10 hotels
        if processed % 10 == 0:
            with open(results_file, "w") as f:
                json.dump(list(existing.values()), f, indent=2, ensure_ascii=False)
        
        time.sleep(0.5)  # Rate limiting
    
    # Final save
    with open(results_file, "w") as f:
        json.dump(list(existing.values()), f, indent=2, ensure_ascii=False)
    
    # Generate CSV index
    with open(f"{WORKSPACE}/hotel_ai_index.csv", "w") as f:
        f.write("Naziv,Kategorija,Spletna strani,Ocena AI vidljivosti,Gradacija\n")
        for name, data in existing.items():
            f.write(f'"{data["name"]}","{data["stars"]}","{data["website"]}",{data["score"]},{data["grade"]}\n')
    
    # Stats
    grades = {}
    for data in existing.values():
        g = data["grade"]
        grades[g] = grades.get(g, 0) + 1
    
    print(f"\n=== REZULTATI ===")
    print(f"Skupaj: {len(existing)}")
    for g in sorted(grades.keys()):
        print(f"  {g}: {grades[g]}")
    print(f"\nShranjeno: hotel_audit_results.json, hotel_ai_index.csv")

if __name__ == "__main__":
    main()
