#!/usr/bin/env python3
"""
Runner script for the Enhanced Scanner Webhook
"""
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_scanner_webhook import main_loop

if __name__ == "__main__":
    print("🚀 Starting Enhanced Scanner Webhook...")
    main_loop()