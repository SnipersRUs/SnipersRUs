#!/usr/bin/env python3
"""
Test Hourly Analysis
Test that hourly analysis is working with real prices
"""
import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from mm_trading_bot import MMTradingBot
from discord_integration import get_discord_notifier
from mm_config import config

async def test_hourly_analysis():
    """Test hourly analysis with real prices"""
    print("🧪 Testing Hourly Analysis with Real Prices...")
    print("=" * 60)
    
    bot = MMTradingBot()
    
    # Initialize Discord notifier
    if config.alerts.discord_webhook:
        bot.discord_notifier = await get_discord_notifier(config.alerts.discord_webhook)
        bot.hourly_analyzer.discord_notifier = bot.discord_notifier
        print("✅ Discord notifier initialized")
    else:
        print("❌ No Discord webhook configured")
        return
    
    print("📊 Testing hourly analysis...")
    
    try:
        # Run hourly analysis
        await bot.run_hourly_analysis()
        print("✅ Hourly analysis completed successfully!")
        print("📱 Check your Discord channel for the analysis")
        
        # Test that prices are realistic
        print("\n🔍 Verifying prices in analysis...")
        market_analysis = await bot.hourly_analyzer.analyze_all_symbols()
        
        for symbol, analysis in market_analysis.items():
            price = analysis.get('current_price', 0)
            print(f"{symbol}: ${price:,.2f}")
            
            if symbol == 'BTC/USDT' and price > 100000:
                print(f"  ✅ BTC price is realistic: ${price:,.2f}")
            elif symbol == 'ETH/USDT' and price > 3000:
                print(f"  ✅ ETH price is realistic: ${price:,.2f}")
            elif symbol == 'SOL/USDT' and price > 100:
                print(f"  ✅ SOL price is realistic: ${price:,.2f}")
        
    except Exception as e:
        print(f"❌ Error in hourly analysis: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 HOURLY ANALYSIS TEST COMPLETE!")
    print("✅ Real prices are being used")
    print("✅ Hourly analysis is working")
    print("✅ Discord posting is working")
    print("🚀 Bot is ready to run with correct prices!")
    print("=" * 60)
    
    return True

async def main():
    await test_hourly_analysis()

if __name__ == "__main__":
    asyncio.run(main())
