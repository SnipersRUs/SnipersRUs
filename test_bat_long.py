#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test BAT Long Trade on Phemex
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
            "title": "🧪 BAT LONG TEST",
            "description": message,
            "color": color,
            "footer": {"text": f"Test Trade • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        payload = {"embeds": [embed]}
        response = requests.post(PHEMEX_CONFIG["DISCORD_WEBHOOK"], json=payload, timeout=10)
        print(f"📤 Discord alert sent: {response.status_code}")

    except Exception as e:
        print(f"❌ Discord alert failed: {e}")

def test_bat_long_trade():
    """Test placing a long trade on BAT"""
    print("🎯 Testing BAT Long Trade on Phemex")
    print("=" * 50)

    try:
        # Initialize Phemex exchange (no sandbox for live trading)
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

        # Get account balance
        balance = exchange.fetch_balance()
        print(f"💰 Account balance: {balance}")

        # Calculate position size (small test amount)
        position_size_usdt = 5.0  # $5 test trade
        position_size = position_size_usdt / current_price

        # Set leverage
        leverage = 20

        # Calculate stop loss and take profit (wider spread for Phemex)
        stop_loss = current_price * 0.95  # 5% stop loss
        take_profit = current_price * 1.05  # 5% take profit

        print(f"📈 Position size: {position_size:.6f} BAT")
        print(f"⚡ Leverage: {leverage}x")
        print(f"🛡️ Stop loss: ${stop_loss:.6f}")
        print(f"🎯 Take profit: ${take_profit:.6f}")

        # Send Discord notification before trade
        message = f"**BAT LONG TEST STARTING**\n"
        message += f"**Symbol:** BAT/USDT\n"
        message += f"**Side:** LONG\n"
        message += f"**Entry:** ${current_price:.6f}\n"
        message += f"**Size:** {position_size:.6f} BAT\n"
        message += f"**Leverage:** {leverage}x\n"
        message += f"**Stop Loss:** ${stop_loss:.6f}\n"
        message += f"**Take Profit:** ${take_profit:.6f}\n"
        message += f"**Test Amount:** ${position_size_usdt}"

        send_discord_alert(message, 0x3498DB)  # Blue for test

        # Place long order (without stop loss and take profit first)
        print("\n🚀 Placing BAT long order...")
        order = exchange.create_order(
            symbol='BAT/USDT',
            type='market',
            side='buy',
            amount=position_size,
            params={
                'leverage': leverage
            }
        )

        print(f"✅ Order placed successfully!")
        print(f"📋 Order ID: {order['id']}")
        print(f"📊 Order Status: {order['status']}")
        print(f"💰 Filled Amount: {order.get('filled', 'N/A')}")
        print(f"💵 Average Price: {order.get('average', 'N/A')}")

        # Send success notification
        success_message = f"**BAT LONG TEST EXECUTED**\n"
        success_message += f"**Symbol:** BAT/USDT\n"
        success_message += f"**Side:** LONG\n"
        success_message += f"**Entry:** ${current_price:.6f}\n"
        success_message += f"**Size:** {position_size:.6f} BAT\n"
        success_message += f"**Leverage:** {leverage}x\n"
        success_message += f"**Stop Loss:** ${stop_loss:.6f}\n"
        success_message += f"**Take Profit:** ${take_profit:.6f}\n"
        success_message += f"**Order ID:** {order['id']}\n"
        success_message += f"**Status:** {order['status']}\n"
        success_message += f"**Filled:** {order.get('filled', 'N/A')}\n"
        success_message += f"**Average Price:** {order.get('average', 'N/A')}"

        send_discord_alert(success_message, 0x00FF00)  # Green for success

        return order

    except Exception as e:
        print(f"❌ BAT long trade failed: {e}")
        error_message = f"**BAT LONG TEST FAILED**\n"
        error_message += f"**Error:** {str(e)}\n"
        error_message += f"**Action:** Check API credentials and permissions"
        send_discord_alert(error_message, 0xFF0000)  # Red for error
        return None

def check_order_status(exchange, order_id):
    """Check order status"""
    print(f"\n🔍 Checking order status: {order_id}")

    try:
        order = exchange.fetch_order(order_id, 'BAT/USDT')
        print(f"📊 Order Status: {order['status']}")
        print(f"💰 Filled Amount: {order.get('filled', 'N/A')}")
        print(f"💵 Average Price: {order.get('average', 'N/A')}")

        return order

    except Exception as e:
        print(f"❌ Failed to fetch order: {e}")
        return None

def main():
    """Main test function"""
    print("🧪 PHEMEX BAT LONG TEST")
    print("=" * 50)

    # Test BAT long trade
    order = test_bat_long_trade()
    if order:
        print("✅ BAT long trade test completed successfully!")

        # Check order status after a moment
        import time
        time.sleep(3)
        check_order_status(exchange, order['id'])

        # Send completion notification
        completion_message = f"**BAT LONG TEST COMPLETED**\n"
        completion_message += f"✅ **Order Executed Successfully**\n"
        completion_message += f"📊 **Order ID:** {order['id']}\n"
        completion_message += f"🎯 **Status:** {order['status']}\n"
        completion_message += f"💰 **Phemex API is working correctly!**"
        send_discord_alert(completion_message, 0x00FF00)
    else:
        print("❌ BAT long trade test failed")

if __name__ == "__main__":
    main()
