#!/usr/bin/env python3
"""
Batch Hotel AI Visibility Audit
Processes hotels in batches of 10 with delays.
Can resume from where it left off.
"""
import json
import subprocess
import time
import sys
import os
import re

WORKSPACE = "/home/darko/.openclaw/workspace"
PROGRESS_FILE = f"{WORKSPACE}/outreach/hotel_batch_progress.json"
RESULTS_FILE = f"{WORKSPACE}/outreach/hotel_batch_results.json"

BATCH_SIZE = 10
DELAY_BETWEEN = 3  # seconds between hotels
DELAY_BATCH = 10   # seconds between batches

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"processed": [], "last_index": 0}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return []

def save_results(results):
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def find_website_approx(name):
    """Try to guess website from hotel name."""
    # Clean name
    clean = name.lower()
    clean = re.sub(r'[^a-z0-9\s]', '', clean)
    clean = re.sub(r'\s+', '', clean)
    
    # Common patterns
    guesses = [
        f"{clean}.si",
        f"www.{clean}.si",
        f"{clean}.com",
    ]
    return guesses

def check_url(url):
    """Check if URL returns 200."""
    try:
        result = subprocess.run(
            ["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}", f"https://{url}", 
             "--max-time", "8", "-L"],
            capture_output=True, text=True, timeout=12
        )
        code = result.stdout.strip()
        return code in ["200", "301", "302"]
    except:
        return False

def check_ai_visibility(domain):
    """Check AI visibility indicators."""
    checks = {"robots": False, "llms": False, "schema": False, "meta": False}
    
    try:
        r = subprocess.run(["curl", "-s", f"https://{domain}/robots.txt", "--max-time", "8"],
                          capture_output=True, text=True, timeout=12)
        if r.stdout.strip():
            checks["robots"] = True
        if "llms" in r.stdout.lower():
            checks["llms"] = True
    except: pass
    
    try:
        r = subprocess.run(["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}", 
                           f"https://{domain}/llms.txt", "--max-time", "8"],
                          capture_output=True, text=True, timeout=12)
        if r.stdout.strip() == "200":
            checks["llms"] = True
    except: pass
    
    try:
        r = subprocess.run(["curl", "-s", f"https://{domain}", "--max-time", "10"],
                          capture_output=True, text=True, timeout=15)
        html = r.stdout
        if "application/ld+json" in html:
            checks["schema"] = True
        if '<meta name="description"' in html:
            checks["meta"] = True
    except: pass
    
    return checks

def calc_score(checks):
    s = 0
    if checks["robots"]: s += 1
    if checks["llms"]: s += 3
    if checks["schema"]: s += 3
    if checks["meta"]: s += 1
    if s >= 7: return "A"
    if s >= 5: return "B"
    if s >= 3: return "C"
    if s >= 1: return "D"
    return "F"

def main():
    # Load all hotels
    with open(f"{WORKSPACE}/hotels_parsed.json") as f:
        all_hotels = json.load(f)
    
    # Skip 5-star (already done)
    hotels = [h for h in all_hotels if h.get("stars") != "5 zvezdic"]
    
    progress = load_progress()
    results = load_results()
    processed = set(progress.get("processed", []))
    
    start_idx = progress.get("last_index", 0)
    
    print(f"📋 Skupaj hotelov: {len(hotels)} (brez 5★)")
    print(f"✅ Že obdelano: {len(processed)}")
    print(f"🔄 Nadaljujem od: {start_idx}")
    print(f"{'='*60}")
    
    batch_count = 0
    
    for i, hotel in enumerate(hotels[start_idx:], start=start_idx):
        name = hotel["name"]
        
        # Skip if already processed
        if name in processed:
            continue
        
        # Try to find website
        website_found = False
        guesses = find_website_approx(name)
        
        for guess in guesses[:2]:  # Try max 2 guesses
            if check_url(guess):
                # Found website, check AI visibility
                checks = check_ai_visibility(guess)
                score = calc_score(checks)
                
                result = {
                    "name": name,
                    "stars": hotel.get("stars", "?"),
                    "website": guess,
                    "score": score,
                    "checks": checks
                }
                results.append(result)
                processed.add(name)
                website_found = True
                
                print(f"[{i+1}] {name} → {guess} → {score}")
                break
            time.sleep(1)
        
        if not website_found:
            result = {
                "name": name,
                "stars": hotel.get("stars", "?"),
                "website": "Ni najden",
                "score": "N/A",
                "checks": {}
            }
            results.append(result)
            processed.add(name)
            print(f"[{i+1}] {name} → ❌ ni strani")
        
        batch_count += 1
        
        # Save progress
        progress["processed"] = list(processed)
        progress["last_index"] = i + 1
        save_progress(progress)
        save_results(results)
        
        # Delay
        time.sleep(DELAY_BETWEEN)
        
        # Batch pause
        if batch_count >= BATCH_SIZE:
            print(f"\n⏳ Pavza {DELAY_BATCH}s po {BATCH_SIZE} hotelih...\n")
            time.sleep(DELAY_BATCH)
            batch_count = 0
    
    # Final summary
    print(f"\n{'='*60}")
    print("📊 KONČNO POROČILO")
    print(f"{'='*60}")
    
    scores = {}
    for r in results:
        s = r.get("score", "N/A")
        scores[s] = scores.get(s, 0) + 1
    
    for g in ["A", "B", "C", "D", "F", "N/A"]:
        if g in scores:
            print(f"  {g}: {scores[g]} hotelov")
    
    print(f"\nRezultati: {RESULTS_FILE}")

if __name__ == "__main__":
    main()
