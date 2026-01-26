#!/usr/bin/env python3
"""
Enhanced Market Maker Trading Bot - Main Entry Point
Run this script to start the comprehensive MM detection and trading system
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from mm_trading_bot import MMTradingBot
from mm_config import config
import logging

def setup_logging():
    """Setup comprehensive logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mm_bot.log'),
            logging.StreamHandler()
        ]
    )

def print_banner():
    """Print startup banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                ENHANCED MM TRADING BOT                       ║
    ║                                                              ║
    ║  🎯 Advanced Market Maker Detection                          ║
    ║  💰 Automated Trading System                                ║
    ║  📊 Comprehensive Risk Management                            ║
    ║  🚨 Real-time Alerts & Monitoring                           ║
    ║                                                              ║
    ║  Features:                                                   ║
    ║  • Iceberg Order Detection                                  ║
    ║  • Spoofing Pattern Recognition                             ║
    ║  • Layering Analysis                                        ║
    ║  • Major Flush Alerts                                       ║
    ║  • Multi-timeframe Bias Analysis                            ║
    ║  • Automated Position Management                             ║
    ║  • Detailed Trading Cards                                   ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def print_config_summary():
    """Print current configuration summary"""
    print("\n📋 CONFIGURATION SUMMARY:")
    print("-" * 50)
    print(f"Account Balance: ${config.trading.initial_balance:,.2f}")
    print(f"Position Size: ${config.trading.position_size:,.2f}")
    print(f"Max Risk per Trade: {config.trading.max_risk_per_trade:.1%}")
    print(f"Max Daily Loss: {config.trading.max_daily_loss:.1%}")
    print(f"Max Open Positions: {config.trading.max_open_positions}")
    print(f"Divergence Threshold: {config.thresholds.divergence_threshold}")
    print(f"MM Confidence Threshold: {config.thresholds.mm_confidence_threshold}")
    print(f"M15 Enabled: {config.thresholds.m15_enabled}")
    print(f"Priority Symbols: {len(config.symbols.priority_symbols)}")
    print("-" * 50)

def validate_environment():
    """Validate environment and configuration"""
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append("Python 3.8+ required")
    
    # Check required modules
    try:
        import numpy
        import pandas
    except ImportError as e:
        issues.append(f"Missing required module: {e}")
    
    # Validate configuration
    config_issues = config.validate_config()
    if config_issues:
        issues.extend(config_issues)
    
    if issues:
        print("❌ ENVIRONMENT VALIDATION FAILED:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    
    print("✅ Environment validation passed")
    return True

async def main():
    """Main function"""
    print_banner()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Validate environment
    if not validate_environment():
        print("\n❌ Please fix the issues above before running the bot")
        sys.exit(1)
    
    # Print configuration
    print_config_summary()
    
    # Confirm startup
    print("\n🚀 Starting Enhanced MM Trading Bot...")
    print("Press Ctrl+C to stop the bot gracefully")
    
    try:
        # Create and start bot
        bot = MMTradingBot()
        await bot.start()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Bot stopped by user")
        logger.info("Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")
        logger.error(f"Bot error: {e}")
        sys.exit(1)
    finally:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    # Check if running in correct directory
    if not os.path.exists("src"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Run the bot
    asyncio.run(main())

