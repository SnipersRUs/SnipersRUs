#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Ultimate Scalper Bot
Tests Phemex connection and scalping functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ultimate_scalper_bot import UltimateScalperBot, PhemexScalper, ScalpingSignalDetector
import json
import time

def test_phemex_connection():
    """Test Phemex API connection"""
    print("🔌 Testing Phemex connection...")

    try:
        bot = UltimateScalperBot()

        # Test balance fetch
        balance = bot.phemex.get_balance()
        print(f"✅ Balance: {balance}")

        # Test ticker fetch
        ticker = bot.phemex.get_ticker("BTC/USDT")
        if ticker:
            print(f"✅ BTC/USDT Price: ${ticker['last']:.2f}")
        else:
            print("❌ Failed to fetch BTC/USDT ticker")

        # Test OHLCV data
        df = bot.phemex.get_ohlcv("BTC/USDT", "1m", 10)
        if df is not None and len(df) > 0:
            print(f"✅ OHLCV data: {len(df)} candles")
            print(f"   Latest close: ${df['close'].iloc[-1]:.2f}")
        else:
            print("❌ Failed to fetch OHLCV data")

        return True

    except Exception as e:
        print(f"❌ Phemex connection failed: {e}")
        return False

def test_signal_detection():
    """Test scalping signal detection"""
    print("\n🔍 Testing signal detection...")

    try:
        bot = UltimateScalperBot()
        signals = bot.detector.detect_scalping_signals()

        print(f"📊 Found {len(signals)} signals")

        for signal in signals[:3]:  # Show top 3 signals
            print(f"   {signal['symbol']} {signal['direction']} - Confidence: {signal['confidence']}/10")
            print(f"   Entry: ${signal['entry']:.6f} | Target: ${signal['take_profit']:.6f}")
            print(f"   Reasons: {', '.join(signal['reasons'])}")
            print()

        return len(signals) > 0

    except Exception as e:
        print(f"❌ Signal detection failed: {e}")
        return False

def test_risk_management():
    """Test risk management functions"""
    print("\n🛡️ Testing risk management...")

    try:
        bot = UltimateScalperBot()

        # Test daily stats reset
        bot.reset_daily_stats()
        print("✅ Daily stats reset")

        # Test trade limits
        can_trade = bot.can_trade()
        print(f"✅ Can trade: {can_trade}")

        # Test position sizing
        position_size = bot.calculate_position_size("BTC/USDT", 50000.0)
        print(f"✅ Position size for BTC at $50k: {position_size:.4f}")

        return True

    except Exception as e:
        print(f"❌ Risk management test failed: {e}")
        return False

def test_discord_integration():
    """Test Discord webhook integration"""
    print("\n📱 Testing Discord integration...")

    try:
        bot = UltimateScalperBot()

        # Create test signal
        test_signal = {
            "symbol": "BTC/USDT",
            "direction": "LONG",
            "entry": 50000.0,
            "confidence": 8,
            "reasons": ["Test signal", "Volume spike"]
        }

        test_order = {
            "id": "test_order_123",
            "symbol": "BTC/USDT",
            "side": "buy",
            "amount": 0.002,
            "price": 50000.0
        }

        # Send test alert
        bot.send_discord_alert(test_signal, test_order)
        print("✅ Discord test alert sent")

        return True

    except Exception as e:
        print(f"❌ Discord integration failed: {e}")
        return False

def run_live_test():
    """Run a live test of the scalping bot for 5 minutes"""
    print("\n🚀 Running live test (5 minutes)...")

    try:
        bot = UltimateScalperBot()

        # Run for 5 minutes
        start_time = time.time()
        test_duration = 300  # 5 minutes

        while time.time() - start_time < test_duration:
            print(f"\n⏰ Test time: {int(time.time() - start_time)}s / {test_duration}s")

            # Run one scan
            bot.scan_for_scalping_opportunities()

            # Wait for next scan
            time.sleep(bot.config["SCAN_INTERVAL_SEC"])

        print("\n✅ Live test completed")
        return True

    except KeyboardInterrupt:
        print("\n🛑 Live test interrupted by user")
        return True
    except Exception as e:
        print(f"\n❌ Live test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Ultimate Scalper Bot - Test Suite")
    print("=" * 50)

    tests = [
        ("Phemex Connection", test_phemex_connection),
        ("Signal Detection", test_signal_detection),
        ("Risk Management", test_risk_management),
        ("Discord Integration", test_discord_integration),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔬 Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🚀 All tests passed! Bot is ready to run.")
        print("\nTo start the bot:")
        print("   python ultimate_scalper_bot.py")
        print("\nTo run live test:")
        print("   python test_scalper_bot.py --live")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")

    # Ask if user wants to run live test
    if passed >= 3:  # If most tests passed
        try:
            response = input("\n🤔 Run live test? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                run_live_test()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test Ultimate Scalper Bot")
    parser.add_argument("--live", action="store_true", help="Run live test")
    args = parser.parse_args()

    if args.live:
        run_live_test()
    else:
        main()
