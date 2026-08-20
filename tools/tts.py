#!/usr/bin/env python3
"""
Text-to-Speech using Xiaomi MiMo TTS model.
Outputs WAV audio to speakers via PulseAudio.

Usage:
  python3 tts.py "Hello Darko"
  python3 tts.py --file output.wav "Save this to file"
  echo "Text" | python3 tts.py --stdin
"""

import sys
import json
import base64
import subprocess
import tempfile
import os
import argparse

API_URL = "https://token-plan-ams.xiaomimimo.com/v1/chat/completions"
API_KEY = "tp-eidnr0nccr8a4aoe5l398sarjax77jfva5zmrk3yyvk951d7"
MODEL = "mimo-v2.5-tts"

def generate_speech(text):
    """Generate speech from text using MiMo TTS."""
    import urllib.request
    
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "user", "content": text},
            {"role": "assistant", "content": ""}
        ]
    }).encode()
    
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
    )
    
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    
    audio_b64 = data['choices'][0]['message']['audio']['data']
    return base64.b64decode(audio_b64)

def play_audio(audio_bytes):
    """Play audio through PulseAudio."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name
    
    try:
        subprocess.run(['paplay', tmp_path], check=True)
    finally:
        os.unlink(tmp_path)

def main():
    parser = argparse.ArgumentParser(description='Max TTS - Speak through speakers')
    parser.add_argument('text', nargs='?', help='Text to speak')
    parser.add_argument('--file', '-f', help='Save to WAV file instead of playing')
    parser.add_argument('--stdin', action='store_true', help='Read text from stdin')
    parser.add_argument('--play', '-p', action='store_true', default=True, help='Play through speakers (default)')
    parser.add_argument('--no-play', action='store_true', help='Don\'t play, just save')
    
    args = parser.parse_args()
    
    # Get text
    if args.stdin:
        text = sys.stdin.read().strip()
    elif args.text:
        text = args.text
    else:
        print("Usage: python3 tts.py \"Your text here\"")
        sys.exit(1)
    
    if not text:
        print("Error: No text provided")
        sys.exit(1)
    
    print(f"🎤 Generating speech ({len(text)} chars)...")
    audio = generate_speech(text)
    print(f"🔊 Audio: {len(audio)} bytes")
    
    if args.file:
        with open(args.file, 'wb') as f:
            f.write(audio)
        print(f"💾 Saved to {args.file}")
    
    if not args.no_play and not args.file:
        print("🔈 Playing...")
        play_audio(audio)
        print("✅ Done")

if __name__ == "__main__":
    main()
