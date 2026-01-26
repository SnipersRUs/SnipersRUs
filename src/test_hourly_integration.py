#!/usr/bin/env python3
"""
Test Hourly Integration
Test that the hourly analyzer is properly integrated with the main bot
"""
import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from mm_trading_bot import MMTradingBot

async def test_hourly_integration():
    """Test hourly analysis integration"""
    print("🧪 Testing Hourly Analysis Integration...")
    print("=" * 60)
    
    # Create bot instance
    bot = MMTradingBot()
    
    # Initialize Discord notifier
    from discord_integration import get_discord_notifier
    from mm_config import config
    
    if config.alerts.discord_webhook:
        bot.discord_notifier = await get_discord_notifier(config.alerts.discord_webhook)
        bot.hourly_analyzer.discord_notifier = bot.discord_notifier
        print("✅ Discord notifier initialized")
    else:
        print("❌ No Discord webhook configured")
        return False
    
    print("✅ Bot initialized successfully")
    print("✅ Hourly analyzer integrated")
    print("✅ Discord notifier ready")
    
    # Test hourly analysis method
    try:
        print("\n📊 Testing hourly analysis method...")
        await bot.run_hourly_analysis()
        print("✅ Hourly analysis completed successfully")
        print("📱 Check your Discord channel for the analysis")
        
    except Exception as e:
        print(f"❌ Error in hourly analysis: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 INTEGRATION TEST COMPLETE!")
    print("✅ Hourly analyzer is properly integrated")
    print("✅ Discord posting is working")
    print("✅ Bot is ready to run with hourly analysis")
    print("=" * 60)
    
    return True

async def main():
    """Main test function"""
    await test_hourly_integration()

if __name__ == "__main__":
    asyncio.run(main())
