#!/usr/bin/env python3
"""
Test Real Prices
Test that the bot is using real current prices
"""
import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from mm_trading_bot import MMTradingBot

async def test_real_prices():
    """Test that real prices are being used"""
    print("🧪 Testing Real Prices...")
    print("=" * 50)
    
    bot = MMTradingBot()
    
    # Test BTC price
    print("📊 Testing BTC/USDT price...")
    spot_data, futures_data = await bot.get_market_data('BTC/USDT')
    current_price = spot_data.get('current_price', 0)
    
    print(f"Current BTC Price: ${current_price:,.2f}")
    
    if current_price > 100000:
        print("✅ BTC price is realistic (>$100k)")
    else:
        print(f"❌ BTC price is too low: ${current_price:,.2f}")
        print("   Should be over $100,000")
    
    # Test ETH price
    print("\n📊 Testing ETH/USDT price...")
    spot_data, futures_data = await bot.get_market_data('ETH/USDT')
    current_price = spot_data.get('current_price', 0)
    
    print(f"Current ETH Price: ${current_price:,.2f}")
    
    if current_price > 3000:
        print("✅ ETH price is realistic (>$3k)")
    else:
        print(f"❌ ETH price is too low: ${current_price:,.2f}")
        print("   Should be over $3,000")
    
    print("\n" + "=" * 50)
    print("🎉 Price test complete!")

async def main():
    await test_real_prices()

if __name__ == "__main__":
    asyncio.run(main())
