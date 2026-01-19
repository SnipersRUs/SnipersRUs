#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple BAT test using existing balance
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
            "title": "🧪 PHEMEX BALANCE TEST",
            "description": message,
            "color": color,
            "footer": {"text": f"Balance Test • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        payload = {"embeds": [embed]}
        response = requests.post(PHEMEX_CONFIG["DISCORD_WEBHOOK"], json=payload, timeout=10)
        print(f"📤 Discord alert sent: {response.status_code}")

    except Exception as e:
        print(f"❌ Discord alert failed: {e}")

def test_account_balance():
    """Test account balance and available funds"""
    print("💰 Testing Phemex Account Balance")
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

        # Get account balance
        balance = exchange.fetch_balance()
        print(f"📊 Account balance: {balance}")

        # Check available balances
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        bat_balance = balance.get('BAT', {}).get('free', 0)
        pt_balance = balance.get('PT', {}).get('free', 0)

        print(f"💰 USDT Balance: {usdt_balance}")
        print(f"🦇 BAT Balance: {bat_balance}")
        print(f"🎯 PT Balance: {pt_balance}")

        # Get BAT price
        ticker = exchange.fetch_ticker('BAT/USDT')
        bat_price = ticker['last']
        print(f"📈 BAT Price: ${bat_price:.6f}")

        # Calculate BAT value in USDT
        bat_value_usdt = bat_balance * bat_price
        print(f"💵 BAT Value: ${bat_value_usdt:.6f}")

        # Send Discord notification
        message = f"**PHEMEX ACCOUNT STATUS**\n"
        message += f"**USDT Balance:** ${usdt_balance:.6f}\n"
        message += f"**BAT Balance:** {bat_balance:.6f} BAT\n"
        message += f"**BAT Value:** ${bat_value_usdt:.6f}\n"
        message += f"**PT Balance:** {pt_balance:.6f} PT\n"
        message += f"**BAT Price:** ${bat_price:.6f}\n"
        message += f"**Total Value:** ${bat_value_usdt:.6f}"

        send_discord_alert(message, 0x3498DB)

        # Check if we can trade
        if usdt_balance > 0:
            print("✅ Sufficient USDT balance for trading")
            return True
        elif bat_balance > 0:
            print("⚠️ No USDT balance, but have BAT tokens")
            print("💡 Need to deposit USDT or convert BAT to USDT for trading")
            return False
        else:
            print("❌ No trading balance available")
            return False

    except Exception as e:
        print(f"❌ Balance check failed: {e}")
        error_message = f"**PHEMEX BALANCE CHECK FAILED**\n"
        error_message += f"**Error:** {str(e)}\n"
        error_message += f"**Action:** Check API credentials"
        send_discord_alert(error_message, 0xFF0000)
        return False

def main():
    """Main test function"""
    print("🧪 PHEMEX ACCOUNT BALANCE TEST")
    print("=" * 50)

    # Test account balance
    success = test_account_balance()

    if success:
        print("✅ Account balance test completed successfully!")
        completion_message = f"**PHEMEX ACCOUNT READY**\n"
        completion_message += f"✅ **Account Status:** Active\n"
        completion_message += f"💰 **Trading Balance:** Available\n"
        completion_message += f"🎯 **Ready for trading!**"
        send_discord_alert(completion_message, 0x00FF00)
    else:
        print("⚠️ Account needs funding for trading")
        funding_message = f"**PHEMEX ACCOUNT NEEDS FUNDING**\n"
        funding_message += f"⚠️ **USDT Balance:** Insufficient\n"
        funding_message += f"💡 **Action:** Deposit USDT to start trading\n"
        funding_message += f"📊 **Current:** Only have BAT/PT tokens"
        send_discord_alert(funding_message, 0xFFA500)

if __name__ == "__main__":
    main()















