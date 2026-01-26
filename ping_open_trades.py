#!/usr/bin/env python3
"""Quick script to ping Discord with open trades"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bounty_seeker_kcex import BountySeekerV5

# Get webhook
webhook = os.getenv("DISCORD_WEBHOOK", "").strip()
if not webhook and os.path.exists(".webhook"):
    try:
        webhook = open(".webhook").read().strip()
    except:
        pass

if not webhook:
    print("No webhook found!")
    sys.exit(1)

bot = BountySeekerV5(webhook_url=webhook)
bot._send_open_trades_ping()
print("Open trades ping sent!")







