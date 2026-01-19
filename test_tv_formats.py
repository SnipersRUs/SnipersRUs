#!/usr/bin/env python3
"""
Test different TradingView link formats to find what works
"""

def test_tradingview_formats():
    """Test various TradingView link formats"""
    
    test_pairs = ["BTC", "ETH", "SOL", "SAGA", "ANKR", "BOT"]
    
    print("🔗 Testing TradingView Link Formats")
    print("=" * 60)
    
    for pair in test_pairs:
        ticker = f"{pair}/USDT"
        
        # Test different formats
        formats = {
            "BINANCE": f"https://www.tradingview.com/chart/?symbol=BINANCE:{ticker}",
            "BINANCE_ALT": f"https://www.tradingview.com/chart/?symbol=BINANCE:{pair}USDT",
            "COINBASE": f"https://www.tradingview.com/chart/?symbol=COINBASE:{ticker}",
            "COINBASE_ALT": f"https://www.tradingview.com/chart/?symbol=COINBASE:{pair}USDT",
            "NO_EXCHANGE": f"https://www.tradingview.com/chart/?symbol={ticker}",
            "NO_EXCHANGE_ALT": f"https://www.tradingview.com/chart/?symbol={pair}USDT",
        }
        
        print(f"\n📊 Testing {ticker}:")
        for format_name, link in formats.items():
            print(f"  {format_name:15}: {link}")
    
    print(f"\n💡 **Recommendation:**")
    print(f"   Try BINANCE format first - it has the best TradingView support")
    print(f"   If that fails, try COINBASE format")
    print(f"   If both fail, try without exchange prefix")

if __name__ == "__main__":
    test_tradingview_formats()




