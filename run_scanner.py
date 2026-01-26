#!/usr/bin/env python3
"""
Simple runner for the COOKED REVERSAL scanner
"""

import subprocess
import sys

def main():
    """Run the scanner with default settings"""
    print("🔴 Starting COOKED REVERSAL Scanner...")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        # Run the scanner in loop mode with 120 second intervals
        subprocess.run([
            sys.executable, 
            "cooked_reversal.py", 
            "--loop", 
            "--interval", "120",
            "--exchanges", "binance", "bybit", "mexc"
        ])
    except KeyboardInterrupt:
        print("\n⏹ Scanner stopped by user")
    except Exception as e:
        print(f"❌ Error running scanner: {e}")

if __name__ == "__main__":
    main()




