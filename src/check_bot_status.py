#!/usr/bin/env python3
"""
Check Bot Status
Check if the MM trading bot is running and show status
"""
import subprocess
import sys

def check_bot_status():
    """Check if the bot is running"""
    print("🔍 Checking MM Trading Bot Status...")
    print("=" * 50)
    
    try:
        # Check for running Python processes
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        bot_processes = []
        for line in lines:
            if 'start_mm_bot' in line or 'mm_trading_bot' in line:
                bot_processes.append(line)
        
        if bot_processes:
            print("✅ MM Trading Bot is RUNNING!")
            print("\n📊 Running Processes:")
            for process in bot_processes:
                print(f"   {process}")
        else:
            print("❌ MM Trading Bot is NOT running")
            print("\n🚀 To start the bot:")
            print("   python3 start_mm_bot_with_analyzer.py")
        
        print("\n" + "=" * 50)
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")

if __name__ == "__main__":
    check_bot_status()
