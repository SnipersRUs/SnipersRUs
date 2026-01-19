#!/usr/bin/env python3
"""
Bybit Trading Bot Setup Script
Helps configure and test the Bybit trading bot before deployment
"""

import os
import sys
import asyncio
from bybit_config import validate_config, BYBIT_CONFIG
from bybit_golden_pocket_bot import BybitGoldenPocketBot

def setup_environment():
    """Setup environment variables"""
    print("🔧 Setting up Bybit Trading Bot...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("📝 Creating .env file from template...")
        with open('env.example', 'r') as f:
            template = f.read()
        with open('.env', 'w') as f:
            f.write(template)
        print("✅ .env file created. Please edit it with your API credentials.")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if API credentials are set
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    
    if not api_key or not api_secret or api_key == 'your_bybit_api_key_here':
        print("❌ Please set your Bybit API credentials in the .env file")
        print("   1. Get API key from Bybit.com → Account → API Management")
        print("   2. Edit .env file with your actual credentials")
        return False
    
    print("✅ Environment variables loaded")
    return True

async def test_connection():
    """Test connection to Bybit"""
    print("\n🔗 Testing connection to Bybit...")
    
    try:
        bot = BybitGoldenPocketBot()
        success = await bot.test_connection()
        
        if success:
            print("✅ Connection successful!")
            return True
        else:
            print("❌ Connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

async def test_trading_functions():
    """Test trading functions"""
    print("\n📊 Testing trading functions...")
    
    try:
        bot = BybitGoldenPocketBot()
        
        # Test account info
        print("   Testing account info...")
        account_info = await bot.get_account_info()
        if account_info:
            print("   ✅ Account info retrieved")
        else:
            print("   ❌ Failed to get account info")
            return False
        
        # Test market data
        print("   Testing market data...")
        ticker = await bot.exchange.get_ticker('BTCUSDT')
        if ticker:
            print(f"   ✅ Market data retrieved: BTC = ${ticker.get('lastPrice', 'N/A')}")
        else:
            print("   ❌ Failed to get market data")
            return False
        
        # Test Golden Pocket analysis
        print("   Testing Golden Pocket analysis...")
        signal = await bot.analyze_golden_pocket('BTCUSDT')
        if signal:
            print(f"   ✅ Signal generated: {signal.direction} {signal.symbol}")
        else:
            print("   ℹ️  No signal found (normal)")
        
        print("✅ All trading functions working!")
        return True
        
    except Exception as e:
        print(f"❌ Trading function error: {e}")
        return False

def check_dependencies():
    """Check if all dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'pandas', 'numpy', 
        'requests', 'asyncio', 'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed!")
    return True

def show_configuration():
    """Show current configuration"""
    print("\n⚙️  Current Configuration:")
    
    config_items = [
        ('Paper Trading', os.getenv('BYBIT_PAPER_TRADING', 'true')),
        ('Testnet', os.getenv('BYBIT_TESTNET', 'true')),
        ('Live Trading', os.getenv('BYBIT_LIVE_TRADING', 'false')),
        ('Discord Webhook', 'Set' if os.getenv('DISCORD_WEBHOOK') else 'Not Set'),
        ('Max Trades', os.getenv('MAX_OPEN_POSITIONS', '3')),
        ('Position Size', f"${os.getenv('BASE_POSITION_SIZE', '10.0')}"),
    ]
    
    for key, value in config_items:
        status = "✅" if value in ['true', 'Set'] else "⚠️" if value == 'false' else "❌"
        print(f"   {status} {key}: {value}")

async def main():
    """Main setup function"""
    print("🚀 Bybit Trading Bot Setup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Setup environment
    if not setup_environment():
        return
    
    # Show configuration
    show_configuration()
    
    # Test connection
    if not await test_connection():
        print("\n❌ Setup failed: Cannot connect to Bybit")
        print("   Please check your API credentials and internet connection")
        return
    
    # Test trading functions
    if not await test_trading_functions():
        print("\n❌ Setup failed: Trading functions not working")
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next Steps:")
    print("   1. Review your configuration above")
    print("   2. Test locally: python app.py")
    print("   3. Deploy to Railway: Follow RAILWAY_DEPLOYMENT_GUIDE.md")
    print("   4. Start trading: POST /start to your API")
    
    print("\n⚠️  Important:")
    print("   - Bot starts in PAPER TRADING mode by default")
    print("   - Set BYBIT_LIVE_TRADING=true only when ready for real money")
    print("   - Always test thoroughly before going live")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        sys.exit(1)
