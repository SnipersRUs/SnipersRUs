#!/usr/bin/env python3
"""
Bot Analyzer - Analyzes and provides information about existing trading bots
"""
import os
import subprocess
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent

# Bot definitions with their characteristics
BOT_INFO = {
    "short_sniper": {
        "name": "Short Sniper Bot",
        "file": "short_sniper_bot.py",
        "description": "SHORT-ONLY trading bot that identifies coins at local resistances",
        "features": ["Deviation VWAP zones", "GPS resistance", "Liquidation reversal", "Order blocks"],
        "timeframes": ["15m", "1h", "4h"],
        "focus": "Short trades only"
    },
    "pivotx": {
        "name": "PivotX Scanner Bot",
        "file": "pivotx_scanner_bot.py",
        "description": "Detects pivot points and pullback setups across multiple timeframes",
        "features": ["Multi-timeframe scanning", "Pullback detection", "A+ setup detection"],
        "timeframes": ["5m", "15m", "1H"],
        "focus": "Pivot detection and pullbacks"
    },
    "mcro": {
        "name": "Macro Huntr Bot",
        "file": "mcro_bot.py",
        "description": "High-precision scanner for A and A+ setups only",
        "features": ["GPS", "Tactical Deviation", "PivotX Pro", "3-Wave Pullback"],
        "timeframes": ["15m", "1h", "4h"],
        "focus": "Top 50 cryptos, A/A+ setups"
    },
    "cloudflare": {
        "name": "Cloudflare Bot",
        "file": "cloudflare_discord_bot.py",
        "description": "Market sentiment scanner with dynamic cloud system",
        "features": ["Dynamic cloud system", "Diamond signals", "Multi-timeframe VWAP"],
        "timeframes": ["Multiple"],
        "focus": "Market sentiment and reversals"
    },
    "liquidation": {
        "name": "Liquidation Scanner Bot",
        "file": "liquidation_scanner_bot.py",
        "description": "Scans for liquidation events and reversal opportunities",
        "features": ["Liquidation detection", "Reversal signals"],
        "timeframes": ["Multiple"],
        "focus": "Liquidation reversals"
    },
    "traditional": {
        "name": "Traditional Markets Bot",
        "file": "traditional_markets_bot.py",
        "description": "Scans stocks, futures, and forex markets",
        "features": ["GPS signals", "Head Hunter", "Oath Keeper"],
        "timeframes": ["Daily", "4-hour"],
        "focus": "Traditional markets (stocks, futures, forex)"
    },
    "forex": {
        "name": "Forex Pivot Reversal Bot",
        "file": "forex_pivot_reversal_bot.py",
        "description": "Forex trading bot with pivot reversal detection",
        "features": ["Pivot detection", "Reversal signals"],
        "timeframes": ["Multiple"],
        "focus": "Forex markets"
    }
}

def check_bot_status(bot_name: str) -> Dict:
    """Check if a bot is currently running"""
    bot_info = BOT_INFO.get(bot_name)
    if not bot_info:
        return {"running": False, "error": "Bot not found"}

    bot_file = bot_info.get("file")
    bot_path = PROJECT_ROOT / bot_file

    # Check if bot file exists
    if not bot_path.exists():
        return {"running": False, "error": "Bot file not found"}

    # Check if process is running
    try:
        result = subprocess.run(
            ["pgrep", "-f", bot_file],
            capture_output=True,
            text=True,
            timeout=2
        )
        is_running = result.returncode == 0
    except Exception:
        is_running = False

    # Check for log files
    log_file = PROJECT_ROOT / f"{bot_file.replace('.py', '.log')}"
    has_log = log_file.exists()

    # Check for database/state files
    db_files = [
        PROJECT_ROOT / f"{bot_name}_trades.db",
        PROJECT_ROOT / "trades.db",
        PROJECT_ROOT / f"{bot_name}_state.json",
    ]
    has_db = any(db.exists() for db in db_files)

    return {
        "running": is_running,
        "file_exists": True,
        "has_log": has_log,
        "has_db": has_db,
        "bot_info": bot_info
    }

def get_bot_trades(bot_name: str, limit: int = 5) -> List[Dict]:
    """Get recent trades from bot database"""
    trades = []

    # Try different database file names
    db_files = [
        PROJECT_ROOT / f"{bot_name}_trades.db",
        PROJECT_ROOT / "trades.db",
        PROJECT_ROOT / f"{bot_name}.db",
    ]

    for db_file in db_files:
        if db_file.exists():
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()

                # Try to get trades (table name might vary)
                for table in ["trades", "positions", "signals"]:
                    try:
                        cursor.execute(f"SELECT * FROM {table} ORDER BY timestamp DESC LIMIT ?", (limit,))
                        rows = cursor.fetchall()
                        if rows:
                            # Get column names
                            columns = [description[0] for description in cursor.description]
                            for row in rows:
                                trades.append(dict(zip(columns, row)))
                            break
                    except sqlite3.OperationalError:
                        continue

                conn.close()
                if trades:
                    break
            except Exception as e:
                logger.warning(f"Error reading {db_file}: {e}")
                continue

    return trades[:limit]

def get_bot_summary(bot_name: str) -> str:
    """Get a summary of bot information"""
    bot_info = BOT_INFO.get(bot_name)
    if not bot_info:
        return f"❌ Bot '{bot_name}' not found."

    status = check_bot_status(bot_name)

    summary = f"**{bot_info['name']}**\n\n"
    summary += f"📝 **Description:** {bot_info['description']}\n"
    summary += f"🎯 **Focus:** {bot_info['focus']}\n\n"

    summary += "**Features:**\n"
    for feature in bot_info['features']:
        summary += f"- {feature}\n"

    summary += f"\n**Timeframes:** {', '.join(bot_info['timeframes'])}\n\n"

    summary += "**Status:**\n"
    summary += f"- Running: {'✅ Yes' if status['running'] else '❌ No'}\n"
    summary += f"- Log file: {'✅ Exists' if status['has_log'] else '❌ Not found'}\n"
    summary += f"- Database: {'✅ Exists' if status['has_db'] else '❌ Not found'}\n"

    return summary



