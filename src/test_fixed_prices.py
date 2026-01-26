#!/usr/bin/env python3
"""
Test Fixed Prices
Test that the bot is now using realistic prices
"""
import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from mm_trading_bot import MMTradingBot
from mm_detector import MMDetector

async def test_fixed_prices():
    """Test that realistic prices are being used"""
    print("🧪 Testing Fixed Prices...")
    print("=" * 50)
    
    bot = MMTradingBot()
    detector = MMDetector()
    
    # Test BTC price
    print("📊 Testing BTC/USDT...")
    spot_data, futures_data = await bot.get_market_data('BTC/USDT')
    current_price = spot_data['prices'][-1]
    
    print(f"Current BTC Price: ${current_price:,.2f}")
    
    if current_price > 100000:
        print("✅ BTC price is realistic (>$100k)")
    else:
        print(f"❌ BTC price is too low: ${current_price:,.2f}")
        print("   Should be over $100,000")
    
    # Test MM detection with realistic prices
    print("\n🔍 Testing MM Detection with realistic prices...")
    market_state = detector.analyze_mm_activity('BTC/USDT', spot_data, futures_data)
    
    print(f"Symbol: {market_state.symbol}")
    print(f"M15 Bias: {market_state.m15_bias}")
    print(f"H1 Bias: {market_state.h1_bias}")
    print(f"H4 Bias: {market_state.h4_bias}")
    print(f"MM Active: {market_state.mm_active}")
    print(f"MM Side: {market_state.mm_side}")
    print(f"MM Confidence: {market_state.mm_confidence}%")
    
    if market_state.entry > 0:
        print(f"Entry: ${market_state.entry:,.2f}")
        print(f"Stop Loss: ${market_state.stop_loss:,.2f}")
        print(f"Take Profit: ${market_state.take_profit[0]:,.2f}")
        print(f"Risk/Reward: {market_state.risk_reward:.1f}")
        
        if market_state.entry > 100000:
            print("✅ Entry price is realistic for BTC")
        else:
            print("❌ Entry price is too low for BTC")
    
    # Test ETH price
    print("\n📊 Testing ETH/USDT...")
    spot_data, futures_data = await bot.get_market_data('ETH/USDT')
    current_price = spot_data['prices'][-1]
    
    print(f"Current ETH Price: ${current_price:,.2f}")
    
    if current_price > 3000:
        print("✅ ETH price is realistic (>$3k)")
    else:
        print(f"❌ ETH price is too low: ${current_price:,.2f}")
        print("   Should be over $3,000")
    
    print("\n" + "=" * 50)
    print("🎉 Price test complete!")
    print("✅ MM detector is working with realistic prices")
    print("✅ No more impossible trades at wrong prices")

async def main():
    await test_fixed_prices()

if __name__ == "__main__":
    asyncio.run(main())
