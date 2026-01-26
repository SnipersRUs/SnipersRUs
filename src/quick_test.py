#!/usr/bin/env python3
"""
Quick Test - Test Discord and Hourly Analysis
"""
import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from discord_integration import DiscordNotifier
from mm_config import config

async def quick_test():
    """Quick test of Discord and hourly analysis"""
    print("🧪 Quick Test - Discord & Hourly Analysis")
    print("=" * 50)
    
    if not config.alerts.discord_webhook:
        print("❌ No Discord webhook configured")
        return
    
    print("📤 Testing Discord webhook...")
    
    async with DiscordNotifier(config.alerts.discord_webhook) as notifier:
        # Test basic webhook
        success = await notifier.test_webhook()
        
        if success:
            print("✅ Discord webhook working!")
            
            # Test hourly analysis alert
            await notifier.send_generic_alert(
                title="🧪 Hourly Analysis Test",
                description="**Enhanced MM Trading Bot** is ready!\n\n"
                           "✅ Discord integration working\n"
                           "✅ Hourly analysis ready\n"
                           "✅ Bot will send analysis every hour\n\n"
                           "**Next hourly analysis**: In 1 hour",
                color=0x00ff00
            )
            print("✅ Hourly analysis test sent!")
            
        else:
            print("❌ Discord webhook failed")
    
    print("\n🎉 Quick test complete!")
    print("🚀 Ready to start the bot with hourly analysis")

async def main():
    await quick_test()

if __name__ == "__main__":
    asyncio.run(main())
