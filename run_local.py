#!/usr/bin/env python3
"""
Local Development Server
Run the trading bot API locally for testing
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

def main():
    """Run the local development server"""
    print("🚀 Starting Bybit Trading Bot API (Local Development)")
    print("=" * 60)
    
    # Load environment variables
    if os.path.exists('.env'):
        load_dotenv()
        print("✅ Environment variables loaded from .env")
    else:
        print("⚠️  No .env file found. Using system environment variables.")
    
    # Check if API credentials are set
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    
    if not api_key or not api_secret or api_key == 'your_bybit_api_key_here':
        print("❌ Bybit API credentials not set!")
        print("   Please run: python setup_bybit_bot.py")
        print("   Or set BYBIT_API_KEY and BYBIT_API_SECRET environment variables")
        sys.exit(1)
    
    # Show configuration
    print(f"📊 Configuration:")
    print(f"   Paper Trading: {os.getenv('BYBIT_PAPER_TRADING', 'true')}")
    print(f"   Testnet: {os.getenv('BYBIT_TESTNET', 'true')}")
    print(f"   Live Trading: {os.getenv('BYBIT_LIVE_TRADING', 'false')}")
    print(f"   Discord Webhook: {'Set' if os.getenv('DISCORD_WEBHOOK') else 'Not Set'}")
    
    print(f"\n🌐 Server will be available at:")
    print(f"   http://localhost:8000")
    print(f"   http://localhost:8000/docs (API Documentation)")
    print(f"   http://localhost:8000/health (Health Check)")
    
    print(f"\n📋 Available Endpoints:")
    print(f"   GET  /status     - Bot status")
    print(f"   POST /start      - Start trading bot")
    print(f"   POST /stop       - Stop trading bot")
    print(f"   GET  /account    - Account information")
    print(f"   GET  /trades     - Active trades")
    
    print(f"\n⚠️  Safety Notice:")
    print(f"   - Bot starts in PAPER TRADING mode")
    print(f"   - No real money will be used")
    print(f"   - Perfect for testing strategies")
    
    print(f"\n🚀 Starting server...")
    print("=" * 60)
    
    try:
        # Run the server
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,  # Enable auto-reload for development
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
