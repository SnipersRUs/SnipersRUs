#!/usr/bin/env python3
"""
MCRO Bot Runner
Simple script to start the MCRO bot with proper error handling
"""

import sys
import os
import traceback

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from mcro_bot import main
    print("🚀 Starting MCRO Bot...")
    main()
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
except Exception as e:
    print(f"❌ Error starting MCRO Bot: {e}")
    traceback.print_exc()


















































