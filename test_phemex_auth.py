#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Phemex API authentication methods
"""

import ccxt
import requests
import json
from datetime import datetime, timezone

# Configuration
PHEMEX_CONFIG = {
    "PHEMEX_API_KEY": "2c213e33-e1bd-44ac-bf9a-44a4cd2e065a",
    "PHEMEX_SECRET": "4Q2dti8eGbr-QeADqpGA1n6hSs9K4Fb7PPNOeYUkQHhlNTg1NzdiMy0yNjkyLTRiNjEtYWU2ZS05OTA5YjljYzQ2MTc",
    "DISCORD_WEBHOOK": "",
}

def send_discord_alert(message, color=0x00FF00):
    """Send Discord notification"""
    try:
        embed = {
            "title": "🔐 PHEMEX AUTH TEST",
            "description": message,
            "color": color,
            "footer": {"text": f"Auth Test • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        payload = {"embeds": [embed]}
        response = requests.post(PHEMEX_CONFIG["DISCORD_WEBHOOK"], json=payload, timeout=10)
        print(f"📤 Discord alert sent: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Discord alert failed: {e}")

def test_auth_method_1():
    """Test authentication method 1: Standard CCXT"""
    print("🔐 Testing authentication method 1...")
    
    try:
        exchange = ccxt.phemex({
            'apiKey': PHEMEX_CONFIG["PHEMEX_API_KEY"],
            'secret': PHEMEX_CONFIG["PHEMEX_SECRET"],
            'sandbox': True,
            'enableRateLimit': True,
        })
        
        balance = exchange.fetch_balance()
        print(f"✅ Method 1 successful: {balance}")
        return True
        
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
        return False

def test_auth_method_2():
    """Test authentication method 2: With options"""
    print("🔐 Testing authentication method 2...")
    
    try:
        exchange = ccxt.phemex({
            'apiKey': PHEMEX_CONFIG["PHEMEX_API_KEY"],
            'secret': PHEMEX_CONFIG["PHEMEX_SECRET"],
            'sandbox': True,
            'options': {
                'defaultType': 'spot',
                'test': True
            },
            'enableRateLimit': True,
        })
        
        balance = exchange.fetch_balance()
        print(f"✅ Method 2 successful: {balance}")
        return True
        
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
        return False

def test_auth_method_3():
    """Test authentication method 3: Swap type"""
    print("🔐 Testing authentication method 3...")
    
    try:
        exchange = ccxt.phemex({
            'apiKey': PHEMEX_CONFIG["PHEMEX_API_KEY"],
            'secret': PHEMEX_CONFIG["PHEMEX_SECRET"],
            'sandbox': True,
            'options': {
                'defaultType': 'swap',
                'test': True
            },
            'enableRateLimit': True,
        })
        
        balance = exchange.fetch_balance()
        print(f"✅ Method 3 successful: {balance}")
        return True
        
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")
        return False

def test_auth_method_4():
    """Test authentication method 4: No sandbox"""
    print("🔐 Testing authentication method 4...")
    
    try:
        exchange = ccxt.phemex({
            'apiKey': PHEMEX_CONFIG["PHEMEX_API_KEY"],
            'secret': PHEMEX_CONFIG["PHEMEX_SECRET"],
            'sandbox': False,
            'enableRateLimit': True,
        })
        
        balance = exchange.fetch_balance()
        print(f"✅ Method 4 successful: {balance}")
        return True
        
    except Exception as e:
        print(f"❌ Method 4 failed: {e}")
        return False

def test_direct_api_call():
    """Test direct API call to Phemex"""
    print("🔐 Testing direct API call...")
    
    try:
        # Test direct API call
        url = "https://api.phemex.com/v1/accounts/accountPositions"
        headers = {
            'x-phemex-access-token': PHEMEX_CONFIG["PHEMEX_API_KEY"],
            'x-phemex-request-signature': PHEMEX_CONFIG["PHEMEX_SECRET"],
            'x-phemex-request-timestamp': str(int(datetime.now().timestamp() * 1000)),
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        print(f"📊 Direct API response: {response.status_code}")
        print(f"📋 Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Direct API call successful!")
            return True
        else:
            print(f"❌ Direct API call failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Direct API call failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔐 PHEMEX AUTHENTICATION TEST")
    print("=" * 50)
    
    # Send startup notification
    send_discord_alert("**PHEMEX AUTH TEST STARTED**\nTesting different authentication methods...")
    
    methods = [
        ("Standard CCXT", test_auth_method_1),
        ("With Options", test_auth_method_2),
        ("Swap Type", test_auth_method_3),
        ("No Sandbox", test_auth_method_4),
        ("Direct API", test_direct_api_call)
    ]
    
    results = []
    for name, method in methods:
        print(f"\n--- {name} ---")
        success = method()
        results.append((name, success))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 AUTHENTICATION TEST RESULTS:")
    successful_methods = []
    for name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"   {name}: {status}")
        if success:
            successful_methods.append(name)
    
    # Send Discord notification
    if successful_methods:
        message = f"**PHEMEX AUTH TEST COMPLETED**\n"
        message += f"✅ **Working Methods:** {', '.join(successful_methods)}\n"
        message += f"📊 **Total:** {len(successful_methods)}/{len(methods)} methods working\n"
        message += f"🎯 **API Status:** Ready for trading!"
        send_discord_alert(message, 0x00FF00)
    else:
        message = f"**PHEMEX AUTH TEST FAILED**\n"
        message += f"❌ **All methods failed**\n"
        message += f"🔧 **Action needed:** Check API credentials and permissions\n"
        message += f"📞 **Support:** Contact Phemex support for API access"
        send_discord_alert(message, 0xFF0000)

if __name__ == "__main__":
    main()















