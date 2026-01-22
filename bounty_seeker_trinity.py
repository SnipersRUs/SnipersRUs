#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bounty Seeker Trinity - Using Channeller + GPS + Piv X Pro
Implements your actual indicators for real-time trading signals
Paper Trading: $1,000 starting capital, max 3 open trades
"""

import os
import json
import time
import traceback
import requests
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import ccxt
import pandas as pd
import numpy as np

# Import Trinity indicators
from indicators import TrinityAnalyzer, TradeSignal, SignalType

# ====================== CONFIGURATION ======================
SCAN_INTERVAL_SEC = 1800  # 30 minutes for active scanning (XX:00 and XX:30)
CONFIG_PATH = "config.json"
DATA_DIR = "data"
STATE_FILE = os.path.join(DATA_DIR, "bounty_seeker_trinity_state.json")
TRADES_DB = os.path.join(DATA_DIR, "bounty_seeker_trinity_trades.db")
STATUS_FILE = os.path.join(DATA_DIR, "bounty_seeker_status.json")  # For website
os.makedirs(DATA_DIR, exist_ok=True)

# Trading parameters
LEVERAGE = 15
PAPER_CAPITAL = 1000.0  # Starting capital
MAX_OPEN_TRADES = 3
RISK_PERCENT = 2.0  # Risk 2% per trade
MIN_RR_RATIO = 2.0  # Minimum 2:1 reward:risk

# Trinity analyzer parameters
MIN_CONFLUENCE = 3  # Minimum confluence score required
ADX_THRESHOLD = 20.0  # Minimum ADX for trend

# Watchlist settings
WATCHLIST_SIZE = 5  # Top 5 coins to watch
WATCHLIST_COOLDOWN_SEC = 1800  # 30min cooldown per symbol

# Signal rate limiting
MAX_SIGNALS_PER_HOUR = 3  # Maximum 3 signals per hour

# Volume filter
MIN_24H_VOLUME_USD = 300000  # Minimum $300,000 24h volume

# Stablecoins to exclude
STABLECOINS = {
    "USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "USDD", "FDUSD",
    "PYUSD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "NZD"
}

# Exchange selection
PREFERRED_EXCHANGE = "okx"  # Options: "okx" or "kraken"

# Discord webhook
DISCORD_WEBHOOK = ""

# ====================== DATABASE SETUP ======================
def init_database():
    """Initialize SQLite database for trade tracking"""
    conn = sqlite3.connect(TRADES_DB)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            exchange TEXT NOT NULL,
            direction TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL NOT NULL,
            take_profit_1 REAL,
            take_profit_2 REAL,
            position_size_usd REAL NOT NULL,
            leverage INTEGER NOT NULL,
            confluence_score INTEGER NOT NULL,
            probability REAL NOT NULL,
            entry_time TEXT NOT NULL,
            exit_time TEXT,
            exit_price REAL,
            exit_reason TEXT,
            pnl_usd REAL,
            pnl_percent REAL,
            reasons TEXT,
            status TEXT DEFAULT 'open'
        )
    ''')

    conn.commit()
    conn.close()


# ====================== CORE BOT CLASS ======================
class BountySeekerTrinity:
    def __init__(self, webhook_url: str, config_path: str = CONFIG_PATH):
        self.webhook_url = webhook_url
        self.config_path = config_path
        self.state = self.load_state()
        self.config = self.load_config()
        self.paper_balance = self.state.get("paper_balance", PAPER_CAPITAL)

        # Initialize database
        init_database()
        self.open_trades = self.load_open_trades()
        self.watchlist = []

        # Initialize exchange
        exchange_name = PREFERRED_EXCHANGE.lower()
        if exchange_name == "okx":
            self.exchange = ccxt.okx({
                "enableRateLimit": True,
                "options": {"defaultType": "swap"}
            })
            self.exchange_name = "OKX"
        elif exchange_name == "kraken":
            self.exchange = ccxt.kraken({
                "enableRateLimit": True,
                "options": {"defaultType": "swap"}
            })
            self.exchange_name = "KRAKEN"
        else:
            self.exchange = ccxt.okx({
                "enableRateLimit": True,
                "options": {"defaultType": "swap"}
            })
            self.exchange_name = "OKX"

        # Initialize Trinity Analyzer
        self.analyzer = TrinityAnalyzer(
            min_confluence=MIN_CONFLUENCE,
            adx_threshold=ADX_THRESHOLD
        )

        self.log("🚀 BountySeeker Trinity initialized")
        self.log(f"💰 Paper Trading Balance: ${self.paper_balance:.2f}")
        self.log(f"📊 Open Trades: {len(self.open_trades)}/{MAX_OPEN_TRADES}")
        self.log(f"🎯 Using: Channeller + GPS + Piv X Pro")

        self.load_watchlist()
        self.check_trade_exits()

    # ------------- State & Config -------------
    def load_state(self) -> Dict:
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                self.log(f"⚠️ Could not load state: {e}")
        return {
            "scanned_count": 0,
            "paper_balance": PAPER_CAPITAL,
            "last_daily_pnl": None,
            "signals_sent_this_hour": 0,
            "last_signal_hour": None
        }

    def save_state(self):
        """Save bot state to file"""
        self.state["paper_balance"] = self.paper_balance
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self.log(f"⚠️ Could not save state: {e}")

    def load_config(self) -> Dict:
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                self.log(f"⚠️ Could not load config: {e}")
        return {"AUTO_EXECUTE": False}

    def load_open_trades(self) -> List[Dict]:
        """Load open trades from database"""
        conn = sqlite3.connect(TRADES_DB)
        c = conn.cursor()
        c.execute('''
            SELECT id, symbol, exchange, direction, entry_price, stop_loss,
                   take_profit_1, take_profit_2, position_size_usd, leverage,
                   confluence_score, probability, entry_time, reasons
            FROM trades WHERE status = 'open'
        ''')
        rows = c.fetchall()
        conn.close()

        trades = []
        for row in rows:
            trades.append({
                "id": row[0],
                "symbol": row[1],
                "exchange": row[2],
                "direction": row[3],
                "entry_price": row[4],
                "stop_loss": row[5],
                "take_profit_1": row[6],
                "take_profit_2": row[7],
                "position_size_usd": row[8],
                "leverage": row[9],
                "confluence_score": row[10],
                "probability": row[11],
                "entry_time": row[12],
                "reasons": row[13]
            })
        return trades

    def load_watchlist(self):
        """Load watchlist from state"""
        self.watchlist = self.state.get("watchlist", [])

    def save_watchlist(self):
        """Save watchlist to state"""
        self.state["watchlist"] = self.watchlist
        self.save_state()

    # ------------- Market Data -------------
    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 200) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data and convert to DataFrame"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not ohlcv or len(ohlcv) < 50:
                return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            self.log(f"⚠️ Failed to fetch {symbol}: {e}")
            return None

    def get_top_volume_symbols(self, limit: int = 10) -> List[str]:
        """Get top volume symbols from exchange"""
        try:
            markets = self.exchange.load_markets()
            tickers = self.exchange.fetch_tickers()

            # Filter for USDT perpetual swaps
            candidates = []
            for symbol, ticker in tickers.items():
                if '/USDT:USDT' in symbol or '/USDT' in symbol:
                    # Exclude stablecoins
                    base = symbol.split('/')[0]
                    if base in STABLECOINS:
                        continue

                    volume = ticker.get('quoteVolume', 0)
                    if volume and volume >= MIN_24H_VOLUME_USD:
                        candidates.append((symbol, volume))

            # Sort by volume and return top N
            candidates.sort(key=lambda x: x[1], reverse=True)
            return [s[0] for s in candidates[:limit]]

        except Exception as e:
            self.log(f"⚠️ Error fetching top volume symbols: {e}")
            return []

    # ------------- Analysis -------------
    def analyze_symbol(self, symbol: str) -> Optional[TradeSignal]:
        """
        Analyze symbol using Trinity system (Channeller + GPS + Piv X Pro)
        """
        try:
            # Fetch 1h data for main analysis
            df_1h = self.fetch_ohlcv(symbol, "1h", 200)
            if df_1h is None or len(df_1h) < 100:
                return None

            # Fetch higher timeframes for GPS
            df_daily = self.fetch_ohlcv(symbol, "1d", 50)
            df_weekly = self.fetch_ohlcv(symbol, "1w", 20)

            # Run Trinity analysis
            signal = self.analyzer.analyze(
                symbol=symbol.replace('/USDT:USDT', '').replace('/USDT', ''),
                df=df_1h,
                daily_df=df_daily,
                weekly_df=df_weekly
            )

            return signal

        except Exception as e:
            self.log(f"⚠️ Analysis error for {symbol}: {e}")
            return None

    # ------------- Trade Management -------------
    def calculate_position_size(self, entry: float, stop: float, risk_percent: float = RISK_PERCENT) -> float:
        """Calculate position size based on risk"""
        risk_amount = self.paper_balance * (risk_percent / 100)
        risk_per_contract = abs(entry - stop)
        if risk_per_contract == 0:
            return 0.0
        position_size = risk_amount / risk_per_contract
        return min(position_size, self.paper_balance * 0.33)  # Max 33% per trade

    def open_paper_trade(self, signal: TradeSignal) -> bool:
        """Open a paper trade"""
        if len(self.open_trades) >= MAX_OPEN_TRADES:
            return False

        position_size = self.calculate_position_size(signal.entry_price, signal.stop_loss)

        conn = sqlite3.connect(TRADES_DB)
        c = conn.cursor()
        c.execute('''
            INSERT INTO trades (symbol, exchange, direction, entry_price, stop_loss,
                              take_profit_1, take_profit_2, position_size_usd, leverage,
                              confluence_score, probability, entry_time, reasons, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
        ''', (
            signal.symbol,
            self.exchange_name.lower(),
            signal.signal_type.value,
            signal.entry_price,
            signal.stop_loss,
            signal.target_1,
            signal.target_2,
            position_size,
            LEVERAGE,
            signal.confluence_score,
            signal.probability,
            datetime.utcnow().isoformat(),
            ", ".join(signal.reasons)
        ))
        trade_id = c.lastrowid
        conn.commit()
        conn.close()

        self.open_trades.append({
            "id": trade_id,
            "symbol": signal.symbol,
            "direction": signal.signal_type.value,
            "entry_price": signal.entry_price,
            "stop_loss": signal.stop_loss,
            "take_profit_1": signal.target_1,
            "take_profit_2": signal.target_2,
            "position_size_usd": position_size,
            "leverage": LEVERAGE,
            "confluence_score": signal.confluence_score,
            "probability": signal.probability,
            "entry_time": datetime.utcnow().isoformat()
        })

        self.log(f"✅ Opened paper trade: {signal.symbol} {signal.signal_type.value} @ ${signal.entry_price:.6f}")
        return True

    def check_trade_exits(self):
        """Check if any open trades hit stop loss or take profit"""
        if not self.open_trades:
            return

        updated_trades = []
        for trade in self.open_trades:
            try:
                ticker = self.exchange.fetch_ticker(trade["symbol"])
                current_price = float(ticker["last"])

                exit_reason = None
                exit_price = None
                pnl_usd = 0.0
                pnl_percent = 0.0
                is_long = trade["direction"] == "LONG"

                # LONG TRADE EXITS
                if is_long:
                    if current_price <= trade["stop_loss"]:
                        exit_reason = "Stop Loss"
                        exit_price = trade["stop_loss"]
                        pnl_usd = (exit_price - trade["entry_price"]) * (trade["position_size_usd"] / trade["entry_price"]) * LEVERAGE
                        pnl_percent = ((exit_price - trade["entry_price"]) / trade["entry_price"]) * 100 * LEVERAGE
                    elif current_price >= trade["take_profit_2"]:
                        exit_reason = "Take Profit 2"
                        exit_price = trade["take_profit_2"]
                        pnl_usd = (exit_price - trade["entry_price"]) * (trade["position_size_usd"] / trade["entry_price"]) * LEVERAGE
                        pnl_percent = ((exit_price - trade["entry_price"]) / trade["entry_price"]) * 100 * LEVERAGE
                    elif current_price >= trade["take_profit_1"]:
                        exit_reason = "Take Profit 1"
                        exit_price = trade["take_profit_1"]
                        pnl_usd = (exit_price - trade["entry_price"]) * (trade["position_size_usd"] / trade["entry_price"]) * LEVERAGE
                        pnl_percent = ((exit_price - trade["entry_price"]) / trade["entry_price"]) * 100 * LEVERAGE

                # SHORT TRADE EXITS
                else:
                    if current_price >= trade["stop_loss"]:
                        exit_reason = "Stop Loss"
                        exit_price = trade["stop_loss"]
                        pnl_usd = (trade["entry_price"] - exit_price) * (trade["position_size_usd"] / trade["entry_price"]) * LEVERAGE
                        pnl_percent = ((trade["entry_price"] - exit_price) / trade["entry_price"]) * 100 * LEVERAGE
                    elif current_price <= trade["take_profit_2"]:
                        exit_reason = "Take Profit 2"
                        exit_price = trade["take_profit_2"]
                        pnl_usd = (trade["entry_price"] - exit_price) * (trade["position_size_usd"] / trade["entry_price"]) * LEVERAGE
                        pnl_percent = ((trade["entry_price"] - exit_price) / trade["entry_price"]) * 100 * LEVERAGE
                    elif current_price <= trade["take_profit_1"]:
                        exit_reason = "Take Profit 1"
                        exit_price = trade["take_profit_1"]
                        pnl_usd = (trade["entry_price"] - exit_price) * (trade["position_size_usd"] / trade["entry_price"]) * LEVERAGE
                        pnl_percent = ((trade["entry_price"] - exit_price) / trade["entry_price"]) * 100 * LEVERAGE

                if exit_reason:
                    conn = sqlite3.connect(TRADES_DB)
                    c = conn.cursor()
                    c.execute('''
                        UPDATE trades
                        SET exit_time = ?, exit_price = ?, exit_reason = ?,
                            pnl_usd = ?, pnl_percent = ?, status = 'closed'
                        WHERE id = ?
                    ''', (
                        datetime.utcnow().isoformat(),
                        exit_price,
                        exit_reason,
                        pnl_usd,
                        pnl_percent,
                        trade["id"]
                    ))
                    conn.commit()
                    conn.close()

                    self.paper_balance += pnl_usd
                    self.save_state()

                    self.send_trade_exit_alert(trade, exit_reason, exit_price, pnl_usd, pnl_percent)
                else:
                    updated_trades.append(trade)

            except Exception as e:
                self.log(f"⚠️ Error checking trade {trade['id']}: {e}")
                updated_trades.append(trade)

        self.open_trades = updated_trades

    # ------------- Discord Integration -------------
    def log(self, message: str):
        """Log message with timestamp"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"[{timestamp}] {message}")

    def post_to_discord(self, embeds: List[Dict]):
        """Post embeds to Discord"""
        if not self.webhook_url:
            return

        payload = {"embeds": embeds}

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code == 204:
                self.log("✅ Posted to Discord")
            else:
                self.log(f"⚠️ Discord response: {response.status_code}")
        except Exception as e:
            self.log(f"⚠️ Discord error: {e}")

    def build_signal_embed(self, signal: TradeSignal) -> Dict:
        """Build Discord embed for trade signal"""
        color = 0x0ecb81 if signal.signal_type == SignalType.LONG else 0x9c27b0
        direction_emoji = "🟢" if signal.signal_type == SignalType.LONG else "🔴"

        desc_lines = [
            f"**{direction_emoji} {signal.signal_type.value} Signal** | **Confluence: {signal.confluence_score}/6** | **Probability: {signal.probability:.1f}%**",
            "",
            f"**📍 Entry:** `${signal.entry_price:.6f}`",
            f"**🛑 Stop Loss:** `${signal.stop_loss:.6f}`",
            f"**🎯 Take Profits:**",
            f"  • **TP1:** `${signal.target_1:.6f}` (2:1 RR)",
            f"  • **TP2:** `${signal.target_2:.6f}` (4:1 RR)",
            "",
            "**Setup Reasons:**",
        ]

        for reason in signal.reasons[:8]:
            desc_lines.append(f"  • {reason}")

        desc_lines.append("")
        desc_lines.append("*Always DYOR - Not Financial Advice*")

        return {
            "title": f"🎯 {signal.symbol} - Trinity Signal",
            "description": "\n".join(desc_lines),
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }

    def send_trade_exit_alert(self, trade: Dict, exit_reason: str, exit_price: float, pnl_usd: float, pnl_percent: float):
        """Send trade exit alert to Discord"""
        color = 0x0ecb81 if pnl_usd > 0 else 0xff0000
        embed = {
            "title": f"📊 Trade Closed: {trade['symbol']}",
            "description": (
                f"**Direction:** {trade['direction']}\n"
                f"**Exit Reason:** {exit_reason}\n"
                f"**Entry:** ${trade['entry_price']:.6f}\n"
                f"**Exit:** ${exit_price:.6f}\n"
                f"**P&L:** ${pnl_usd:.2f} ({pnl_percent:.2f}%)\n"
                f"**Balance:** ${self.paper_balance:.2f}"
            ),
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.post_to_discord([embed])

    # ------------- Status Output for Website -------------
    def save_status_for_website(self, signals: List[TradeSignal], watchlist: List[Dict]):
        """Save bot status to JSON file for website consumption"""
        try:
            status = {
                "bot_name": "Bounty Seeker Trinity",
                "status": "active",
                "last_scan": datetime.utcnow().isoformat(),
                "next_scan": (datetime.utcnow() + timedelta(seconds=SCAN_INTERVAL_SEC)).isoformat(),
                "open_trades": [
                    {
                        "symbol": t["symbol"],
                        "direction": t["direction"],
                        "entry_price": t["entry_price"],
                        "stop_loss": t["stop_loss"],
                        "take_profit_1": t["take_profit_1"],
                        "take_profit_2": t["take_profit_2"],
                        "confluence_score": t["confluence_score"],
                        "probability": t["probability"],
                        "entry_time": t["entry_time"]
                    }
                    for t in self.open_trades
                ],
                "signals": [
                    {
                        "symbol": s.symbol,
                        "direction": s.signal_type.value,
                        "entry_price": s.entry_price,
                        "stop_loss": s.stop_loss,
                        "target_1": s.target_1,
                        "target_2": s.target_2,
                        "confluence_score": s.confluence_score,
                        "probability": s.probability,
                        "reasons": s.reasons[:5]
                    }
                    for s in signals[:5]
                ],
                "watchlist": watchlist[:WATCHLIST_SIZE],
                "paper_balance": self.paper_balance,
                "total_scans": self.state.get("scanned_count", 0)
            }

            with open(STATUS_FILE, "w") as f:
                json.dump(status, f, indent=2)

        except Exception as e:
            self.log(f"⚠️ Error saving status: {e}")

    # ------------- Main Scan Loop -------------
    def run_scan_loop(self):
        """Main scanning loop"""
        self.log("🔄 Starting scan loop...")

        while True:
            try:
                start_t = time.time()
                self.log("🔍 Starting scan...")

                # Check for trade exits first
                self.check_trade_exits()

                # Get top volume symbols
                symbols = self.get_top_volume_symbols(limit=10)
                if not symbols:
                    self.log("⚠️ No symbols to scan")
                    time.sleep(SCAN_INTERVAL_SEC)
                    continue

                self.log(f"📊 Scanning {len(symbols)} symbols...")

                # Analyze each symbol
                signals = []
                watchlist_candidates = []

                for symbol in symbols:
                    signal = self.analyze_symbol(symbol)
                    if signal:
                        signals.append(signal)
                    else:
                        # Check if it's a watchlist candidate (near setup but not quite)
                        # Simplified: just add to watchlist if no signal
                        watchlist_candidates.append({
                            "symbol": symbol,
                            "bias": "neutral",
                            "reason": "Monitoring for setup"
                        })

                # Filter signals by confluence
                trade_signals = [s for s in signals if s.confluence_score >= MIN_CONFLUENCE]

                # Rate limiting
                current_hour = datetime.utcnow().hour
                if self.state.get("last_signal_hour") != current_hour:
                    self.state["signals_sent_this_hour"] = 0
                    self.state["last_signal_hour"] = current_hour

                remaining_slots = MAX_SIGNALS_PER_HOUR - self.state.get("signals_sent_this_hour", 0)

                # Build Discord embeds
                embeds = []

                if trade_signals and remaining_slots > 0:
                    filtered_signals = trade_signals[:remaining_slots]
                    for signal in filtered_signals:
                        embeds.append(self.build_signal_embed(signal))
                        self.log(f"✅ Signal: {signal.symbol} {signal.signal_type.value} (Confluence: {signal.confluence_score})")

                    signals_sent = self.state.get("signals_sent_this_hour", 0) + len(filtered_signals)
                    self.state["signals_sent_this_hour"] = signals_sent
                    self.save_state()

                    # Auto-open paper trades if enabled
                    if self.config.get("AUTO_EXECUTE", False):
                        for signal in filtered_signals:
                            if len(self.open_trades) < MAX_OPEN_TRADES:
                                self.open_paper_trade(signal)

                # Update watchlist
                self.watchlist = watchlist_candidates[:WATCHLIST_SIZE]
                self.save_watchlist()

                # Send scan update to Discord
                scan_time = time.time() - start_t
                scan_embed = {
                    "title": "🔍 Scan Update - Trinity System",
                    "description": (
                        f"**Scanned:** {len(symbols)} coins\n"
                        f"**Signals Found:** {len(trade_signals)} (LONG + SHORT)\n"
                        f"**Watchlist:** {len(watchlist_candidates)} coins\n"
                        f"**Open Trades:** {len(self.open_trades)}/{MAX_OPEN_TRADES}\n"
                        f"**Balance:** ${self.paper_balance:.2f}\n"
                        f"**Scan Time:** {scan_time:.1f}s"
                    ),
                    "color": 0x3498db,
                    "timestamp": datetime.utcnow().isoformat(),
                    "footer": {"text": f"Next scan in {SCAN_INTERVAL_SEC//60} minutes"}
                }

                if embeds:
                    embeds.insert(0, scan_embed)
                    self.post_to_discord(embeds)
                else:
                    self.post_to_discord([scan_embed])

                # Save status for website
                self.save_status_for_website(trade_signals, watchlist_candidates)

                # Update scan count
                self.state["scanned_count"] = self.state.get("scanned_count", 0) + 1
                self.save_state()

                self.log(f"✅ Scan complete. Next scan in {SCAN_INTERVAL_SEC}s ({SCAN_INTERVAL_SEC//60} minutes)")

            except KeyboardInterrupt:
                self.log("🛑 Shutting down gracefully...")
                self.save_state()
                break
            except Exception as e:
                self.log(f"❌ CRITICAL ERROR: {e}")
                traceback.print_exc()
                self.log("⚠️ Continuing despite error...")

            time.sleep(SCAN_INTERVAL_SEC)


# ====================== ENTRY POINT ======================
if __name__ == "__main__":
    webhook = os.getenv("DISCORD_WEBHOOK", DISCORD_WEBHOOK)
    if not webhook or webhook == "YOUR_DISCORD_WEBHOOK_HERE":
        print("⚠️ WARNING: No Discord webhook configured!")
        print("Set DISCORD_WEBHOOK environment variable")
        print("Continuing without Discord notifications...\n")

    bot = BountySeekerTrinity(webhook_url=webhook)
    bot.run_scan_loop()
