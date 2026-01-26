#!/usr/bin/env python3
"""
REVERSAL HUNTER — Ultimate Reversal Scanner Runner
- Golden Pocket + Volume Spike + Divergence Detection
- Only 2 priority signals per scan
- Enhanced market analysis with warnings
- Oversold watchlist for coins losing momentum
"""

import subprocess
import sys

def main():
    """Run the REVERSAL HUNTER scanner"""
    print("🎯 Starting REVERSAL HUNTER — Ultimate Reversal Scanner")
    print("Features:")
    print("  🎯 Golden Pocket Detection - 61.8% - 65% retracement zones")
    print("  📈 Volume Spike Analysis - 15m+ timeframe detection")
    print("  🔄 Divergence + Liquidity Spike Logic")
    print("  📊 Market Analysis - Real-time coin condition assessment")
    print("  👀 Oversold Watchlist - Coins losing momentum")
    print("  ⚠️  Warning System - 'Coin exhausted, looking to short soon'")
    print("  🎯 Only 2 Priority Signals - Quality over quantity")
    print("  📈 Paper Trading - $10K balance, $300 trades")
    print("\nPress Ctrl+C to stop")
    print("-" * 70)
    
    try:
        # Run the enhanced scanner
        subprocess.run([
            sys.executable, 
            "cooked_reversal.py", 
            "--loop", 
            "--interval", "1620",  # 27 minutes
            "--exchanges", "mexc", "bybit", "binance"
        ])
    except KeyboardInterrupt:
        print("\n⏹ REVERSAL HUNTER stopped by user")
    except Exception as e:
        print(f"❌ Error running REVERSAL HUNTER: {e}")

if __name__ == "__main__":
    main()




