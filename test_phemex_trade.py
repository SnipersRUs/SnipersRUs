#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Phemex API with BAT short trade
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
    "PAPER_TRADING": True
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

def test_phemex_connection():
    """Test Phemex API connection"""
    print("🔌 Testing Phemex API connection...")
    
    try:
        # Initialize Phemex exchange
        exchange = ccxt.phemex({
            'apiKey': PHEMEX_CONFIG["PHEMEX_API_KEY"],
            'secret': PHEMEX_CONFIG["PHEMEX_SECRET"],
            'sandbox': PHEMEX_CONFIG["PAPER_TRADING"],
            'options': {
                'defaultType': 'swap',
                'test': PHEMEX_CONFIG["PAPER_TRADING"]
            },
            'enableRateLimit': True,
        })
        
        # Load markets
        exchange.load_markets()
        print("✅ Phemex exchange initialized")
        
        # Get account balance
        balance = exchange.fetch_balance()
        print(f"✅ Balance: {balance}")
        
        # Get BAT/USDT ticker
        ticker = exchange.fetch_ticker('BAT/USDT')
        print(f"✅ BAT/USDT Price: ${ticker['last']:.6f}")
        
        return exchange
        
    except Exception as e:
        print(f"❌ Phemex connection failed: {e}")
        return None

def test_bat_short_trade(exchange):
    """Test placing a short trade on BAT"""
    print("\n🎯 Testing BAT short trade...")
    
    try:
        # Get current BAT price
        ticker = exchange.fetch_ticker('BAT/USDT')
        current_price = ticker['last']
        print(f"📊 Current BAT price: ${current_price:.6f}")
        
        # Calculate position size (small test amount)
        position_size_usdt = 5.0  # $5 test trade
        position_size = position_size_usdt / current_price
        
        # Set leverage
        leverage = 20
        
        # Calculate stop loss and take profit
        stop_loss = current_price * 1.01  # 1% stop loss
        take_profit = current_price * 0.99  # 1% take profit
        
        print(f"📈 Position size: {position_size:.6f} BAT")
        print(f"⚡ Leverage: {leverage}x")
        print(f"🛡️ Stop loss: ${stop_loss:.6f}")
        print(f"🎯 Take profit: ${take_profit:.6f}")
        
        # Place short order
        order = exchange.create_order(
            symbol='BAT/USDT',
            type='market',
            side='sell',
            amount=position_size,
            params={
                'leverage': leverage,
                'stopPrice': stop_loss,
                'takeProfit': take_profit
            }
        )
        
        print(f"✅ Order placed successfully!")
        print(f"📋 Order ID: {order['id']}")
        print(f"📊 Order Status: {order['status']}")
        
        # Send Discord notification
        message = f"**BAT SHORT TEST EXECUTED**\n"
        message += f"**Symbol:** BAT/USDT\n"
        message += f"**Side:** SHORT\n"
        message += f"**Entry:** ${current_price:.6f}\n"
        message += f"**Size:** {position_size:.6f} BAT\n"
        message += f"**Leverage:** {leverage}x\n"
        message += f"**Stop Loss:** ${stop_loss:.6f}\n"
        message += f"**Take Profit:** ${take_profit:.6f}\n"
        message += f"**Order ID:** {order['id']}\n"
        message += f"**Status:** {order['status']}"
        
        send_discord_alert(message, 0xFF0000)  # Red for short
        
        return order
        
    except Exception as e:
        print(f"❌ BAT short trade failed: {e}")
        send_discord_alert(f"**BAT SHORT TEST FAILED**\nError: {str(e)}", 0xFF0000)
        return None

def check_order_status(exchange, order_id):
    """Check order status"""
    print(f"\n🔍 Checking order status: {order_id}")
    
    try:
        order = exchange.fetch_order(order_id, 'BAT/USDT')
        print(f"📊 Order Status: {order['status']}")
        print(f"💰 Filled Amount: {order['filled']}")
        print(f"💵 Average Price: {order['average']}")
        
        return order
        
    except Exception as e:
        print(f"❌ Failed to fetch order: {e}")
        return None

def main():
    """Main test function"""
    print("🧪 PHEMEX API TEST - BAT SHORT TRADE")
    print("=" * 50)
    
    # Test connection
    exchange = test_phemex_connection()
    if not exchange:
        print("❌ Cannot proceed without Phemex connection")
        return
    
    # Send startup notification
    send_discord_alert("**PHEMEX API TEST STARTED**\nTesting BAT short trade execution...")
    
    # Test BAT short trade
    order = test_bat_short_trade(exchange)
    if order:
        print("✅ BAT short trade test completed successfully!")
        
        # Check order status after a moment
        import time
        time.sleep(2)
        check_order_status(exchange, order['id'])
        
        # Send completion notification
        send_discord_alert("**PHEMEX API TEST COMPLETED**\nBAT short trade executed successfully!\nAPI is working correctly.", 0x00FF00)
    else:
        print("❌ BAT short trade test failed")
        send_discord_alert("**PHEMEX API TEST FAILED**\nBAT short trade execution failed.\nCheck API credentials and permissions.", 0xFF0000)

if __name__ == "__main__":
    main()















