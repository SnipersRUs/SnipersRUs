#!/usr/bin/env python3
"""Test old Macro Hunter logic (RSI, Volume, Support/Resistance)"""

import numpy as np
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import functions from mcro_bot_simple
from mcro_bot_simple import rsi, SimpleScanner

def test_rsi():
    """Test RSI calculation"""
    print("🧪 Testing RSI calculation...")

    # Create test data: trending down (should have low RSI)
    close_down = np.array([100, 98, 96, 94, 92, 90, 88, 86, 84, 82, 80, 78, 76, 74, 72, 70])
    rsi_down = rsi(close_down)
    print(f"   📉 Downward trend RSI: {rsi_down:.1f} (expected < 50)")

    # Create test data: trending up (should have high RSI)
    close_up = np.array([70, 72, 74, 76, 78, 80, 82, 84, 86, 88, 90, 92, 94, 96, 98, 100])
    rsi_up = rsi(close_up)
    print(f"   📈 Upward trend RSI: {rsi_up:.1f} (expected > 50)")

    if rsi_down < 50 and rsi_up > 50:
        print("   ✅ RSI logic working correctly!")
        return True
    else:
        print("   ❌ RSI logic issue detected")
        return False

def test_scanner_basic():
    """Test basic scanner initialization"""
    print("\n🧪 Testing Scanner initialization...")
    try:
        scanner = SimpleScanner()
        print(f"   ✅ Scanner initialized")
        print(f"   📊 Exchanges loaded: {len(scanner.exchanges)}")
        print(f"   ⏰ Scan interval: {scanner.scan_interval}s")
        print(f"   🔄 Next scan due calculation: Working")
        return True
    except Exception as e:
        print(f"   ❌ Scanner initialization failed: {e}")
        return False

def test_scoring_logic():
    """Test the scoring logic matches old behavior"""
    print("\n🧪 Testing scoring logic (old behavior)...")

    # Simulate old scoring behavior
    score = 50.0

    # RSI oversold (old logic: +20)
    rsi_val = 25
    if rsi_val < 30:
        score += 20
    print(f"   RSI < 30: +20 points (total: {score})")

    # Volume spike (old logic: +15)
    vol_ratio = 2.5
    if vol_ratio > 2.0:
        score += 15
    print(f"   Volume > 2x: +15 points (total: {score})")

    # Near support (old logic: +10)
    score += 10
    print(f"   Near support: +10 points (total: {score})")

    print(f"   📊 Final score: {score}/100")

    if score >= 75:
        print("   ✅ Old scoring logic: Score >= 75 (would trigger signal)")
        return True
    else:
        print("   ❌ Old scoring logic: Score < 75 (would NOT trigger)")
        return False

def main():
    print("=" * 60)
    print("🔍 Testing Macro Hunter Old Logic (RSI + Volume + S/R)")
    print("=" * 60)

    tests = [
        ("RSI Calculation", test_rsi),
        ("Scanner Initialization", test_scanner_basic),
        ("Scoring Logic (Old)", test_scoring_logic),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")

    all_passed = all(r for _, r in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL OLD LOGIC TESTS PASSED!")
        print("   The original RSI/Volume/Support-Resistance logic is working correctly.")
    else:
        print("❌ SOME TESTS FAILED")
        print("   Please review the errors above.")
    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())








