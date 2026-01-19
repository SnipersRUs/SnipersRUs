#!/usr/bin/env python3
"""
Test Discord webhook integration
"""
import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from discord_integration import DiscordNotifier
from mm_config import config

async def test_discord_webhook():
    """Test Discord webhook functionality"""
    print("🧪 Testing Discord webhook integration...")
    
    if not config.alerts.discord_webhook:
        print("❌ No Discord webhook configured")
        return False
    
    print(f"📡 Webhook URL: {config.alerts.discord_webhook[:50]}...")
    
    async with DiscordNotifier(config.alerts.discord_webhook) as notifier:
        # Test basic webhook
        print("🔗 Testing basic webhook connectivity...")
        success = await notifier.test_webhook()
        
        if success:
            print("✅ Basic webhook test passed!")
            
            # Test trade alert
            print("📊 Testing trade alert...")
            trade_data = {
                'symbol': 'BTC/USDT',
                'direction': 'LONG',
                'entry_price': 45000.0,
                'stop_loss': 44000.0,
                'take_profits': [46000.0, 47000.0, 48000.0],
                'risk_reward': 2.0,
                'position_size': 1000.0,
                'leverage': 10,
                'mm_confidence': 75.0,
                'setup_reason': 'Iceberg orders detected with H1 bias alignment',
                'mm_patterns': '🧊 Iceberg | 🎭 Spoofing',
                'volume_analysis': 'SPIKE'
            }
            
            await notifier.send_trade_alert(trade_data)
            print("✅ Trade alert sent!")
            
            # Test flush alert
            print("💥 Testing flush alert...")
            flush_data = {
                'symbol': 'ETH/USDT',
                'type': 'BEARISH_FLUSH',
                'strength': 85.0,
                'price_change': -0.045,
                'volume_spike': 2.5,
                'trade_imbalance': -12
            }
            
            await notifier.send_flush_alert(flush_data)
            print("✅ Flush alert sent!")
            
            # Test portfolio update
            print("📈 Testing portfolio update...")
            portfolio_data = {
                'balance': 10000.0,
                'unrealized_pnl': 250.0,
                'total_balance': 10250.0,
                'daily_pnl': 500.0,
                'open_positions': 2,
                'total_trades': 15,
                'win_rate': 73.3
            }
            
            await notifier.send_portfolio_update(portfolio_data)
            print("✅ Portfolio update sent!")
            
            print("\n🎉 All Discord tests passed! Your webhook is working correctly.")
            return True
        else:
            print("❌ Basic webhook test failed!")
            return False

async def main():
    """Main test function"""
    print("=" * 60)
    print("DISCORD WEBHOOK TEST")
    print("=" * 60)
    
    success = await test_discord_webhook()
    
    if success:
        print("\n✅ Discord integration is working perfectly!")
        print("You can now run the main bot with: python run_mm_bot.py")
    else:
        print("\n❌ Discord integration failed!")
        print("Please check your webhook URL and try again.")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

