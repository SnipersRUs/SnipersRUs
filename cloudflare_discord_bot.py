#!/usr/bin/env python3
"""
Cloudflare Indicator Discord Bot
Receives TradingView webhooks and sends optimized signals to Discord
Only processes BTC, SOL, and ETH signals
"""

from flask import Flask, request, jsonify
import requests
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
import re
import threading
import time
import ccxt
import pandas as pd
import numpy as np

# Configuration
DISCORD_WEBHOOK = ""

# Allowed symbols (case-insensitive)
ALLOWED_SYMBOLS = ["BTC", "SOL", "ETH", "BITCOIN", "SOLANA", "ETHEREUM"]
ALLOWED_SYMBOL_PATTERNS = [
    r"BTC",
    r"SOL",
    r"ETH",
    r"BITCOIN",
    r"SOLANA",
    r"ETHEREUM"
]

# Signal types mapping
LONG_SIGNALS = [
    "master_long",
    "master long",
    "bull confirmed",
    "bull confirmation",
    "bullish divergence",
    "golden cross",
    "vwap break above",
    "weekly vwap break above",
    "4d vwap break above",
    "liquidity flush bull"
]

SHORT_SIGNALS = [
    "master_short",
    "master short",
    "bear confirmed",
    "bear confirmation",
    "bearish divergence",
    "death cross",
    "vwap break below",
    "weekly vwap break below",
    "4d vwap break below",
    "liquidity flush bear"
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Store recent signals to batch them
signal_buffer: List[Dict] = []

# Track sent signals to prevent duplicates (symbol + signal_type + price_range)
sent_signals_cache: Dict[str, float] = {}  # key: "symbol_signaltype", value: timestamp
SIGNAL_CACHE_DURATION = 3600  # 1 hour - don't resend same signal within 1 hour

# Track active signals for invalidation/stop/TP monitoring
active_signals: Dict[str, Dict] = {}  # key: "symbol_signaltype_timestamp", value: signal data
STOP_LOSS_PERCENT = 2.0  # 2% stop loss
TAKE_PROFIT_PERCENT = 3.0  # 3% take profit
INVALIDATION_PERCENT = 1.5  # 1.5% invalidation threshold

# Win/Loss tracking - RESET TO START FRESH (TRACKING FROM HERE)
trade_stats = {
    "wins": 0,
    "losses": 0,
    "total": 0,
    "trade_counter": 0,  # Global trade counter starting from 0 (first trade will be #1)
    "win_rate": 0.0,
    "total_pnl": 0.0,
    "avg_win": 0.0,
    "avg_loss": 0.0,
    "largest_win": 0.0,
    "largest_loss": 0.0
}

# Paper Trading Configuration
PAPER_TRADING_ENABLED = True
STARTING_BALANCE = 1000.0  # $1,000 starting account
MAX_OPEN_TRADES = 3  # Maximum 3 open trades at once
TRADE_SIZE = 150.0  # $150 per trade
DEFAULT_LEVERAGE = 15  # 15x leverage for most coins
BTC_LEVERAGE = 25  # 25x leverage for Bitcoin

# Signal Quality Filters - STRICTER FOR ACCURACY
MIN_SIGNAL_STRENGTH = 70  # Minimum signal strength score (0-100) to take trade
MIN_VOLUME_MULTIPLIER = 1.5  # Minimum 1.5x average volume
MIN_TREND_SCORE_LONG = 7  # Minimum trend score for longs (was 6)
MAX_TREND_SCORE_SHORT = 3  # Maximum trend score for shorts (was 4)
REQUIRE_MA_CROSSOVER = True  # Require MA crossover for signals
REQUIRE_RSI_CONFIRMATION = True  # Require RSI confirmation

# Paper Trading State - RESET TO START FRESH (TRACKING FROM HERE)
paper_account = {
    "balance": STARTING_BALANCE,
    "open_trades": {},  # key: trade_id, value: trade data
    "closed_trades": [],  # Reset all closed trades - tracking from here
    "total_pnl": 0.0,
    "realized_pnl": 0.0,
    "unrealized_pnl": 0.0,
    "starting_balance": STARTING_BALANCE
}

# Scan configuration
SCAN_INTERVAL_MINUTES = 45
SCAN_INTERVAL_SECONDS = SCAN_INTERVAL_MINUTES * 60  # 45 minutes in seconds

# Exchange for market data
exchange = None


def is_allowed_symbol(symbol: str) -> bool:
    """Check if symbol is in allowed list (BTC, SOL, ETH)"""
    if not symbol:
        return False

    symbol_upper = symbol.upper()

    # Direct match
    for allowed in ALLOWED_SYMBOLS:
        if allowed.upper() in symbol_upper:
            return True

    # Pattern match
    for pattern in ALLOWED_SYMBOL_PATTERNS:
        if re.search(pattern, symbol_upper, re.IGNORECASE):
            return True

    return False


def extract_symbol_from_alert(alert_data: Dict) -> Optional[str]:
    """Extract symbol from TradingView alert data"""
    # Try various fields
    symbol = (
        alert_data.get("symbol") or
        alert_data.get("ticker") or
        alert_data.get("pair") or
        alert_data.get("{{ticker}}") or
        ""
    )

    # Try to extract from message/content
    if not symbol:
        message = alert_data.get("message") or alert_data.get("content") or ""
        # Look for common patterns like "BTCUSDT", "BTC/USD", etc.
        for pattern in ALLOWED_SYMBOL_PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(0)

    return symbol.upper() if symbol else None


def parse_signal_type(message: str) -> Dict:
    """Parse signal type from alert message"""
    message_lower = message.lower()

    signal_type = None
    direction = None
    emoji = ""

    # Check for long signals
    for long_sig in LONG_SIGNALS:
        if long_sig.lower() in message_lower:
            signal_type = long_sig
            direction = "LONG"
            emoji = "🟢"
            break

    # Check for short signals
    if not signal_type:
        for short_sig in SHORT_SIGNALS:
            if short_sig.lower() in message_lower:
                signal_type = short_sig
                direction = "SHORT"
                emoji = "🔴"
                break

    # Check for liquidity flush
    if "liquidity" in message_lower or "flush" in message_lower:
        if "bull" in message_lower:
            signal_type = "liquidity_flush_bull"
            direction = "LONG"
            emoji = "⚠️🟢"
        elif "bear" in message_lower:
            signal_type = "liquidity_flush_bear"
            direction = "SHORT"
            emoji = "⚠️🔴"
        else:
            signal_type = "liquidity_flush"
            emoji = "⚠️"

    # Check for divergence
    if "divergence" in message_lower:
        if "bullish" in message_lower or "bull" in message_lower:
            direction = "LONG"
            emoji = "📈"
        elif "bearish" in message_lower or "bear" in message_lower:
            direction = "SHORT"
            emoji = "📉"

    return {
        "type": signal_type or "unknown",
        "direction": direction,
        "emoji": emoji,
        "message": message
    }


def extract_price_from_alert(alert_data: Dict) -> Optional[str]:
    """Extract price from alert data"""
    price = (
        alert_data.get("price") or
        alert_data.get("close") or
        alert_data.get("{{close}}") or
        ""
    )

    # Try to extract from message
    if not price:
        message = alert_data.get("message") or alert_data.get("content") or ""
        price_match = re.search(r'\$?([\d,]+\.?\d*)', message)
        if price_match:
            return price_match.group(1)

    return str(price) if price else None


def get_tradingview_link(symbol: str) -> str:
    """Generate TradingView chart link for OKX perpetual futures"""
    # Map symbols to OKX perpetual futures format
    symbol_map = {
        "BTC": "OKX:BTCUSDTPERP",
        "SOL": "OKX:SOLUSDTPERP",
        "ETH": "OKX:ETHUSDTPERP",
        "BITCOIN": "OKX:BTCUSDTPERP",
        "SOLANA": "OKX:SOLUSDTPERP",
        "ETHEREUM": "OKX:ETHUSDTPERP"
    }

    # Find matching symbol (case-insensitive)
    symbol_upper = symbol.upper()
    for key, tv_symbol in symbol_map.items():
        if key in symbol_upper:
            # URL encode the symbol
            encoded_symbol = tv_symbol.replace(":", "%3A")
            return f"https://www.tradingview.com/chart/?symbol={encoded_symbol}"

    # Fallback - try to construct from symbol
    if "BTC" in symbol_upper:
        return "https://www.tradingview.com/chart/?symbol=KRAKEN%3ABTCUSDTPERP"
    elif "SOL" in symbol_upper:
        return "https://www.tradingview.com/chart/?symbol=KRAKEN%3ASOLUSDTPERP"
    elif "ETH" in symbol_upper:
        return "https://www.tradingview.com/chart/?symbol=KRAKEN%3AETHUSDTPERP"

    return None


def create_discord_embed(signal: Dict) -> Dict:
    """Create a single Discord embed for one signal (potential trade)"""
    symbol = signal.get("symbol", "UNKNOWN")
    signal_info = signal.get("signal_info", {})
    direction = signal_info.get("direction", "")
    emoji = signal_info.get("emoji", "📊")
    signal_type = signal_info.get("type", "Signal")
    price = signal.get("price", "N/A")
    timeframe = signal.get("timeframe", "N/A")

    # Get TradingView chart link
    tv_link = get_tradingview_link(symbol)

    # Determine color - entries are white, shorts are purple
    if direction == "LONG":
        color = 0xFFFFFF  # White for entries
        title = f"{emoji} POTENTIAL LONG TRADE - {symbol}"
    elif direction == "SHORT":
        color = 0x800080  # Purple for shorts
        title = f"{emoji} POTENTIAL SHORT TRADE - {symbol}"
    else:
        color = 0xFFFFFF  # White
        title = f"{emoji} POTENTIAL TRADE - {symbol}"

    # Format signal type nicely
    signal_type_display = signal_type.replace("_", " ").title()

    # Build fields
    fields = [
        {
            "name": "📊 Symbol",
            "value": symbol,
            "inline": True
        },
        {
            "name": "💰 Entry Price",
            "value": f"${price}" if price != "N/A" else price,
            "inline": True
        },
        {
            "name": "⏰ Timeframe",
            "value": timeframe,
            "inline": True
        },
        {
            "name": "📝 Signal Type",
            "value": signal_info.get("message", signal_type_display),
            "inline": False
        }
    ]

    # Add TradingView chart link if available
    if tv_link:
        fields.append({
            "name": "📈 View Chart",
            "value": f"[Open {symbol} Chart on TradingView]({tv_link})",
            "inline": False
        })

    fields.append({
        "name": "⚠️ Disclaimer",
        "value": "This is a signal notification only. Always do your own research and manage risk appropriately.",
        "inline": False
    })

    embed = {
        "title": title,
        "description": f"**{signal_type_display}** - Potential {direction} entry opportunity",
        "color": color,
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Cloudflare Indicator Bot • Signal Only - Not Trade Execution"
        }
    }

    return embed


