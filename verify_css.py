#!/usr/bin/env python3
import paramiko
import os

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

# Find .hero block
import re
hero_match = re.search(r'\.hero\s*\{[^}]*\}', css, re.DOTALL)
if hero_match:
    log("Found .hero block:")
    print(hero_match.group(0))
else:
    log("No .hero block found")
    # Search for background-image anywhere
    if 'background-image' in css:
        lines = [line for line in css.split('\n') if 'background-image' in line]
        for line in lines:
            print(line)

# Check for dark theme rule
dark_match = re.search(r'\[data-theme="dark"\]\s*\.hero[^}]*\}', css, re.DOTALL)
if dark_match:
    log("Dark theme rule for hero:")
    print(dark_match.group(0))

sftp.close()
client.close()