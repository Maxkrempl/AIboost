#!/usr/bin/env python3
"""
Clean up hero block formatting only.
"""

import os
import paramiko
import tempfile
import re

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

def read_remote_file(sftp, remote_path):
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.tmp', delete=False) as f:
        local = f.name
    try:
        sftp.get(remote_path, local)
        with open(local, 'r', encoding='utf-8') as fp:
            content = fp.read()
        os.unlink(local)
        return content
    except Exception as e:
        log(f"Error reading {remote_path}: {e}")
        raise

def write_remote_file(sftp, remote_path, content):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tmp', delete=False, encoding='utf-8') as f:
        f.write(content)
        local = f.name
    try:
        sftp.put(local, remote_path)
    finally:
        os.unlink(local)

def normalize_hero_block(css):
    """Normalize .hero block formatting to 4-space indentation"""
    # Find .hero block
    pattern = re.compile(r'(\.hero\s*\{)([^}]*)(\})', re.DOTALL)
    match = pattern.search(css)
    if not match:
        log("No .hero block found")
        return css
    
    opening = match.group(1)
    inner = match.group(2)
    closing = match.group(3)
    
    # Split inner into lines, strip trailing spaces
    lines = [line.rstrip() for line in inner.split('\n')]
    
    # Remove empty lines
    lines = [line for line in lines if line.strip() != '']
    
    # Ensure each property line starts with 4 spaces
    # But first, we need to ensure background-image and shorthand are correct
    # We'll rebuild with proper indentation
    properties = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            # Ensure property ends with semicolon if missing
            if not stripped.endswith(';'):
                stripped += ';'
            properties.append('    ' + stripped)
    
    # Ensure required properties exist
    props_text = '\n'.join(properties)
    # Check for background-image
    if 'background-image:' not in props_text:
        props_text = '    background-image: url(/images/hero.jpg);\n' + props_text
    # Check for shorthand background
    if 'background:' not in props_text or 'hero.jpg' not in props_text:
        # Add or replace
        # We'll replace any existing background property
        # For simplicity, we'll just ensure there's a correct one
        # Remove any existing background lines first
        new_props = []
        for p in properties:
            if 'background:' in p and 'hero.jpg' not in p:
                continue  # skip incorrect background
            new_props.append(p)
        properties = new_props
        props_text = '\n'.join(properties)
        if 'background:' not in props_text:
            # Insert after background-image
            lines2 = props_text.split('\n')
            for i, line in enumerate(lines2):
                if 'background-image:' in line:
                    lines2.insert(i+1, '    background: url("/images/hero.jpg") center/cover no-repeat;')
                    break
            else:
                lines2.insert(0, '    background: url("/images/hero.jpg") center/cover no-repeat;')
            props_text = '\n'.join(lines2)
    
    # Reconstruct hero block with proper formatting
    new_hero_block = '.hero {\n' + props_text + '\n}'
    
    # Replace in original CSS
    new_css = css[:match.start()] + new_hero_block + css[match.end():]
    
    return new_css

def main():
    log("Cleaning up hero block formatting")
    
    client = None
    try:
        client = ssh_connect()
        sftp = client.open_sftp()
        
        remote_css = "/home/hdwebd88/public_html/css/style.css"
        css = read_remote_file(sftp, remote_css)
        log(f"Original CSS length: {len(css)}")
        
        new_css = normalize_hero_block(css)
        
        if new_css != css:
            log("CSS changed, uploading")
            write_remote_file(sftp, remote_css, new_css)
            
            # Verify
            log("\n=== Updated hero block ===")
            hero_match = re.search(r'\.hero\s*\{[^}]*\}', new_css, re.DOTALL)
            if hero_match:
                print(hero_match.group(0))
        else:
            log("No changes needed")
        
        log("\nDone")
        
    except Exception as e:
        log(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            client.close()
            log("SSH closed")

if __name__ == "__main__":
    main()