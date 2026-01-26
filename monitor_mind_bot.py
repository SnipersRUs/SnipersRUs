#!/usr/bin/env python3
"""
Third Eye Bot Monitor
Simple monitoring script to check bot status and restart if needed
"""

import subprocess
import time
import os
import sys
from datetime import datetime

def check_bot_running():
    """Check if the mind_bot.py process is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'mind_bot.py'],
                              capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except Exception as e:
        print(f"Error checking bot status: {e}")
        return False

def get_bot_pid():
    """Get the PID of the running bot"""
    try:
        result = subprocess.run(['pgrep', '-f', 'mind_bot.py'],
                              capture_output=True, text=True)
        pids = result.stdout.strip().split('\n')
        return [pid for pid in pids if pid]
    except Exception as e:
        print(f"Error getting bot PID: {e}")
        return []

def restart_bot():
    """Restart the mind bot"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Restarting Third Eye Bot...")

    # Kill existing processes
    pids = get_bot_pid()
    for pid in pids:
        try:
            subprocess.run(['kill', pid], check=True)
            print(f"Killed process {pid}")
        except Exception as e:
            print(f"Error killing PID {pid}: {e}")

    time.sleep(2)

    # Start new process
    try:
        os.chdir('/Users/bishop/Documents/GitHub/SnipersRUs')
        subprocess.Popen(['nohup', 'python3', 'mind_bot.py'],
                        stdout=open('mind_bot.log', 'a'),
                        stderr=subprocess.STDOUT)
        print("Third Eye Bot restarted successfully!")
        return True
    except Exception as e:
        print(f"Error restarting bot: {e}")
        return False

def monitor_bot():
    """Main monitoring loop"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Third Eye Bot Monitor...")

    while True:
        if not check_bot_running():
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bot not running! Restarting...")
            restart_bot()
        else:
            pids = get_bot_pid()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bot running (PID: {', '.join(pids)})")

        # Check every 5 minutes
        time.sleep(300)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--restart":
        restart_bot()
    elif len(sys.argv) > 1 and sys.argv[1] == "--status":
        if check_bot_running():
            pids = get_bot_pid()
            print(f"Third Eye Bot is running (PID: {', '.join(pids)})")
        else:
            print("Third Eye Bot is not running")
    else:
        try:
            monitor_bot()
        except KeyboardInterrupt:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitor stopped by user")
            sys.exit(0)























