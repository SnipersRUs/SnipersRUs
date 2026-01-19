#!/usr/bin/env python3
"""
Test Hourly Market Analysis Discord Post
Send a sample hourly analysis to Discord
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from hourly_market_analyzer import HourlyMarketAnalyzer
from discord_integration import get_discord_notifier, cleanup_discord_notifier
from mm_config import config

async def test_hourly_discord():
    """Test posting hourly analysis to Discord"""
    print("📤 Testing Hourly Market Analysis Discord Post...")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = HourlyMarketAnalyzer()
    
    # Initialize Discord notifier
    if config.alerts.discord_webhook:
        discord_notifier = await get_discord_notifier(config.alerts.discord_webhook)
        
        try:
            # Generate sample market analysis
            print("📊 Generating sample market analysis...")
            market_analysis = await analyzer.analyze_all_symbols()
            
            # Generate sample volatility forecast
            volatility_forecast = await analyzer.predict_volatility()
            
            # Generate sample best trading times
            best_times = await analyzer.identify_best_trading_times()
            
            # Get trading status
            trading_status = analyzer.get_trading_status()
            
            current_time = datetime.now(timezone.utc)
            
            # Send market update
            print("📤 Sending market update to Discord...")
            await analyzer.send_market_update(
                market_analysis, 
                volatility_forecast, 
                best_times, 
                trading_status,
                current_time
            )
            
            # Send portfolio card
            print("📤 Sending portfolio card to Discord...")
            await analyzer.send_portfolio_card(trading_status, current_time)
            
            print("✅ Sample hourly analysis posted to Discord!")
            print("🎉 Check your Discord channel for the analysis")
            
        except Exception as e:
            print(f"❌ Error posting to Discord: {e}")
        finally:
            await cleanup_discord_notifier()
    else:
        print("❌ No Discord webhook configured")

async def main():
    """Main test function"""
    await test_hourly_discord()

if __name__ == "__main__":
    asyncio.run(main())
