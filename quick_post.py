#!/usr/bin/env python3
"""
Quick Discord Post Script
Usage: python3 quick_post.py "Your message here" [--everyone]
"""

import sys
import requests
from datetime import datetime

# Your Discord webhook URL
DISCORD_WEBHOOK = ""

def quick_post(message, mention_everyone=False):
    """Quick post to Discord"""
    
    # Add @everyone if requested
    if mention_everyone:
        message = "@everyone " + message
    
    payload = {
        "content": message,
        "username": "Sniper Guru"
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK, json=payload)
        
        if response.status_code == 204:
            print("✅ Posted successfully!")
        else:
            print(f"❌ Failed to post. Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 quick_post.py \"Your message\" [--everyone]")
        print("Example: python3 quick_post.py \"BTC looking bullish!\" --everyone")
        sys.exit(1)
    
    message = sys.argv[1]
    mention_everyone = "--everyone" in sys.argv
    
    quick_post(message, mention_everyone)





