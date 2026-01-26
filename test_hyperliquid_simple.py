#!/usr/bin/env python3
"""
Simple Hyperliquid test
"""

import requests
from datetime import datetime, timezone
from hyperliquid_config import HYPERLIQUID_NOTIFICATION_CONFIG

def test_hyperliquid_connection():
    """Test basic Hyperliquid connection"""
    print("🚀 TESTING HYPERLIQUID CONNECTION...")
    
    try:
        # Test basic API endpoint
        response = requests.get("https://api.hyperliquid.xyz/info", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Hyperliquid API is accessible")
            return True
        else:
            print("❌ Hyperliquid API connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def send_discord_notification():
    """Send Discord notification about Hyperliquid test"""
    try:
        webhook_url = HYPERLIQUID_NOTIFICATION_CONFIG['discord_webhook']
        
        embed = {
            'title': '🔍 HYPERLIQUID CONNECTION TEST',
            'description': 'Testing basic API connectivity',
            'color': 0x0099ff,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'footer': {
                'text': 'Hyperliquid Test'
            },
            'fields': [
                {'name': '✅ API Accessible', 'value': 'Basic connection working', 'inline': True},
                {'name': '🔧 Next Steps', 'value': 'Need to implement proper SDK integration', 'inline': True},
                {'name': '📱 Your Credentials', 'value': 'Private key and wallet loaded', 'inline': True}
            ]
        }
        
        payload = {'embeds': [embed]}
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 204:
            print('✅ Discord notification sent!')
        else:
            print(f'❌ Discord notification failed: {response.status_code}')
    except Exception as e:
        print(f'❌ Error sending Discord notification: {e}')

if __name__ == "__main__":
    if test_hyperliquid_connection():
        send_discord_notification()























































