#!/usr/bin/env python3
"""
BEARISH SNIPER — Advanced Reversal Scanner Runner
- 27-minute scan intervals for high-frequency detection
- Minimum 3 signals per scan with smart validation
- Purple bearish theme with duplicate prevention
- Advanced signal tracking and position management
"""

import subprocess
import sys

def main():
    """Run the BEARISH SNIPER scanner"""
    print("🟣 Starting BEARISH SNIPER — Advanced Reversal Scanner")
    print("Features:")
    print("  🕐 Scan Interval: 27 minutes")
    print("  📊 Minimum Signals: 3 per scan")
    print("  🟣 Bearish Theme: Purple cards")
    print("  🔄 Smart Validation: No duplicate trades")
    print("  📈 Paper Trading: $10K balance, $300 trades")
    print("  🎯 Max Positions: 3 open trades")
    print("\nPress Ctrl+C to stop")
    print("-" * 60)
    
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
        print("\n⏹ BEARISH SNIPER stopped by user")
    except Exception as e:
        print(f"❌ Error running BEARISH SNIPER: {e}")

if __name__ == "__main__":
    main()




