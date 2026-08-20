#!/usr/bin/env python3
import requests
import json

NETLIFY_TOKEN = "***REMOVED***"

def list_sites():
    headers = {
        "Authorization": f"Bearer {NETLIFY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    url = "https://api.netlify.com/api/v1/sites"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            sites = response.json()
            print("Netlify Sites:")
            for site in sites:
                print(f"\n  Name: {site.get('name')}")
                print(f"  ID: {site.get('id')}")
                print(f"  URL: {site.get('url')}")
                print(f"  Custom domain: {site.get('custom_domain')}")
                print(f"  Created: {site.get('created_at')}")
            return sites
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    list_sites()