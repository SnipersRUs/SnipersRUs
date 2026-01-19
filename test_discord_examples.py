"""
Test Discord Examples - Shows what the bot posts look like
Run this to see example embeds in your Discord channel
"""

import os
import json
from datetime import datetime, timezone
import requests
import certifi
from dotenv import load_dotenv

load_dotenv()

WEBHOOK = os.getenv("WEBHOOK", "https://discord.com/api/webhooks/1429350060952391731/CncW1npyHocyY_6pu6csEQXKuVEYDfuchCefjNZT5uDLw4TCN9WDSOtKnBQ-ApXz5-wp").strip()
if not WEBHOOK:
    print("⚠️ No WEBHOOK found in .env file")
    print("Add: WEBHOOK=https://discord.com/api/webhooks/YOUR_WEBHOOK")
    exit(1)

# Colors
COLOR_WHITE = 0xFFFFFF
COLOR_BLUE = 0x1E90FF
COLOR_ORANGE = 0xFFA500
COLOR_RED = 0xCC3333
COLOR_GREEN = 0x00FF00

def tv_link(sym: str) -> str:
    """Generate TradingView link"""
    fmap = {
        "ES=F": "CME_MINI:ES1!",
        "NQ=F": "CME_MINI:NQ1!",
        "YM=F": "CBOT_MINI:YM1!",
        "CL=F": "NYMEX:CL1!",
        "GC=F": "COMEX:GC1!"
    }
    if sym in fmap:
        return f"https://www.tradingview.com/chart/?symbol={fmap[sym]}"
    if sym.endswith("=X"):
        return f"https://www.tradingview.com/chart/?symbol=OANDA:{sym.replace('=X', '')}"
    return f"https://www.tradingview.com/chart/?symbol={sym}"

