#!/usr/bin/env python3
"""
Mindfulness Channel Discord Post Script
"""

import requests
import sys

# Mindfulness channel webhook
MINDFULNESS_WEBHOOK = "https://discord.com/api/webhooks/1417721618028957696/2V-0LHWY8-irDO8JYKZenfN9xtAB0gIMbLLZwEL6zQWVM4juGaLfaKnQCaxIzJ-YKeNk"

def post_mindfulness(message, mention_everyone=False):
    """Post to mindfulness channel"""
    
    if mention_everyone:
        message = "@everyone " + message
    
    payload = {
        "content": message,
        "username": "Sniper Guru"
    }
    
    try:
        response = requests.post(MINDFULNESS_WEBHOOK, json=payload)
        
        if response.status_code == 204:
            print("✅ Posted to mindfulness channel successfully!")
        else:
            print(f"❌ Failed to post. Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 mindfulness_post.py \"Your message\" [--everyone]")
        sys.exit(1)
    
    message = sys.argv[1]
    mention_everyone = "--everyone" in sys.argv
    
    post_mindfulness(message, mention_everyone)





