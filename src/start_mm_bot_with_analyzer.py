#!/usr/bin/env python3
"""
Start MM Trading Bot with Hourly Market Analyzer
Launches the complete system with hourly Discord analysis
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from mm_trading_bot import MMTradingBot

def print_banner():
    """Print startup banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║              ENHANCED MM TRADING BOT + ANALYZER              ║
    ║                                                              ║
    ║  🎯 Market Maker Detection & Trading                         ║
    ║  📊 Hourly Market Analysis (15m, 1h, 4h bias)               ║
    ║  💰 Automated Trading System                                ║
    ║  🚨 Real-time Discord Alerts & Analysis                     ║
    ║                                                              ║
    ║  Features:                                                   ║
    ║  • MM Pattern Detection (Iceberg, Spoofing, Layering)       ║
    ║  • Automated Trade Execution                                ║
    ║  • Hourly Market Analysis with TradingView Links            ║
    ║  • Volatility Forecasts & Best Trading Times                ║
    ║  • Real-time Portfolio & P&L Tracking                       ║
    ║  • Professional Discord Alerts                              ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

async def main():
    """Main function"""
    print_banner()
    
    print("🚀 Starting Enhanced MM Trading Bot with Hourly Analyzer...")
    print("📊 Will provide hourly market analysis with 15m, 1h, 4h bias")
    print("💰 Automated trading based on MM pattern detection")
    print("📱 Discord alerts for trades, patterns, and hourly analysis")
    print("🔗 TradingView links for all symbols")
    print("\nPress Ctrl+C to stop the bot")
    print("=" * 60)
    
    try:
        bot = MMTradingBot()
        await bot.start()
    except KeyboardInterrupt:
        print("\n\n⏹️  Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logging.error(f"Bot error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
