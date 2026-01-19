#!/usr/bin/env python3
"""
Simple SOL Long Order - Direct API Call
"""

import requests
import json
import time
from datetime import datetime, timezone
from hyperliquid_config import HYPERLIQUID_CONFIG, HYPERLIQUID_NOTIFICATION_CONFIG

def place_sol_long():
    """Place a simple SOL long order"""
    print("🚀 PLACING SIMPLE SOL LONG ORDER...")
    
    try:
        # Get current SOL price
        price_url = "https://api.hyperliquid.xyz/info"
        price_payload = {
            "type": "allMids"
        }
        
        response = requests.post(price_url, json=price_payload)
        if response.status_code != 200:
            print(f"❌ Failed to get price: {response.status_code}")
            return False
            
        all_mids = response.json()
        sol_price = float(all_mids.get('SOL', 0))
        
        if not sol_price:
            print("❌ Could not get SOL price")
            return False
            
        print(f"💰 SOL Current Price: ${sol_price:.4f}")
        
        # Calculate position size for $15
        position_size = round(15.0 / sol_price, 6)
        
        print(f"🎯 Order Details:")
        print(f"  Symbol: SOL")
        print(f"  Side: LONG")
        print(f"  Position Size: {position_size:.6f} SOL")
        print(f"  Position Value: $15.00")
        print(f"  Entry Price: ${sol_price:.4f}")
        
        # Place order using direct API
        order_url = "https://api.hyperliquid.xyz/exchange"
        
        # Create order payload
        order_payload = {
            "action": {
                "type": "order",
                "orders": [{
                    "a": 0,  # asset id for SOL
                    "b": True,  # is buy
                    "p": str(sol_price),  # price
                    "s": str(position_size),  # size
                    "r": False,  # reduce only
                    "t": {"limit": {"tif": "Ioc"}},  # order type
                    "c": None  # client order id
                }]
            },
            "nonce": int(time.time() * 1000),
            "signature": "dummy_signature"  # This would need proper signing
        }
        
        print("📝 Order payload created")
        print("⚠️  Note: This requires proper signature generation")
        print("   For now, let's try the working bot approach...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    place_sol_long()























































