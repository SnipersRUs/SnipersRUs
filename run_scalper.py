#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultimate Scalper Bot Runner
Simple script to start the scalping bot
"""

import sys
import os
import json
from ultimate_scalper_bot import UltimateScalperBot

def load_config():
    """Load configuration from file"""
    try:
        with open("scalper_config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ scalper_config.json not found")
        return None
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

def main():
    """Main runner function"""
    print("🚀 Ultimate Scalper Bot")
    print("=" * 40)

    # Load configuration
    config = load_config()
    if not config:
        print("Please create scalper_config.json first")
        return

    # Show configuration
    print(f"📊 Target Profit: {config['TARGET_PROFIT_PCT']}%")
    print(f"🛡️ Stop Loss: {config['STOP_LOSS_PCT']}%")
    print(f"💰 Position Size: ${config['POSITION_SIZE_USDT']}")
    print(f"📈 Max Total Trades: {config['MAX_TOTAL_TRADES']}")
    print(f"📈 Max Open Positions: {config['MAX_OPEN_POSITIONS']}")
    print(f"⏰ Scan Interval: {config['SCAN_INTERVAL_SEC']}s")
    print(f"🧪 Paper Trading: {'ON' if config['PAPER_TRADING'] else 'OFF'}")
    print()

    # Confirm before starting
    if not config['PAPER_TRADING']:
        print("⚠️  WARNING: LIVE TRADING MODE ENABLED!")
        print("This will use real money. Are you sure?")
        response = input("Type 'YES' to continue: ").strip()
        if response != "YES":
            print("❌ Aborted")
            return

    try:
        # Start the bot
        bot = UltimateScalperBot()
        bot.run_scalping_bot()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")

if __name__ == "__main__":
    main()