def create_combined_discord_embed(signals: List[Dict]) -> Dict:
    """Create a combined Discord embed for multiple signals on same symbol"""
    if not signals:
        return None

    # All signals should be for the same symbol (grouped before calling)
    symbol = signals[0].get("symbol", "UNKNOWN")

    # Determine color based on directions
    has_long = any(s.get("signal_info", {}).get("direction") == "LONG" for s in signals)
    has_short = any(s.get("signal_info", {}).get("direction") == "SHORT" for s in signals)

    if has_long and has_short:
        color = 0x0099FF  # Blue for mixed
        title = f"📊 MULTIPLE SIGNALS - {symbol}"
    elif has_long:
        color = 0xFFFFFF  # White for longs
        title = f"📊 MULTIPLE LONG SIGNALS - {symbol}"
    else:
        color = 0x800080  # Purple for shorts
        title = f"📊 MULTIPLE SHORT SIGNALS - {symbol}"

    # Create main embed
    embed = {
        "title": title,
        "description": f"**{len(signals)} signal(s)** detected for {symbol}",
        "color": color,
        "fields": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Cloudflare Indicator Bot • Grouped Signals"
        }
    }

    # Add each signal as a field
    signal_text = []
    for sig in signals:
        signal_info = sig.get("signal_info", {})
        direction = signal_info.get("direction", "")
        emoji = signal_info.get("emoji", "📊")
        signal_type = signal_info.get("type", "Signal").replace("_", " ").title()
        price = sig.get("price", "N/A")

        signal_line = f"{emoji} **{direction}** - {signal_type}"
        if price != "N/A":
            signal_line += f" @ ${price}"
        signal_text.append(signal_line)

    embed["fields"].append({
        "name": f"🔹 {symbol} Signals",
        "value": "\n".join(signal_text) if signal_text else "No signals",
        "inline": False
    })

    # Add TradingView link
    tv_link = get_tradingview_link(symbol)
    if tv_link:
        embed["fields"].append({
            "name": "📈 View Chart",
            "value": f"[Open {symbol} Chart on TradingView]({tv_link})",
            "inline": False
        })

    embed["fields"].append({
        "name": "⚠️ Disclaimer",
        "value": "This is a signal notification only. Always do your own research and manage risk appropriately.",
        "inline": False
    })

    return embed


def is_duplicate_signal(symbol: str, signal_type: str, price: float) -> bool:
    """Check if this signal was already sent recently"""
    current_time = time.time()

    # Create cache key
    cache_key = f"{symbol}_{signal_type}"

    # Check if signal exists in cache and is still valid
    if cache_key in sent_signals_cache:
        last_sent_time = sent_signals_cache[cache_key]
        time_diff = current_time - last_sent_time

        # If sent within cache duration, check if price is similar (within 2%)
        if time_diff < SIGNAL_CACHE_DURATION:
            # Get last price from cache (we'll store it)
            # For now, just check time - if same signal type within 1 hour, it's duplicate
            logger.debug(f"Duplicate signal detected: {cache_key} (sent {time_diff:.0f}s ago)")
            return True

    # Not a duplicate - update cache
    sent_signals_cache[cache_key] = current_time
    return False


