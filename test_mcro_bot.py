#!/usr/bin/env python3
"""
MCRO Bot Test Script
Test the Discord webhook integration and basic functionality
"""

import sys
import os
import requests
import config

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_discord_webhook():
    """Test the Discord webhook connection"""
    print("🧪 Testing Discord webhook...")
    
    if not config.DISCORD_WEBHOOK:
        print("❌ No Discord webhook configured")
        return False
    
    try:
        test_message = {
            "content": "🤖 **MCRO Bot Test**\n"
                      "Discord webhook connection successful!\n"
                      "Bot is ready to scan macro coins."
        }
        
        response = requests.post(config.DISCORD_WEBHOOK, json=test_message, timeout=10)
        
        if response.status_code == 204:
            print("✅ Discord webhook test successful!")
            return True
        else:
            print(f"❌ Discord webhook test failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Discord webhook test error: {e}")
        return False

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import ccxt
        import numpy as np
        import pandas as pd
        import requests
        import pytz
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    print("🚀 MCRO Bot Test Suite")
    print("=" * 30)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed. Install dependencies:")
        print("pip install -r requirements.txt")
        return
    
    # Test Discord webhook
    if not test_discord_webhook():
        print("\n❌ Discord webhook test failed.")
        print("Check your webhook URL in config.py")
        return
    
    print("\n✅ All tests passed!")
    print("MCRO Bot is ready to run!")
    print("\nTo start the bot, run:")
    print("python3 run_mcro_bot.py")

if __name__ == "__main__":
    main()


















































