#!/usr/bin/env python3
import paramiko
import re

HOST = "hd-webdesign.si"
USER = "hdwebd88"
KEY_PATH = "/home/darko/Downloads/adboost-fixed/id_rsa"
PASSWORD = "gRwu.&#^gaB?HxA{"

def log(msg):
    print(f"[*] {msg}")

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

client = ssh_connect()
sftp = client.open_sftp()
remote_css = "/home/hdwebd88/public_html/css/style.css"
with sftp.open(remote_css, 'r') as f:
    css = f.read().decode('utf-8')

print(f"CSS length: {len(css)}")

# Check hero block
hero_match = re.search(r'\.hero\s*\{[^}]*\}', css, re.DOTALL)
if hero_match:
    print("\n=== HERO BLOCK ===")
    print(hero_match.group(0))
else:
    print("No hero block found")

# Check for dark theme rule
dark_pattern = r'/\* Ensure hero background visible in dark mode \*/\s*\n\[data-theme="dark"\] \.hero,\s*\n\.dark \.hero \{[^}]*\}'
dark_match = re.search(dark_pattern, css, re.DOTALL)
if dark_match:
    print("\n=== DARK RULE FOUND ===")
    print(dark_match.group(0))
else:
    print("\nDark rule not found with pattern")
    # Try simpler search
    if 'Ensure hero background visible' in css:
        print("But comment exists, maybe different formatting")
        # Find the comment position
        idx = css.find('Ensure hero background visible')
        snippet = css[idx:idx+300]
        print("Snippet:", snippet)

# Check for any other dark theme rules for .hero
all_hero_rules = re.findall(r'[^{]*(\.hero)[^{]*\{[^}]*\}', css, re.DOTALL)
if all_hero_rules:
    print(f"\nTotal .hero rules found: {len(all_hero_rules)}")

sftp.close()
client.close()