def cleanup_old_signals():
    """Remove old signals from cache"""
    current_time = time.time()
    keys_to_remove = []

    for key, timestamp in sent_signals_cache.items():
        if current_time - timestamp > SIGNAL_CACHE_DURATION:
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del sent_signals_cache[key]

    if keys_to_remove:
        logger.debug(f"Cleaned up {len(keys_to_remove)} old signal(s) from cache")


def send_discord_message(embeds: List[Dict]):
    """Send message(s) to Discord webhook"""
    try:
        payload = {"embeds": embeds} if isinstance(embeds, list) else {"embeds": [embeds]}
        response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)

        if response.status_code == 204:
            logger.info(f"✅ Sent {len(payload['embeds'])} embed(s) to Discord")
            return True
        else:
            logger.error(f"❌ Discord webhook returned {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error sending Discord message: {e}")
        return False


def create_trade_execution_embed(trade: Dict, execution_type: str) -> Dict:
    """Create embed for trade execution (entry, exit, stop, TP)"""
    symbol = trade.get("symbol", "UNKNOWN")
    direction = trade.get("direction", "")
    entry_price = trade.get("entry_price", 0)
    position_size = trade.get("position_size", 0)
    leverage = trade.get("leverage", 1)
    trade_number = trade.get("trade_number", 0)

    if execution_type == "entry":
        color = 0x00FF00  # Green for entry alerts (more visible)
        title = f"🚨 TRADE #{trade_number} ENTRY TRIGGERED - {symbol} {direction}"
        description = f"**⚠️ TRADE ENTRY EXECUTED ⚠️**\n\n**Trade #{trade_number}** has been opened at ${entry_price:.2f}"
        fields = [
            {
                "name": "🔢 Trade Number",
                "value": f"**#{trade_number}**",
                "inline": True
            },
            {
                "name": "📊 Symbol",
                "value": symbol,
                "inline": True
            },
            {
                "name": "📈 Direction",
                "value": f"**{direction}**",
                "inline": True
            },
            {
                "name": "💰 Entry Price",
                "value": f"**${entry_price:.2f}**",
                "inline": True
            },
            {
                "name": "💵 Position Size",
                "value": f"${position_size:.2f}",
                "inline": True
            },
            {
                "name": "⚡ Leverage",
                "value": f"{leverage}x",
                "inline": True
            },
            {
                "name": "🛑 Stop Loss",
                "value": f"${trade.get('stop_loss', 0):.2f}",
                "inline": True
            },
            {
                "name": "🎯 Take Profit",
                "value": f"${trade.get('take_profit', 0):.2f}",
                "inline": True
            },
            {
                "name": "📝 Signal Type",
                "value": trade.get("signal_type", "unknown").replace("_", " ").title(),
                "inline": True
            },
            {
                "name": "💼 Account Balance",
                "value": f"${paper_account['balance']:.2f}",
                "inline": True
            },
            {
                "name": "📊 Open Trades",
                "value": f"{len(paper_account['open_trades'])}/{MAX_OPEN_TRADES}",
                "inline": True
            }
        ]
    elif execution_type == "exit":
        exit_price = trade.get("exit_price", entry_price)
        exit_reason = trade.get("exit_reason", "Manual")
        pnl = trade.get("pnl", 0)
        pnl_pct = trade.get("pnl_pct", 0)

        if exit_reason == "STOP_LOSS":
            color = 0xFF0000  # Red
            title = f"🛑 TRADE #{trade_number} CLOSED - STOP LOSS - {symbol}"
        elif "TAKE_PROFIT" in exit_reason:
            color = 0x00FF00  # Green for TP
            title = f"🎯 TRADE #{trade_number} CLOSED - TAKE PROFIT - {symbol}"
        else:
            color = 0x808080  # Gray
            title = f"📤 TRADE #{trade_number} CLOSED - {symbol}"

        description = f"**Trade #{trade_number} closed** at ${exit_price:.2f} - {exit_reason}"

        # Update stats with detailed tracking
        if pnl > 0:
            trade_stats["wins"] += 1
            trade_stats["total_pnl"] += pnl
            if pnl > trade_stats["largest_win"]:
                trade_stats["largest_win"] = pnl
            # Update average win
            if trade_stats["wins"] > 0:
                trade_stats["avg_win"] = trade_stats["total_pnl"] / trade_stats["wins"]
        else:
            trade_stats["losses"] += 1
            trade_stats["total_pnl"] += pnl
            if pnl < trade_stats["largest_loss"]:
                trade_stats["largest_loss"] = pnl
            # Update average loss
            if trade_stats["losses"] > 0:
                total_losses = abs(sum(t.get("pnl", 0) for t in paper_account["closed_trades"] if t.get("pnl", 0) < 0))
                trade_stats["avg_loss"] = total_losses / trade_stats["losses"] if trade_stats["losses"] > 0 else 0
        
        trade_stats["total"] += 1
        trade_stats["win_rate"] = (trade_stats["wins"] / trade_stats["total"] * 100) if trade_stats["total"] > 0 else 0
        win_rate = trade_stats["win_rate"]

        fields = [
            {
                "name": "🔢 Trade Number",
                "value": f"**#{trade_number}**",
                "inline": True
            },
            {
                "name": "📊 Symbol",
                "value": symbol,
                "inline": True
            },
            {
                "name": "💰 Entry Price",
                "value": f"${entry_price:.2f}",
                "inline": True
            },
            {
                "name": "💰 Exit Price",
                "value": f"${exit_price:.2f}",
                "inline": True
            },
            {
                "name": "📈 P&L",
                "value": f"${pnl:+.2f} ({pnl_pct:+.2f}%)",
                "inline": True
            },
            {
                "name": "📝 Exit Reason",
                "value": exit_reason.replace("_", " ").title(),
                "inline": True
            },
            {
                "name": "💼 Account Balance",
                "value": f"${paper_account['balance']:.2f}",
                "inline": True
            },
            {
                "name": "📊 W/L Ratio",
                "value": f"**{trade_stats['wins']}W / {trade_stats['losses']}L** ({win_rate:.1f}% win rate)",
                "inline": True
            },
            {
                "name": "💰 Total P&L",
                "value": f"${paper_account['realized_pnl']:+.2f}",
                "inline": True
            },
            {
                "name": "📈 Avg Win",
                "value": f"${trade_stats['avg_win']:.2f}",
                "inline": True
            },
            {
                "name": "📉 Avg Loss",
                "value": f"${trade_stats['avg_loss']:.2f}",
                "inline": True
            },
            {
                "name": "🏆 Largest Win",
                "value": f"${trade_stats['largest_win']:.2f}",
                "inline": True
            },
            {
                "name": "📉 Largest Loss",
                "value": f"${trade_stats['largest_loss']:.2f}",
                "inline": True
            }
        ]
    else:
        color = 0x808080
        title = f"ℹ️ Trade Update - {symbol}"
        description = f"**{execution_type}**"
        fields = []

    embed = {
        "title": title,
        "description": description,
        "color": color,
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Cloudflare Indicator Bot • Paper Trading"
        }
    }

    # Add TradingView link
    tv_link = get_tradingview_link(symbol)
    if tv_link:
        embed["fields"].append({
            "name": "📈 View Chart",
            "value": f"[Open {symbol} Chart]({tv_link})",
            "inline": False
        })

    return embed


