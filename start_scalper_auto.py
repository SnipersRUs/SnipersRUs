#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-start Ultimate Scalper Bot
24/7 Active Trading with $52.82 Balance
"""

import os
import sys
import time
import signal
import subprocess
from datetime import datetime, timezone

def send_startup_notification():
    """Send Discord notification that bot is starting"""
    import requests

    webhook_url = "https://discord.com/api/webhooks/1430429617696673852/UmIz28ug7uMqCyuVyOy7LeGXRj91sGLM9NuZicfzSZQOvYlGdfulww0WZzqRLos2I6Jz"

    try:
        embed = {
            "title": "🚀 ULTIMATE SCALPER BOT STARTING",
            "description": "**24/7 Active Trading Mode**\n"
                         "**Account:** $52.82 USDT (Futures)\n"
                         "**Position Size:** $5 per trade\n"
                         "**Leverage:** 20x\n"
                         "**Target:** 1.5% profit per trade\n"
                         "**Stop Loss:** 0.8%\n"
                         "**Max Trades:** 20 total, 2 open\n"
                         "**Scan Interval:** 30 seconds\n"
                         "**Status:** 🔴 LIVE TRADING",
            "color": 0x00FF00,
            "footer": {"text": f"Auto Start • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        payload = {"embeds": [embed]}
        response = requests.post(webhook_url, json=payload, timeout=10)
        print(f"📤 Startup notification sent: {response.status_code}")

    except Exception as e:
        print(f"❌ Startup notification failed: {e}")

def start_scalper_bot():
    """Start the scalper bot with auto-restart"""
    print("🚀 ULTIMATE SCALPER BOT - AUTO START")
    print("=" * 50)
    print("💰 Account: $52.82 USDT (Futures)")
    print("📊 Position Size: $5 per trade")
    print("⚡ Leverage: 20x")
    print("🎯 Target: 1.5% profit per trade")
    print("🛡️ Stop Loss: 0.8%")
    print("📈 Max Trades: 20 total, 2 open")
    print("⏰ Scan Interval: 30 seconds")
    print("🔄 Auto-restart: Enabled")
    print("=" * 50)

    # Send startup notification
    send_startup_notification()

    # Start the bot
    try:
        print("\n🚀 Starting Ultimate Scalper Bot...")
        print("📱 Discord notifications enabled")
        print("🔄 Bot will auto-restart if it crashes")
        print("⏹️ Press Ctrl+C to stop")
        print()

        # Run the scalper bot
        subprocess.run([sys.executable, "ultimate_scalper_bot.py"], check=True)

    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
        send_shutdown_notification()
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Bot crashed with error: {e}")
        print("🔄 Restarting in 5 seconds...")
        time.sleep(5)
        start_scalper_bot()  # Auto-restart
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("🔄 Restarting in 10 seconds...")
        time.sleep(10)
        start_scalper_bot()  # Auto-restart

def send_shutdown_notification():
    """Send Discord notification that bot is stopping"""
    import requests

    webhook_url = "https://discord.com/api/webhooks/1430429617696673852/UmIz28ug7uMqCyuVyOy7LeGXRj91sGLM9NuZicfzSZQOvYlGdfulww0WZzqRLos2I6Jz"

    try:
        embed = {
            "title": "⏹️ ULTIMATE SCALPER BOT STOPPED",
            "description": "**Bot has been stopped**\n"
                         "**Status:** 🔴 OFFLINE\n"
                         "**Action:** Manual stop",
            "color": 0xFF0000,
            "footer": {"text": f"Manual Stop • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        payload = {"embeds": [embed]}
        response = requests.post(webhook_url, json=payload, timeout=10)
        print(f"📤 Shutdown notification sent: {response.status_code}")

    except Exception as e:
        print(f"❌ Shutdown notification failed: {e}")

def main():
    """Main function"""
    print("🧪 ULTIMATE SCALPER BOT - AUTO START")
    print("=" * 50)

    # Check if bot file exists
    if not os.path.exists("ultimate_scalper_bot.py"):
        print("❌ ultimate_scalper_bot.py not found!")
        return

    # Start the bot
    start_scalper_bot()

if __name__ == "__main__":
    main()















