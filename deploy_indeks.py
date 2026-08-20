#!/usr/bin/env python3
"""Deploy Indeks AI-vidljivosti to hd-webdesign.si"""
import paramiko
import os

KEY_PATH = os.path.expanduser('~/.ssh/domenca_server_key')
HOST = 'hd-webdesign.si'
USER = 'hdwebd88'
REMOTE_BASE = '/home/hdwebd88/public_html/indeks-ai-vidljivosti'
LOCAL_DIR = os.path.expanduser('~/.openclaw/workspace/domenca_site/indeks-ai-vidljivosti')

def deploy():
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH, password='***REMOVED***')
    transport = paramiko.Transport((HOST, 22))
    transport.connect(username=USER, pkey=key)
    sftp = paramiko.SFTPClient.from_transport(transport)
    
    # Create remote dir
    try:
        sftp.mkdir(REMOTE_BASE)
    except:
        pass
    
    # Upload files
    for filename in os.listdir(LOCAL_DIR):
        local_path = os.path.join(LOCAL_DIR, filename)
        remote_path = f"{REMOTE_BASE}/{filename}"
        sftp.put(local_path, remote_path)
        print(f"✅ Uploaded: {filename}")
    
    sftp.close()
    transport.close()
    print(f"\n🎉 Deployed to https://hd-webdesign.si/indeks-ai-vidljivosti/")

if __name__ == '__main__':
    deploy()
