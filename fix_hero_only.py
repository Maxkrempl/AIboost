#!/usr/bin/env python3
"""
Fix ONLY the hero background image as per Darko's instructions.
- Add/ensure .hero has background-image: url(/images/hero.jpg) (cover, centered)
- Remove any dark theme rules we added (since they use wrong selectors)
- Leave everything else exactly as is
"""

import os
import sys
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

def fix_css(css_content):
    """Apply minimal fixes: hero background only"""
    original = css_content
    
    # 1. Fix .hero block: ensure background-image and proper shorthand
    # Current pattern: .hero {    background-image: url(/images/hero.jpg);
    # We want: .hero { background-image: url(/images/hero.jpg); padding: 5rem 0; ...
    # Also ensure shorthand background with cover/center
    # The shorthand already exists: background: url("/images/hero.jpg") center/cover no-repeat;
    # We'll just normalize formatting and ensure consistency.
    
    # Find .hero block
    hero_pattern = re.compile(r'(\.hero\s*\{)([^}]*)(\})', re.DOTALL)
    match = hero_pattern.search(css_content)
    if not match:
        log("ERROR: No .hero block found!")
        return css_content
    
    hero_block = match.group(0)
    opening = match.group(1)
    inner = match.group(2)
    closing = match.group(3)
    
    # Check if background-image is present
    has_bg_image = 'background-image:' in inner
    has_shorthand_bg = 'background:' in inner and 'hero.jpg' in inner
    
    # If background-image missing, add it
    if not has_bg_image:
        # Add background-image as first property
        lines = inner.strip().split('\n')
        lines.insert(0, '    background-image: url(/images/hero.jpg);')
        inner = '\n'.join(lines)
        log("Added background-image to .hero")
    else:
        # Ensure it points to correct image
        # Replace any existing background-image with correct one
        bg_image_pattern = r'background-image\s*:[^;]*;'
        inner = re.sub(bg_image_pattern, '    background-image: url(/images/hero.jpg);', inner)
        log("Ensured background-image points to /images/hero.jpg")
    
    # Ensure shorthand background exists with correct values
    if not has_shorthand_bg:
        # Find position to insert (after background-image)
        lines = inner.strip().split('\n')
        # Insert after background-image line
        for i, line in enumerate(lines):
            if 'background-image:' in line:
                lines.insert(i+1, '    background: url("/images/hero.jpg") center/cover no-repeat;')
                break
        else:
            # If no background-image line, add at beginning
            lines.insert(0, '    background: url("/images/hero.jpg") center/cover no-repeat;')
        inner = '\n'.join(lines)
        log("Added shorthand background property")
    else:
        # Ensure shorthand uses correct image and values
        bg_pattern = r'background\s*:[^;]*;'
        # Replace with correct shorthand
        inner = re.sub(bg_pattern, '    background: url("/images/hero.jpg") center/cover no-repeat;', inner)
        log("Ensured shorthand background property is correct")
    
    # Remove any extra blank lines introduced by previous edits
    # The current CSS has an empty line after background-image; remove it
    inner = re.sub(r'\n\s*\n', '\n', inner)
    
    # Reconstruct hero block
    new_hero_block = opening + inner + closing
    css_content = css_content[:match.start()] + new_hero_block + css_content[match.end():]
    
    # 2. Remove dark theme rule we added (if present)
    # Look for the exact comment and rule we added
    dark_rule_pattern = r'/\* Ensure hero background visible in dark mode \*/\s*\n\[data-theme="dark"\] \.hero,\s*\n\.dark \.hero \{[^}]*\}'
    dark_match = re.search(dark_rule_pattern, css_content, re.DOTALL)
    if dark_match:
        css_content = css_content[:dark_match.start()] + css_content[dark_match.end():]
        log("Removed dark theme rule we added")
    
    # Also remove any other dark theme rule for .hero that's not using body.dark-mode
    # Keep only body.dark-mode .hero if it exists
    # For safety, we'll only remove rules that match our pattern
    
    # 3. Ensure no changes to project cards or other sections
    # (We're not touching them)
    
    if css_content != original:
        log("CSS has been modified")
    else:
        log("CSS already correct, no changes needed")
    
    return css_content

def main():
    log("Starting hero-only background fix")
    
    client = None
    try:
        client = ssh_connect()
        sftp = client.open_sftp()
        
        remote_css = "/home/hdwebd88/public_html/css/style.css"
        
        # Read current CSS
        css_content = read_remote_file(sftp, remote_css)
        log(f"Read CSS ({len(css_content)} chars)")
        
        # Apply fixes
        new_css = fix_css(css_content)
        
        # Write back if changed
        if new_css != css_content:
            log("Uploading updated CSS")
            write_remote_file(sftp, remote_css, new_css)
        else:
            log("No changes needed")
        
        # Verify by checking hero block
        log("\n--- Updated hero block preview ---")
        hero_match = re.search(r'\.hero\s*\{[^}]*\}', new_css, re.DOTALL)
        if hero_match:
            print(hero_match.group(0))
        
        log("\nTask completed successfully")
        
    except Exception as e:
        log(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if client:
            client.close()
            log("SSH connection closed")

if __name__ == "__main__":
    main()