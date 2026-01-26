#!/usr/bin/env python3
"""
Test script for MMS system
Tests the main functionality without requiring full configuration
"""
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from src.logger import info, err
        from src.discord_notifier import send_embed
        from src.mm_detector_v2 import MMDetectorWithMonitoring
        from src.data_fetcher import get_spot_data, get_futures_data, get_orderbook
        from src.volatility_profile import typical_high_vol_hours, next24_windows
        from src.flush_detector import start_flush_monitor
        from src.metrics import cvd_from_trades, orderbook_imbalance, vwap_and_bands
        from src.scalp_signal import scalp_setup, _score_prob, attach_probability
        from src.top_gainer import pick_coin_of_day
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_metrics():
    """Test metrics functions"""
    try:
        from src.metrics import cvd_from_trades, orderbook_imbalance, vwap_and_bands
        
        # Test CVD calculation
        trades = [
            {'side': 'buy', 'size': 100},
            {'side': 'sell', 'size': 50},
            {'side': 'buy', 'size': 75}
        ]
        cvd = cvd_from_trades(trades)
        print(f"✅ CVD calculation: {cvd}")
        
        # Test orderbook imbalance
        bids = [[100, 10], [99, 15], [98, 20]]
        asks = [[101, 12], [102, 18], [103, 25]]
        imb, bid_w, ask_w = orderbook_imbalance(bids, asks)
        print(f"✅ Orderbook imbalance: {imb:.3f}")
        
        # Test VWAP calculation
        prices = [100, 101, 102, 103, 104]
        volumes = [1000, 1200, 800, 1500, 900]
        vwap, v_up, v_dn = vwap_and_bands(prices, volumes)
        print(f"✅ VWAP calculation: {vwap:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Metrics error: {e}")
        return False

def test_scalp_signals():
    """Test scalp signal functions"""
    try:
        from src.scalp_signal import scalp_setup, _score_prob, attach_probability
        
        # Test scalp setup
        idea = scalp_setup("LONG", 100, 95, 105, 100, 102, 98)
        print(f"✅ Scalp setup: {idea}")
        
        # Test probability scoring
        prob = _score_prob(True, 1000, 0.1, "neutral", 2.0, "below VWAP (value)")
        print(f"✅ Probability score: {prob}")
        
        return True
    except Exception as e:
        print(f"❌ Scalp signals error: {e}")
        return False

def test_data_fetcher():
    """Test data fetcher functions"""
    try:
        from src.data_fetcher import get_spot_data, get_futures_data, get_orderbook
        
        # Test spot data
        spot = get_spot_data("https://api.binance.com", "BTCUSDT", 10)
        print(f"✅ Spot data: {len(spot['prices'])} prices")
        
        # Test futures data
        fut = get_futures_data("https://fapi.binance.com", "BTCUSDT", 10)
        print(f"✅ Futures data: {len(fut['open_interest'])} OI points")
        
        # Test orderbook
        bids, asks = get_orderbook("https://api.binance.com", "BTCUSDT", 10)
        print(f"✅ Orderbook: {len(bids)} bids, {len(asks)} asks")
        
        return True
    except Exception as e:
        print(f"❌ Data fetcher error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing MMS System Components")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Metrics Test", test_metrics),
        ("Scalp Signals Test", test_scalp_signals),
        ("Data Fetcher Test", test_data_fetcher)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! MMS system is ready.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()













































