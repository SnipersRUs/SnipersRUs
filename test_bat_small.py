#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test BAT trade with small amount
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
            "title": "🧪 BAT SMALL TRADE",
            "description": message,
            "color": color,
            "footer": {"text": f"Small Trade • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        payload = {"embeds": [embed]}
        response = requests.post(PHEMEX_CONFIG["DISCORD_WEBHOOK"], json=payload, timeout=10)
        print(f"📤 Discord alert sent: {response.status_code}")

    except Exception as e:
        print(f"❌ Discord alert failed: {e}")

def test_bat_small_trade():
    """Test BAT trade with small amount"""
    print("🎯 Testing BAT Small Trade")
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

        # Get current balance
        balance = exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        print(f"💰 USDT Balance: ${usdt_balance:.6f}")

        # Get current BAT price
        ticker = exchange.fetch_ticker('BAT/USDT')
        current_price = ticker['last']
        print(f"📊 Current BAT price: ${current_price:.6f}")

        # Try very small trade first
        position_size_usdt = 1.0  # $1 test trade
        position_size = position_size_usdt / current_price

        print(f"📈 Position size: {position_size:.6f} BAT")
        print(f"💰 Trade value: ${position_size_usdt}")

        # Send notification
        message = f"**BAT SMALL TRADE TEST**\n"
        message += f"**Symbol:** BAT/USDT\n"
        message += f"**Entry:** ${current_price:.6f}\n"
        message += f"**Size:** {position_size:.6f} BAT\n"
        message += f"**Value:** ${position_size_usdt}\n"
        message += f"**Balance:** ${usdt_balance:.2f}"

        send_discord_alert(message, 0x3498DB)

        # Place order
        print("\n🚀 Placing BAT long order...")
        order = exchange.create_order(
            symbol='BAT/USDT',
            type='market',
            side='buy',
            amount=position_size
        )

        print(f"✅ Order placed successfully!")
        print(f"📋 Order ID: {order['id']}")
        print(f"📊 Order Status: {order['status']}")
        print(f"💰 Filled Amount: {order.get('filled', 'N/A')}")
        print(f"💵 Average Price: {order.get('average', 'N/A')}")

        # Send success notification
        success_message = f"**BAT SMALL TRADE EXECUTED**\n"
        success_message += f"**Symbol:** BAT/USDT\n"
        success_message += f"**Entry:** ${current_price:.6f}\n"
        success_message += f"**Size:** {position_size:.6f} BAT\n"
        success_message += f"**Value:** ${position_size_usdt}\n"
        success_message += f"**Order ID:** {order['id']}\n"
        success_message += f"**Status:** {order['status']}\n"
        success_message += f"**Filled:** {order.get('filled', 'N/A')}\n"
        success_message += f"**Average Price:** {order.get('average', 'N/A')}\n"
        success_message += f"**✅ TRADE SUCCESSFUL!**"

        send_discord_alert(success_message, 0x00FF00)
        return order

    except Exception as e:
        print(f"❌ BAT small trade failed: {e}")
        error_message = f"**BAT SMALL TRADE FAILED**\n"
        error_message += f"**Error:** {str(e)}\n"
        error_message += f"**Balance:** ${usdt_balance:.2f}\n"
        error_message += f"**Action:** Check account settings"
        send_discord_alert(error_message, 0xFF0000)
        return None

def main():
    """Main test function"""
    print("🧪 PHEMEX BAT SMALL TRADE TEST")
    print("=" * 50)

    # Test BAT small trade
    order = test_bat_small_trade()
    if order:
        print("✅ BAT small trade test completed successfully!")

        # Send completion notification
        completion_message = f"**BAT TRADE TEST COMPLETED**\n"
        completion_message += f"✅ **Order Executed Successfully**\n"
        completion_message += f"📊 **Order ID:** {order['id']}\n"
        completion_message += f"🎯 **Status:** {order['status']}\n"
        completion_message += f"💰 **Phemex API is working!**\n"
        completion_message += f"🚀 **Ready for scalper bot!**"
        send_discord_alert(completion_message, 0x00FF00)
    else:
        print("❌ BAT small trade test failed")

if __name__ == "__main__":
    main()















