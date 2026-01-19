#!/usr/bin/env python3
"""
Run script for Forex Pivot Reversal Bot
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from forex_pivot_reversal_bot import ForexPivotReversalBot

if __name__ == "__main__":
    print("=" * 60)
    print("FOREX PIVOT REVERSAL BOT")
    print("=" * 60)
    print()
    print("Features:")
    print("  • PivotX Pro - Pivot detection")
    print("  • Golden Pocket Syndicate (GPS) - GP zones")
    print("  • Tactical Deviation - VWAP deviation bands")
    print()
    print("Paper Trading:")
    print("  • Starting Balance: $1,000")
    print("  • Leverage: 150x")
    print("  • Trade Size: $50 per trade")
    print("  • Max Positions: 3")
    print("  • TP Management: 25% take first TP")
    print()
    print("=" * 60)
    print()

    bot = ForexPivotReversalBot()
    bot.run()







