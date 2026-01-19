#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test signal detection to see why no trades are found
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ultimate_scalper_bot import ScalpingSignalDetector, PhemexScalper, SCALPER_CONFIG

def test_signal_detection():
    """Test signal detection on major pairs"""
    print("🔍 Testing Signal Detection")
    print("=" * 50)

    try:
        # Initialize the scalper
        scalper = PhemexScalper(SCALPER_CONFIG)
        detector = ScalpingSignalDetector(scalper)

        print("✅ Bot initialized")

        # Test on major pairs
        test_pairs = [
            "BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT", "BNB/USDT:USDT",
            "XRP/USDT:USDT", "ADA/USDT:USDT", "DOGE/USDT:USDT", "AVAX/USDT:USDT"
        ]

        print(f"🔍 Testing {len(test_pairs)} major pairs...")

        for pair in test_pairs:
            try:
                print(f"\n📊 Testing {pair}...")

                # Get ticker data
                ticker = scalper.get_ticker(pair)
                if ticker:
                    print(f"  💰 Price: ${ticker['last']:.6f}")
                    percentage = ticker.get('percentage', 0) or 0
                    print(f"  📈 24h Change: {percentage:.2f}%")
                else:
                    print(f"  ❌ No ticker data for {pair}")
                    continue

                # Test signal detection
                signals = detector.detect_scalping_signals()

                if signals:
                    print(f"  ✅ Found {len(signals)} signals")
                    for signal in signals:
                        if signal['symbol'] == pair:
                            print(f"    🎯 {signal['symbol']} {signal['direction']} (confidence: {signal['confidence']}/10)")
                            print(f"    📊 Entry: ${signal.get('entry', 'N/A')}")
                            print(f"    🛡️ Stop: ${signal.get('stop', 'N/A')}")
                            print(f"    🎯 Target: ${signal.get('target', 'N/A')}")
                else:
                    print(f"  ❌ No signals found for {pair}")

            except Exception as e:
                print(f"  ❌ Error testing {pair}: {e}")

        # Test overall signal detection
        print(f"\n🔍 Testing overall signal detection...")
        all_signals = detector.detect_scalping_signals()

        if all_signals:
            print(f"✅ Found {len(all_signals)} total signals")
            for signal in all_signals[:5]:  # Show first 5
                print(f"  🎯 {signal['symbol']} {signal['direction']} (confidence: {signal['confidence']}/10)")
        else:
            print("❌ No signals found at all!")
            print("🔍 This might be why no trades are being executed")

            # Check if the issue is with the signal detection logic
            print("\n🔍 Debugging signal detection...")
            print("  - Check if indicators are calculating properly")
            print("  - Check if confidence thresholds are too high")
            print("  - Check if market conditions are suitable")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_signal_detection()
