#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Phemex API test
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
            "title": "🧪 PHEMEX API TEST",
            "description": message,
            "color": color,
            "footer": {"text": f"Test Bot • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        payload = {"embeds": [embed]}
        response = requests.post(PHEMEX_CONFIG["DISCORD_WEBHOOK"], json=payload, timeout=10)
        print(f"📤 Discord alert sent: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Discord alert failed: {e}")

def test_phemex_public():
    """Test Phemex public API (no authentication required)"""
    print("🔌 Testing Phemex public API...")
    
    try:
        # Initialize Phemex exchange without API keys
        exchange = ccxt.phemex({
            'enableRateLimit': True,
        })
        
        # Load markets
        exchange.load_markets()
        print("✅ Phemex markets loaded")
        
        # Get BAT/USDT ticker
        ticker = exchange.fetch_ticker('BAT/USDT')
        print(f"✅ BAT/USDT Price: ${ticker['last']:.6f}")
        print(f"✅ 24h Volume: ${ticker['quoteVolume']:,.2f}")
        
        # Get order book
        orderbook = exchange.fetch_order_book('BAT/USDT')
        print(f"✅ Order book loaded: {len(orderbook['bids'])} bids, {len(orderbook['asks'])} asks")
        
        return exchange
        
    except Exception as e:
        print(f"❌ Phemex public API failed: {e}")
        return None

def test_phemex_private():
    """Test Phemex private API with authentication"""
    print("\n🔐 Testing Phemex private API...")
    
    try:
        # Initialize Phemex exchange with API keys
        exchange = ccxt.phemex({
            'apiKey': PHEMEX_CONFIG["PHEMEX_API_KEY"],
            'secret': PHEMEX_CONFIG["PHEMEX_SECRET"],
            'sandbox': True,  # Use sandbox mode
            'options': {
                'defaultType': 'swap',
                'test': True
            },
            'enableRateLimit': True,
        })
        
        # Load markets
        exchange.load_markets()
        print("✅ Phemex private exchange initialized")
        
        # Get account balance
        balance = exchange.fetch_balance()
        print(f"✅ Balance: {balance}")
        
        return exchange
        
    except Exception as e:
        print(f"❌ Phemex private API failed: {e}")
        return None

def test_bat_market_data(exchange):
    """Test BAT market data"""
    print("\n📊 Testing BAT market data...")
    
    try:
        # Get ticker
        ticker = exchange.fetch_ticker('BAT/USDT')
        print(f"📈 BAT Price: ${ticker['last']:.6f}")
        print(f"📊 24h High: ${ticker['high']:.6f}")
        print(f"📊 24h Low: ${ticker['low']:.6f}")
        print(f"📊 24h Volume: ${ticker['quoteVolume']:,.2f}")
        
        # Get recent trades
        trades = exchange.fetch_trades('BAT/USDT', limit=5)
        print(f"📋 Recent trades: {len(trades)}")
        for trade in trades[-3:]:  # Show last 3 trades
            print(f"   {trade['side']} {trade['amount']} @ ${trade['price']:.6f}")
        
        # Get OHLCV data
        ohlcv = exchange.fetch_ohlcv('BAT/USDT', '1m', limit=10)
        print(f"📊 OHLCV data: {len(ohlcv)} candles")
        if ohlcv:
            latest = ohlcv[-1]
            print(f"   Latest: O=${latest[1]:.6f} H=${latest[2]:.6f} L=${latest[3]:.6f} C=${latest[4]:.6f}")
        
        return True
        
    except Exception as e:
        print(f"❌ BAT market data failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 PHEMEX API TEST - BAT MARKET DATA")
    print("=" * 50)
    
    # Send startup notification
    send_discord_alert("**PHEMEX API TEST STARTED**\nTesting BAT market data and API connection...")
    
    # Test public API
    exchange = test_phemex_public()
    if not exchange:
        print("❌ Cannot proceed without Phemex connection")
        send_discord_alert("**PHEMEX API TEST FAILED**\nFailed to connect to Phemex public API.", 0xFF0000)
        return
    
    # Test BAT market data
    if test_bat_market_data(exchange):
        print("✅ BAT market data test completed successfully!")
        
        # Test private API
        private_exchange = test_phemex_private()
        if private_exchange:
            print("✅ Private API connection successful!")
            send_discord_alert("**PHEMEX API TEST COMPLETED**\n✅ Public API: Working\n✅ Private API: Working\n✅ BAT Market Data: Working\nAPI is ready for trading!", 0x00FF00)
        else:
            print("⚠️ Private API connection failed, but public API works")
            send_discord_alert("**PHEMEX API TEST PARTIAL**\n✅ Public API: Working\n❌ Private API: Failed\n⚠️ Check API credentials for trading", 0xFFA500)
    else:
        print("❌ BAT market data test failed")
        send_discord_alert("**PHEMEX API TEST FAILED**\nBAT market data test failed.\nCheck API connection.", 0xFF0000)

if __name__ == "__main__":
    main()















