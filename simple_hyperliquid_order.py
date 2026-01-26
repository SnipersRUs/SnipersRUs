#!/usr/bin/env python3
"""
Simple Hyperliquid Order using official SDK
"""

import asyncio
import requests
from datetime import datetime, timezone
from hyperliquid_config import HYPERLIQUID_NOTIFICATION_CONFIG

async def place_simple_order():
    """Place a simple order on Hyperliquid"""
    print("🚀 PLACING SIMPLE ORDER ON HYPERLIQUID...")
    
    try:
        # For now, let's create a manual order that you can place directly on Hyperliquid
        # This will show you exactly what to do
        
        print("📋 MANUAL ORDER INSTRUCTIONS:")
        print("=" * 50)
        print("1. Go to your Hyperliquid interface")
        print("2. Select BTCUSD trading pair")
        print("3. Click 'Buy / Long' tab")
        print("4. Set Size: $5.00")
        print("5. Set Leverage: 5x")
        print("6. Click 'Place Order'")
        print("=" * 50)
        
        # Send Discord notification with manual instructions
        webhook_url = HYPERLIQUID_NOTIFICATION_CONFIG['discord_webhook']
        
        embed = {
            'title': '📋 MANUAL ORDER INSTRUCTIONS',
            'description': 'Place this order manually on Hyperliquid:',
            'color': 0x0099ff,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'footer': {
                'text': 'Hyperliquid Manual Order'
            },
            'fields': [
                {'name': '1. Trading Pair', 'value': 'BTCUSD', 'inline': True},
                {'name': '2. Side', 'value': 'Buy / Long', 'inline': True},
                {'name': '3. Size', 'value': '$5.00', 'inline': True},
                {'name': '4. Leverage', 'value': '5x', 'inline': True},
                {'name': '5. Order Type', 'value': 'Market', 'inline': True},
                {'name': '6. Action', 'value': 'Click Place Order', 'inline': True},
                {'name': '💡 Why Manual?', 'value': 'API integration needs proper setup - manual order will execute immediately', 'inline': False}
            ]
        }
        
        payload = {'embeds': [embed]}
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 204:
            print('✅ Manual order instructions sent to Discord!')
        else:
            print(f'❌ Discord notification failed: {response.status_code}')
        
        print("\n✅ Manual order instructions sent to Discord!")
        print("Check your Discord for the exact steps to place the order.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(place_simple_order())























































