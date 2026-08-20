#!/usr/bin/env python3
"""
SSH check for hd-webdesign.si
"""

import paramiko
import os
import sys

def ssh_check():
    host = 'hd-webdesign.si'
    user = 'hdwebd88'
    key_path = '/home/darko/Downloads/adboost-fixed/id_rsa'
    passphrase = 'gRwu.&#^gaB?HxA{'
    
    if not os.path.exists(key_path):
        print(f"Key file not found: {key_path}")
        return []
    
    issues = []
    
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load private key
        key = paramiko.RSAKey.from_private_key_file(key_path, password=passphrase)
        
        print(f"Connecting to {host}...")
        ssh.connect(hostname=host, username=user, pkey=key, timeout=10)
        print("Connected.")
        
        # Check public_html directory
        sftp = ssh.open_sftp()
        try:
            files = sftp.listdir('public_html')
            print(f"Files in public_html: {files}")
        except Exception as e:
            issues.append(f"Cannot list public_html: {e}")
            # maybe directory doesn't exist
            files = []
        
        # Check essential files
        essential = ['index.html', 'blog.html', 'privacy.html']
        for fname in essential:
            try:
                sftp.stat(f'public_html/{fname}')
            except Exception:
                issues.append(f"Missing file: public_html/{fname}")
        
        # Check blog directory
        try:
            blog_files = sftp.listdir('public_html/blog')
            print(f"Blog files: {blog_files}")
            if not blog_files:
                issues.append("Blog directory is empty")
        except Exception:
            issues.append("Blog directory missing or inaccessible")
        
        # Check CSS and JS files
        css_js = ['style.css', 'script.js', 'main.css', 'main.js']
        for fname in css_js:
            try:
                sftp.stat(f'public_html/{fname}')
            except Exception:
                # Not necessarily an issue
                pass
        
        # Read index.html to check for CSS/JS links
        try:
            with sftp.open('public_html/index.html', 'r') as f:
                content = f.read().decode('utf-8', errors='ignore')
                if 'style.css' not in content and 'main.css' not in content:
                    issues.append("index.html may not link to a CSS file")
                if 'script.js' not in content and 'main.js' not in content:
                    issues.append("index.html may not link to a JS file")
        except Exception as e:
            issues.append(f"Cannot read index.html: {e}")
        
        sftp.close()
        ssh.close()
        
    except paramiko.AuthenticationException:
        issues.append("SSH authentication failed (wrong key/passphrase)")
    except Exception as e:
        issues.append(f"SSH connection error: {e}")
    
    return issues

if __name__ == '__main__':
    issues = ssh_check()
    if issues:
        print("\nIssues found:")
        for i in issues:
            print(f"- {i}")
    else:
        print("\nNo SSH issues found.")