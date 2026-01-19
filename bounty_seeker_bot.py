#!/usr/bin/env python3
"""
Bounty Seeker Bot - Reversal Trading Bot
- Catches bottoms and tops using Elliott Wave 3 pullbacks
- Uses GPS (Golden Pocket Syndicate) for optimal entry zones
- Uses Oath Keeper for macro divergences (white circle prints)
- Uses SFP (Smart Fibonacci Points) for 3-level confluence
- Uses Mini VWAPs for trend analysis
- Paper trading with $1k starting balance
- Max 3 trades open, aggressive TP1 (1.5-2%), max 3% loss with 15x leverage
"""
import os
import json
import time
import sqlite3
import logging
import requests
import ccxt
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(
    level=logging.INFO,  # Changed from DEBUG to INFO for production, but DEBUG messages will still show in file
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bounty_seeker.log'),
        logging.StreamHandler()
    ]
)
# Also log DEBUG to file for troubleshooting
file_handler = logging.FileHandler('bounty_seeker.log')
file_handler.setLevel(logging.DEBUG)
logger = logging.getLogger("BountySeeker")
logger.addHandler(file_handler)
logger = logging.getLogger("BountySeeker")

# Discord webhook
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1432976746692612147/SLf6oNcxTZfnmt1LmGLv-asGHwi-BnR2T8XIneUr7zM1tTbsSMncMZgzytvTFiAHmpcr"

# Configuration
SCAN_INTERVAL_SEC = 60 * 60  # 1 hour
# WHITELIST: Only scan coins from screenshots
ALLOWED_COINS = {
    # Major coins
    'BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE',
    # Layer 1s & Layer 2s
    'NEAR', 'SUI', 'APT', 'OP', 'ARB', 'SEI', 'TIA', 'INJ', 'AVAX',
    # DeFi & Staking
    'LDO', 'AAVE', 'PENDLE', 'ENA', 'ONDO', 'RENDER',
    # Meme coins
    'PEPE', 'WIF', 'SHIB', 'BONK', 'FARTCOIN', 'CHILLGUY', 'PENGU', 'POPCAT', 'GOAT',
    # Newer/Alt coins
    'ZK', 'EIGEN', 'ZRO', 'ETHFI', 'REZ', 'POL', 'XMR', 'PUMP', 'XPL', 'BERA',
    'ASTER', 'DYM', 'WLD', 'VIRTUAL', 'BRETT', 'ARKM', 'ORDI', 'STX', 'JUP',
    'ZORA', 'AVNT', 'MON', 'ZEC', 'HYPE', 'TRUMP', 'INLI',
    # Forex pairs (from screenshots)
    'USDJPY', 'USDTRY', 'EURUSD', 'GBPUSD', 'AUDUSD', 'USDBRL', 'USDCAD', 'USDCHF',
    'USDINR', 'USDSEK', 'NZDUSD', 'USDSGD', 'USDCNH', 'USDMXN', 'USDZAR'
}
TIMEFRAMES = ["5m", "15m", "1h"]  # PivotX Pro: 5m, 15m, 1h for A+ setups
MAX_SIGNALS_PER_HOUR = 4  # 4 trades per hour
MAX_OPEN_TRADES = 3
STARTING_BALANCE = 1000.0  # $1k paper trading
LEVERAGE = 15
TP1_PCT = 0.0175  # 1.75% (between 1.5-2%)
TP2_PCT = 0.03  # 3% second target
STOP_LOSS_PCT = 0.03  # Max 3% loss
POSITION_SIZE_USD = 100.0  # $100 per trade (with 15x leverage = $1500 exposure)


class TradeDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class TradeStatus(Enum):
    ACTIVE = "ACTIVE"
    CLOSED_TP1 = "CLOSED_TP1"
    CLOSED_TP2 = "CLOSED_TP2"
    CLOSED_STOP = "CLOSED_STOP"
    CLOSED_MANUAL = "CLOSED_MANUAL"


@dataclass
class Signal:
    """Trading signal"""
    symbol: str
    direction: TradeDirection
    trade_kind: str  # "SCALP" or "SWING"
    entry_price: float
    stop_loss: float
    tp1: float
    tp2: float
    confidence: float
    confluence_score: float
    reasons: List[str]
    timeframe: str
    timestamp: datetime
    gps_touched: bool
    oath_keeper_div: bool
    oath_keeper_tf: str  # Timeframe where Oath Keeper divergence was detected
    sfp_levels: int  # 1, 2, or 3 levels of SFP confluence
    sfp_timeframes: List[str]  # Which timeframes have SFPs (e.g., ["15m", "1h", "4h"])
    vwap_trend: str  # "BULLISH", "BEARISH", "NEUTRAL"
    vwap_trend_tf: str  # Timeframe where VWAP trend was determined
    wave3_tf: str  # Timeframe where Wave 3 pullback was detected
    chart_url: str


