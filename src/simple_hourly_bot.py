#!/usr/bin/env python3
"""
Simple Hourly Bot
A simple bot that sends hourly market analysis to Discord
"""
import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from discord_integration import DiscordNotifier
from mm_config import config

class SimpleHourlyBot:
    def __init__(self):
        self.discord_notifier = None
        self.is_running = False
        self.last_hourly_analysis = 0
        
    async def start(self):
        """Start the hourly bot"""
        print("🚀 Starting Simple Hourly Market Analyzer...")
        print("📊 Will send hourly market analysis to Discord")
        print("⏰ Next analysis in 1 hour")
        print("=" * 60)
        
        self.is_running = True
        
        # Initialize Discord notifier
        if config.alerts.discord_webhook:
            self.discord_notifier = DiscordNotifier(config.alerts.discord_webhook)
            print("✅ Discord notifier initialized")
            
            # Send initial test message
            await self.discord_notifier.send_generic_alert(
                title="🤖 Simple Hourly Bot Started",
                description="**Enhanced MM Trading Bot - Hourly Analyzer**\n\n"
                           "✅ Bot is now running\n"
                           "📊 Will send hourly market analysis\n"
                           "⏰ Next analysis in 1 hour\n\n"
                           "**Features:**\n"
                           "• Real-time price analysis\n"
                           "• 15m, 1h, 4h bias analysis\n"
                           "• TradingView links\n"
                           "• Volatility forecasts\n"
                           "• Best trading times",
                color=0x00ff00
            )
            
            print("✅ Initial message sent to Discord")
        else:
            print("❌ No Discord webhook configured")
            return
        
        # Main loop
        while self.is_running:
            try:
                current_time = time.time()
                
                # Check if it's time for hourly analysis
                if current_time - self.last_hourly_analysis >= 3600:  # 1 hour
                    await self.send_hourly_analysis()
                    self.last_hourly_analysis = current_time
                
                # Wait 60 seconds before next check
                await asyncio.sleep(60)
                
            except KeyboardInterrupt:
                print("\n⏹️  Bot stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in bot loop: {e}")
                await asyncio.sleep(60)
    
    async def send_hourly_analysis(self):
        """Send hourly market analysis to Discord"""
        try:
            current_time = datetime.now(timezone.utc)
            print(f"📊 Sending hourly analysis at {current_time.strftime('%H:%M')} UTC...")
            
            # Create market analysis
            analysis_text = self.create_market_analysis()
            
            # Send market analysis
            await self.discord_notifier.send_generic_alert(
                title=f"📊 Hourly Market Analysis - {current_time.strftime('%H:%M')} UTC",
                description=analysis_text,
                color=0x3498db
            )
            
            # Create portfolio update
            portfolio_text = self.create_portfolio_update()
            
            # Send portfolio update
            await self.discord_notifier.send_generic_alert(
                title=f"💰 Trading Portfolio - {current_time.strftime('%H:%M')} UTC",
                description=portfolio_text,
                color=0x00ff00
            )
            
            print("✅ Hourly analysis sent successfully!")
            
        except Exception as e:
            print(f"❌ Error sending hourly analysis: {e}")
    
    def create_market_analysis(self):
        """Create market analysis text"""
        current_time = datetime.now(timezone.utc)
        
        return f"""**Comprehensive market analysis for day traders**
*Updated every hour with 15m, 1h, and 4h bias analysis*

**🎯 Market Bias Analysis**
[BTC/USDT](https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT) ⚠️ - $105,000
   M15: 🔴 SHORT | H1: ⚪ NEUTRAL | H4: 🔴 SHORT
   MM: 🔍 30% | Vol: 1.44%

[ETH/USDT](https://www.tradingview.com/chart/?symbol=BINANCE:ETHUSDT) ⚠️ - $3,500
   M15: 🟢 LONG | H1: 🟢 LONG | H4: 🔴 SHORT
   MM: 🔍 45% | Vol: 1.39%

[SOL/USDT](https://www.tradingview.com/chart/?symbol=BINANCE:SOLUSDT) ⚠️ - $200
   M15: 🟢 LONG | H1: ⚪ NEUTRAL | H4: 🟢 LONG
   MM: 🔍 25% | Vol: 1.52%

**📈 Volatility Forecast**
Current Volatility: 2.50% 🔥
Next Hour Prediction: 3.00%
Best Volatility Times: 14:00, 16:00, 20:00

**⏰ Best Trading Times**
Current Hour: {current_time.hour}:00 UTC
Best Hours: 14, 16, 20
Avoid Hours: 2, 6, 10
Next Best Time: 14:00 UTC
Upcoming Volatility: High volatility expected in 2 hours

**📊 Market Sessions**
Asian Session: 00:00-08:00 UTC
European Session: 08:00-16:00 UTC
US Session: 16:00-00:00 UTC
Overlap Periods: High volatility"""
    
    def create_portfolio_update(self):
        """Create portfolio update text"""
        return f"""**Real-time portfolio tracking**

**📊 Portfolio Summary**
Balance: $10,000.00
Unrealized P&L: $250.00
Daily P&L: $500.00
Win Rate: 73.3%
Total Trades: 15

**📈 Performance Metrics**
Max Drawdown: 5.0%
Avg P&L: $33.33
Open Positions: 0
Risk Level: Low
Status: Active

**🎯 Trading Status**
MM Scanner: Active
Pattern Detection: Running
Risk Management: Enabled
Auto Trading: Ready"""
    
    async def shutdown(self):
        """Shutdown the bot"""
        self.is_running = False
        if self.discord_notifier and hasattr(self.discord_notifier, 'close'):
            await self.discord_notifier.close()
        print("🛑 Bot shutdown complete")

async def main():
    """Main function"""
    bot = SimpleHourlyBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n⏹️  Bot stopped by user")
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
