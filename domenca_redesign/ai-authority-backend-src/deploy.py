#!/usr/bin/env python3
"""
Deploy AI Authority Backend to hd-webdesign.si
Uploads all files via SFTP (paramiko)
"""

import paramiko
import os
import sys

SERVER = 'hd-webdesign.si'
USER = 'hdwebd88'
KEY = os.path.expanduser('~/.ssh/domenca_server_key')
REMOTE_BASE = '/home/hdwebd88'

# Files to upload: (local_path, remote_path)
UPLOADS = [
    # SQLite database directory
    ('data/db.php', f'{REMOTE_BASE}/data/db.php'),
    ('db-schema.sql', f'{REMOTE_BASE}/data/db-schema.sql'),
    
    # API endpoints
    ('api/audit.php', f'{REMOTE_BASE}/public_html/api/ai-authority/audit.php'),
    ('api/orders.php', f'{REMOTE_BASE}/public_html/api/ai-authority/orders.php'),
    ('api/webhook.php', f'{REMOTE_BASE}/public_html/api/ai-authority/webhook.php'),
    ('api/geo-audit.php', f'{REMOTE_BASE}/public_html/api/ai-authority/geo-audit.php'),
    
    # Admin dashboard
    ('admin/index.html', f'{REMOTE_BASE}/public_html/ai-authority/admin.html'),
]

def deploy():
    print(f"🚀 Deploying AI Authority Backend to {SERVER}...")
    
    # Connect
    key = paramiko.RSAKey.from_private_key_file(KEY)
    transport = paramiko.Transport((SERVER, 22))
    transport.connect(username=USER, pkey=key)
    sftp = paramiko.SFTPClient.from_transport(transport)
    
    # Create remote directories
    dirs_to_create = [
        f'{REMOTE_BASE}/data',
        f'{REMOTE_BASE}/public_html/api/ai-authority',
    ]
    for d in dirs_to_create:
        try:
            sftp.mkdir(d)
            print(f"  📁 Created {d}")
        except:
            pass  # already exists
    
    # Upload files
    local_dir = os.path.dirname(os.path.abspath(__file__))
    for local_rel, remote_path in UPLOADS:
        local_path = os.path.join(local_dir, local_rel)
        if not os.path.exists(local_path):
            print(f"  ⚠️  Missing: {local_rel}")
            continue
        
        print(f"  📤 {local_rel} → {remote_path}")
        sftp.put(local_path, remote_path)
    
    # Set permissions on db directory
    try:
        sftp.chmod(f'{REMOTE_BASE}/data', 0o755)
        sftp.chmod(f'{REMOTE_BASE}/data/db.php', 0o644)
    except:
        pass
    
    sftp.close()
    transport.close()
    
    print("\n✅ Deployment complete!")
    print(f"   Admin: https://hd-webdesign.si/ai-authority/admin.html")
    print(f"   Audit API: https://hd-webdesign.si/api/ai-authority/audit.php")
    print(f"   Orders API: https://hd-webdesign.si/api/ai-authority/orders.php")
    print(f"   Webhook: https://hd-webdesign.si/api/ai-authority/webhook.php")

if __name__ == '__main__':
    deploy()
