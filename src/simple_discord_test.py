#!/usr/bin/env python3
"""
Simple Discord webhook test without SSL issues
"""
import requests
import json
from datetime import datetime, timezone

def test_discord_webhook():
    """Test Discord webhook with requests library"""
    webhook_url = ""
    
    print("🧪 Testing Discord webhook...")
    print(f"📡 Webhook URL: {webhook_url[:50]}...")
    
    # Test payload
    payload = {
        "embeds": [{
            "title": "🧪 Discord Webhook Test",
            "description": "**Enhanced MM Trading Bot** is working correctly!\n\n"
                         "✅ Webhook connection successful\n"
                         "✅ Bot is ready to send alerts\n"
                         "✅ All systems operational",
            "color": 0x00ff00,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": "Enhanced MM Trading Bot - Test"
            },
            "fields": [
                {
                    "name": "Status",
                    "value": "🟢 Online",
                    "inline": True
                },
                {
                    "name": "Version",
                    "value": "v1.0.0",
                    "inline": True
                }
            ]
        }]
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 204:
            print("✅ Discord webhook test successful!")
            print("🎉 You should see a test message in your Discord channel")
            return True
        else:
            print(f"❌ Discord webhook failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Discord webhook: {e}")
        return False

def test_trade_alert():
    """Test a trade alert"""
    webhook_url = ""
    
    print("\n📊 Testing trade alert...")
    
    payload = {
        "embeds": [{
            "title": "🟢 TRADE EXECUTED - BTC/USDT",
            "description": "**Direction**: LONG\n"
                         "**Entry Price**: $45,000.00\n"
                         "**Stop Loss**: $44,000.00\n"
                         "**Take Profits**: $46,000.00 | $47,000.00 | $48,000.00\n"
                         "**Risk/Reward**: 2.0\n"
                         "**Position Size**: $1,000.00\n"
                         "**Leverage**: 10x\n"
                         "**MM Confidence**: 75%\n"
                         "**Setup Reason**: Iceberg orders detected with H1 bias alignment",
            "color": 0x00ff00,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": "Enhanced MM Trading Bot"
            },
            "fields": [
                {
                    "name": "MM Patterns",
                    "value": "🧊 Iceberg | 🎭 Spoofing",
                    "inline": True
                },
                {
                    "name": "Volume Analysis",
                    "value": "SPIKE",
                    "inline": True
                }
            ]
        }]
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 204:
            print("✅ Trade alert sent successfully!")
            return True
        else:
            print(f"❌ Trade alert failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending trade alert: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("SIMPLE DISCORD WEBHOOK TEST")
    print("=" * 60)
    
    # Test basic webhook
    success1 = test_discord_webhook()
    
    # Test trade alert
    success2 = test_trade_alert()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Discord integration is working perfectly")
        print("✅ You can now run the main bot")
        print("\n🚀 Next steps:")
        print("1. Open 'mm-trading-bot.code-workspace' in Cursor")
        print("2. Press F5 → Select 'Run MM Trading Bot'")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check your Discord webhook URL")
    print("=" * 60)

if __name__ == "__main__":
    main()
