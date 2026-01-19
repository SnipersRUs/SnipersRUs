#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wait for BNB position settlement and check balance
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
    "DISCORD_WEBHOOK": "https://discord.com/api/webhooks/1430429617696673852/UmIz28ug7uMqCyuVyOy7LeGXRj91sGLM9NuZicfzSZQOvYlGdfulww0WZzqRLos2I6Jz",
}

def send_discord_alert(message, color=0x00FF00):
    """Send Discord notification"""
    try:
        embed = {
            "title": "⏳ SETTLEMENT CHECK",
            "description": message,
            "color": color,
            "footer": {"text": f"Settlement • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        payload = {"embeds": [embed]}
        response = requests.post(PHEMEX_CONFIG["DISCORD_WEBHOOK"], json=payload, timeout=10)
        print(f"📤 Discord alert sent: {response.status_code}")

    except Exception as e:
        print(f"❌ Discord alert failed: {e}")

def wait_for_settlement():
    """Wait for BNB position settlement and check balance"""
    print("⏳ Waiting for BNB Position Settlement")
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

        # Check balance multiple times
        for i in range(6):  # Check 6 times over 30 seconds
            print(f"\n🔍 Check {i+1}/6...")

            # Get current balance
            balance = exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            bat_balance = balance.get('BAT', {}).get('free', 0)

            print(f"💰 USDT Balance: ${usdt_balance:.6f}")
            print(f"🦇 BAT Balance: {bat_balance:.6f} BAT")

            # Check positions
            positions = exchange.fetch_positions()
            active_positions = [pos for pos in positions if pos['contracts'] > 0]
            print(f"📊 Active positions: {len(active_positions)}")

            if active_positions:
                for pos in active_positions:
                    print(f"  📈 {pos['symbol']}: {pos['contracts']} contracts, ${pos['collateral']:.2f} collateral")

            # If we have USDT balance, try to trade
            if usdt_balance > 0:
                print(f"✅ USDT balance found: ${usdt_balance:.2f}")

                # Send notification
                message = f"**SETTLEMENT COMPLETE**\n"
                message += f"**USDT Balance:** ${usdt_balance:.2f}\n"
                message += f"**BAT Balance:** {bat_balance:.6f} BAT\n"
                message += f"**Active Positions:** {len(active_positions)}\n"
                message += f"**Status:** Ready for trading!"

                send_discord_alert(message, 0x00FF00)

                # Try BAT trade
                return try_bat_trade_now(exchange, usdt_balance)

            # Wait 5 seconds before next check
            if i < 5:
                print("⏳ Waiting 5 seconds...")
                time.sleep(5)

        # If no USDT balance found after all checks
        print("❌ No USDT balance found after settlement period")
        message = f"**SETTLEMENT INCOMPLETE**\n"
        message += f"**USDT Balance:** $0.00\n"
        message += f"**BAT Balance:** {bat_balance:.6f} BAT\n"
        message += f"**Status:** Need to deposit USDT or check account"

        send_discord_alert(message, 0xFF0000)
        return False

    except Exception as e:
        print(f"❌ Settlement check failed: {e}")
        error_message = f"**SETTLEMENT CHECK FAILED**\n"
        error_message += f"**Error:** {str(e)}"
        send_discord_alert(error_message, 0xFF0000)
        return False

def try_bat_trade_now(exchange, usdt_balance):
    """Try BAT trade with available USDT balance"""
    try:
        # Get current BAT price
        ticker = exchange.fetch_ticker('BAT/USDT')
        current_price = ticker['last']

        # Calculate position size
        position_size_usdt = min(usdt_balance * 0.8, 5.0)  # Use 80% of balance, max $5
        position_size = position_size_usdt / current_price

        print(f"📊 Current BAT price: ${current_price:.6f}")
        print(f"📈 Position size: {position_size:.6f} BAT")
        print(f"💰 Trade value: ${position_size_usdt:.2f}")

        # Send notification
        message = f"**BAT LONG TRADE ATTEMPT**\n"
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

        print(f"✅ BAT trade successful!")
        print(f"📋 Order ID: {order['id']}")
        print(f"📊 Order Status: {order['status']}")
        print(f"💰 Filled Amount: {order.get('filled', 'N/A')}")
        print(f"💵 Average Price: {order.get('average', 'N/A')}")

        success_message = f"**BAT LONG TRADE EXECUTED**\n"
        success_message += f"**Symbol:** BAT/USDT\n"
        success_message += f"**Entry:** ${current_price:.6f}\n"
        success_message += f"**Size:** {position_size:.6f} BAT\n"
        success_message += f"**Value:** ${position_size_usdt:.2f}\n"
        success_message += f"**Order ID:** {order['id']}\n"
        success_message += f"**Status:** {order['status']}\n"
        success_message += f"**Filled:** {order.get('filled', 'N/A')}\n"
        success_message += f"**Average Price:** {order.get('average', 'N/A')}\n"
        success_message += f"**✅ TRADE SUCCESSFUL!**"

        send_discord_alert(success_message, 0x00FF00)
        return True

    except Exception as e:
        print(f"❌ BAT trade failed: {e}")
        error_message = f"**BAT TRADE FAILED**\n"
        error_message += f"**Error:** {str(e)}\n"
        error_message += f"**Action:** Check balance and try again"
        send_discord_alert(error_message, 0xFF0000)
        return False

def main():
    """Main test function"""
    print("🧪 PHEMEX SETTLEMENT WAIT")
    print("=" * 50)

    # Wait for settlement and try trade
    success = wait_for_settlement()

    if success:
        print("✅ BAT trade completed successfully!")
    else:
        print("❌ BAT trade failed or no balance available")

if __name__ == "__main__":
    main()















