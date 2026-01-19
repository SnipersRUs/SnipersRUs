#!/usr/bin/env python3
"""
Hourly Market Analyzer Launcher
Runs the hourly market analysis bot
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from hourly_market_analyzer import HourlyMarketAnalyzer

def print_banner():
    """Print startup banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║              HOURLY MARKET ANALYZER                          ║
    ║                                                              ║
    ║  📊 Comprehensive Market Analysis Every Hour                 ║
    ║  🎯 15m, 1h, and 4h Bias Analysis                           ║
    ║  ⏰ Best Trading Times & Volatility Forecasts               ║
    ║  💰 Real-time Portfolio & P&L Tracking                      ║
    ║                                                              ║
    ║  Features:                                                   ║
    ║  • Hourly market bias analysis                               ║
    ║  • Volatility predictions and forecasts                      ║
    ║  • Best trading times identification                         ║
    ║  • Portfolio status and P&L tracking                        ║
    ║  • Market session analysis                                   ║
    ║  • Key support/resistance levels                             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

async def main():
    """Main function"""
    print_banner()
    
    print("🚀 Starting Hourly Market Analyzer...")
    print("📊 Will provide comprehensive market analysis every hour")
    print("⏰ Analysis includes 15m, 1h, and 4h bias for day traders")
    print("💰 Separate portfolio cards with open trades and P&L")
    print("🎯 Volatility forecasts and best trading times")
    print("\nPress Ctrl+C to stop the analyzer")
    print("=" * 60)
    
    try:
        analyzer = HourlyMarketAnalyzer()
        await analyzer.start()
    except KeyboardInterrupt:
        print("\n\n⏹️  Hourly Market Analyzer stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logging.error(f"Hourly analyzer error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

