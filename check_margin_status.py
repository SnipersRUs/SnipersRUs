#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Phemex margin status and available balance
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
            "title": "💰 PHEMEX MARGIN STATUS",
            "description": message,
            "color": color,
            "footer": {"text": f"Margin Check • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        payload = {"embeds": [embed]}
        response = requests.post(PHEMEX_CONFIG["DISCORD_WEBHOOK"], json=payload, timeout=10)
        print(f"📤 Discord alert sent: {response.status_code}")

    except Exception as e:
        print(f"❌ Discord alert failed: {e}")

def check_margin_status():
    """Check detailed margin status"""
    print("💰 Phemex Margin Status Check")
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

        # Get positions
        positions = exchange.fetch_positions()
        print(f"📊 Found {len(positions)} positions")

        # Find active positions
        active_positions = []
        total_collateral = 0
        total_notional = 0

        for pos in positions:
            if pos['contracts'] > 0:
                active_positions.append(pos)
                total_collateral += pos['collateral']
                total_notional += pos['notional']
                print(f"📈 {pos['symbol']}: {pos['contracts']} contracts, ${pos['collateral']:.2f} collateral, ${pos['notional']:.2f} notional")

        print(f"\n💰 Total Collateral: ${total_collateral:.2f}")
        print(f"💵 Total Notional: ${total_notional:.2f}")

        # Check if we can get account info
        try:
            account_info = exchange.fetch_account()
            print(f"📊 Account info: {account_info}")
        except Exception as e:
            print(f"Account info error: {e}")

        # Try to get margin requirements for BAT
        try:
            market = exchange.market('BAT/USDT')
            print(f"📊 BAT Market: {market}")
        except Exception as e:
            print(f"Market info error: {e}")

        # Send Discord notification
        message = f"**PHEMEX MARGIN STATUS**\n"
        message += f"**Active Positions:** {len(active_positions)}\n"
        message += f"**Total Collateral:** ${total_collateral:.2f}\n"
        message += f"**Total Notional:** ${total_notional:.2f}\n"
        message += f"**USDT Balance:** ${balance.get('USDT', {}).get('free', 0):.2f}\n"
        message += f"**Status:** {'Ready for trading' if balance.get('USDT', {}).get('free', 0) > 0 else 'Need USDT deposit'}"

        send_discord_alert(message, 0x3498DB)

        # Recommendations
        if balance.get('USDT', {}).get('free', 0) == 0:
            print("\n💡 RECOMMENDATIONS:")
            print("1. Deposit USDT to your Phemex account")
            print("2. Or close the BNB position to free up margin")
            print("3. Or reduce the BNB position size")

            recommendation_message = f"**TRADING RECOMMENDATIONS**\n"
            recommendation_message += f"**Option 1:** Deposit USDT to account\n"
            recommendation_message += f"**Option 2:** Close BNB position to free margin\n"
            recommendation_message += f"**Option 3:** Reduce BNB position size\n"
            recommendation_message += f"**Current:** All margin tied up in BNB position"

            send_discord_alert(recommendation_message, 0xFFA500)

        return balance.get('USDT', {}).get('free', 0) > 0

    except Exception as e:
        print(f"❌ Margin check failed: {e}")
        error_message = f"**MARGIN CHECK FAILED**\n"
        error_message += f"**Error:** {str(e)}"
        send_discord_alert(error_message, 0xFF0000)
        return False

def main():
    """Main test function"""
    print("🧪 PHEMEX MARGIN STATUS CHECK")
    print("=" * 50)

    # Check margin status
    can_trade = check_margin_status()

    if can_trade:
        print("✅ Account ready for trading!")
    else:
        print("⚠️ Account needs funding or position adjustment")

if __name__ == "__main__":
    main()