@dataclass
class Trade:
    """Active trade"""
    id: str
    signal_id: str
    symbol: str
    direction: TradeDirection
    entry_price: float
    stop_loss: float
    tp1: float
    tp2: float
    position_size_usd: float
    leverage: int
    entry_time: datetime
    status: TradeStatus
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class PaperTradingAccount:
    """Paper trading account with SQLite storage"""

    def __init__(self, db_path: str = "bounty_seeker_trades.db"):
        self.db_path = db_path
        self.balance = STARTING_BALANCE
        self.starting_balance = STARTING_BALANCE
        self.init_database()
        self.load_state()

    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Account state
        c.execute("""CREATE TABLE IF NOT EXISTS account_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            balance REAL,
            starting_balance REAL,
            total_trades INTEGER,
            winning_trades INTEGER,
            losing_trades INTEGER,
            total_pnl REAL,
            last_updated TIMESTAMP
        )""")

        # Trades
        c.execute("""CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            symbol TEXT,
            direction TEXT,
            entry_price REAL,
            stop_loss REAL,
            tp1 REAL,
            tp2 REAL,
            position_size_usd REAL,
            leverage INTEGER,
            entry_time TIMESTAMP,
            exit_time TIMESTAMP,
            exit_price REAL,
            status TEXT,
            pnl REAL,
            pnl_pct REAL,
            exit_reason TEXT,
            confluence_score REAL,
            reasons TEXT
        )""")

        # Failed trades (to avoid repeat entries)
        c.execute("""CREATE TABLE IF NOT EXISTS failed_trades (
            symbol TEXT,
            direction TEXT,
            entry_time TIMESTAMP,
            failure_reason TEXT,
            PRIMARY KEY (symbol, direction, entry_time)
        )""")

        conn.commit()
        conn.close()

    def load_state(self):
        """Load account state from database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT balance, starting_balance FROM account_state ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if row:
            self.balance, self.starting_balance = row
        else:
            self.save_state()
        conn.close()

    def save_state(self):
        """Save account state"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        stats = self.get_stats()
        c.execute("""INSERT INTO account_state
                     (balance, starting_balance, total_trades, winning_trades, losing_trades, total_pnl, last_updated)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (self.balance, self.starting_balance, stats['total_trades'],
                   stats['winning_trades'], stats['losing_trades'], stats['total_pnl'],
                   datetime.now(timezone.utc)))
        conn.commit()
        conn.close()

    def get_active_trades_count(self) -> int:
        """Get count of active trades"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM trades WHERE status = ?", (TradeStatus.ACTIVE.value,))
        count = c.fetchone()[0]
        conn.close()
        return count

    def can_enter_trade(self) -> bool:
        """Check if we can enter a new trade"""
        return self.get_active_trades_count() < MAX_OPEN_TRADES

    def has_active_trade_for_symbol(self, symbol: str, direction: TradeDirection) -> bool:
        """Check if there's already an active trade for this symbol/direction"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM trades WHERE symbol = ? AND direction = ? AND status = ?",
                  (symbol, direction.value, TradeStatus.ACTIVE.value))
        count = c.fetchone()[0]
        conn.close()
        return count > 0

    def enter_trade(self, signal: Signal) -> Optional[Trade]:
        """Enter a new trade"""
        if not self.can_enter_trade():
            logger.warning(f"Cannot enter trade. Active trades: {self.get_active_trades_count()}")
            return None

        # STRICT CHECK: Block if this symbol/direction has ANY losing history
        if self.is_failed_trade(signal.symbol, signal.direction):
            logger.warning(f"🚫 BLOCKED: {signal.symbol} {signal.direction.value} - Has losing trade history. Moving on to next coin.")
            return None

        # Additional check: Block if there's an active trade for this symbol/direction
        if self.has_active_trade_for_symbol(signal.symbol, signal.direction):
            logger.warning(f"🚫 BLOCKED: {signal.symbol} {signal.direction.value} - Already have active trade. Moving on.")
            return None

        trade_id = f"BS_{int(time.time())}_{signal.symbol.replace('/', '_')}"

        trade = Trade(
            id=trade_id,
            signal_id=trade_id,
            symbol=signal.symbol,
            direction=signal.direction,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            tp1=signal.tp1,
            tp2=signal.tp2,
            position_size_usd=POSITION_SIZE_USD,
            leverage=LEVERAGE,
            entry_time=datetime.now(timezone.utc),
            status=TradeStatus.ACTIVE,
            current_price=signal.entry_price,
            unrealized_pnl=0.0,
            unrealized_pnl_pct=0.0
        )

        # Save to database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT INTO trades
                     (id, symbol, direction, entry_price, stop_loss, tp1, tp2,
                      position_size_usd, leverage, entry_time, status, confluence_score, reasons)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (trade.id, trade.symbol, trade.direction.value, trade.entry_price,
                   trade.stop_loss, trade.tp1, trade.tp2, trade.position_size_usd,
                   trade.leverage, trade.entry_time, trade.status.value,
                   signal.confluence_score, json.dumps(signal.reasons)))
        conn.commit()
        conn.close()

        logger.info(f"✅ ENTERED TRADE: {trade.symbol} {trade.direction.value} @ ${trade.entry_price:.6f}")
        return trade

    def update_trade(self, trade: Trade, current_price: float) -> Optional[str]:
        """Update trade and check for exits"""
        # Calculate unrealized P&L
        if trade.direction == TradeDirection.LONG:
            pnl_pct = ((current_price - trade.entry_price) / trade.entry_price) * 100
        else:
            pnl_pct = ((trade.entry_price - current_price) / trade.entry_price) * 100

        pnl_usd = (pnl_pct / 100) * trade.position_size_usd * trade.leverage

        trade.current_price = current_price
        trade.unrealized_pnl = pnl_usd
        trade.unrealized_pnl_pct = pnl_pct

        # Check for TP1
        if trade.direction == TradeDirection.LONG:
            if current_price >= trade.tp1:
                return self.close_trade(trade, current_price, TradeStatus.CLOSED_TP1, "TP1 Hit")
        else:
            if current_price <= trade.tp1:
                return self.close_trade(trade, current_price, TradeStatus.CLOSED_TP1, "TP1 Hit")

        # Check for TP2
        if trade.direction == TradeDirection.LONG:
            if current_price >= trade.tp2:
                return self.close_trade(trade, current_price, TradeStatus.CLOSED_TP2, "TP2 Hit")
        else:
            if current_price <= trade.tp2:
                return self.close_trade(trade, current_price, TradeStatus.CLOSED_TP2, "TP2 Hit")

        # Check for stop loss
        if trade.direction == TradeDirection.LONG:
            if current_price <= trade.stop_loss:
                self.mark_failed_trade(trade.symbol, trade.direction, "Stop Loss Hit")
                return self.close_trade(trade, current_price, TradeStatus.CLOSED_STOP, "Stop Loss Hit")
        else:
            if current_price >= trade.stop_loss:
                self.mark_failed_trade(trade.symbol, trade.direction, "Stop Loss Hit")
                return self.close_trade(trade, current_price, TradeStatus.CLOSED_STOP, "Stop Loss Hit")

        return None

    def close_trade(self, trade: Trade, exit_price: float, status: TradeStatus, reason: str) -> str:
        """Close a trade"""
        # Calculate P&L
        if trade.direction == TradeDirection.LONG:
            pnl_pct = ((exit_price - trade.entry_price) / trade.entry_price) * 100
        else:
            pnl_pct = ((trade.entry_price - exit_price) / trade.entry_price) * 100

        pnl_usd = (pnl_pct / 100) * trade.position_size_usd * trade.leverage
        self.balance += pnl_usd

        # Update database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""UPDATE trades SET
                     exit_time = ?, exit_price = ?, status = ?, pnl = ?, pnl_pct = ?, exit_reason = ?
                     WHERE id = ?""",
                  (datetime.now(timezone.utc), exit_price, status.value, pnl_usd, pnl_pct, reason, trade.id))
        conn.commit()
        conn.close()

        # IMMEDIATELY mark as failed if it's a losing trade (negative P&L) or stop loss
        # This prevents retrying the same losing trade - NO EXCEPTIONS
        if pnl_usd < 0 or status == TradeStatus.CLOSED_STOP:
            self.mark_failed_trade(trade.symbol, trade.direction, f"Loss: ${pnl_usd:.2f} ({reason})")
            logger.warning(f"🚫 PERMANENTLY MARKED {trade.symbol} {trade.direction.value} as FAILED - Will NEVER retry this trade")

            # Also mark all symbol variants to be extra safe
            base_symbol = trade.symbol.split(':')[0] if ':' in trade.symbol else trade.symbol
            for variant in [trade.symbol, base_symbol, f"{base_symbol}:USDT", f"{base_symbol}:USDT:USDT"]:
                if variant != trade.symbol:
                    self.mark_failed_trade(variant, trade.direction, f"Loss: ${pnl_usd:.2f} ({reason}) - Variant of {trade.symbol}")

        self.save_state()

        logger.info(f"💰 CLOSED TRADE: {trade.symbol} {trade.direction.value} @ ${exit_price:.6f} | P&L: ${pnl_usd:.2f} ({pnl_pct:.2f}%) | {reason}")

        # Send PNL update to Discord
        self.send_pnl_update()

        return reason

    def mark_failed_trade(self, symbol: str, direction: TradeDirection, reason: str):
        """Mark a trade as failed to avoid repeat entries - PERMANENT BLOCK"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Normalize symbol for consistent blocking
        base_symbol = symbol.split(':')[0] if ':' in symbol else symbol

        # Create all possible symbol variations
        symbol_variants = [
            symbol,
            base_symbol,
            f"{base_symbol}:USDT",
            f"{base_symbol}:USDT:USDT"
        ]

        # Mark ALL variations as failed - be thorough
        for variant in symbol_variants:
            c.execute("""INSERT OR REPLACE INTO failed_trades (symbol, direction, entry_time, failure_reason)
                         VALUES (?, ?, ?, ?)""",
                      (variant, direction.value, datetime.now(timezone.utc), f"PERMANENT BLOCK: {reason}"))

        conn.commit()
        conn.close()

        logger.warning(f"🔒 PERMANENTLY BLOCKED: {symbol} {direction.value} - {reason} (all variants marked)")

    def is_failed_trade(self, symbol: str, direction: TradeDirection) -> bool:
        """STRICT CHECK: Block if this symbol/direction has ANY losing history - NO RETRIES"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Normalize symbol - handle all variations
        base_symbol = symbol.split(':')[0] if ':' in symbol else symbol
        base_only = base_symbol.split('/')[0] if '/' in base_symbol else base_symbol

        # Create all possible symbol variations to check
        symbol_patterns = [symbol, base_symbol, f"{base_symbol}:USDT", f"{base_symbol}:USDT:USDT", f"{base_only}/USDT", f"{base_only}/USDT:USDT"]

        # CHECK 1: Explicitly marked as failed
        placeholders = ','.join(['?'] * len(symbol_patterns))
        c.execute(f"""SELECT COUNT(*) FROM failed_trades
                     WHERE symbol IN ({placeholders}) AND direction = ?""",
                  (*symbol_patterns, direction.value))
        failed_count = c.fetchone()[0]

        # CHECK 2: ANY closed losing trade (negative P&L) - BLOCK IMMEDIATELY
        c.execute(f"""SELECT COUNT(*) FROM trades
                     WHERE symbol IN ({placeholders})
                     AND direction = ?
                     AND status != ?
                     AND pnl < 0""",
                  (*symbol_patterns, direction.value, TradeStatus.ACTIVE.value))
        losing_count = c.fetchone()[0]

        # CHECK 3: ANY stop loss hit - BLOCK IMMEDIATELY
        c.execute(f"""SELECT COUNT(*) FROM trades
                     WHERE symbol IN ({placeholders})
                     AND direction = ?
                     AND status = ?""",
                  (*symbol_patterns, direction.value, TradeStatus.CLOSED_STOP.value))
        stop_loss_count = c.fetchone()[0]

        conn.close()

        # BLOCK if ANY losing trade exists - NO EXCEPTIONS, NO RETRIES, MOVE ON TO NEXT COIN
        is_failed = (failed_count > 0) or (losing_count > 0) or (stop_loss_count > 0)

        if is_failed:
            logger.warning(f"🚫 PERMANENTLY BLOCKED: {symbol} {direction.value} - Failed marks: {failed_count}, Losing trades: {losing_count}, Stop losses: {stop_loss_count} - MOVING ON TO NEXT COIN")

        return is_failed

    def get_stats(self) -> Dict:
        """Get trading statistics"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT
                     COUNT(*) as total,
                     SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                     SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
                     SUM(pnl) as total_pnl
                     FROM trades WHERE status != ?""", (TradeStatus.ACTIVE.value,))
        row = c.fetchone()
        conn.close()

        if row and row[0]:
            return {
                'total_trades': row[0],
                'winning_trades': row[1] or 0,
                'losing_trades': row[2] or 0,
                'total_pnl': row[3] or 0.0
            }
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0
        }

    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent closed trades"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT symbol, direction, entry_price, exit_price, pnl, pnl_pct, exit_reason, exit_time
                     FROM trades WHERE status != ? ORDER BY exit_time DESC LIMIT ?""",
                  (TradeStatus.ACTIVE.value, limit))
        rows = c.fetchall()
        conn.close()

        trades = []
        for row in rows:
            trades.append({
                'symbol': row[0],
                'direction': row[1],
                'entry_price': row[2],
                'exit_price': row[3],
                'pnl': row[4],
                'pnl_pct': row[5],
                'exit_reason': row[6],
                'exit_time': row[7]
            })
        return trades

    def get_active_trades(self) -> List[Trade]:
        """Get all active trades"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""SELECT id, symbol, direction, entry_price, stop_loss, tp1, tp2,
                     position_size_usd, leverage, entry_time, status
                     FROM trades WHERE status = ?""", (TradeStatus.ACTIVE.value,))
        rows = c.fetchall()
        conn.close()

        trades = []
        for row in rows:
            trades.append(Trade(
                id=row[0],
                signal_id=row[0],
                symbol=row[1],
                direction=TradeDirection(row[2]),
                entry_price=row[3],
                stop_loss=row[4],
                tp1=row[5],
                tp2=row[6],
                position_size_usd=row[7],
                leverage=row[8],
                entry_time=datetime.fromisoformat(row[9]),
                status=TradeStatus(row[10]),
                current_price=row[3],
                unrealized_pnl=0.0,
                unrealized_pnl_pct=0.0
            ))
        return trades

    def send_pnl_update(self):
        """Send PNL update to Discord after trade closes"""
        recent_trades = self.get_recent_trades(10)
        if not recent_trades:
            return

        stats = self.get_stats()

        # Create embed
        embed = {
            "title": "💰 PNL Update - Last 10 Trades",
            "color": 0x00FF00 if stats['total_pnl'] > 0 else 0xFF0000,
            "fields": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Add recent trades
        trade_text = ""
        for trade in recent_trades[:10]:
            emoji = "🟢" if trade['pnl'] > 0 else "🔴"
            trade_text += f"{emoji} **{trade['symbol']}** {trade['direction']}\n"
            trade_text += f"   Entry: ${trade['entry_price']:.6f} → Exit: ${trade['exit_price']:.6f}\n"
            trade_text += f"   P&L: ${trade['pnl']:.2f} ({trade['pnl_pct']:.2f}%) | {trade['exit_reason']}\n\n"

        embed["fields"].append({
            "name": "Recent Trades",
            "value": trade_text[:1024] if len(trade_text) > 1024 else trade_text,
            "inline": False
        })

        # Add stats
        win_rate = (stats['winning_trades'] / stats['total_trades'] * 100) if stats['total_trades'] > 0 else 0
        embed["fields"].append({
            "name": "Statistics",
            "value": f"**Total Trades:** {stats['total_trades']}\n"
                    f"**Wins:** {stats['winning_trades']} | **Losses:** {stats['losing_trades']}\n"
                    f"**Win Rate:** {win_rate:.1f}%\n"
                    f"**Total P&L:** ${stats['total_pnl']:.2f}\n"
                    f"**Balance:** ${self.balance:.2f}",
            "inline": False
        })

        # Send to Discord
        try:
            payload = {"embeds": [embed]}
            r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
            r.raise_for_status()
            logger.info("📤 Sent PNL update to Discord")
        except Exception as e:
            logger.error(f"Failed to send PNL update: {e}")


def tv_link(symbol: str) -> str:
    """Generate TradingView link"""
    base = symbol.split("/")[0] if "/" in symbol else symbol.replace("USDT", "").replace("USDC", "")
    quote = "USDT" if "USDT" in symbol else "USDC"
    tv_symbol = f"BINANCE:{base.upper()}{quote.upper()}"
    return f"https://www.tradingview.com/chart/?symbol={tv_symbol}"


class IndicatorCalculator:
    """Calculate indicators from OHLCV data"""

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> float:
        """Calculate VWAP"""
        if len(df) == 0:
            return None
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        pv = (typical_price * df['volume']).sum()
        v = df['volume'].sum()
        return pv / v if v > 0 else None

    @staticmethod
    def calculate_gps_zones(high: float, low: float) -> Dict:
        """Calculate Golden Pocket zones (0.618 and 0.65)"""
        range_val = high - low
        gp_high = high - (range_val * 0.618)
        gp_low = high - (range_val * 0.65)
        return {'gp_high': gp_high, 'gp_low': gp_low}

    @staticmethod
    def detect_sfp(df: pd.DataFrame, timeframe: str) -> Tuple[bool, int, Optional[Dict]]:
        """Detect SFP (Fair Value Gap) - 3-candle FVG detection"""
        if len(df) < 3:
            return False, 0, None

        # 3-candle FVG detection (matching Pine Script logic)
        # Bullish FVG: gap between candle[2].low and candle[0].high (candle[1] is the gap)
        # Bearish FVG: gap between candle[2].high and candle[0].low

        sfp_info = None

        # Check for bullish FVG
        if len(df) >= 3:
            candle2_low = df['low'].iloc[-3]
            candle0_high = df['high'].iloc[-1]
            if candle2_low > candle0_high:
                gap_top = candle2_low
                gap_bottom = candle0_high
                sfp_info = {
                    'type': 'BULLISH',
                    'top': gap_top,
                    'bottom': gap_bottom,
                    'mid': (gap_top + gap_bottom) / 2
                }
                return True, 1, sfp_info

        # Check for bearish FVG
        if len(df) >= 3:
            candle2_high = df['high'].iloc[-3]
            candle0_low = df['low'].iloc[-1]
            if candle2_high < candle0_low:
                gap_top = candle0_low
                gap_bottom = candle2_high
                sfp_info = {
                    'type': 'BEARISH',
                    'top': gap_top,
                    'bottom': gap_bottom,
                    'mid': (gap_top + gap_bottom) / 2
                }
                return True, 1, sfp_info

        return False, 0, None

    @staticmethod
    def detect_elliott_wave3_pullback(df: pd.DataFrame, direction: str) -> bool:
        """Detect Elliott Wave 3 pullback pattern (ABC correction)"""
        if len(df) < 30:
            return False

        # Get recent price action (last 30 bars)
        recent = df.tail(30)
        highs = recent['high'].values
        lows = recent['low'].values
        closes = recent['close'].values

        if direction == "LONG":
            # Look for 3-wave down (ABC correction): A down, B up (retrace), C down (final)
            min_low = np.min(lows)
            min_low_idx = np.argmin(lows)

            if min_low_idx >= 5 and min_low_idx < len(lows) - 3:
                before_low = lows[:min_low_idx]
                if len(before_low) >= 3:
                    a_start = np.max(before_low[:3])
                    a_end = np.min(before_low[-3:]) if len(before_low) >= 3 else before_low[-1]

                    after_low = lows[min_low_idx+1:min_low_idx+5] if min_low_idx+5 < len(lows) else []
                    if len(after_low) > 0:
                        b_high = np.max(after_low)
                        # Pattern: A down -> B up -> C down to low
                        if a_start > a_end and b_high > min_low and min_low < a_end:
                            return True

        else:  # SHORT
            # Look for 3-wave up (ABC correction): A up, B down (retrace), C up (final)
            max_high = np.max(highs)
            max_high_idx = np.argmax(highs)

            if max_high_idx >= 5 and max_high_idx < len(highs) - 3:
                before_high = highs[:max_high_idx]
                if len(before_high) >= 3:
                    a_start = np.min(before_high[:3])
                    a_end = np.max(before_high[-3:]) if len(before_high) >= 3 else before_high[-1]

                    after_high = highs[max_high_idx+1:max_high_idx+5] if max_high_idx+5 < len(highs) else []
                    if len(after_high) > 0:
                        b_low = np.min(after_high)
                        # Pattern: A up -> B down -> C up to high
                        if a_start < a_end and b_low < max_high and max_high > a_end:
                            return True

        return False

    @staticmethod
    def detect_oath_keeper_divergence(df: pd.DataFrame) -> bool:
        """Detect Oath Keeper macro divergence (simplified - white circle print)"""
        if len(df) < 20:
            return False

        # Calculate money flow
        closes = df['close'].values
        volumes = df['volume'].values

        # Simple money flow calculation
        mf_period = 8
        if len(closes) < mf_period + 1:
            return False

        up_volume = []
        down_volume = []
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                up_volume.append(volumes[i])
                down_volume.append(0)
            elif closes[i] < closes[i-1]:
                up_volume.append(0)
                down_volume.append(volumes[i])
            else:
                up_volume.append(0)
                down_volume.append(0)

        if len(up_volume) < mf_period:
            return False

        mf_up = np.mean(up_volume[-mf_period:])
        mf_down = np.mean(down_volume[-mf_period:])

        if mf_up + mf_down == 0:
            return False

        money_flow = 100 * mf_up / (mf_up + mf_down)

        # Detect divergence: price makes lower low but money flow makes higher low (bullish)
        # or price makes higher high but money flow makes lower high (bearish)
        if len(closes) >= 10:
            # Look for pivot points
            recent_lows = closes[-10:]
            recent_mf = [money_flow] * 10  # Simplified

            # Bullish divergence: price lower low, MF higher low
            if closes[-1] < closes[-5] and money_flow > 50:  # Simplified check
                return True

        return False

    @staticmethod
    def check_vwap_trend(df_1h: pd.DataFrame, df_4h: pd.DataFrame, df_daily: pd.DataFrame) -> Tuple[str, float]:
        """Check VWAP trend: bullish stack (1H < 4H < Daily) or bearish (1H > 4H > Daily)
        Returns: (trend, strength) where strength is 0-100"""
        vwap_1h = IndicatorCalculator.calculate_vwap(df_1h) if len(df_1h) > 0 else None
        vwap_4h = IndicatorCalculator.calculate_vwap(df_4h) if len(df_4h) > 0 else None
        vwap_daily = IndicatorCalculator.calculate_vwap(df_daily) if len(df_daily) > 0 else None

        if not all([vwap_1h, vwap_4h, vwap_daily]):
            return "NEUTRAL", 0.0

        # Bullish stack: 1H < 4H < Daily
        if vwap_1h < vwap_4h < vwap_daily:
            # Calculate strength based on separation
            separation = ((vwap_daily - vwap_1h) / vwap_1h) * 100
            strength = min(100, max(0, separation * 10))  # Scale to 0-100
            return "BULLISH", strength

        # Bearish stack: 1H > 4H > Daily
        if vwap_1h > vwap_4h > vwap_daily:
            # Calculate strength based on separation
            separation = ((vwap_1h - vwap_daily) / vwap_daily) * 100
            strength = min(100, max(0, separation * 10))  # Scale to 0-100
            return "BEARISH", strength

        return "NEUTRAL", 0.0

    @staticmethod
    def detect_price_trend(df: pd.DataFrame, period: int = 50) -> str:
        """Detect price trend using EMA and price structure"""
        if len(df) < period:
            return "NEUTRAL"

        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values

        # Calculate EMA
        ema = pd.Series(closes).ewm(span=period, adjust=False).mean().values

        # Price relative to EMA
        price_above_ema = closes[-1] > ema[-1]
        price_below_ema = closes[-1] < ema[-1]

        # EMA slope
        ema_slope = ema[-1] - ema[-5] if len(ema) >= 5 else 0

        # Price structure (higher highs/lower lows)
        recent_highs = highs[-20:]
        recent_lows = lows[-20:]

        higher_highs = sum(1 for i in range(1, len(recent_highs)) if recent_highs[i] > recent_highs[i-1])
        lower_lows = sum(1 for i in range(1, len(recent_lows)) if recent_lows[i] < recent_lows[i-1])

        # Determine trend
        if price_above_ema and ema_slope > 0 and higher_highs > lower_lows:
            return "BULLISH"
        elif price_below_ema and ema_slope < 0 and lower_lows > higher_highs:
            return "BEARISH"

        return "NEUTRAL"

    @staticmethod
    def calculate_tactical_deviation(df_daily: pd.DataFrame) -> Optional[Dict]:
        """Calculate Tactical Deviation VWAP with ±1σ, ±2σ, ±3σ bands"""
        if df_daily is None or len(df_daily) < 20:
            return None

        # Calculate VWAP: sum(price * volume) / sum(volume)
        typical_price = (df_daily['high'] + df_daily['low'] + df_daily['close']) / 3.0
        sum_pv = (typical_price * df_daily['volume']).sum()
        sum_v = df_daily['volume'].sum()
        sum_pv2 = ((typical_price ** 2) * df_daily['volume']).sum()

        if sum_v == 0:
            return None

        vwap = sum_pv / sum_v

        # Calculate variance and standard deviation
        variance = (sum_pv2 / sum_v) - (vwap ** 2)
        std_dev = np.sqrt(max(variance, 0))

        if std_dev == 0:
            return None

        # Deviation bands: ±1σ, ±2σ, ±3σ
        return {
            "vwap": vwap,
            "std_dev": std_dev,
            "upper_1": vwap + (std_dev * 1.0),
            "lower_1": vwap - (std_dev * 1.0),
            "upper_2": vwap + (std_dev * 2.0),
            "lower_2": vwap - (std_dev * 2.0),
            "upper_3": vwap + (std_dev * 3.0),
            "lower_3": vwap - (std_dev * 3.0),
        }

    @staticmethod
    def get_deviation_level(price: float, deviation_data: Dict) -> Tuple[int, float]:
        """Get deviation level (0, 1, 2, 3) and deviation percentage"""
        if deviation_data is None:
            return 0, 0.0

        vwap = deviation_data["vwap"]
        std_dev = deviation_data["std_dev"]

        if std_dev == 0:
            return 0, 0.0

        dev_percent = ((price - vwap) / std_dev)

        level = 0
        if price >= deviation_data["upper_3"] or price <= deviation_data["lower_3"]:
            level = 3  # ±3σ = A+ reversal
        elif price >= deviation_data["upper_2"] or price <= deviation_data["lower_2"]:
            level = 2  # ±2σ = Plus (add to confluence)
        elif price >= deviation_data["upper_1"] or price <= deviation_data["lower_1"]:
            level = 1

        return level, dev_percent

    @staticmethod
    def detect_pivotx_pivots(df: pd.DataFrame, timeframe: str, atr_multiplier: float = 0.5,
                            volume_threshold: float = 1.5, exhaustion_periods: int = 3,
                            min_price_move: float = 2.0, atr_confirm_mult: float = 0.2) -> Dict:
        """
        PivotX Pro pivot detection - Updated with new logic from Pine Script
        Includes: ATR-based dynamic pivot strength, exhaustion detection, volume spikes
        """
        if len(df) < 30:
            return {
                'pivot_high': None,
                'pivot_low': None,
                'has_pivot': False,
                'pivot_type': None,
                'atr_confirmed': False,
                'is_aplus': False,
                'exhaustion': None,
                'volume_spike': False
            }

        # Calculate ATR (14-period)
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        volume = df['volume'].values
        open_price = df['open'].values if 'open' in df.columns else close

        # True Range calculation
        tr_list = []
        for i in range(1, len(df)):
            tr = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
            tr_list.append(tr)

        # ATR = SMA of TR over 14 periods
        if len(tr_list) >= 14:
            atr = np.mean(tr_list[-14:])
        else:
            atr = np.mean(tr_list) if tr_list else 0.001

        # Volume spike detection
        avg_vol = np.mean(volume[-20:]) if len(volume) >= 20 else np.mean(volume)
        vol_spike = volume[-1] > avg_vol * volume_threshold if len(volume) > 0 else False

        # Determine if lower timeframe (5m or less) vs higher timeframe (15m+)
        is_lower_tf = timeframe == "5m" or timeframe == "3m"
        is_higher_tf = timeframe in ["15m", "1h", "4h", "1d"]

        # Dynamic Pivot Strength - matching Pine Script logic
        # Calculate raw strength from ATR
        if atr > 0 and close[-1] > 0:
            # Use a simplified calculation (mintick approximation)
            mintick_approx = close[-1] * 0.0001  # Approximate minimum tick
            if mintick_approx > 0:
                pivot_strength_raw = max(2, int(atr / mintick_approx * atr_multiplier))
            else:
                pivot_strength_raw = 5
        else:
            pivot_strength_raw = 5

        # Cap based on timeframe (matching Pine Script)
        if is_lower_tf:
            min_strength = 5  # Higher minimum for lower TFs to filter noise
            max_strength = 15
        else:
            min_strength = 2
            max_strength = 20 if is_higher_tf else 20

        pivot_strength = max(min_strength, min(pivot_strength_raw, max_strength))

        # Detect pivot high and pivot low (most recent)
        pivot_high = None
        pivot_low = None
        pivot_high_idx = None
        pivot_low_idx = None

        # Look for most recent pivot high (scanning backwards from end)
        for i in range(len(high) - pivot_strength - 1, pivot_strength - 1, -1):
            is_ph = True
            for j in range(i - pivot_strength, i + pivot_strength + 1):
                if j != i and j < len(high) and high[j] >= high[i]:
                    is_ph = False
                    break
            if is_ph:
                pivot_high = high[i]
                pivot_high_idx = i
                break

        # Look for most recent pivot low (scanning backwards from end)
        for i in range(len(low) - pivot_strength - 1, pivot_strength - 1, -1):
            is_pl = True
            for j in range(i - pivot_strength, i + pivot_strength + 1):
                if j != i and j < len(low) and low[j] <= low[i]:
                    is_pl = False
                    break
            if is_pl:
                pivot_low = low[i]
                pivot_low_idx = i
                break

        # Exhaustion Detection
        exhaustion = None
        if len(close) >= exhaustion_periods + 1:
            price_change_pct = ((close[-1] - close[-exhaustion_periods-1]) / close[-exhaustion_periods-1]) * 100

            # Price direction
            price_rising = close[-1] > close[-2] if len(close) >= 2 else False
            price_falling = close[-1] < close[-2] if len(close) >= 2 else False

            # Sell exhaustion: price dropped significantly, volume spike, but not rising yet
            if price_change_pct <= -min_price_move and vol_spike and not price_rising:
                exhaustion = "SELL_EXHAUSTION"  # Potential reversal up

            # Buy exhaustion: price rallied significantly, volume spike, but not falling yet
            elif price_change_pct >= min_price_move and vol_spike and not price_falling:
                exhaustion = "BUY_EXHAUSTION"  # Potential reversal down

        # ATR Confirmation - price must close beyond pivot +/- (ATR * multiplier)
        atr_confirmed_ph = False
        atr_confirmed_pl = False

        if pivot_high is not None and len(close) > 0:
            # For pivot high: price must close below pivot - (ATR * mult)
            atr_confirmed_ph = close[-1] < (pivot_high - (atr * atr_confirm_mult))

        if pivot_low is not None and len(close) > 0:
            # For pivot low: price must close above pivot + (ATR * mult)
            atr_confirmed_pl = close[-1] > (pivot_low + (atr * atr_confirm_mult))

        # Determine pivot type and A+ setup
        has_pivot = (pivot_high is not None) or (pivot_low is not None)
        pivot_type = None
        is_aplus = False

        # A+ setup: ATR-confirmed pivot (major pivot)
        if atr_confirmed_pl:
            pivot_type = "PIVOT_LOW"
            is_aplus = True  # A+ setup when ATR-confirmed pivot low
        elif atr_confirmed_ph:
            pivot_type = "PIVOT_HIGH"
            is_aplus = True  # A+ setup when ATR-confirmed pivot high
        elif pivot_low is not None:
            pivot_type = "PIVOT_LOW"
        elif pivot_high is not None:
            pivot_type = "PIVOT_HIGH"

        return {
            'pivot_high': pivot_high,
            'pivot_low': pivot_low,
            'pivot_high_idx': pivot_high_idx,
            'pivot_low_idx': pivot_low_idx,
            'has_pivot': has_pivot,
            'pivot_type': pivot_type,
            'atr_confirmed': atr_confirmed_ph or atr_confirmed_pl,
            'is_aplus': is_aplus,
            'timeframe': timeframe,
            'exhaustion': exhaustion,
            'volume_spike': vol_spike,
            'atr': atr,
            'pivot_strength': pivot_strength
        }

    @staticmethod
    def detect_pivotx_mtf_confluence(df_5m: pd.DataFrame, df_15m: pd.DataFrame, df_1h: pd.DataFrame) -> Dict:
        """
        Check for PivotX Pro multi-timeframe confluence (5m, 15m, 1h)
        Returns A+ setup if pivots align across timeframes with exhaustion signals
        """
        if df_5m is None or df_15m is None or df_1h is None:
            return {
                'is_aplus_setup': False,
                'aplus_count': 0,
                'has_pivot_low': False,
                'pivot_types': [],
                'timeframes': [],
                'exhaustion_signals': []
            }

        pivots_5m = IndicatorCalculator.detect_pivotx_pivots(df_5m, "5m")
        pivots_15m = IndicatorCalculator.detect_pivotx_pivots(df_15m, "15m")
        pivots_1h = IndicatorCalculator.detect_pivotx_pivots(df_1h, "1h")

        # Count A+ pivots across timeframes
        aplus_count = 0
        pivot_types = []
        timeframes_with_pivots = []
        exhaustion_signals = []

        for tf_name, pivot_data in [("5m", pivots_5m), ("15m", pivots_15m), ("1h", pivots_1h)]:
            if pivot_data['is_aplus']:
                aplus_count += 1
                pivot_types.append(pivot_data['pivot_type'])
                timeframes_with_pivots.append(tf_name)

            # Track exhaustion signals (especially sell exhaustion for long entries)
            if pivot_data.get('exhaustion'):
                exhaustion_signals.append({
                    'timeframe': tf_name,
                    'type': pivot_data['exhaustion']
                })

        # A+ setup: at least 2 timeframes with ATR-confirmed pivots, or 1h A+ pivot
        # Extra boost if exhaustion signals are present
        is_aplus_setup = (aplus_count >= 2) or (pivots_1h['is_aplus'])

        # If we have sell exhaustion on 1h or multiple timeframes, it's a strong A+ setup
        sell_exhaustion_count = sum(1 for e in exhaustion_signals if e['type'] == 'SELL_EXHAUSTION')
        if sell_exhaustion_count >= 1 and (pivots_1h['is_aplus'] or aplus_count >= 1):
            is_aplus_setup = True

        # Prefer pivot lows for long entries (especially with sell exhaustion)
        has_pivot_low = any(p['pivot_type'] == 'PIVOT_LOW' and p['is_aplus']
                           for p in [pivots_5m, pivots_15m, pivots_1h])

        # Extra strong: pivot low + sell exhaustion
        has_pivot_low_exhaustion = (has_pivot_low and sell_exhaustion_count >= 1)

        return {
            'is_aplus_setup': is_aplus_setup,
            'aplus_count': aplus_count,
            'has_pivot_low': has_pivot_low,
            'has_pivot_low_exhaustion': has_pivot_low_exhaustion,
            'pivot_types': pivot_types,
            'timeframes': timeframes_with_pivots,
            'exhaustion_signals': exhaustion_signals,
            'sell_exhaustion_count': sell_exhaustion_count,
            'pivots_5m': pivots_5m,
            'pivots_15m': pivots_15m,
            'pivots_1h': pivots_1h
        }


class BountySeekerScanner:
    """Main scanner for Bounty Seeker bot"""

    def __init__(self, exchange: ccxt.Exchange):
        self.exchange = exchange
        self.last_scan_time = {}
        self.signals_this_hour = []
        self.hour_start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    def get_futures_pairs(self) -> List[str]:
        """Get whitelisted MEXC futures perpetual pairs from screenshots only"""
        pairs = []
        try:
            # Get all active perpetual swap markets with USDT quote
            for symbol, market in self.exchange.markets.items():
                if (market.get('type') == 'swap' and
                    market.get('active', True) and
                    market.get('quote') == 'USDT'):

                    # Extract base symbol (e.g., "BTC/USDT:USDT" -> "BTC", "EUR/USDT" -> "EUR")
                    base_symbol = symbol.split('/')[0].split(':')[0]

                    # Only include coins from the whitelist
                    if base_symbol in ALLOWED_COINS:
                        pairs.append(symbol)

            logger.info(f"📊 Found {len(pairs)} whitelisted MEXC futures pairs (from screenshots only)")
            logger.info(f"✅ Whitelisted coins: {sorted(ALLOWED_COINS)}")
            return pairs
        except Exception as e:
            logger.error(f"Error fetching futures pairs: {e}")
            return []

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 200) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.debug(f"Error fetching {symbol} {timeframe}: {e}")
            return None

    def scan_symbol(self, symbol: str) -> Optional[Signal]:
        """Scan a single symbol for trading signals with PivotX Pro"""
        try:
            # Fetch data for multiple timeframes (including 5m for PivotX Pro)
            df_5m = self.fetch_ohlcv(symbol, '5m', 200)
            df_15m = self.fetch_ohlcv(symbol, '15m', 200)
            df_1h = self.fetch_ohlcv(symbol, '1h', 200)
            df_4h = self.fetch_ohlcv(symbol, '4h', 200)
            df_daily = self.fetch_ohlcv(symbol, '1d', 200)

            if df_15m is None or len(df_15m) < 50:
                return None

            current_price = df_15m['close'].iloc[-1]
            current_high = df_15m['high'].iloc[-1]
            current_low = df_15m['low'].iloc[-1]

            reasons = []
            confluence_score = 0.0
            direction = None

            # 1. Check GPS (Golden Pocket) zones
            daily_high = df_daily['high'].max() if df_daily is not None and len(df_daily) > 0 else current_high
            daily_low = df_daily['low'].min() if df_daily is not None and len(df_daily) > 0 else current_low

            gps_zones = IndicatorCalculator.calculate_gps_zones(daily_high, daily_low)
            gp_high = gps_zones['gp_high']
            gp_low = gps_zones['gp_low']

            gps_touched = False
            if gp_low <= current_price <= gp_high:
                gps_touched = True
                confluence_score += 25
                reasons.append("✅ Price at Golden Pocket zone (0.618-0.65)")

            # 2. Check Oath Keeper divergence (macro) - check multiple timeframes
            oath_div = False
            oath_keeper_tf = "None"

            # Check daily first (macro - highest priority)
            if df_daily is not None and len(df_daily) >= 20:
                oath_div = IndicatorCalculator.detect_oath_keeper_divergence(df_daily)
                if oath_div:
                    oath_keeper_tf = "Daily"
                    confluence_score += 30
                    reasons.append("✅ Macro divergence detected (Oath Keeper white circle) - **Daily timeframe**")

            # Also check 4H for macro divergences
            if not oath_div and df_4h is not None and len(df_4h) >= 20:
                oath_div = IndicatorCalculator.detect_oath_keeper_divergence(df_4h)
                if oath_div:
                    oath_keeper_tf = "4H"
                    confluence_score += 25  # Slightly less than daily
                    reasons.append("✅ Macro divergence detected (Oath Keeper white circle) - **4H timeframe**")

            # 3. Check SFP levels (15min, 1h, 4h) - 3 levels of confluence
            sfp_levels = 0
            sfp_details = []

            for tf_name, tf_df in [('15m', df_15m), ('1h', df_1h), ('4h', df_4h)]:
                if tf_df is not None and len(tf_df) >= 3:
                    has_sfp, levels, sfp_info = IndicatorCalculator.detect_sfp(tf_df, tf_name)
                    if has_sfp and sfp_info:
                        sfp_levels += 1
                        sfp_details.append({
                            'timeframe': tf_name,
                            'type': sfp_info['type'],
                            'mid': sfp_info['mid']
                        })

            # Track which timeframes have SFPs
            sfp_timeframes = [sfp['timeframe'] for sfp in sfp_details]

            if sfp_levels >= 3:
                confluence_score += 30
                tf_list = ", ".join(sfp_timeframes)
                reasons.append(f"✅ SFP 3-level confluence: {sfp_levels} levels - **Timeframes: {tf_list}**")
            elif sfp_levels >= 2:
                confluence_score += 20
                tf_list = ", ".join(sfp_timeframes)
                reasons.append(f"✅ SFP confluence: {sfp_levels} levels - **Timeframes: {tf_list}**")
            elif sfp_levels >= 1:
                confluence_score += 10
                tf_list = ", ".join(sfp_timeframes)
                reasons.append(f"✅ SFP detected: {sfp_levels} level - **Timeframe: {tf_list}**")

            # 4. Check Elliott Wave 3 pullback - check multiple timeframes
            wave3_pullback = False
            wave3_tf = "None"

            # Check 15m first
            if df_15m is not None and len(df_15m) >= 30:
                wave3_long = IndicatorCalculator.detect_elliott_wave3_pullback(df_15m, "LONG")
                wave3_short = IndicatorCalculator.detect_elliott_wave3_pullback(df_15m, "SHORT")
                if wave3_long or wave3_short:
                    wave3_pullback = True
                    wave3_tf = "15m"
                    confluence_score += 15
                    reasons.append("✅ Elliott Wave 3 pullback detected (ABC correction) - **15m timeframe**")

            # Also check 1H (higher timeframe = better)
            if not wave3_pullback and df_1h is not None and len(df_1h) >= 30:
                wave3_long = IndicatorCalculator.detect_elliott_wave3_pullback(df_1h, "LONG")
                wave3_short = IndicatorCalculator.detect_elliott_wave3_pullback(df_1h, "SHORT")
                if wave3_long or wave3_short:
                    wave3_pullback = True
                    wave3_tf = "1H"
                    confluence_score += 18  # Higher timeframe = more points
                    reasons.append("✅ Elliott Wave 3 pullback detected (ABC correction) - **1H timeframe**")

            # 5. Check VWAP trend (with strength) - uses 1H, 4H, Daily
            vwap_trend, vwap_strength = IndicatorCalculator.check_vwap_trend(df_1h, df_4h, df_daily)
            vwap_trend_tf = "1H/4H/Daily"  # VWAP stack uses multiple timeframes

            # 6. Check price trend (EMA + price structure)
            price_trend_4h = IndicatorCalculator.detect_price_trend(df_4h, 50) if df_4h is not None and len(df_4h) >= 50 else "NEUTRAL"
            price_trend_daily = IndicatorCalculator.detect_price_trend(df_daily, 50) if df_daily is not None and len(df_daily) >= 50 else "NEUTRAL"

            # Overall trend: prioritize higher timeframe
            overall_trend = price_trend_daily if price_trend_daily != "NEUTRAL" else price_trend_4h
            overall_trend_tf = "Daily" if price_trend_daily != "NEUTRAL" else "4H"
            if overall_trend == "NEUTRAL":
                overall_trend = vwap_trend  # Fallback to VWAP trend
                overall_trend_tf = "VWAP Stack"

            # Trend alignment score (for longs at bottoms, even bearish markets can have good bounces)
            trend_aligned = False
            if overall_trend == "BULLISH" and vwap_trend == "BULLISH":
                trend_aligned = True
                confluence_score += 20  # Boost for bullish alignment
                reasons.append(f"✅ Strong BULLISH trend - VWAP stack + Price structure aligned - **Trend from: {overall_trend_tf}**")
            elif vwap_trend == "BULLISH":
                confluence_score += 10
                reasons.append(f"⚠️ VWAP bullish but price trend neutral - **Trend from: {overall_trend_tf}**")
            elif overall_trend == "BEARISH":
                # Even in bearish markets, we can catch bounces at extreme lows
                # Don't block, but don't add points either
                reasons.append(f"⚠️ Bearish trend but hunting for bottom bounces - **Trend from: {overall_trend_tf}**")

            # 7. Check Tactical Deviation (Daily VWAP with ±2σ and ±3σ bands) - main long filter
            tactical_dev = IndicatorCalculator.calculate_tactical_deviation(df_daily)
            deviation_level = 0
            deviation_pct = 0.0
            is_aplus_reversal = False

            if tactical_dev:
                deviation_level, deviation_pct = IndicatorCalculator.get_deviation_level(current_price, tactical_dev)

                if deviation_level >= 3:  # ±3σ = A++ swing candidate
                    is_aplus_reversal = True
                    confluence_score += 30  # Stronger weighting
                    reasons.append(f"✅ A++ REVERSAL: Price at ±3σ deviation ({deviation_pct:.2f}σ) - **Daily VWAP**")
                elif deviation_level >= 2:  # ±2σ = A+ scalp candidate
                    confluence_score += 20
                    reasons.append(f"✅ A+ REVERSAL: Price at ±2σ deviation ({deviation_pct:.2f}σ) - **Daily VWAP**")

            # 8. Check PivotX Pro pivots (5m, 15m, 1h) for A+ setups - UPDATED LOGIC
            pivotx_confluence = None
            pivotx_tfs = []
            if df_5m is not None and df_15m is not None and df_1h is not None:
                pivotx_confluence = IndicatorCalculator.detect_pivotx_mtf_confluence(df_5m, df_15m, df_1h)

                if pivotx_confluence['is_aplus_setup']:
                    # A+ setup: significant boost to confluence
                    if pivotx_confluence['aplus_count'] >= 2:
                        confluence_score += 40  # Multi-timeframe A+ pivot confluence (increased)
                        tf_list = ", ".join(pivotx_confluence['timeframes'])
                        reasons.append(f"✅ A+ PIVOTX PRO: {pivotx_confluence['aplus_count']} timeframes with ATR-confirmed pivots - **Timeframes: {tf_list}**")
                    elif pivotx_confluence['pivots_1h']['is_aplus']:
                        confluence_score += 30  # 1H A+ pivot is strong (increased)
                        reasons.append(f"✅ A+ PIVOTX PRO: 1H ATR-confirmed pivot - **1H timeframe**")

                    # Extra boost for pivot lows (better for long entries)
                    if pivotx_confluence['has_pivot_low']:
                        confluence_score += 20  # Increased boost
                        reasons.append("✅ PivotX Pro: ATR-confirmed Pivot Low detected (optimal for long entries)")

                    # EXHAUSTION SIGNALS - Strong reversal indicator
                    if pivotx_confluence.get('sell_exhaustion_count', 0) >= 1:
                        confluence_score += 25  # Strong boost for sell exhaustion (potential reversal up)
                        exhaustion_tfs = [e['timeframe'] for e in pivotx_confluence.get('exhaustion_signals', [])
                                         if e['type'] == 'SELL_EXHAUSTION']
                        tf_list = ", ".join(exhaustion_tfs)
                        reasons.append(f"✅ PivotX Pro: SELL EXHAUSTION detected - Potential reversal up - **Timeframes: {tf_list}**")

                    # Extra strong: Pivot Low + Sell Exhaustion = Best setup
                    if pivotx_confluence.get('has_pivot_low_exhaustion', False):
                        confluence_score += 15  # Additional boost
                        reasons.append("✅ PivotX Pro: A+ SETUP - Pivot Low + Sell Exhaustion (Best reversal signal)")

                    pivotx_tfs = pivotx_confluence['timeframes']

            # Determine direction: LONGS ONLY - RELAXED to catch bottoms
            # Priority: PivotX Pro A+ setups can override strict requirements

            # Check if we have a strong PivotX Pro A+ setup
            has_pivotx_aplus = pivotx_confluence and pivotx_confluence.get('is_aplus_setup', False)
            has_pivotx_exhaustion = pivotx_confluence and pivotx_confluence.get('sell_exhaustion_count', 0) >= 1
            has_pivotx_low = pivotx_confluence and pivotx_confluence.get('has_pivot_low', False)

            # GP proximity check (more lenient)
            gp_near = gps_touched
            if not gp_near:
                # More lenient: within 3% of GP zone (increased from 2%)
                gp_near = abs(current_price - gp_low) / current_price <= 0.03 or abs(current_price - gp_high) / current_price <= 0.03

            # Deviation check (optional if we have strong PivotX Pro)
            deviation_ok = deviation_level >= 1
            strong_deviation = deviation_level >= 2

            # Extra confirmation: include PivotX Pro signals
            extra_confirm = (wave3_pullback or (sfp_levels >= 1) or oath_div or strong_deviation or
                           has_pivotx_aplus or has_pivotx_exhaustion)

            # VERY RELAXED REQUIREMENTS to catch bottoms:
            # Priority 1: PivotX Pro A+ setup (strongest signal - minimal other requirements)
            if has_pivotx_aplus and confluence_score >= 35:
                direction = TradeDirection.LONG
                if has_pivotx_exhaustion:
                    reasons.append("✅ Long: PivotX Pro A+ with SELL EXHAUSTION - Strong reversal signal")
                elif has_pivotx_low:
                    reasons.append("✅ Long: PivotX Pro A+ Pivot Low - Reversal setup")
                else:
                    reasons.append("✅ Long: PivotX Pro A+ setup - Multi-timeframe pivot confluence")

            # Priority 2: Good confluence with at least one strong signal
            elif confluence_score >= 40 and extra_confirm:
                direction = TradeDirection.LONG
                if has_pivotx_aplus:
                    reasons.append("✅ Long: PivotX Pro A+ + other confluence")
                elif strong_deviation:
                    reasons.append("✅ Long: Strong deviation (≥2σ) + confluence")
                elif oath_div:
                    reasons.append("✅ Long: Oath Keeper divergence + confluence")
                elif wave3_pullback:
                    reasons.append("✅ Long: Elliott Wave 3 pullback + confluence")
                elif sfp_levels >= 1:
                    reasons.append("✅ Long: SFP detected + confluence")
                else:
                    reasons.append("✅ Long: Good confluence score")

            # Priority 3: Lower threshold but still need some confirmation
            elif confluence_score >= 50 and (gp_near or deviation_ok or has_pivotx_aplus):
                direction = TradeDirection.LONG
                reasons.append("✅ Long: High confluence + (GP or Deviation or PivotX)")
            else:
                # Log rejection reasons for troubleshooting (only if score is close)
                if confluence_score >= 30:  # Only log if it's close to passing
                    logger.info(f"🔍 {symbol} CLOSE - Score: {confluence_score:.0f}, GP: {gp_near}, Dev: {deviation_level}, "
                               f"PivotX A+: {has_pivotx_aplus}, Exhaustion: {has_pivotx_exhaustion}, "
                               f"Extra: {extra_confirm} (Wave3: {wave3_pullback}, SFP: {sfp_levels}, Oath: {oath_div})")
                return None

            # Calculate entry, stop, and targets (long only)
            entry_price = current_price
            stop_loss = entry_price * (1 - STOP_LOSS_PCT)
            tp1 = entry_price * (1 + TP1_PCT)
            tp2 = entry_price * (1 + TP2_PCT)

            # Adjust confidence for A+ reversals
            base_confidence = min(confluence_score / 100.0, 1.0)
            if is_aplus_reversal:
                base_confidence = min(base_confidence * 1.2, 1.0)  # Boost confidence for A+ reversals

            trade_kind = "SWING" if is_aplus_reversal else "SCALP"

            signal = Signal(
                symbol=symbol,
                direction=direction,
                trade_kind=trade_kind,
                entry_price=entry_price,
                stop_loss=stop_loss,
                tp1=tp1,
                tp2=tp2,
                confidence=base_confidence,
                confluence_score=confluence_score,
                reasons=reasons,
                timeframe="15m",
                timestamp=datetime.now(timezone.utc),
                gps_touched=gps_touched,
                oath_keeper_div=oath_div,
                oath_keeper_tf=oath_keeper_tf,
                sfp_levels=sfp_levels,
                sfp_timeframes=sfp_timeframes,
                vwap_trend=overall_trend,
                vwap_trend_tf=overall_trend_tf,
                wave3_tf=wave3_tf,
                chart_url=tv_link(symbol)
            )

            return signal

        except Exception as e:
            logger.debug(f"Error scanning {symbol}: {e}")
            return None

    def check_sfp_approaching(self, symbol: str) -> Optional[Dict]:
        """Check if price is approaching an SFP (for notifications) - returns probability score"""
        try:
            df_15m = self.fetch_ohlcv(symbol, '15m', 50)
            df_1h = self.fetch_ohlcv(symbol, '1h', 50)
            df_4h = self.fetch_ohlcv(symbol, '4h', 50)
            df_daily = self.fetch_ohlcv(symbol, '1d', 50)

            if df_15m is None or len(df_15m) < 3:
                return None

            current_price = df_15m['close'].iloc[-1]
            approaching_sfps = []
            probability_score = 0.0

            # Check SFPs across timeframes
            for tf_name, tf_df in [('15m', df_15m), ('1h', df_1h), ('4h', df_4h)]:
                if tf_df is not None and len(tf_df) >= 3:
                    has_sfp, levels, sfp_info = IndicatorCalculator.detect_sfp(tf_df, tf_name)
                    if has_sfp and sfp_info:
                        distance_pct = abs(current_price - sfp_info['mid']) / current_price * 100
                        if distance_pct < 1.0:  # Within 1% of SFP
                            # Higher timeframe = higher probability
                            tf_weight = {'15m': 1.0, '1h': 1.5, '4h': 2.0}.get(tf_name, 1.0)
                            # Closer = higher probability
                            distance_score = (1.0 - distance_pct / 1.0) * 100

                            approaching_sfps.append({
                                'timeframe': tf_name,
                                'type': sfp_info['type'],
                                'mid': sfp_info['mid'],
                                'distance_pct': distance_pct
                            })

                            probability_score += distance_score * tf_weight

            if approaching_sfps:
                # Check for additional confluence factors
                # GPS proximity
                if df_daily is not None and len(df_daily) > 0:
                    daily_high = df_daily['high'].max()
                    daily_low = df_daily['low'].min()
                    gps_zones = IndicatorCalculator.calculate_gps_zones(daily_high, daily_low)
                    distance_to_gp = min(abs(current_price - gps_zones['gp_high']),
                                        abs(current_price - gps_zones['gp_low'])) / current_price * 100
                    if distance_to_gp < 2.0:  # Near GPS
                        probability_score += 20

                # NO VOLUME FILTER - All market caps are valid, especially smaller caps for pump potential
                # Removed volume-based scoring to focus on all caps, not just big caps

                # More SFP levels = higher probability
                if len(approaching_sfps) >= 2:
                    probability_score += 25
                elif len(approaching_sfps) >= 1:
                    probability_score += 10

                return {
                    'symbol': symbol,
                    'current_price': current_price,
                    'sfps': approaching_sfps,
                    'chart_url': tv_link(symbol),
                    'probability_score': probability_score
                }
            return None
        except:
            return None

    def scan_all(self) -> Tuple[List[Signal], List[Dict]]:
        """Scan all symbols and return signals + SFP notifications (watchlist removed)"""
        # Check if we've hit the hourly limit
        current_hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        if current_hour > self.hour_start:
            self.signals_this_hour = []
            self.hour_start = current_hour

        if len(self.signals_this_hour) >= MAX_SIGNALS_PER_HOUR:
            logger.info(f"Hourly signal limit reached ({MAX_SIGNALS_PER_HOUR})")
            return [], []

        pairs = self.get_futures_pairs()
        signals = []

        # Scan ALL pairs for long opportunities (no watchlist)
        logger.info(f"🔍 Scanning {len(pairs)} pairs for long bottom opportunities...")
        for symbol in pairs:
            # Check if we've already signaled this symbol this hour
            if any(s.symbol == symbol for s in self.signals_this_hour):
                continue

            signal = self.scan_symbol(symbol)
            if signal:
                signals.append(signal)
                self.signals_this_hour.append(signal)
                logger.info(f"✅ Found LONG signal: {signal.symbol} (Confluence: {signal.confluence_score:.0f})")

                if len(signals) >= MAX_SIGNALS_PER_HOUR:
                    break

        # Check for SFP approaching notifications (potential setups)
        # Get best probable SFPs (max 3, ranked by probability)
        sfp_notifications = []
        sfp_candidates = []

        # Scan ALL pairs for SFP opportunities (no volume limit - focusing on all caps, especially smaller ones that will pump)
        for symbol in pairs:
            sfp_info = self.check_sfp_approaching(symbol)
            if sfp_info:
                sfp_candidates.append(sfp_info)

        # Sort by probability score (highest first) and take top 3
        if sfp_candidates:
            sfp_candidates.sort(key=lambda x: x.get('probability_score', 0), reverse=True)
            sfp_notifications = sfp_candidates[:3]  # Max 3 best probable SFPs

        # Post-process: Only provide 2 scalps + 1 swing (longs only)
        swings = [s for s in signals if s.trade_kind == "SWING"]
        scalps = [s for s in signals if s.trade_kind == "SCALP"]

        swings_sorted = sorted(swings, key=lambda x: x.confluence_score, reverse=True)
        scalps_sorted = sorted(scalps, key=lambda x: x.confluence_score, reverse=True)

        final_signals = []
        if swings_sorted:
            final_signals.append(swings_sorted[0])  # Top swing
        final_signals.extend(scalps_sorted[:2])     # Top 2 scalps

        logger.info(f"📊 Scan complete: {len(final_signals)} signals found ({len(swings)} swings, {len(scalps)} scalps)")
        return final_signals, sfp_notifications


class BountySeekerBot:
    """Main Bounty Seeker bot"""

    def __init__(self):
        self.exchange = None
        self.scanner = None
        self.paper_account = PaperTradingAccount()
        self.init_exchange()

    def init_exchange(self):
        """Initialize MEXC exchange"""
        try:
            self.exchange = ccxt.mexc({
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'},
                'timeout': 30000
            })
            self.exchange.load_markets()
            self.scanner = BountySeekerScanner(self.exchange)
            logger.info("✅ MEXC exchange initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MEXC: {e}")
            raise

    def send_sfp_notifications_batch(self, sfp_notifications: List[Dict]):
        """Send all SFP approaching notifications in one card (top 3 most probable)"""
        if not sfp_notifications:
            return

        embed = {
            "title": f"🔔 SFP Approaching - Top {len(sfp_notifications)} Most Probable",
            "color": 0xFFD700,  # Gold
            "description": "Price approaching Smart Fibonacci Points (Fair Value Gaps) - Ranked by probability",
            "fields": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        for idx, sfp_info in enumerate(sfp_notifications, 1):
            prob_score = sfp_info.get('probability_score', 0)
            sfp_text = f"**Rank #{idx}** | Probability Score: {prob_score:.0f}\n"
            sfp_text += f"**Price:** ${sfp_info['current_price']:.6f}\n"
            sfp_text += "**Approaching SFPs:**\n"

            for sfp in sfp_info['sfps']:
                tf_emoji = "🟢" if sfp['timeframe'] == '4h' else "🟡" if sfp['timeframe'] == '1h' else "🔵"
                sfp_text += f"{tf_emoji} {sfp['timeframe']} {sfp['type']} - ${sfp['mid']:.6f} ({sfp['distance_pct']:.2f}% away)\n"

            sfp_text += f"\n[Chart]({sfp_info['chart_url']})"

            embed["fields"].append({
                "name": f"{sfp_info['symbol']}",
                "value": sfp_text,
                "inline": False
            })

        embed["footer"] = {
            "text": "Top 3 most probable SFPs based on distance, timeframe, GPS proximity, volume, and confluence"
        }

        try:
            payload = {"embeds": [embed]}
            r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
            r.raise_for_status()
            logger.info(f"📤 Sent {len(sfp_notifications)} SFP notifications in one card (top probable)")
        except Exception as e:
            logger.error(f"Failed to send SFP notifications: {e}")

    def send_discord_signal(self, signal: Signal):
        """Send signal to Discord"""
        # Check if this is an A+ reversal (look for ±3σ in reasons)
        is_aplus = any("A+ REVERSAL" in reason or "±3σ" in reason for reason in signal.reasons)
        if is_aplus:
            color = 0xFFD700  # Gold for A+ reversals
            title = f"⭐ A+ REVERSAL: {signal.symbol} {signal.direction.value}"
        else:
            color = 0x00FF00 if signal.direction == TradeDirection.LONG else 0x9370DB  # Green for long, Purple for short
            title = f"🎯 Bounty Seeker Signal: {signal.symbol} {signal.direction.value}"

        embed = {
            "title": title,
            "color": color,
            "fields": [
                {
                    "name": "Direction",
                    "value": f"**{signal.direction.value}**",
                    "inline": True
                },
                {
                    "name": "Entry Price",
                    "value": f"${signal.entry_price:.6f}",
                    "inline": True
                },
                {
                    "name": "Confluence Score",
                    "value": f"{signal.confluence_score:.0f}/100",
                    "inline": True
                },
                {
                    "name": "Stop Loss",
                    "value": f"${signal.stop_loss:.6f}",
                    "inline": True
                },
                {
                    "name": "Take Profit 1",
                    "value": f"${signal.tp1:.6f} ({TP1_PCT*100:.2f}%)",
                    "inline": True
                },
                {
                    "name": "Take Profit 2",
                    "value": f"${signal.tp2:.6f} ({TP2_PCT*100:.2f}%)",
                    "inline": True
                },
                {
                    "name": "Why This Trade?",
                    "value": "\n".join(signal.reasons) if signal.reasons else "Multiple confluence factors",
                    "inline": False
                },
                {
                    "name": "Indicators & Timeframes",
                    "value": f"GPS: {'✅' if signal.gps_touched else '❌'} (Daily)\n"
                            f"Oath Keeper Div: {'✅' if signal.oath_keeper_div else '❌'} **{signal.oath_keeper_tf}**\n"
                            f"SFP Levels: {signal.sfp_levels}/3 - **Timeframes: {', '.join(signal.sfp_timeframes) if signal.sfp_timeframes else 'None'}**\n"
                            f"Wave 3 Pullback: {'✅' if signal.wave3_tf != 'None' else '❌'} **{signal.wave3_tf}**\n"
                            f"VWAP Trend: {signal.vwap_trend} - **From: {signal.vwap_trend_tf}**\n"
                            f"Tactical Deviation: **Daily VWAP**",
                    "inline": False
                }
            ],
            "timestamp": signal.timestamp.isoformat(),
            "url": signal.chart_url
        }

        try:
            payload = {"embeds": [embed]}
            r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
            r.raise_for_status()
            logger.info(f"📤 Sent signal to Discord: {signal.symbol}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")


    def send_multiple_signals(self, signals: List[Signal]):
        """Send multiple signals in one card"""
        if not signals:
            return

        # Use white card with colors to differentiate
        embed = {
            "title": f"🎯 Bounty Seeker Signals ({len(signals)} trades)",
            "color": 0xFFFFFF,  # White
            "fields": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        for signal in signals:
            color_emoji = "🟢" if signal.direction == TradeDirection.LONG else "🟣"
            field_value = f"{color_emoji} **{signal.symbol} {signal.direction.value}**\n"
            field_value += f"Entry: ${signal.entry_price:.6f} | TP1: ${signal.tp1:.6f} ({TP1_PCT*100:.2f}%)\n"
            field_value += f"Confluence: {signal.confluence_score:.0f}/100\n"
            field_value += "\n".join(signal.reasons[:2])  # First 2 reasons
            field_value += f"\n[Chart]({signal.chart_url})"

            embed["fields"].append({
                "name": f"{signal.symbol}",
                "value": field_value,
                "inline": False
            })

        try:
            payload = {"embeds": [embed]}
            r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
            r.raise_for_status()
            logger.info(f"📤 Sent {len(signals)} signals in one card")
        except Exception as e:
            logger.error(f"Failed to send multiple signals: {e}")

    def update_active_trades(self):
        """Update all active trades and check for exits"""
        active_trades = self.paper_account.get_active_trades()

        for trade in active_trades:
            try:
                ticker = self.exchange.fetch_ticker(trade.symbol)
                current_price = float(ticker['last'])

                exit_reason = self.paper_account.update_trade(trade, current_price)
                if exit_reason:
                    logger.info(f"Trade closed: {trade.symbol} - {exit_reason}")
            except Exception as e:
                logger.error(f"Error updating trade {trade.symbol}: {e}")

    def run_scan(self):
        """Run a single scan"""
        logger.info("🔍 Starting Bounty Seeker scan...")

        # Update active trades first
        self.update_active_trades()

        # Scan for new signals (watchlist removed)
        signals, sfp_notifications = self.scanner.scan_all()

        # Send SFP approaching notifications (batched in one card)
        if sfp_notifications:
            self.send_sfp_notifications_batch(sfp_notifications)

        # Send signals to Discord
        if signals:
            if len(signals) == 1:
                self.send_discord_signal(signals[0])
            else:
                self.send_multiple_signals(signals)

            # Enter trades
            for signal in signals:
                if self.paper_account.can_enter_trade():
                    trade = self.paper_account.enter_trade(signal)
                    if trade:
                        # Send entry notification
                        self.send_trade_entry_notification(trade, signal)

    def send_trade_entry_notification(self, trade: Trade, signal: Signal):
        """Send trade entry notification"""
        color = 0xFF0000  # Red color for all trade entries

        embed = {
            "title": f"🚨 Trade Entered: {trade.symbol} {trade.direction.value}",
            "color": color,
            "fields": [
                {
                    "name": "Entry Price",
                    "value": f"${trade.entry_price:.6f}",
                    "inline": True
                },
                {
                    "name": "Indicator Timeframes",
                    "value": f"Oath Keeper: **{signal.oath_keeper_tf}**\n"
                            f"SFP: **{', '.join(signal.sfp_timeframes) if signal.sfp_timeframes else 'None'}**\n"
                            f"Wave 3: **{signal.wave3_tf}**\n"
                            f"Trend: **{signal.vwap_trend_tf}**",
                    "inline": False
                },
                {
                    "name": "Stop Loss",
                    "value": f"${trade.stop_loss:.6f}",
                    "inline": True
                },
                {
                    "name": "Take Profit 1",
                    "value": f"${trade.tp1:.6f} ({TP1_PCT*100:.2f}%)",
                    "inline": True
                },
                {
                    "name": "Position Size",
                    "value": f"${trade.position_size_usd:.2f} @ {trade.leverage}x",
                    "inline": True
                },
                {
                    "name": "Confluence",
                    "value": f"{signal.confluence_score:.0f}/100",
                    "inline": True
                },
                {
                    "name": "Reasons",
                    "value": "\n".join(signal.reasons),
                    "inline": False
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "url": signal.chart_url
        }

        try:
            payload = {"embeds": [embed]}
            r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send entry notification: {e}")

    def run(self):
        """Main bot loop"""
        logger.info("🚀 Bounty Seeker Bot starting...")
        logger.info(f"Starting balance: ${self.paper_account.balance:.2f}")

        while True:
            try:
                self.run_scan()
                logger.info(f"⏰ Next scan in {SCAN_INTERVAL_SEC // 60} minutes...")
                time.sleep(SCAN_INTERVAL_SEC)
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute before retrying


if __name__ == "__main__":
    bot = BountySeekerBot()
    bot.run()
