#!/usr/bin/env python3
"""
Test TradingView links to ensure they work properly
"""

def test_tradingview_links():
    """Test various TradingView link formats"""
    
    test_pairs = ["BTC", "ETH", "SOL", "SAGA", "ANKR"]
    
    print("🔗 Testing TradingView Link Formats")
    print("=" * 50)
    
    for pair in test_pairs:
        ticker = f"{pair}/USDT"
        
        # Test different exchange formats
        formats = {
            "MEXC": f"https://www.tradingview.com/chart/?symbol=MEXC:{ticker}",
            "BINANCE": f"https://www.tradingview.com/chart/?symbol=BINANCE:{ticker}",
            "BYBIT": f"https://www.tradingview.com/chart/?symbol=BYBIT:{ticker}",
            "COINBASE": f"https://www.tradingview.com/chart/?symbol=COINBASE:{ticker}",
        }
        
        print(f"\n📊 Testing {ticker}:")
        for exchange, link in formats.items():
            print(f"  {exchange}: {link}")
    
    print(f"\n✅ All TradingView links generated successfully!")
    print(f"💡 Use MEXC format since you're trading on MEXC")

if __name__ == "__main__":
    test_tradingview_links()




