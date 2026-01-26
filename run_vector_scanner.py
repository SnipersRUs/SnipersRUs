#!/usr/bin/env python3
"""
Vector Sniper Pro Scanner Runner
Simple runner script for the Vector Sniper Pro scanner
"""

import asyncio
import logging
from vector_sniper_scanner import VectorSniperScanner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main runner function"""
    logger.info("🚀 Starting Vector Sniper Pro Scanner...")
    
    try:
        # Initialize scanner
        scanner = VectorSniperScanner()
        
        # Run single scan
        logger.info("🔍 Running single scan...")
        signals = await scanner.run_scan()
        
        logger.info(f"✅ Scan completed! Found {len(signals)} signals")
        
        # Print signal summary
        if signals:
            logger.info("\n📊 SIGNAL SUMMARY:")
            for i, signal in enumerate(signals[:10], 1):  # Show top 10
                logger.info(f"{i}. {signal.symbol} ({signal.exchange}) - {signal.signal_type} {signal.direction} - {signal.confidence:.0f}%")
        else:
            logger.info("No signals found in this scan")
        
        logger.info("🎯 Scanner test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Scanner error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())



















































