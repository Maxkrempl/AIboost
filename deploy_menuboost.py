#!/usr/bin/env python3
import requests
import json
import sys
import os
import time
import zipfile
import tempfile
import shutil

# Configuration
SITE_ID = "efc046de-e764-4b22-a973-181d8564acb8"
NETLIFY_TOKEN = "***REMOVED***"
SOURCE_DIR = "/home/darko/Downloads/menuboost"

def create_zip():
    """Create zip file from menuboost directory."""
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "menuboost-frontend.zip")
    
    # Copy all necessary files to temp directory
    files_to_copy = ["index.html", "_headers", "netlify.toml"]
    
    for file_name in files_to_copy:
        src_path = os.path.join(SOURCE_DIR, file_name)
        if os.path.exists(src_path):
            shutil.copy(src_path, os.path.join(temp_dir, file_name))
    
    # Create zip with all files
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_name in files_to_copy:
            temp_file_path = os.path.join(temp_dir, file_name)
            if os.path.exists(temp_file_path):
                zipf.write(temp_file_path, file_name)
    
    return zip_path, temp_dir

def deploy_site(zip_path):
    """Deploy zip to Netlify."""
    headers = {
        "Authorization": f"Bearer {NETLIFY_TOKEN}",
        "Content-Type": "application/zip"
    }
    
    # Create deploy
    deploy_url = f"https://api.netlify.com/api/v1/sites/{SITE_ID}/deploys"
    
    print(f"📤 Uploading {zip_path} to site {SITE_ID}...")
    
    try:
        with open(zip_path, "rb") as f:
            response = requests.post(deploy_url, headers=headers, data=f)
        
        if response.status_code == 200:
            deploy_data = response.json()
            deploy_id = deploy_data.get("id")
            deploy_url = deploy_data.get("deploy_url", "")
            print(f"✅ Deploy created: {deploy_id}")
            print(f"📦 Deploy URL: {deploy_url}")
            
            # Wait a moment for processing
            print("⏳ Waiting for processing...")
            time.sleep(2)
            
            # Publish the deploy
            publish_url = f"https://api.netlify.com/api/v1/sites/{SITE_ID}/deploys/{deploy_id}/restore"
            publish_resp = requests.post(publish_url, headers={"Authorization": f"Bearer {NETLIFY_TOKEN}"})
            
            if publish_resp.status_code == 200:
                print("✅ Deploy published successfully!")
                print(f"🌐 Live site: https://menuboostai.netlify.app")
                return True
            else:
                print(f"❌ Failed to publish: {publish_resp.status_code} {publish_resp.text}")
                return False
        else:
            print(f"❌ Failed to create deploy: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Starting MenuBoost deployment with Italian translation...")
    
    # Check source directory
    if not os.path.exists(SOURCE_DIR):
        print(f"❌ Source directory not found: {SOURCE_DIR}")
        return False
    
    index_file = os.path.join(SOURCE_DIR, "index.html")
    if not os.path.exists(index_file):
        print(f"❌ Index.html not found: {index_file}")
        return False
    
    # Create zip
    print("📦 Creating deployment package...")
    zip_path, temp_dir = create_zip()
    
    try:
        # Deploy
        success = deploy_site(zip_path)
        return success
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)