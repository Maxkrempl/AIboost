#!/usr/bin/env python3
"""
Lead Generator API — CGI Script
Handles POST requests and returns JSON results.
"""

import cgi
import json
import os
import sys
import subprocess

# Add the lead generator directory to path
sys.path.insert(0, '/home/hdwebd88/lead-gen/lead-generator')

# Set CORS headers
print("Content-Type: application/json")
print("Access-Control-Allow-Origin: *")
print("Access-Control-Allow-Methods: POST, OPTIONS")
print("Access-Control-Allow-Headers: Content-Type")
print()

# Handle preflight
if os.environ.get('REQUEST_METHOD') == 'OPTIONS':
    sys.exit(0)

# Only accept POST
if os.environ.get('REQUEST_METHOD') != 'POST':
    print(json.dumps({'error': 'Method not allowed'}))
    sys.exit(1)

# Get POST data
try:
    content_length = int(os.environ.get('CONTENT_LENGTH', 0))
    body = sys.stdin.read(content_length)
    data = json.loads(body)
except:
    print(json.dumps({'error': 'Invalid JSON'}))
    sys.exit(1)

# Validate input
business_type = data.get('type', 'restaurant')
location = data.get('location', '')
email = data.get('email', '')
limit = min(int(data.get('limit', 5)), 50)

if not location:
    print(json.dumps({'error': 'Location is required'}))
    sys.exit(1)

if not email or '@' not in email:
    print(json.dumps({'error': 'Valid email is required'}))
    sys.exit(1)

# Valid types
valid_types = ['restaurant', 'cafe', 'bar', 'hotel', 'fast_food', 'dentist', 'doctor', 'gym', 'salon', 'mechanic']
if business_type not in valid_types:
    print(json.dumps({'error': 'Invalid business type'}))
    sys.exit(1)

# Run the lead generator
script_path = '/home/hdwebd88/lead-gen/lead-generator/overpass_leads.py'
cmd = [
    'python3', script_path,
    '--type', business_type,
    '--location', location,
    '--limit', str(limit),
    '--email', email
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    output = result.stdout + result.stderr
except subprocess.TimeoutExpired:
    print(json.dumps({'error': 'Request timed out'}))
    sys.exit(1)
except Exception as e:
    print(json.dumps({'error': str(e)}))
    sys.exit(1)

# Parse output
stats = {'total': 0, 'with_email': 0, 'with_phone': 0, 'with_website': 0}

import re
if m := re.search(r'Total:\s+(\d+)', output):
    stats['total'] = int(m.group(1))
if m := re.search(r'With email:\s+(\d+)', output):
    stats['with_email'] = int(m.group(1))
if m := re.search(r'With phone:\s+(\d+)', output):
    stats['with_phone'] = int(m.group(1))
if m := re.search(r'With website:\s+(\d+)', output):
    stats['with_website'] = int(m.group(1))

email_sent = 'Email sent to' in output

print(json.dumps({
    'success': True,
    'stats': stats,
    'email_sent': email_sent,
    'message': f"Found {stats['total']} leads. Email sent to {email}." if email_sent else f"Found {stats['total']} leads.",
}))
