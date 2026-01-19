#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check different Phemex account types and wallets
"""

import ccxt
import requests
import json
from datetime import datetime, timezone

# Configuration
PHEMEX_CONFIG = {
    "PHEMEX_API_KEY": "2c213e33-e1bd-44ac-bf9a-44a4cd2e065a",
    "PHEMEX_SECRET": "4Q2dti8eGbr-QeADqpGA1n6hSs9K4Fb7PPNOeYUkQHhlNTg1NzdiMy0yNjkyLTRiNjEtYWU2ZS05OTA5YjljYzQ2MTc",
    "DISCORD_WEBHOOK": "https://discord.com/api/webhooks/1430429617696673852/UmIz28ug7uMqCyuVyOy7LeGXRj91sGLM9NuZicfzSZQOvYlGdfulww0WZzqRLos2I6Jz",
}

def send_discord_alert(message, color=0x00FF00):
    """Send Discord notification"""
    try:
        embed = {
            "title": "🔍 ACCOUNT TYPE CHECK",
            "description": message,
            "color": color,
            "footer": {"text": f"Account Check • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        payload = {"embeds": [embed]}
        response = requests.post(PHEMEX_CONFIG["DISCORD_WEBHOOK"], json=payload, timeout=10)
        print(f"📤 Discord alert sent: {response.status_code}")

    except Exception as e:
        print(f"❌ Discord alert failed: {e}")

def check_account_types():
    """Check different account types and wallets"""
    print("🔍 Checking Phemex Account Types")
    print("=" * 50)

    try:
        # Initialize Phemex exchange
        exchange = ccxt.phemex({
            'apiKey': PHEMEX_CONFIG["PHEMEX_API_KEY"],
            'secret': PHEMEX_CONFIG["PHEMEX_SECRET"],
            'sandbox': False,  # Live trading
            'enableRateLimit': True,
        })

        print("✅ Phemex exchange initialized")

        # Check different account types
        print("\n🔍 Checking different account types...")

        # Try different options
        options = [
            {'sandbox': False},
            {'sandbox': False, 'options': {'defaultType': 'spot'}},
            {'sandbox': False, 'options': {'defaultType': 'future'}},
            {'sandbox': False, 'options': {'defaultType': 'margin'}},
        ]

        for i, option in enumerate(options):
            try:
                print(f"\n📊 Option {i+1}: {option}")

                # Create exchange with different options
                test_exchange = ccxt.phemex({
                    'apiKey': PHEMEX_CONFIG["PHEMEX_API_KEY"],
                    'secret': PHEMEX_CONFIG["PHEMEX_SECRET"],
                    'enableRateLimit': True,
                    **option
                })

                # Get balance
                balance = test_exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                print(f"  💰 USDT Balance: ${usdt_balance:.6f}")

                if usdt_balance > 0:
                    print(f"  ✅ Found USDT balance: ${usdt_balance:.2f}")

                    # Send notification
                    message = f"**ACCOUNT TYPE FOUND**\n"
                    message += f"**Option:** {option}\n"
                    message += f"**USDT Balance:** ${usdt_balance:.2f}\n"
                    message += f"**Status:** Ready for trading!"

                    send_discord_alert(message, 0x00FF00)
                    return test_exchange, usdt_balance

            except Exception as e:
                print(f"  ❌ Option {i+1} failed: {e}")

        # If no balance found, check if we need to transfer funds
        print("\n💡 No USDT balance found in any account type")
        print("🔍 This might mean:")
        print("  1. Funds are in a different wallet (spot vs futures)")
        print("  2. Need to transfer funds between wallets")
        print("  3. API keys don't have access to the right account")

        # Send notification
        message = f"**ACCOUNT TYPE CHECK COMPLETE**\n"
        message += f"**USDT Balance:** $0.00 in all account types\n"
        message += f"**Issue:** API may not have access to main account\n"
        message += f"**Solution:** Check API permissions or transfer funds"

        send_discord_alert(message, 0xFFA500)
        return None, 0

    except Exception as e:
        print(f"❌ Account type check failed: {e}")
        error_message = f"**ACCOUNT TYPE CHECK FAILED**\n"
        error_message += f"**Error:** {str(e)}"
        send_discord_alert(error_message, 0xFF0000)
        return None, 0

def main():
    """Main test function"""
    print("🧪 PHEMEX ACCOUNT TYPE CHECK")
    print("=" * 50)

    # Check account types
    exchange, balance = check_account_types()

    if exchange and balance > 0:
        print(f"✅ Found working account with ${balance:.2f} USDT balance!")
    else:
        print("❌ No working account found with USDT balance")

if __name__ == "__main__":
    main()















