#!/usr/bin/env python3
"""Quick test to verify SFP detection is working"""

import pandas as pd
import ccxt
from sfp_scanner_bot import SFPScanner

# Test on a few popular coins
test_symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']

scanner = SFPScanner("")
scanner.initialize_exchange()

print("🧪 Testing SFP Detection...\n")

for symbol in test_symbols:
    print(f"Testing {symbol}...")
    for tf in ['15m', '30m', '1h']:
        try:
            ohlcv = scanner.exchange.fetch_ohlcv(symbol, tf, limit=200)
            if ohlcv:
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                active_sfps = scanner.get_active_sfps(df, tf)
                approaches = scanner.find_approaching_sfps(symbol, tf)
                print(f"  {tf}: {len(active_sfps)} SFPs found, {len(approaches)} approaching")
                if approaches:
                    for app in approaches[:2]:  # Show first 2
                        print(f"    - {app.symbol}: {app.direction} @ ${app.current_price:.2f}, {app.distance_pct:.2f}% to SFP")
        except Exception as e:
            print(f"  {tf}: Error - {e}")

print("\n✅ Test complete!")
