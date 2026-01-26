#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test BAT trade using existing BAT tokens
"""

import ccxt
import requests
import json
import time
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
            "title": "🧪 BAT TRADE WITH TOKENS",
            "description": message,
            "color": color,
            "footer": {"text": f"Token Trade • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        payload = {"embeds": [embed]}
        response = requests.post(PHEMEX_CONFIG["DISCORD_WEBHOOK"], json=payload, timeout=10)
        print(f"📤 Discord alert sent: {response.status_code}")

    except Exception as e:
        print(f"❌ Discord alert failed: {e}")

def test_bat_trade_with_tokens():
    """Test BAT trade using existing BAT tokens"""
    print("🎯 Testing BAT Trade with Existing Tokens")
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

        # Wait a moment for balance to update
        print("⏳ Waiting for balance to update...")
        time.sleep(5)

        # Get current balance
        balance = exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        bat_balance = balance.get('BAT', {}).get('free', 0)

        print(f"💰 USDT Balance: ${usdt_balance:.6f}")
        print(f"🦇 BAT Balance: {bat_balance:.6f} BAT")

        # Get current BAT price
        ticker = exchange.fetch_ticker('BAT/USDT')
        current_price = ticker['last']
        print(f"📊 Current BAT price: ${current_price:.6f}")

        # Calculate BAT value
        bat_value_usdt = bat_balance * current_price
        print(f"💵 BAT Value: ${bat_value_usdt:.6f}")

        # Try different approaches
        if usdt_balance > 0:
            print("✅ USDT balance available, trying USDT trade...")
            return try_usdt_trade(exchange, usdt_balance, current_price)
        elif bat_balance > 0:
            print("✅ BAT tokens available, trying BAT trade...")
            return try_bat_trade(exchange, bat_balance, current_price)
        else:
            print("❌ No balance available for trading")
            return False

    except Exception as e:
        print(f"❌ BAT trade test failed: {e}")
        error_message = f"**BAT TRADE TEST FAILED**\n"
        error_message += f"**Error:** {str(e)}"
        send_discord_alert(error_message, 0xFF0000)
        return False

def try_usdt_trade(exchange, usdt_balance, current_price):
    """Try trading with USDT balance"""
    try:
        # Calculate position size
        position_size_usdt = min(usdt_balance * 0.8, 5.0)  # Use 80% of balance, max $5
        position_size = position_size_usdt / current_price

        print(f"📈 Position size: {position_size:.6f} BAT")
        print(f"💰 Trade value: ${position_size_usdt:.2f}")

        # Send notification
        message = f"**BAT LONG WITH USDT**\n"
        message += f"**Symbol:** BAT/USDT\n"
        message += f"**Entry:** ${current_price:.6f}\n"
        message += f"**Size:** {position_size:.6f} BAT\n"
        message += f"**Value:** ${position_size_usdt:.2f}\n"
        message += f"**Balance:** ${usdt_balance:.2f}"

        send_discord_alert(message, 0x3498DB)

        # Place order
        order = exchange.create_order(
            symbol='BAT/USDT',
            type='market',
            side='buy',
            amount=position_size
        )

        print(f"✅ USDT trade successful!")
        print(f"📋 Order ID: {order['id']}")

        success_message = f"**BAT LONG EXECUTED WITH USDT**\n"
        success_message += f"**Order ID:** {order['id']}\n"
        success_message += f"**Status:** {order['status']}\n"
        success_message += f"**✅ Trade successful!**"

        send_discord_alert(success_message, 0x00FF00)
        return True

    except Exception as e:
        print(f"❌ USDT trade failed: {e}")
        return False

def try_bat_trade(exchange, bat_balance, current_price):
    """Try trading with BAT tokens"""
    try:
        # Calculate position size (use 80% of BAT balance)
        position_size = bat_balance * 0.8

        print(f"📈 Position size: {position_size:.6f} BAT")
        print(f"💰 Trade value: ${position_size * current_price:.2f}")

        # Send notification
        message = f"**BAT TRADE WITH TOKENS**\n"
        message += f"**Symbol:** BAT/USDT\n"
        message += f"**Entry:** ${current_price:.6f}\n"
        message += f"**Size:** {position_size:.6f} BAT\n"
        message += f"**Value:** ${position_size * current_price:.2f}\n"
        message += f"**Balance:** {bat_balance:.6f} BAT"

        send_discord_alert(message, 0x3498DB)

        # Place order
        order = exchange.create_order(
            symbol='BAT/USDT',
            type='market',
            side='sell',  # Sell BAT for USDT
            amount=position_size
        )

        print(f"✅ BAT trade successful!")
        print(f"📋 Order ID: {order['id']}")

        success_message = f"**BAT TRADE EXECUTED**\n"
        success_message += f"**Order ID:** {order['id']}\n"
        success_message += f"**Status:** {order['status']}\n"
        success_message += f"**✅ Trade successful!**"

        send_discord_alert(success_message, 0x00FF00)
        return True

    except Exception as e:
        print(f"❌ BAT trade failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 PHEMEX BAT TRADE WITH TOKENS")
    print("=" * 50)

    # Test BAT trade with existing tokens
    success = test_bat_trade_with_tokens()

    if success:
        print("✅ BAT trade test completed successfully!")
    else:
        print("❌ BAT trade test failed")

if __name__ == "__main__":
    main()