def execute_paper_trade(signal: Dict) -> Optional[str]:
    """Execute a paper trade based on signal"""
    if not PAPER_TRADING_ENABLED:
        return None

    # Check max open trades - can only open new trade after one of the 3 hits TP
    # When we have 3 open trades, we must wait for one of them to hit TP before opening a new one
    if len(paper_account["open_trades"]) >= MAX_OPEN_TRADES:
        logger.info(f"⚠️ Max open trades reached ({MAX_OPEN_TRADES}) - waiting for one of the open trades to hit TP before opening new trade. Skipping {signal.get('symbol')}")
        return None

    symbol = signal.get("symbol", "").upper()
    direction = signal.get("signal_info", {}).get("direction", "")
    entry_price_str = signal.get("price", "0")

    try:
        entry_price = float(entry_price_str) if entry_price_str != "N/A" else 0.0
    except:
        entry_price = 0.0

    if entry_price == 0:
        logger.warning(f"⚠️ Invalid entry price for {symbol}, skipping trade")
        return None

    # Increment trade counter and assign trade number
    trade_stats["trade_counter"] += 1
    trade_number = trade_stats["trade_counter"]

    # Determine leverage (25x for BTC, 15x for others)
    leverage = BTC_LEVERAGE if "BTC" in symbol else DEFAULT_LEVERAGE

    # Calculate position size
    # Position size = Trade size * leverage
    position_size = TRADE_SIZE * leverage

    # Calculate stop loss and take profit
    if direction == "LONG":
        stop_loss = entry_price * (1 - STOP_LOSS_PERCENT / 100)
        take_profit = entry_price * (1 + TAKE_PROFIT_PERCENT / 100)
    else:  # SHORT
        stop_loss = entry_price * (1 + STOP_LOSS_PERCENT / 100)
        take_profit = entry_price * (1 - TAKE_PROFIT_PERCENT / 100)

    # Create trade ID
    trade_id = f"CF_{symbol}_{int(time.time())}"

    # Create trade record
    trade = {
        "trade_id": trade_id,
        "trade_number": trade_number,  # Add trade number
        "symbol": symbol,
        "direction": direction,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "position_size": position_size,
        "leverage": leverage,
        "entry_time": time.time(),
        "status": "OPEN",
        "signal_type": signal.get("signal_info", {}).get("type", "unknown")
    }

    # Add to open trades
    paper_account["open_trades"][trade_id] = trade

    logger.info(f"📝 Trade #{trade_number} OPENED: {symbol} {direction} @ ${entry_price:.2f} (Size: ${position_size:.2f}, Leverage: {leverage}x)")

    # Send trade execution alert IMMEDIATELY
    embed = create_trade_execution_embed(trade, "entry")
    send_discord_message([embed])

    return trade_id


def monitor_paper_trades():
    """Monitor open paper trades for stop loss and take profit"""
    if not PAPER_TRADING_ENABLED or not paper_account["open_trades"]:
        return

    if not exchange:
        if not init_exchange():
            return

    trades_to_close = []

    for trade_id, trade in paper_account["open_trades"].items():
        try:
            symbol = trade["symbol"]
            direction = trade["direction"]
            entry_price = trade["entry_price"]
            stop_loss = trade["stop_loss"]
            take_profit = trade["take_profit"]

            # Get current price (OKX format: BTC/USDT:USDT for perpetuals)
            exchange_symbol = f"{symbol}/USDT:USDT"
            if exchange_symbol not in exchange.markets:
                exchange_symbol = f"{symbol}/USDT"
                if exchange_symbol not in exchange.markets:
                    exchange_symbol = symbol

            ticker = exchange.fetch_ticker(exchange_symbol)
            current_price = float(ticker.get('last', 0))

            if current_price == 0:
                continue

            # Check for stop loss
            if direction == "LONG" and current_price <= stop_loss:
                close_trade(trade_id, current_price, "STOP_LOSS")
                trades_to_close.append(trade_id)
            elif direction == "SHORT" and current_price >= stop_loss:
                close_trade(trade_id, current_price, "STOP_LOSS")
                trades_to_close.append(trade_id)

            # Check for take profit
            elif direction == "LONG" and current_price >= take_profit:
                close_trade(trade_id, current_price, "TAKE_PROFIT")
                trades_to_close.append(trade_id)
            elif direction == "SHORT" and current_price <= take_profit:
                close_trade(trade_id, current_price, "TAKE_PROFIT")
                trades_to_close.append(trade_id)

        except Exception as e:
            logger.error(f"Error monitoring trade {trade_id}: {e}")

    # Remove closed trades
    for trade_id in trades_to_close:
        if trade_id in paper_account["open_trades"]:
            del paper_account["open_trades"][trade_id]


def close_trade(trade_id: str, exit_price: float, exit_reason: str):
    """Close a paper trade"""
    if trade_id not in paper_account["open_trades"]:
        return

    trade = paper_account["open_trades"][trade_id]
    entry_price = trade["entry_price"]
    direction = trade["direction"]
    position_size = trade["position_size"]
    leverage = trade["leverage"]

    # Calculate P&L
    if direction == "LONG":
        price_change = exit_price - entry_price
        pnl_pct = (price_change / entry_price) * 100
    else:  # SHORT
        price_change = entry_price - exit_price
        pnl_pct = (price_change / entry_price) * 100

    # P&L in dollars (with leverage)
    pnl = (position_size / leverage) * (pnl_pct / 100) * leverage

    # Update account
    paper_account["balance"] += pnl
    paper_account["realized_pnl"] += pnl
    paper_account["total_pnl"] = paper_account["realized_pnl"] + paper_account["unrealized_pnl"]

    # Update trade record
    trade["exit_price"] = exit_price
    trade["exit_reason"] = exit_reason
    trade["exit_time"] = time.time()
    trade["pnl"] = pnl
    trade["pnl_pct"] = pnl_pct
    trade["status"] = "CLOSED"

    # Move to closed trades
    paper_account["closed_trades"].append(trade)

    logger.info(f"📤 Paper trade closed: {trade['symbol']} {direction} @ ${exit_price:.2f} - {exit_reason} (P&L: ${pnl:+.2f})")

    # If TP was hit, log that we can now open new trades (slot opened)
    if exit_reason == "TAKE_PROFIT":
        current_open = len(paper_account["open_trades"])
        logger.info(f"✅ Take profit hit - Trade #{trade.get('trade_number', '?')} closed. Slot opened - can now open new trades (currently {current_open}/{MAX_OPEN_TRADES} open).")
    elif exit_reason == "STOP_LOSS":
        # If SL was hit and we're at max, we still can't open new trades until a TP is hit
        current_open = len(paper_account["open_trades"])
        if current_open >= MAX_OPEN_TRADES:
            logger.info(f"⚠️ Stop loss hit - Trade #{trade.get('trade_number', '?')} closed. Still at max ({current_open}/{MAX_OPEN_TRADES}) - waiting for TP before opening new trades.")

    # Send trade execution alert
    embed = create_trade_execution_embed(trade, "exit")
    send_discord_message([embed])