def send_embeds(embeds):
    """Send embeds to Discord"""
    try:
        r = requests.post(WEBHOOK, json={"embeds": embeds}, timeout=15)
        if r.status_code in (200, 201, 204):
            print("✅ Posted to Discord!")
            return True
        else:
            print(f"❌ Error: {r.status_code} {r.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def example_regular_scan():
    """Example regular scan embeds (Monday-Friday)"""
    print("\n📤 Sending Example: Regular Scan (Top 3 Stocks + Futures + Forex)...")

    embeds = []

    # Stocks - Top 3
    embeds.append({
        "title": "Stocks — Top 3 Breakout Signals",
        "description": (
            "🟢 **AAPL** LONG • A+\n"
            "Entry: $178.50 | Stop: $175.20 | TP: $184.80\n"
            "R:R 2.50:1 • Confluence: 72/100\n"
            "[Chart](https://www.tradingview.com/chart/?symbol=AAPL)\n\n"

            "🔴 **TSLA** SHORT • A\n"
            "Entry: $245.30 | Stop: $248.90 | TP: $239.20\n"
            "R:R 2.30:1 • Confluence: 68/100\n"
            "[Chart](https://www.tradingview.com/chart/?symbol=TSLA)\n\n"

            "🟢 **NVDA** LONG • B\n"
            "Entry: $128.75 | Stop: $126.50 | TP: $132.80\n"
            "R:R 2.90:1 • Confluence: 58/100\n"
            "[Chart](https://www.tradingview.com/chart/?symbol=NVDA)"
        ),
        "color": COLOR_WHITE,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    # Futures
    embeds.append({
        "title": "Futures — Daily Breakout Pick",
        "description": (
            "🟢 **ES=F** LONG • A\n"
            "Entry: $5,845.50 | Stop: $5,820.00 | TP: $5,895.75\n"
            "R:R 2.60:1 • Confluence: 65/100\n"
            "[Chart](https://www.tradingview.com/chart/?symbol=CME_MINI:ES1!)"
        ),
        "color": COLOR_BLUE,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    # Forex
    embeds.append({
        "title": "Forex — Daily Breakout Pick",
        "description": (
            "🔴 **EURUSD=X** SHORT • A\n"
            "Entry: 1.08450 | Stop: 1.08720 | TP: 1.08010\n"
            "R:R 2.40:1 • Confluence: 70/100\n"
            "[Chart](https://www.tradingview.com/chart/?symbol=OANDA:EURUSD)"
        ),
        "color": COLOR_ORANGE,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    # Paper Trading Status
    embeds.append({
        "title": "Paper Trading Status",
        "fields": [
            {"name": "Balance", "value": "$10,245.50", "inline": True},
            {"name": "Open Positions", "value": "2", "inline": True},
            {"name": "Wins/Losses", "value": "8/3", "inline": True},
            {"name": "Realized PnL", "value": "$+245.50", "inline": True},
            {"name": "Unrealized PnL", "value": "$+89.20", "inline": True},
        ],
        "color": COLOR_GREEN,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return send_embeds(embeds)

def example_weekly_picks():
    """Example weekly picks embed (Sunday)"""
    print("\n📤 Sending Example: Weekly Picks (Sunday)...")

    week_start = "January 21, 2024"

    embed = {
        "title": "📅 Weekly Picks for Upcoming Week",
        "description": (
            f"**Week Starting:** {week_start}\n\n"
            "### 🎯 Weekly Picks (Swing Trades)\n\n"

            "🟢 **MSFT** LONG • A+\n"
            "Entry: $415.80 | Stop: $408.50 | TP: $432.20\n"
            "R:R 2.65:1 • Confluence: 75/100\n"
            "[Chart](https://www.tradingview.com/chart/?symbol=MSFT)\n\n"

            "🟢 **NQ=F** LONG • A\n"
            "Entry: $17,845.00 | Stop: $17,720.00 | TP: $18,095.00\n"
            "R:R 2.40:1 • Confluence: 68/100\n"
            "[Chart](https://www.tradingview.com/chart/?symbol=CME_MINI:NQ1!)\n\n"

            "🔴 **GBPUSD=X** SHORT • A\n"
            "Entry: 1.26850 | Stop: 1.27320 | TP: 1.25800\n"
            "R:R 2.30:1 • Confluence: 72/100\n"
            "[Chart](https://www.tradingview.com/chart/?symbol=OANDA:GBPUSD)"
        ),
        "color": COLOR_BLUE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "Weekly swing trades - Daily timeframe analysis"}
    }

    return send_embeds([embed])

def example_bot_startup():
    """Example bot startup notification"""
    print("\n📤 Sending Example: Bot Startup Notification...")

    embed = {
        "title": "🤖 Traditional Markets Bot Activated",
        "description": (
            "**Scan Interval:** Every 4.0 hours\n"
            "**Schedule:**\n"
            "- Monday-Friday: Regular scans\n"
            "- Saturday: Silent (no scans)\n"
            "- Sunday: Weekly picks generated\n"
            "\nBot is now running and will scan markets automatically."
        ),
        "color": COLOR_GREEN,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    return send_embeds([embed])

def example_position_closed():
    """Example position closed notification"""
    print("\n📤 Sending Example: Position Closed (Take Profit)...")

    embed = {
        "title": "🎉 Position Closed: AAPL LONG",
        "color": COLOR_GREEN,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": [
            {"name": "Reason", "value": "TAKE PROFIT", "inline": True},
            {"name": "Entry", "value": "$178.50", "inline": True},
            {"name": "Exit", "value": "$184.80", "inline": True},
            {"name": "PnL", "value": "$+157.50 (+2.5%)", "inline": True},
            {"name": "Balance", "value": "$10,157.50", "inline": True},
        ],
        "footer": {"text": "AAPL 1h • A+ signal"}
    }

    return send_embeds([embed])

def example_position_stop_loss():
    """Example stop loss notification"""
    print("\n📤 Sending Example: Position Closed (Stop Loss)...")

    embed = {
        "title": "🛑 Position Closed: TSLA SHORT",
        "color": COLOR_RED,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": [
            {"name": "Reason", "value": "STOP LOSS", "inline": True},
            {"name": "Entry", "value": "$245.30", "inline": True},
            {"name": "Exit", "value": "$248.90", "inline": True},
            {"name": "PnL", "value": "$-108.00 (-1.5%)", "inline": True},
            {"name": "Balance", "value": "$9,892.00", "inline": True},
        ],
        "footer": {"text": "TSLA 1h • A signal"}
    }

    return send_embeds([embed])

def example_all():
    """Send all examples"""
    print("\n" + "="*60)
    print("📬 Sending All Discord Examples")
    print("="*60)

    examples = [
        ("Bot Startup", example_bot_startup),
        ("Weekly Picks", example_weekly_picks),
        ("Regular Scan", example_regular_scan),
        ("Position Closed (TP)", example_position_closed),
        ("Position Closed (SL)", example_position_stop_loss),
    ]

    for name, func in examples:
        print(f"\n--- {name} ---")
        func()
        import time
        time.sleep(1)  # Small delay between posts

    print("\n" + "="*60)
    print("✅ All examples sent!")
    print("="*60)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "startup":
            example_bot_startup()
        elif cmd == "weekly":
            example_weekly_picks()
        elif cmd == "scan":
            example_regular_scan()
        elif cmd == "tp":
            example_position_closed()
        elif cmd == "sl":
            example_position_stop_loss()
        elif cmd == "all":
            example_all()
        else:
            print(f"Unknown command: {cmd}")
            print("\nUsage:")
            print("  python test_discord_examples.py [startup|weekly|scan|tp|sl|all]")
    else:
        print("📬 Discord Example Posts")
        print("="*60)
        print("\nUsage:")
        print("  python test_discord_examples.py startup  # Bot startup notification")
        print("  python test_discord_examples.py weekly  # Weekly picks example")
        print("  python test_discord_examples.py scan     # Regular scan example")
        print("  python test_discord_examples.py tp       # Take profit example")
        print("  python test_discord_examples.py sl       # Stop loss example")
        print("  python test_discord_examples.py all       # Send all examples")
        print("\nOr run with no args to see this help.")
