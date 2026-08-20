import requests
import json
import sys
import os
import time

# Configuration
SITE_ID = "8f91e217-e319-4255-81b1-e00d3f1c93be"
NETLIFY_TOKEN = "***REMOVED***"
ZIP_PATH = "/home/darko/.openclaw/workspace/AdBoost/frontend.zip"

def deploy_site():
    headers = {
        "Authorization": f"Bearer {NETLIFY_TOKEN}",
        "Content-Type": "application/zip"
    }
    
    # Create deploy
    deploy_url = f"https://api.netlify.com/api/v1/sites/{SITE_ID}/deploys"
    
    print(f"Uploading {ZIP_PATH} to site {SITE_ID}...")
    
    try:
        with open(ZIP_PATH, "rb") as f:
            response = requests.post(deploy_url, headers=headers, data=f)
        
        if response.status_code == 200:
            deploy_data = response.json()
            deploy_id = deploy_data.get("id")
            deploy_url = deploy_data.get("deploy_url", "")
            print(f"✅ Deploy created: {deploy_id}")
            print(f"📦 Deploy URL: {deploy_url}")
            
            # Wait a moment for processing
            time.sleep(2)
            
            # Publish the deploy
            publish_url = f"https://api.netlify.com/api/v1/sites/{SITE_ID}/deploys/{deploy_id}/restore"
            publish_resp = requests.post(publish_url, headers={"Authorization": f"Bearer {NETLIFY_TOKEN}"})
            
            if publish_resp.status_code == 200:
                print("✅ Deploy published successfully!")
                print(f"🌐 Live site: https://adboost-mvp.netlify.app")
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

if __name__ == "__main__":
    success = deploy_site()
    sys.exit(0 if success else 1)