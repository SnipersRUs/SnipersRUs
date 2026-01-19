#!/usr/bin/env python3
"""
Simple logger module for MMS trading system
Provides info and err functions for logging
"""
import logging
import sys
from datetime import datetime

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def info(*args):
    """Log info message"""
    message = ' '.join(str(arg) for arg in args)
    logger.info(message)

def err(*args):
    """Log error message"""
    message = ' '.join(str(arg) for arg in args)
    logger.error(message)













































