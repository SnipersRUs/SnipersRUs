#!/usr/bin/env python3
"""
Run script for Sniper Guru Bot
Usage examples:
- python3 run_sniper_guru.py --ping          # Send ping to Discord
- python3 run_sniper_guru.py --now           # Run analysis now
- python3 run_sniper_guru.py --now --post    # Run analysis and post to Discord
- python3 run_sniper_guru.py --loop          # Run in scheduled loop mode
- python3 run_sniper_guru.py --loop --post   # Run in loop mode with Discord posting
"""

import subprocess
import sys
import os

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bot_script = os.path.join(script_dir, "sniper_guru_bot.py")

    # Pass all arguments to the bot script
    cmd = ["python3", bot_script] + sys.argv[1:]

    try:
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"Error running bot: {e}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()



