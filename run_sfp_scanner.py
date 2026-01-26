#!/usr/bin/env python3
"""
Simple runner for the SFP Scanner Bot
"""

import subprocess
import sys

def main():
    """Run the SFP scanner bot"""
    print("🎯 Starting SFP Scanner Bot...")
    print("   Scans MEXC for Fair Value Gaps on 15m, 30m, and 1h")
    print("   Finds coins approaching SFPs for reversal trades")
    print("   Scans every 30 minutes")
    print("Press Ctrl+C to stop")
    print("-" * 50)

    try:
        subprocess.run([sys.executable, "sfp_scanner_bot.py"])
    except KeyboardInterrupt:
        print("\n⏹ SFP Scanner stopped by user")
    except Exception as e:
        print(f"❌ Error running scanner: {e}")

if __name__ == "__main__":
    main()
