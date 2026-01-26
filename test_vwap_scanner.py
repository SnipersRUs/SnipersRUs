#!/usr/bin/env python3
"""
Test script for VWAP Bottom Scanner
"""

import asyncio
import sys
from vwap_bottom_scanner import VWAPBottomScanner

async def test_scanner():
    """Test the scanner"""
    print("🧪 Testing VWAP Bottom Scanner...")
    
    scanner = VWAPBottomScanner()
    
    # Test one symbol
    print("🔍 Testing PEPE...")
    signal = await scanner.analyze_bottom_coin("PEPE")
    
    if signal:
        print(f"✅ Found signal: {signal.symbol} {signal.direction} @ ${signal.entry_price:.6f} ({signal.confidence:.1f}%)")
        print(f"   Reason: {signal.reason}")
    else:
        print("❌ No signal found for PEPE")
    
    # Test a few more
    test_symbols = ["SHIB", "DOGE", "FLOKI"]
    for symbol in test_symbols:
        print(f"🔍 Testing {symbol}...")
        signal = await scanner.analyze_bottom_coin(symbol)
        if signal:
            print(f"✅ Found signal: {signal.symbol} {signal.direction} @ ${signal.entry_price:.6f} ({signal.confidence:.1f}%)")
        else:
            print(f"❌ No signal found for {symbol}")

if __name__ == "__main__":
    asyncio.run(test_scanner())






















































