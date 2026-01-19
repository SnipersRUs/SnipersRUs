#!/usr/bin/env python3
"""
Test Vector Sniper Scanner
Simple test to validate the scanner functionality
"""

import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required modules can be imported"""
    try:
        import numpy as np
        import pandas as pd
        import requests
        import ccxt
        import asyncio
        from datetime import datetime, timezone
        from dataclasses import dataclass
        logger.info("✅ All required modules imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False

def test_scanner_import():
    """Test if the scanner module can be imported"""
    try:
        from vector_sniper_scanner import VectorSniperScanner, VectorSignal
        logger.info("✅ Vector Sniper scanner imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Scanner import error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    try:
        from vector_sniper_config import DISCORD_WEBHOOK, EXCHANGES, VECTOR_PARAMS
        logger.info("✅ Configuration loaded successfully")
        logger.info(f"Discord webhook configured: {bool(DISCORD_WEBHOOK)}")
        logger.info(f"Exchanges configured: {list(EXCHANGES.keys())}")
        return True
    except ImportError as e:
        logger.error(f"❌ Config import error: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🧪 Testing Vector Sniper Pro Scanner...")
    
    tests = [
        ("Module Imports", test_imports),
        ("Scanner Import", test_scanner_import),
        ("Configuration", test_config)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name} test...")
        if test_func():
            logger.info(f"✅ {test_name} test passed")
            passed += 1
        else:
            logger.error(f"❌ {test_name} test failed")
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Scanner is ready to use.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



















