def create_trade_update_embed(signal_key: str, update_type: str, current_price: float, entry_price: float, direction: str) -> Dict:
    """Create embed for trade updates (stop, TP, invalidation)"""
    symbol = signal_key.split("_")[0]

    if update_type == "stop_loss":
        color = 0xFF0000  # Red
        title = f"🛑 STOP LOSS HIT - {symbol}"
        description = f"**Stop loss triggered** at ${current_price:.2f}"
        pnl = ((current_price - entry_price) / entry_price * 100) if direction == "LONG" else ((entry_price - current_price) / entry_price * 100)
        trade_stats["losses"] += 1
        trade_stats["total"] += 1
    elif update_type == "take_profit":
        color = 0xFFFFFF  # White for TP
        title = f"🎯 TAKE PROFIT HIT - {symbol}"
        description = f"**Take profit reached** at ${current_price:.2f}"
        pnl = ((current_price - entry_price) / entry_price * 100) if direction == "LONG" else ((entry_price - current_price) / entry_price * 100)
        trade_stats["wins"] += 1
        trade_stats["total"] += 1
    elif update_type == "invalidation":
        color = 0xFFA500  # Orange
        title = f"❌ TRADE INVALIDATED - {symbol}"
        description = f"**Signal invalidated** - price moved against entry"
        pnl = ((current_price - entry_price) / entry_price * 100) if direction == "LONG" else ((entry_price - current_price) / entry_price * 100)
    else:
        color = 0x808080  # Gray
        title = f"ℹ️ Trade Update - {symbol}"
        description = f"**{update_type}**"
        pnl = 0

    # Calculate W/L ratio
    win_rate = (trade_stats["wins"] / trade_stats["total"] * 100) if trade_stats["total"] > 0 else 0

    embed = {
        "title": title,
        "description": description,
        "color": color,
        "fields": [
            {
                "name": "📊 Symbol",
                "value": symbol,
                "inline": True
            },
            {
                "name": "💰 Entry Price",
                "value": f"${entry_price:.2f}",
                "inline": True
            },
            {
                "name": "💰 Current Price",
                "value": f"${current_price:.2f}",
                "inline": True
            },
            {
                "name": "📈 P&L",
                "value": f"{pnl:+.2f}%",
                "inline": True
            },
            {
                "name": "📊 W/L Ratio",
                "value": f"**{trade_stats['wins']}W / {trade_stats['losses']}L** ({win_rate:.1f}% win rate)",
                "inline": True
            },
            {
                "name": "📝 Status",
                "value": f"**{update_type.replace('_', ' ').title()}**",
                "inline": True
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Cloudflare Indicator Bot • Trade Tracking"
        }
    }

    # Add TradingView link
    tv_link = get_tradingview_link(symbol)
    if tv_link:
        embed["fields"].append({
            "name": "📈 View Chart",
            "value": f"[Open {symbol} Chart]({tv_link})",
            "inline": False
        })

    return embed


def check_active_signals():
    """Check all active signals for stop loss, take profit, or invalidation"""
    if not active_signals:
        return

    if not exchange:
        if not init_exchange():
            return

    signals_to_remove = []

    for signal_key, signal_data in active_signals.items():
        try:
            symbol = signal_data["symbol"]
            entry_price = signal_data["entry_price"]
            direction = signal_data["direction"]

            # Get current price (OKX format: BTC/USDT:USDT for perpetuals)
            exchange_symbol = f"{symbol}/USDT:USDT"
            if exchange_symbol not in exchange.markets:
                exchange_symbol = f"{symbol}/USDT"
                if exchange_symbol not in exchange.markets:
                    exchange_symbol = symbol

            ticker = exchange.fetch_ticker(exchange_symbol)
            current_price = float(ticker.get('last', 0))

            if current_price == 0:
                continue

            # Calculate price change
            if direction == "LONG":
                price_change_pct = ((current_price - entry_price) / entry_price) * 100
                stop_price = entry_price * (1 - STOP_LOSS_PERCENT / 100)
                tp_price = entry_price * (1 + TAKE_PROFIT_PERCENT / 100)
                invalidation_price = entry_price * (1 - INVALIDATION_PERCENT / 100)
            else:  # SHORT
                price_change_pct = ((entry_price - current_price) / entry_price) * 100
                stop_price = entry_price * (1 + STOP_LOSS_PERCENT / 100)
                tp_price = entry_price * (1 - TAKE_PROFIT_PERCENT / 100)
                invalidation_price = entry_price * (1 + INVALIDATION_PERCENT / 100)

            # Check for stop loss
            if direction == "LONG" and current_price <= stop_price:
                embed = create_trade_update_embed(signal_key, "stop_loss", current_price, entry_price, direction)
                send_discord_message([embed])
                signals_to_remove.append(signal_key)
                logger.info(f"🛑 Stop loss hit for {symbol} at ${current_price:.2f}")
            elif direction == "SHORT" and current_price >= stop_price:
                embed = create_trade_update_embed(signal_key, "stop_loss", current_price, entry_price, direction)
                send_discord_message([embed])
                signals_to_remove.append(signal_key)
                logger.info(f"🛑 Stop loss hit for {symbol} at ${current_price:.2f}")

            # Check for take profit
            elif direction == "LONG" and current_price >= tp_price:
                embed = create_trade_update_embed(signal_key, "take_profit", current_price, entry_price, direction)
                send_discord_message([embed])
                signals_to_remove.append(signal_key)
                logger.info(f"🎯 Take profit hit for {symbol} at ${current_price:.2f}")
            elif direction == "SHORT" and current_price <= tp_price:
                embed = create_trade_update_embed(signal_key, "take_profit", current_price, entry_price, direction)
                send_discord_message([embed])
                signals_to_remove.append(signal_key)
                logger.info(f"🎯 Take profit hit for {symbol} at ${current_price:.2f}")

            # Check for invalidation (price moves against entry by invalidation threshold)
            elif direction == "LONG" and price_change_pct <= -INVALIDATION_PERCENT:
                embed = create_trade_update_embed(signal_key, "invalidation", current_price, entry_price, direction)
                send_discord_message([embed])
                signals_to_remove.append(signal_key)
                logger.info(f"❌ Trade invalidated for {symbol} at ${current_price:.2f} ({price_change_pct:.2f}%)")
            elif direction == "SHORT" and price_change_pct <= -INVALIDATION_PERCENT:
                embed = create_trade_update_embed(signal_key, "invalidation", current_price, entry_price, direction)
                send_discord_message([embed])
                signals_to_remove.append(signal_key)
                logger.info(f"❌ Trade invalidated for {symbol} at ${current_price:.2f} ({price_change_pct:.2f}%)")

        except Exception as e:
            logger.error(f"Error checking signal {signal_key}: {e}")

    # Remove closed signals
    for key in signals_to_remove:
        if key in active_signals:
            del active_signals[key]


def init_exchange():
    """Initialize exchange connection - prioritize OKX"""
    global exchange
    if exchange is None:
        try:
            # Try OKX first (primary exchange)
            exchange = ccxt.okx({
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'}  # Use perpetual futures
            })
            exchange.load_markets()
            logger.info("✅ Connected to OKX exchange")
        except Exception as e:
            logger.error(f"❌ Failed to connect to OKX: {e}")
            try:
                # Fallback to Binance
                exchange = ccxt.binance({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'spot'}
                })
                exchange.load_markets()
                logger.info("✅ Connected to Binance exchange (fallback)")
            except Exception as e2:
                logger.error(f"❌ Failed to connect to Binance: {e2}")
                try:
                    # Fallback to Coinbase
                    exchange = ccxt.coinbase({
                        'enableRateLimit': True
                    })
                    exchange.load_markets()
                    logger.info("✅ Connected to Coinbase exchange (fallback)")
                except Exception as e3:
                    logger.error(f"❌ Failed to connect to Coinbase: {e3}")
                    exchange = None
    return exchange is not None


