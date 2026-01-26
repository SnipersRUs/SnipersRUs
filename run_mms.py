#!/usr/bin/env python3
"""
Run script for MMS trading system
"""
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

def main():
    """Main entry point"""
    print("🚀 Starting MMS Trading System")
    print("=" * 50)
    
    try:
        # Import and run the main system
        from src.main import run
        run()
    except KeyboardInterrupt:
        print("\n⏹️ System stopped by user")
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()













































