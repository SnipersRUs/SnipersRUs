#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detailed Phemex balance checker
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
            "title": "💰 PHEMEX BALANCE CHECK",
            "description": message,
            "color": color,
            "footer": {"text": f"Balance Check • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        payload = {"embeds": [embed]}
        response = requests.post(PHEMEX_CONFIG["DISCORD_WEBHOOK"], json=payload, timeout=10)
        print(f"📤 Discord alert sent: {response.status_code}")

    except Exception as e:
        print(f"❌ Discord alert failed: {e}")

def check_balance_detailed():
    """Check balance with detailed parsing"""
    print("💰 Detailed Phemex Balance Check")
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
        print(f"📊 Raw balance data:")
        print(json.dumps(balance, indent=2))

        # Parse balance data more carefully
        print("\n🔍 Parsing balance data...")

        # Check different ways to access USDT
        usdt_balance_1 = balance.get('USDT', {}).get('free', 0)
        usdt_balance_2 = balance.get('USDT', {}).get('total', 0)
        usdt_balance_3 = balance.get('free', {}).get('USDT', 0)
        usdt_balance_4 = balance.get('total', {}).get('USDT', 0)

        print(f"USDT free: {usdt_balance_1}")
        print(f"USDT total: {usdt_balance_2}")
        print(f"free.USDT: {usdt_balance_3}")
        print(f"total.USDT: {usdt_balance_4}")

        # Check raw info data
        if 'info' in balance and 'data' in balance['info']:
            print("\n📋 Raw account data:")
            for item in balance['info']['data']:
                currency = item.get('currency', '')
                balance_ev = item.get('balanceEv', '0')
                locked_trading = item.get('lockedTradingBalanceEv', '0')
                locked_withdraw = item.get('lockedWithdrawEv', '0')

                print(f"  {currency}: balance={balance_ev}, locked_trading={locked_trading}, locked_withdraw={locked_withdraw}")

                # Convert from EV (exchange value) to actual value
                if currency == 'USDT':
                    try:
                        # Phemex uses EV format, need to divide by 10^8 for USDT
                        usdt_balance_raw = int(balance_ev) / 100000000
                        usdt_locked_trading = int(locked_trading) / 100000000
                        usdt_locked_withdraw = int(locked_withdraw) / 100000000
                        usdt_available = usdt_balance_raw - usdt_locked_trading - usdt_locked_withdraw

                        print(f"    USDT Raw: {usdt_balance_raw}")
                        print(f"    USDT Locked Trading: {usdt_locked_trading}")
                        print(f"    USDT Locked Withdraw: {usdt_locked_withdraw}")
                        print(f"    USDT Available: {usdt_available}")

                        if usdt_available > 0:
                            print(f"✅ FOUND USDT BALANCE: ${usdt_available:.2f}")

                            # Send Discord notification
                            message = f"**PHEMEX BALANCE FOUND**\n"
                            message += f"**USDT Available:** ${usdt_available:.2f}\n"
                            message += f"**USDT Total:** ${usdt_balance_raw:.2f}\n"
                            message += f"**Locked Trading:** ${usdt_locked_trading:.2f}\n"
                            message += f"**Locked Withdraw:** ${usdt_locked_withdraw:.2f}\n"
                            message += f"**Status:** Ready for trading!"

                            send_discord_alert(message, 0x00FF00)
                            return True
                    except Exception as e:
                        print(f"Error parsing USDT: {e}")

        # If no USDT found in raw data, check other methods
        print("\n🔍 Checking other balance methods...")

        # Try different exchange methods
        try:
            # Try fetching positions
            positions = exchange.fetch_positions()
            print(f"Positions: {positions}")
        except Exception as e:
            print(f"Positions error: {e}")

        try:
            # Try fetching open orders
            orders = exchange.fetch_open_orders()
            print(f"Open orders: {len(orders)}")
        except Exception as e:
            print(f"Orders error: {e}")

        return False

    except Exception as e:
        print(f"❌ Balance check failed: {e}")
        error_message = f"**PHEMEX BALANCE CHECK FAILED**\n"
        error_message += f"**Error:** {str(e)}"
        send_discord_alert(error_message, 0xFF0000)
        return False

def main():
    """Main test function"""
    print("🧪 DETAILED PHEMEX BALANCE CHECK")
    print("=" * 50)

    # Check balance with detailed parsing
    success = check_balance_detailed()

    if success:
        print("✅ USDT balance found!")
    else:
        print("❌ No USDT balance found in detailed check")

if __name__ == "__main__":
    main()















