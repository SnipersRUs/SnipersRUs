#!/usr/bin/env python3
"""
Liquidation Scanner Bot Runner
Simple runner script for the liquidation scanner bot
"""

import asyncio
import logging
from liquidation_scanner_bot import LiquidationScanner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main runner function"""
    logger.info("🚀 Starting Liquidation Scanner Bot...")

    try:
        # Initialize scanner
        scanner = LiquidationScanner()

        # Run single scan
        logger.info("🔍 Running single scan...")
        levels = await scanner.run_scan()

        logger.info(f"✅ Scan completed! Found {len(levels)} approaching liquidations")

        # Print level summary
        if levels:
            logger.info("\n📊 LIQUIDATION LEVELS SUMMARY:")
            for i, level in enumerate(levels[:20], 1):  # Show top 20
                logger.info(
                    f"{i}. {level.symbol} ({level.exchange}) - {level.timeframe} - "
                    f"{level.type.upper()} @ ${level.level:.4f} - "
                    f"Distance: {level.distance_pct:.2f}% - Importance: {level.importance:.0f}%"
                )
        else:
            logger.info("No approaching liquidations found in this scan")

        logger.info("🎯 Scanner test completed successfully!")

    except Exception as e:
        logger.error(f"❌ Scanner error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
