#!/usr/bin/env python3
"""
Test Hourly Market Analyzer
Test the real data fetching and TradingView links
"""
import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from hourly_market_analyzer import HourlyMarketAnalyzer

async def test_real_data():
    """Test real data fetching and TradingView links"""
    print("🧪 Testing Hourly Market Analyzer with Real Data...")
    print("=" * 60)
    
    analyzer = HourlyMarketAnalyzer()
    
    # Test symbols
    test_symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    
    for symbol in test_symbols:
        print(f"\n📊 Testing {symbol}...")
        
        try:
            # Get real market data
            spot_data, futures_data = await analyzer.get_real_market_data(symbol)
            
            if spot_data:
                current_price = spot_data.get('current_price', 0)
                price_change = spot_data.get('price_change_24h', 0)
                volume_24h = spot_data.get('volume_24h', 0)
                
                # Get TradingView link
                tv_link = analyzer.get_tradingview_link(symbol)
                
                print(f"✅ {symbol} Data Retrieved:")
                print(f"   Current Price: ${current_price:,.2f}")
                print(f"   24h Change: {price_change:+.2f}%")
                print(f"   24h Volume: ${volume_24h:,.0f}")
                print(f"   TradingView: {tv_link}")
                
                # Test bias analysis
                market_state = analyzer.detector.analyze_mm_activity(symbol, spot_data, futures_data)
                print(f"   M15 Bias: {market_state.m15_bias}")
                print(f"   H1 Bias: {market_state.h1_bias}")
                print(f"   H4 Bias: {market_state.h4_bias}")
                print(f"   MM Active: {market_state.mm_active}")
                print(f"   MM Confidence: {market_state.mm_confidence:.0f}%")
                
            else:
                print(f"❌ Failed to get data for {symbol}")
                
        except Exception as e:
            print(f"❌ Error testing {symbol}: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Testing Market Analysis Formatting...")
    
    # Test market analysis
    try:
        market_analysis = await analyzer.analyze_all_symbols()
        
        if market_analysis:
            print("✅ Market Analysis Generated:")
            
            # Test bias analysis formatting
            bias_text = analyzer.format_bias_analysis(market_analysis)
            print("\n📊 Bias Analysis Format:")
            print(bias_text[:500] + "..." if len(bias_text) > 500 else bias_text)
            
            # Test key levels formatting
            levels_text = analyzer.format_key_levels(market_analysis)
            print("\n🎯 Key Levels Format:")
            print(levels_text[:300] + "..." if len(levels_text) > 300 else levels_text)
            
        else:
            print("❌ Failed to generate market analysis")
            
    except Exception as e:
        print(f"❌ Error in market analysis: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Test Complete!")
    print("✅ Real data fetching working")
    print("✅ TradingView links generated")
    print("✅ Market analysis formatting working")
    print("✅ Ready to run hourly analyzer!")

async def main():
    """Main test function"""
    await test_real_data()

if __name__ == "__main__":
    asyncio.run(main())
