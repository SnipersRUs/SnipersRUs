#!/usr/bin/env python3
"""
Run Bottom Coin Scanner
Simple runner script for the bottom coin scanner
"""

import asyncio
import sys
import os
from bottom_coin_scanner import BottomCoinScanner

async def main():
    """Main runner function"""
    print("🚀 Starting Bottom Coin Scanner...")
    print("📊 This bot will find bottom coins and futures-only opportunities!")
    print("⏰ Scanning every hour for 10 top opportunities")
    print("📱 Alerts will be sent to Discord webhook")
    print("=" * 50)
    
    try:
        scanner = BottomCoinScanner()
        await scanner.run_hourly_scanner()
    except KeyboardInterrupt:
        print("\n🛑 Scanner stopped by user")
    except Exception as e:
        print(f"❌ Error running scanner: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())






















































