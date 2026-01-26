#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the scalper bot silently (no Discord notifications)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ultimate_scalper_bot import UltimateScalperBot
import time

def test_bot_silent():
    """Test the bot without Discord notifications"""
    print("🧪 Testing Ultimate Scalper Bot (Silent Mode)")
    print("=" * 50)

    # Create bot instance
    bot = UltimateScalperBot()

    # Test one scan cycle
    print("🔍 Running one scan cycle...")
    bot.scan_for_scalping_opportunities()

    print("✅ Scan cycle completed")
    print(f"📊 Total trades: {bot.daily_stats['total_trades']}/20")
    print(f"📈 Open positions: {len(bot.active_positions)}/2")
    print(f"💰 Daily P&L: ${bot.daily_stats['profit_today']:.2f}")

    return True

if __name__ == "__main__":
    test_bot_silent()















