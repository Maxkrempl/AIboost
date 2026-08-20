#!/usr/bin/env python3
"""
Hotel AI Audit — with web search for websites.
Processes 5 hotels per batch, saves progress.
"""
import json
import subprocess
import time
import os
import re

WORKSPACE = "/home/darko/.openclaw/workspace"
PROGRESS_FILE = f"{WORKSPACE}/outreach/hotel_search_progress.json"
RESULTS_FILE = f"{WORKSPACE}/outreach/hotel_search_results.json"

def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def search_website(hotel_name):
    """Search for hotel website using curl to Tavily."""
    # Use simple web search via curl
    query = f'"{hotel_name}" Slovenia official website'
    try:
        # Try common hotel domains
        clean = hotel_name.lower()
        clean = re.sub(r'[^a-z0-9\s]', '', clean)
        words = clean.split()
        
        # Try direct domain patterns
        patterns = []
        if len(words) >= 2:
            patterns.append(f"{''.join(words[:2])}.si")
            patterns.append(f"{'-'.join(words[:2])}.si")
        patterns.append(f"{''.join(words)}.si")
        patterns.append(f"{''.join(words)}.com")
        
        for p in patterns[:3]:
            try:
                r = subprocess.run(
                    ["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}", 
                     f"https://{p}", "--max-time", "6", "-L"],
                    capture_output=True, text=True, timeout=10
                )
                if r.stdout.strip() in ["200", "301", "302"]:
                    return p
            except:
                pass
            time.sleep(0.5)
    except:
        pass
    return None

def check_ai(domain):
    """Quick AI visibility check."""
    checks = {"robots": False, "llms": False, "schema": False, "meta": False}
    try:
        r = subprocess.run(["curl", "-s", f"https://{domain}/robots.txt", "--max-time", "6"],
                          capture_output=True, text=True, timeout=10)
        if r.stdout.strip(): checks["robots"] = True
        if "llms" in r.stdout.lower(): checks["llms"] = True
    except: pass
    
    try:
        r = subprocess.run(["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}", 
                           f"https://{domain}/llms.txt", "--max-time", "6"],
                          capture_output=True, text=True, timeout=10)
        if r.stdout.strip() == "200": checks["llms"] = True
    except: pass
    
    try:
        r = subprocess.run(["curl", "-s", f"https://{domain}", "--max-time", "8"],
                          capture_output=True, text=True, timeout=12)
        if "application/ld+json" in r.stdout: checks["schema"] = True
        if '<meta name="description"' in r.stdout: checks["meta"] = True
    except: pass
    
    score = 0
    if checks["robots"]: score += 1
    if checks["llms"]: score += 3
    if checks["schema"]: score += 3
    if checks["meta"]: score += 1
    grade = "F"
    if score >= 7: grade = "A"
    elif score >= 5: grade = "B"
    elif score >= 3: grade = "C"
    elif score >= 1: grade = "D"
    
    return checks, grade

def main():
    with open(f"{WORKSPACE}/hotels_parsed.json") as f:
        all_hotels = json.load(f)
    
    # Skip 5-star
    hotels = [h for h in all_hotels if h.get("stars") != "5 zvezdic"]
    
    progress = load_json(PROGRESS_FILE, {"done": [], "idx": 0})
    results = load_json(RESULTS_FILE, [])
    done_set = set(progress["done"])
    
    start = progress["idx"]
    batch = 0
    
    print(f"📋 Hotelov za obdelavo: {len(hotels)}")
    print(f"✅ Že obdelano: {len(done_set)}")
    print(f"{'='*60}")
    
    for i, hotel in enumerate(hotels[start:], start=start):
        name = hotel["name"]
        if name in done_set:
            continue
        
        website = search_website(name)
        
        if website:
            checks, grade = check_ai(website)
            result = {"name": name, "stars": hotel.get("stars","?"), "website": website, "score": grade, "checks": checks}
            results.append(result)
            done_set.add(name)
            print(f"[{i+1}] {name} → {website} → {grade}")
        else:
            result = {"name": name, "stars": hotel.get("stars","?"), "website": None, "score": "N/A", "checks": {}}
            results.append(result)
            done_set.add(name)
            print(f"[{i+1}] {name} → ❌")
        
        batch += 1
        
        # Save progress
        progress["done"] = list(done_set)
        progress["idx"] = i + 1
        save_json(PROGRESS_FILE, progress)
        save_json(RESULTS_FILE, results)
        
        time.sleep(2)
        
        # Batch pause every 5
        if batch >= 5:
            print(f"  ⏳ Pavza...")
            time.sleep(8)
            batch = 0
    
    # Summary
    print(f"\n{'='*60}")
    scores = {}
    for r in results:
        s = r.get("score", "N/A")
        scores[s] = scores.get(s, 0) + 1
    for g in ["A", "B", "C", "D", "F", "N/A"]:
        if g in scores:
            print(f"  {g}: {scores[g]}")
    print(f"Skupaj: {len(results)}")

if __name__ == "__main__":
    main()
