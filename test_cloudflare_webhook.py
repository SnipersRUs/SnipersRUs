#!/usr/bin/env python3
"""
Test script for Cloudflare Discord Bot webhook
Tests various signal types to ensure they're processed correctly
"""

import requests
import json
import time

WEBHOOK_URL = "http://localhost:5000/webhook"

# Test signals
test_signals = [
    {
        "name": "BTC Master Long",
        "data": {
            "symbol": "BTCUSDT",
            "message": "🟢 MASTER LONG SIGNAL - HIGH ACCURACY",
            "price": "45000.50",
            "timeframe": "1h",
            "ticker": "BTCUSDT"
        }
    },
    {
        "name": "SOL Master Short",
        "data": {
            "symbol": "SOLUSDT",
            "message": "🔴 MASTER SHORT SIGNAL - HIGH ACCURACY",
            "price": "95.25",
            "timeframe": "4h",
            "ticker": "SOLUSDT"
        }
    },
    {
        "name": "ETH Bull Confirmation",
        "data": {
            "symbol": "ETHUSDT",
            "message": "🟢 BULL CONFIRMED",
            "price": "2500.75",
            "timeframe": "1D",
            "ticker": "ETHUSDT"
        }
    },
    {
        "name": "BTC Bearish Divergence",
        "data": {
            "symbol": "BTCUSDT",
            "message": "📉 BEARISH DIVERGENCE DETECTED",
            "price": "44500",
            "timeframe": "1h",
            "ticker": "BTCUSDT"
        }
    },
    {
        "name": "SOL Liquidity Flush Bull",
        "data": {
            "symbol": "SOLUSDT",
            "message": "⚠️ LIQUIDITY FLUSH BULL - SOLUSDT @ $96.50",
            "price": "96.50",
            "timeframe": "1h",
            "ticker": "SOLUSDT"
        }
    },
    {
        "name": "ETH VWAP Break (should be ignored - no direction)",
        "data": {
            "symbol": "ETHUSDT",
            "message": "Some random message without direction",
            "price": "2500",
            "timeframe": "1h",
            "ticker": "ETHUSDT"
        }
    },
    {
        "name": "DOGE Signal (should be ignored - not allowed)",
        "data": {
            "symbol": "DOGEUSDT",
            "message": "🟢 MASTER LONG SIGNAL",
            "price": "0.10",
            "timeframe": "1h",
            "ticker": "DOGEUSDT"
        }
    }
]

def test_webhook():
    """Test the webhook with various signals"""
    print("🧪 Testing Cloudflare Discord Bot Webhook\n")
    print(f"📍 Webhook URL: {WEBHOOK_URL}\n")

    # Test health endpoint first
    try:
        health_response = requests.get("http://localhost:5000/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Bot is running\n")
        else:
            print(f"⚠️ Bot health check returned {health_response.status_code}\n")
    except Exception as e:
        print(f"❌ Cannot connect to bot: {e}")
        print("💡 Make sure the bot is running: python3 cloudflare_discord_bot.py\n")
        return

    # Test each signal
    for i, test in enumerate(test_signals, 1):
        print(f"Test {i}/{len(test_signals)}: {test['name']}")
        try:
            response = requests.post(
                WEBHOOK_URL,
                json=test['data'],
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                status = result.get("status", "unknown")
                if status == "success":
                    print(f"  ✅ Success: {result.get('direction')} signal for {result.get('symbol')}")
                elif status == "ignored":
                    print(f"  ⚠️  Ignored: {result.get('reason')}")
                else:
                    print(f"  📊 Status: {status}")
            else:
                print(f"  ❌ Error: HTTP {response.status_code}")
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  ❌ Exception: {e}")

        # Small delay between tests
        time.sleep(1)
        print()

    print("✅ Testing complete!")
    print("💡 Check your Discord channel for the signals that were sent")

if __name__ == "__main__":
    test_webhook()

