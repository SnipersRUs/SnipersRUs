#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test BAT Long Trade using existing margin
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
            "title": "🧪 BAT LONG WITH MARGIN",
            "description": message,
            "color": color,
            "footer": {"text": f"Margin Test • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        payload = {"embeds": [embed]}
        response = requests.post(PHEMEX_CONFIG["DISCORD_WEBHOOK"], json=payload, timeout=10)
        print(f"📤 Discord alert sent: {response.status_code}")

    except Exception as e:
        print(f"❌ Discord alert failed: {e}")

def test_bat_long_with_margin():
    """Test placing a BAT long trade using cross margin"""
    print("🎯 Testing BAT Long Trade with Cross Margin")
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

        # Get current BAT price
        ticker = exchange.fetch_ticker('BAT/USDT')
        current_price = ticker['last']
        print(f"📊 Current BAT price: ${current_price:.6f}")

        # Get positions to see available margin
        positions = exchange.fetch_positions()
        print(f"📊 Found {len(positions)} positions")

        # Find BNB position
        bnb_position = None
        for pos in positions:
            if pos['symbol'] == 'BNB/USDT:USDT' and pos['contracts'] > 0:
                bnb_position = pos
                break

        if bnb_position:
            print(f"📈 BNB Position: {bnb_position['contracts']} contracts")
            print(f"💰 Collateral: ${bnb_position['collateral']:.2f}")
            print(f"💵 Notional: ${bnb_position['notional']:.2f}")
            print(f"⚡ Leverage: {bnb_position['leverage']}x")

        # Calculate position size using available margin (meet minimum requirements)
        position_size_usdt = 5.0  # $5 test trade (meets minimum)
        position_size = position_size_usdt / current_price

        # Set leverage
        leverage = 20

        print(f"📈 Position size: {position_size:.6f} BAT")
        print(f"⚡ Leverage: {leverage}x")
        print(f"💰 Trade value: ${position_size_usdt}")

        # Send Discord notification before trade
        message = f"**BAT LONG TEST WITH MARGIN**\n"
        message += f"**Symbol:** BAT/USDT\n"
        message += f"**Side:** LONG\n"
        message += f"**Entry:** ${current_price:.6f}\n"
        message += f"**Size:** {position_size:.6f} BAT\n"
        message += f"**Leverage:** {leverage}x\n"
        message += f"**Trade Value:** ${position_size_usdt}\n"
        message += f"**Using:** Cross margin from BNB position"

        send_discord_alert(message, 0x3498DB)  # Blue for test

        # Place long order with cross margin
        print("\n🚀 Placing BAT long order with cross margin...")
        order = exchange.create_order(
            symbol='BAT/USDT',
            type='market',
            side='buy',
            amount=position_size,
            params={
                'leverage': leverage,
                'marginMode': 'cross'  # Use cross margin
            }
        )

        print(f"✅ Order placed successfully!")
        print(f"📋 Order ID: {order['id']}")
        print(f"📊 Order Status: {order['status']}")
        print(f"💰 Filled Amount: {order.get('filled', 'N/A')}")
        print(f"💵 Average Price: {order.get('average', 'N/A')}")

        # Send success notification
        success_message = f"**BAT LONG TEST EXECUTED WITH MARGIN**\n"
        success_message += f"**Symbol:** BAT/USDT\n"
        success_message += f"**Side:** LONG\n"
        success_message += f"**Entry:** ${current_price:.6f}\n"
        success_message += f"**Size:** {position_size:.6f} BAT\n"
        success_message += f"**Leverage:** {leverage}x\n"
        success_message += f"**Trade Value:** ${position_size_usdt}\n"
        success_message += f"**Order ID:** {order['id']}\n"
        success_message += f"**Status:** {order['status']}\n"
        success_message += f"**Filled:** {order.get('filled', 'N/A')}\n"
        success_message += f"**Average Price:** {order.get('average', 'N/A')}\n"
        success_message += f"**✅ Cross margin working!**"

        send_discord_alert(success_message, 0x00FF00)  # Green for success

        return order

    except Exception as e:
        print(f"❌ BAT long trade failed: {e}")
        error_message = f"**BAT LONG TEST FAILED**\n"
        error_message += f"**Error:** {str(e)}\n"
        error_message += f"**Action:** Check margin requirements"
        send_discord_alert(error_message, 0xFF0000)  # Red for error
        return None

def main():
    """Main test function"""
    print("🧪 PHEMEX BAT LONG WITH MARGIN TEST")
    print("=" * 50)

    # Test BAT long trade with margin
    order = test_bat_long_with_margin()
    if order:
        print("✅ BAT long trade test completed successfully!")

        # Send completion notification
        completion_message = f"**BAT LONG TEST COMPLETED**\n"
        completion_message += f"✅ **Order Executed Successfully**\n"
        completion_message += f"📊 **Order ID:** {order['id']}\n"
        completion_message += f"🎯 **Status:** {order['status']}\n"
        completion_message += f"💰 **Cross margin is working!**\n"
        completion_message += f"🚀 **Ready for scalper bot!**"
        send_discord_alert(completion_message, 0x00FF00)
    else:
        print("❌ BAT long trade test failed")

if __name__ == "__main__":
    main()