def fetch_klines(symbol: str, timeframe: str = '1h', limit: int = 500) -> Optional[pd.DataFrame]:
    """Fetch OHLCV data for a symbol"""
    global exchange
    if not exchange:
        if not init_exchange():
            return None

    try:
        # Map symbol format for OKX (perpetual futures)
        # OKX uses format like BTC/USDT:USDT for perpetuals
        exchange_symbol = f"{symbol}/USDT:USDT"
        if exchange_symbol not in exchange.markets:
            # Try standard format
            exchange_symbol = f"{symbol}/USDT"
            if exchange_symbol not in exchange.markets:
                # Try without /USDT
                exchange_symbol = symbol
                if exchange_symbol not in exchange.markets:
                    logger.warning(f"Symbol {symbol} not found on exchange")
                    return None

        ohlcv = exchange.fetch_ohlcv(exchange_symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) == 0:
            return None

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df.set_index('timestamp', inplace=True)

        return df
    except Exception as e:
        logger.error(f"Error fetching klines for {symbol}: {e}")
        return None


def calculate_cloudflare_signals(df: pd.DataFrame, symbol: str) -> List[Dict]:
    """Calculate Cloudflare indicator signals"""
    if df is None or len(df) < 200:
        return []

    signals = []

    try:
        # Calculate Moving Averages
        ma20 = df['close'].rolling(20).mean()
        ma50 = df['close'].rolling(50).mean()
        ma200 = df['close'].rolling(200).mean()

        # Calculate ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        # Volume - STRICTER REQUIREMENT
        avg_volume = df['volume'].rolling(20).mean()
        volume_ok = df['volume'].iloc[-1] > avg_volume.iloc[-1] * MIN_VOLUME_MULTIPLIER
        volume_ratio = df['volume'].iloc[-1] / avg_volume.iloc[-1] if avg_volume.iloc[-1] > 0 else 0

        # Trend Score (simplified Cloudflare logic)
        score = 0.0
        current_price = df['close'].iloc[-1]
        if current_price > ma200.iloc[-1]:
            score += 3
        if current_price > ma50.iloc[-1]:
            score += 2
        if ma50.iloc[-1] > ma200.iloc[-1]:
            score += 2
        if ma20.iloc[-1] > ma20.iloc[-2]:
            score += 1
        if current_price > df['close'].iloc[-2]:
            score += 1

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        # MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9).mean()

        # VWAP (simplified - using rolling VWAP)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).rolling(20).sum() / df['volume'].rolling(20).sum()
        current_vwap = vwap.iloc[-1]

        # Trend line (MA50)
        trend_line = ma50.iloc[-1]

        # Detect signals
        price_change = ((current_price - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
        move_significant = abs(price_change) > (atr.iloc[-1] / current_price * 100 * 1.5) if not pd.isna(atr.iloc[-1]) else False

        # Calculate signal strength (0-100) for filtering
        def calculate_signal_strength(signal_type: str, direction: str) -> float:
            strength = 0.0
            
            # Base trend score (30 points)
            if direction == "LONG" and score >= MIN_TREND_SCORE_LONG:
                strength += 30
            elif direction == "SHORT" and score <= MAX_TREND_SCORE_SHORT:
                strength += 30
            
            # Volume confirmation (20 points)
            if volume_ok:
                strength += min(20, (volume_ratio - 1) * 10)
            
            # RSI confirmation (20 points)
            if REQUIRE_RSI_CONFIRMATION:
                if direction == "LONG" and current_rsi < 50 and current_rsi > 30:
                    strength += 20
                elif direction == "SHORT" and current_rsi > 50 and current_rsi < 70:
                    strength += 20
            
            # MA crossover (15 points)
            if REQUIRE_MA_CROSSOVER:
                if direction == "LONG" and current_price > ma50.iloc[-1] and df['close'].iloc[-2] <= ma50.iloc[-2]:
                    strength += 15
                elif direction == "SHORT" and current_price < ma50.iloc[-1] and df['close'].iloc[-2] >= ma50.iloc[-2]:
                    strength += 15
            
            # MACD confirmation (15 points)
            if direction == "LONG" and macd.iloc[-1] > macd_signal.iloc[-1] and macd.iloc[-2] <= macd_signal.iloc[-2]:
                strength += 15
            elif direction == "SHORT" and macd.iloc[-1] < macd_signal.iloc[-1] and macd.iloc[-2] >= macd_signal.iloc[-2]:
                strength += 15
            
            return strength

        # Bull signals - STRICTER: score crosses above MIN_TREND_SCORE_LONG (7)
        prev_score = 0.0
        if len(df) > 1:
            prev_price = df['close'].iloc[-2]
            if prev_price > ma200.iloc[-2] if len(ma200) > 1 else False:
                prev_score += 3
            if prev_price > ma50.iloc[-2] if len(ma50) > 1 else False:
                prev_score += 2

        # Only take strong bull signals
        if score >= MIN_TREND_SCORE_LONG and prev_score < MIN_TREND_SCORE_LONG and volume_ok and move_significant:
            signal_strength = calculate_signal_strength("bull_confirmation", "LONG")
            if signal_strength >= MIN_SIGNAL_STRENGTH:
                signals.append({
                    "type": "bull_confirmation",
                    "direction": "LONG",
                    "emoji": "🟢",
                    "strength": f"Confirmed Bull (Strength: {signal_strength:.0f})",
                    "price": current_price,
                    "score": score,
                    "signal_strength": signal_strength
                })

        # Bear signals - STRICTER: score crosses below MAX_TREND_SCORE_SHORT (3)
        if score <= MAX_TREND_SCORE_SHORT and prev_score > MAX_TREND_SCORE_SHORT and volume_ok and move_significant:
            signal_strength = calculate_signal_strength("bear_confirmation", "SHORT")
            if signal_strength >= MIN_SIGNAL_STRENGTH:
                signals.append({
                    "type": "bear_confirmation",
                    "direction": "SHORT",
                    "emoji": "🔴",
                    "strength": f"Confirmed Bear (Strength: {signal_strength:.0f})",
                    "price": current_price,
                    "score": score,
                    "signal_strength": signal_strength
                })

        # Golden Cross / Death Cross - ONLY IF STRONG
        if ma50.iloc[-1] > ma200.iloc[-1] and ma50.iloc[-2] <= ma200.iloc[-2] and volume_ok and score >= MIN_TREND_SCORE_LONG:
            signal_strength = calculate_signal_strength("golden_cross", "LONG")
            if signal_strength >= MIN_SIGNAL_STRENGTH:
                signals.append({
                    "type": "golden_cross",
                    "direction": "LONG",
                    "emoji": "🌟",
                    "strength": f"Golden Cross (Strength: {signal_strength:.0f})",
                    "price": current_price,
                    "signal_strength": signal_strength
                })

        if ma50.iloc[-1] < ma200.iloc[-1] and ma50.iloc[-2] >= ma200.iloc[-2] and volume_ok and score <= MAX_TREND_SCORE_SHORT:
            signal_strength = calculate_signal_strength("death_cross", "SHORT")
            if signal_strength >= MIN_SIGNAL_STRENGTH:
                signals.append({
                    "type": "death_cross",
                    "direction": "SHORT",
                    "emoji": "💀",
                    "strength": f"Death Cross (Strength: {signal_strength:.0f})",
                    "price": current_price,
                    "signal_strength": signal_strength
                })

        # VWAP breaks - REMOVED (too many false signals)
        # Only take VWAP breaks if they align with strong trend

        # Divergence detection - STRICTER (only strong divergences)
        if current_rsi < 35 and df['low'].iloc[-1] < df['low'].iloc[-10] and rsi.iloc[-1] > rsi.iloc[-10] and score >= 4:
            signal_strength = calculate_signal_strength("bullish_divergence", "LONG")
            if signal_strength >= MIN_SIGNAL_STRENGTH:
                signals.append({
                    "type": "bullish_divergence",
                    "direction": "LONG",
                    "emoji": "📈",
                    "strength": f"Bullish Divergence (Strength: {signal_strength:.0f})",
                    "price": current_price,
                    "rsi": current_rsi,
                    "signal_strength": signal_strength
                })

        if current_rsi > 65 and df['high'].iloc[-1] > df['high'].iloc[-10] and rsi.iloc[-1] < rsi.iloc[-10] and score <= 6:
            signal_strength = calculate_signal_strength("bearish_divergence", "SHORT")
            if signal_strength >= MIN_SIGNAL_STRENGTH:
                signals.append({
                    "type": "bearish_divergence",
                    "direction": "SHORT",
                    "emoji": "📉",
                    "strength": f"Bearish Divergence (Strength: {signal_strength:.0f})",
                    "price": current_price,
                    "rsi": current_rsi,
                    "signal_strength": signal_strength
                })

        # Liquidity flush detection
        volume_spike = df['volume'].iloc[-1] > avg_volume.iloc[-1] * 3.0
        price_spike = abs(price_change) > (atr.iloc[-1] / current_price * 100 * 2.0) if not pd.isna(atr.iloc[-1]) else False

        if volume_spike and price_spike:
            if df['high'].iloc[-1] > df['high'].rolling(20).max().iloc[-2]:
                signals.append({
                    "type": "liquidity_flush_bull",
                    "direction": "LONG",
                    "emoji": "⚠️🟢",
                    "strength": "Liquidity Flush Bull",
                    "price": current_price
                })
            elif df['low'].iloc[-1] < df['low'].rolling(20).min().iloc[-2]:
                signals.append({
                    "type": "liquidity_flush_bear",
                    "direction": "SHORT",
                    "emoji": "⚠️🔴",
                    "strength": "Liquidity Flush Bear",
                    "price": current_price
                })

    except Exception as e:
        logger.error(f"Error calculating signals for {symbol}: {e}", exc_info=True)

    return signals


def scan_markets():
    """Scan markets for Cloudflare signals (runs every 45 minutes)"""
    try:
        logger.info("🔍 Starting scheduled market scan...")

        # Initialize exchange if needed
        if not init_exchange():
            logger.error("❌ Cannot scan - exchange not available")
            return

        # Symbols to scan
        symbols = ["BTC", "SOL", "ETH"]
        all_signals = []

        for symbol in symbols:
            logger.info(f"  📊 Scanning {symbol}...")

            # Fetch 1h data
            df = fetch_klines(symbol, '1h', limit=500)
            if df is None or len(df) < 200:
                logger.warning(f"  ⚠️ Insufficient data for {symbol}")
                continue

            # Detect signals
            signals = calculate_cloudflare_signals(df, symbol)

            if signals:
                logger.info(f"  ✅ Found {len(signals)} signal(s) for {symbol}")
                for signal in signals:
                    signal['symbol'] = symbol
                    signal['timeframe'] = '1h'
                    all_signals.append(signal)
            else:
                logger.info(f"  ℹ️ No signals detected for {symbol}")

        logger.info(f"✅ Market scan completed: {len(all_signals)} total signal(s) found")

        # Clean up old signals from cache
        cleanup_old_signals()

        # Send signals to Discord (with deduplication and grouping by symbol)
        new_signals = []
        duplicate_count = 0
        signals_by_symbol = {}  # Group signals by symbol

        if all_signals:
            for signal in all_signals:
                symbol = signal['symbol']
                signal_type = signal['type']
                price = signal['price']

                # Check if this is a duplicate
                if is_duplicate_signal(symbol, signal_type, price):
                    logger.info(f"  ⏭️ Skipping duplicate signal: {symbol} - {signal_type}")
                    duplicate_count += 1
                    continue

                # New signal - add to group
                new_signals.append(signal)
                if symbol not in signals_by_symbol:
                    signals_by_symbol[symbol] = []
                signals_by_symbol[symbol].append(signal)

                # Track this signal for monitoring
                signal_key = f"{signal['symbol']}_{signal['type']}_{int(time.time())}"
                active_signals[signal_key] = {
                    "symbol": signal['symbol'],
                    "entry_price": signal['price'],
                    "direction": signal['direction'],
                    "signal_type": signal['type'],
                    "timestamp": time.time()
                }
                logger.info(f"📝 Tracking new signal: {signal['symbol']} {signal['direction']} @ ${signal['price']:.2f}")

            # Execute paper trade only once per symbol (first signal)
            if PAPER_TRADING_ENABLED:
                for symbol, symbol_signals in signals_by_symbol.items():
                    if symbol_signals:
                        first_signal = symbol_signals[0]
                        trade_signal = {
                            "symbol": first_signal['symbol'],
                            "signal_info": {
                                "direction": first_signal['direction'],
                                "type": first_signal['type']
                            },
                            "price": f"{first_signal['price']:.2f}",
                            "timeframe": first_signal['timeframe']
                        }
                        trade_id = execute_paper_trade(trade_signal)
                        if trade_id:
                            logger.info(f"✅ Paper trade executed: {trade_id}")

            # Send grouped signals - one card per symbol
            for symbol, symbol_signals in signals_by_symbol.items():
                if len(symbol_signals) == 1:
                    # Single signal - use regular embed
                    signal = symbol_signals[0]
                    embed = create_discord_embed({
                        "symbol": signal['symbol'],
                        "signal_info": {
                            "type": signal['type'],
                            "direction": signal['direction'],
                            "emoji": signal['emoji'],
                            "message": signal.get('strength', signal['type'])
                        },
                        "price": f"{signal['price']:.2f}",
                        "timeframe": signal['timeframe']
                    })
                    send_discord_message([embed])
                else:
                    # Multiple signals for same symbol - use combined embed
                    combined_signals = []
                    for signal in symbol_signals:
                        combined_signals.append({
                            "symbol": signal['symbol'],
                            "signal_info": {
                                "type": signal['type'],
                                "direction": signal['direction'],
                                "emoji": signal['emoji'],
                                "message": signal.get('strength', signal['type'])
                            },
                            "price": f"{signal['price']:.2f}",
                            "timeframe": signal['timeframe']
                        })
                    embed = create_combined_discord_embed(combined_signals)
                    if embed:
                        send_discord_message([embed])
                time.sleep(1)  # Rate limit between symbols

        if new_signals:
            logger.info(f"📤 Sent {len(new_signals)} new signal(s) to Discord in {len(signals_by_symbol)} card(s) (skipped {duplicate_count} duplicate(s))")

        # Scan completed - no notification sent (only notify on actual signals)
        logger.info(f"✅ Scan completed: {len(new_signals)} new signal(s), {duplicate_count} duplicate(s) skipped")

    except Exception as e:
        logger.error(f"❌ Error during market scan: {e}", exc_info=True)


def signal_monitoring_loop():
    """Background thread that monitors active signals for stops/TPs/invalidations"""
    logger.info("🔍 Signal monitoring thread started")
    time.sleep(60)  # Wait 1 minute for Flask to start

    while True:
        try:
            check_active_signals()
            # Monitor paper trades
            if PAPER_TRADING_ENABLED:
                monitor_paper_trades()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in signal monitoring: {e}")
            time.sleep(60)


def scheduled_scan_loop():
    """Background thread that runs market scans every 45 minutes"""
    logger.info(f"⏰ Scheduled scan thread started (interval: {SCAN_INTERVAL_MINUTES} minutes)")

    # Run initial scan after a short delay
    time.sleep(30)  # Wait 30 seconds for Flask to start

    # Run first scan immediately
    logger.info("🔍 Running initial scan...")
    scan_markets()

    while True:
        try:
            scan_markets()

            # Wait for next scan interval
            logger.info(f"⏰ Next scan in {SCAN_INTERVAL_MINUTES} minutes...")
            time.sleep(SCAN_INTERVAL_SECONDS)

        except Exception as e:
            logger.error(f"❌ Error in scheduled scan loop: {e}", exc_info=True)
            # Wait a bit before retrying
            time.sleep(300)  # 5 minutes


@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    """Handle TradingView webhook alerts"""
    try:
        # Get data from request
        if request.is_json:
            data = request.get_json()
        else:
            # Try form data
            data = request.form.to_dict()
            # Try to parse JSON from form data
            if 'json' in data:
                try:
                    data = json.loads(data['json'])
                except:
                    pass

        logger.info(f"Received webhook data: {json.dumps(data, indent=2)}")

        # Extract symbol
        symbol = extract_symbol_from_alert(data)

        if not symbol:
            logger.warning("⚠️ No symbol found in alert data")
            return jsonify({"status": "ignored", "reason": "no_symbol"}), 200

        # Check if symbol is allowed
        if not is_allowed_symbol(symbol):
            logger.info(f"⚠️ Symbol {symbol} not in allowed list (BTC, SOL, ETH only)")
            return jsonify({"status": "ignored", "reason": "symbol_not_allowed", "symbol": symbol}), 200

        # Extract signal information
        message = data.get("message") or data.get("content") or data.get("alert_message") or ""
        signal_info = parse_signal_type(message)

        # Only process long/short signals
        if not signal_info.get("direction"):
            logger.info(f"⚠️ Signal has no direction (not long/short), ignoring: {message}")
            return jsonify({"status": "ignored", "reason": "no_direction"}), 200

        # Extract price
        price = extract_price_from_alert(data)

        # Extract timeframe
        timeframe = (
            data.get("timeframe") or
            data.get("interval") or
            data.get("{{interval}}") or
            "N/A"
        )

        # Create signal object
        signal = {
            "symbol": symbol,
            "signal_info": signal_info,
            "price": price,
            "timeframe": timeframe,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "raw_data": data
        }

        logger.info(f"✅ Processed signal: {symbol} - {signal_info.get('direction')} - {signal_info.get('type')}")

        # Check for duplicates before sending
        signal_type = signal_info.get('type', 'unknown')
        try:
            price = float(price) if price and price != "N/A" else 0.0
        except:
            price = 0.0

        if is_duplicate_signal(symbol, signal_type, price):
            logger.info(f"⏭️ Skipping duplicate webhook signal: {symbol} - {signal_type}")
            return jsonify({
                "status": "ignored",
                "reason": "duplicate_signal",
                "symbol": symbol,
                "signal": signal_type
            }), 200

        # Track this signal for monitoring
        signal_key = f"{symbol}_{signal_type}_{int(time.time())}"
        try:
            entry_price = float(price) if price and price != "N/A" else 0.0
        except:
            entry_price = 0.0

        if entry_price > 0:
            active_signals[signal_key] = {
                "symbol": symbol,
                "entry_price": entry_price,
                "direction": signal_info.get("direction", ""),
                "signal_type": signal_type,
                "timestamp": time.time()
            }
            logger.info(f"📝 Tracking new signal: {symbol} {signal_info.get('direction')} @ ${entry_price:.2f}")

        # Execute paper trade if enabled
        if PAPER_TRADING_ENABLED:
            trade_id = execute_paper_trade(signal)
            if trade_id:
                logger.info(f"✅ Paper trade executed: {trade_id}")

        # Send immediately (single signal = single card)
        embed = create_discord_embed(signal)
        send_discord_message([embed])

        return jsonify({
            "status": "success",
            "symbol": symbol,
            "signal": signal_info.get("type"),
            "direction": signal_info.get("direction")
        }), 200

    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Cloudflare Discord Bot",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "service": "Cloudflare Indicator Discord Bot",
        "status": "running",
        "allowed_symbols": ["BTC", "SOL", "ETH"],
        "webhook_endpoint": "/webhook",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


if __name__ == '__main__':
    logger.info("🚀 Starting Cloudflare Discord Bot...")
    logger.info(f"📊 Monitoring symbols: {', '.join(ALLOWED_SYMBOLS[:3])}")
    logger.info(f"🔗 Discord webhook configured")
    logger.info(f"🌐 Webhook endpoint: http://localhost:5001/webhook")
    logger.info(f"⏰ Scheduled scans: Every {SCAN_INTERVAL_MINUTES} minutes")
    if PAPER_TRADING_ENABLED:
        logger.info(f"💰 Paper Trading: ENABLED")
        logger.info(f"   Starting Balance: ${STARTING_BALANCE:.2f}")
        logger.info(f"   Trade Size: ${TRADE_SIZE:.2f}")
        logger.info(f"   Max Open Trades: {MAX_OPEN_TRADES}")
        logger.info(f"   Leverage: {DEFAULT_LEVERAGE}x (BTC: {BTC_LEVERAGE}x)")

    # Start background scan thread
    scan_thread = threading.Thread(target=scheduled_scan_loop, daemon=True)
    scan_thread.start()
    logger.info("✅ Scheduled scan thread started")

    # Start signal monitoring thread
    monitor_thread = threading.Thread(target=signal_monitoring_loop, daemon=True)
    monitor_thread.start()
    logger.info("✅ Signal monitoring thread started")

    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False
    )

