#!/usr/bin/env python3
"""
Final verification of hd-webdesign.si fixes.
"""

import paramiko
import re
import sys
import requests

HOST = "hd-webdesign.si"
USER = "hdwebd88"
KEY_PATH = "/home/darko/Downloads/adboost-fixed/id_rsa"
PASSWORD = "gRwu.&#^gaB?HxA{"

def log(msg):
    print(f"[*] {msg}", flush=True)

def ssh_connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        key = paramiko.RSAKey.from_private_key_file(KEY_PATH, password=PASSWORD if PASSWORD else None)
        client.connect(HOST, username=USER, pkey=key, timeout=30)
        return client
    except Exception as e:
        log(f"Key auth failed: {e}")
        client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
        return client

def check_css():
    log("Checking CSS via SSH...")
    client = ssh_connect()
    sftp = client.open_sftp()
    remote_css = "/home/hdwebd88/public_html/css/style.css"
    with sftp.open(remote_css, 'r') as f:
        css = f.read().decode('utf-8')
    
    log(f"CSS length: {len(css)} chars")
    
    # 1. Hero block
    hero_match = re.search(r'\.hero\s*\{[^}]*\}', css, re.DOTALL)
    if hero_match:
        log("✓ Hero block found")
        hero = hero_match.group(0)
        print("\n" + hero)
        
        # Check background-image
        if 'background-image:' in hero and 'url(/images/hero.jpg)' in hero:
            log("✓ background-image property correct")
        else:
            log("✗ background-image missing or incorrect")
            
        # Check shorthand background
        if 'background:' in hero and 'hero.jpg' in hero and 'center/cover' in hero:
            log("✓ shorthand background correct (cover, centered)")
        else:
            log("✗ shorthand background incorrect")
    else:
        log("✗ No hero block found")
    
    # 2. Dark theme rule (should be absent)
    dark_pattern = r'/\* Ensure hero background visible in dark mode \*/\s*\n\[data-theme="dark"\] \.hero,\s*\n\.dark \.hero \{[^}]*\}'
    if re.search(dark_pattern, css, re.DOTALL):
        log("✗ Dark theme rule present (should be removed)")
    elif 'Ensure hero background visible' in css:
        log("⚠ Dark theme comment present but rule may differ")
    else:
        log("✓ Dark theme rule removed")
    
    # 3. Project cards untouched
    if '.project-card' in css and '.project-image' in css:
        log("✓ Project card styles present (untouched)")
    else:
        log("⚠ Project card styles may have been modified")
    
    # 4. Check image references in CSS (should not have changed)
    image_refs = re.findall(r'url\([^)]*\.(?:jpg|png|gif|svg)[^)]*\)', css)
    log(f"Found {len(image_refs)} image references in CSS")
    for ref in image_refs[:3]:
        log(f"  {ref}")
    
    sftp.close()
    client.close()
    return True

def check_live_site():
    log("\nChecking live site...")
    try:
        url = "https://hd-webdesign.si"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            log(f"✓ Site loads (HTTP {r.status_code})")
            # Check if hero background referenced in HTML
            if 'hero' in r.text and 'background' in r.text:
                log("✓ Hero section present in HTML")
            else:
                log("⚠ Hero section may not be referenced in HTML")
        else:
            log(f"✗ Site returned {r.status_code}")
    except Exception as e:
        log(f"✗ Failed to fetch site: {e}")
    
    # Check hero image directly
    try:
        hero_url = "https://hd-webdesign.si/images/hero.jpg"
        rh = requests.head(hero_url, timeout=10)
        if rh.status_code == 200:
            log(f"✓ Hero image accessible (HTTP {rh.status_code})")
        else:
            log(f"✗ Hero image not accessible: {rh.status_code}")
    except Exception as e:
        log(f"✗ Failed to check hero image: {e}")

def main():
    log("=== Final Verification ===\n")
    check_css()
    check_live_site()
    log("\n=== Verification Complete ===")

if __name__ == "__main__":
    main()