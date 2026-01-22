#!/usr/bin/env python3
"""
Piv X Signal Bot for Discord
- Scans BTC, SOL, ETH every hour using Piv X indicator logic
- Tracks trade states to avoid duplicate signals
- Groups same trades on same card
- White cards for bullish, purple cards for bearish
- Entry, Stop, and Open alerts
- Waits for price to reach entry zone before triggering
"""

import os
import json
import time
import logging
import sqlite3
import requests
import pandas as pd
import numpy as np
import ccxt
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pivx_signal_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PivXSignalBot")

# Discord webhook
DISCORD_WEBHOOK = ""

# Configuration
SCAN_INTERVAL_SEC = 60 * 60  # 1 hour
SYMBOLS = ["BTCUSDT", "SOLUSDT", "ETHUSDT"]
TIMEFRAMES = ["15m", "1h", "4h"]  # Multiple timeframes for confluence
PRIMARY_TIMEFRAME = "1h"  # Main timeframe for signals
LEVERAGE = 15
TARGET_PCT = 0.02  # 2% move target
SECOND_TARGET_PCT = 0.04  # Optional runner target
STOP_PCT = 0.03  # Max 3% drawdown
ENTRY_BUFFER_PCT = 0.003  # 0.3% proximity alert
MIN_CONFLUENCE_SCORE = 60  # Only take 60-65%+ quality setups
ATR_MULTIPLIER = 0.8
MIN_PIVOT_SIGNIFICANCE = 0.3
REQUIRE_VOLUME_CONFIRMATION = False
ATR_CONFIRM_ENABLED = False
ATR_CONFIRM_MULT = 0.2
REAL_TIME_MODE = True
MAX_ACTIVE_TRADES = 3
RESET_TRADES_ON_START = True

# Williams %R settings (from updated PivotX + Williams Divergence VWAP)
WILLR_LENGTH = 14
WILLR_OB_LEVEL = -20
WILLR_OS_LEVEL = -80
WILLR_PIVOT_LOOKBACK = 5
WILLR_DIV_LOOKBACK_RANGE = 60

# Database for trade state tracking
DB_FILE = "pivx_trades.db"


class TradeStatus(Enum):
    """Trade status enum"""
    PENDING = "pending"      # Setup detected, waiting for entry
    OPEN = "open"           # Entry triggered
    STOPPED = "stopped"     # Hit stop loss
    TARGET_HIT = "target"   # Hit target
    INVALIDATED = "invalid" # Setup no longer valid
    STILL_VALID = "valid"   # Same setup still valid on rescan


class TradeDirection(Enum):
    """Trade direction"""
    LONG = "long"
    SHORT = "short"


@dataclass
class PivXSignal:
    """Piv X trading signal"""
    symbol: str
    direction: TradeDirection
    timeframe: str
    entry_price: float
    stop_price: float
    target1: float
    target2: float
    pivot_price: float
    pivot_type: str  # "HIGH" or "LOW"
    confluence_score: int
    rsi: float
    ma_trend: int  # 1 = bullish, -1 = bearish
    volume_spike: bool
    exhaustion: bool
    timestamp: datetime
    current_price: float
    atr: float
    willr_value: float = 0.0
    willr_divergence: bool = False
    entry_distance_pct: float = 0.0
    trade_number: int = 0

    def to_dict(self) -> dict:
        return {
            'symbol': self.symbol,
            'direction': self.direction.value,
            'timeframe': self.timeframe,
            'entry_price': self.entry_price,
            'stop_price': self.stop_price,
            'target1': self.target1,
            'target2': self.target2,
            'pivot_price': self.pivot_price,
            'pivot_type': self.pivot_type,
            'confluence_score': self.confluence_score,
            'rsi': self.rsi,
            'ma_trend': self.ma_trend,
            'volume_spike': self.volume_spike,
            'exhaustion': self.exhaustion,
            'timestamp': self.timestamp.isoformat(),
            'current_price': self.current_price,
            'atr': self.atr,
            'willr_value': self.willr_value,
            'willr_divergence': self.willr_divergence,
            'entry_distance_pct': self.entry_distance_pct,
            'trade_number': self.trade_number
        }


@dataclass
class TrackedTrade:
    """Trade being tracked"""
    id: str
    signal: PivXSignal
    status: TradeStatus
    created_at: datetime
    last_update: datetime
    entry_triggered: bool = False
    entry_triggered_at: Optional[datetime] = None


class TradeDatabase:
    """SQLite database for trade tracking"""

    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                trade_number INTEGER,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                entry_price REAL NOT NULL,
                stop_price REAL NOT NULL,
                target1 REAL NOT NULL,
                target2 REAL NOT NULL,
                pivot_price REAL NOT NULL,
                pivot_type TEXT NOT NULL,
                confluence_score INTEGER NOT NULL,
                rsi REAL,
                ma_trend INTEGER,
                volume_spike INTEGER,
                exhaustion INTEGER,
                atr REAL,
                willr_value REAL,
                willr_divergence INTEGER,
                entry_distance_pct REAL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_update TEXT NOT NULL,
                entry_triggered INTEGER DEFAULT 0,
                entry_triggered_at TEXT,
                current_price REAL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts_sent (
                id TEXT PRIMARY KEY,
                trade_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                sent_at TEXT NOT NULL,
                FOREIGN KEY (trade_id) REFERENCES trades(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        conn.commit()
        self._ensure_columns(conn)
        conn.close()
        logger.info("Database initialized")

    def _ensure_columns(self, conn: sqlite3.Connection):
        """Add missing columns for schema upgrades."""
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(trades)")
        existing = {row[1] for row in cursor.fetchall()}
        required = {
            "trade_number": "INTEGER",
            "willr_value": "REAL",
            "willr_divergence": "INTEGER",
            "entry_distance_pct": "REAL",
        }
        for column, col_type in required.items():
            if column not in existing:
                cursor.execute(f"ALTER TABLE trades ADD COLUMN {column} {col_type}")
        conn.commit()

    def get_next_trade_number(self) -> int:
        """Get next sequential trade number."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key = 'trade_counter'")
        row = cursor.fetchone()
        current = int(row[0]) if row and row[0] else 0
        next_number = current + 1
        cursor.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("trade_counter", str(next_number))
        )
        conn.commit()
        conn.close()
        return next_number

    def reset_trade_tracking(self):
        """Reset trades, alerts, and trade numbering."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trades")
        cursor.execute("DELETE FROM alerts_sent")
        cursor.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("trade_counter", "0")
        )
        conn.commit()
        conn.close()

    def save_trade(self, trade: TrackedTrade):
        """Save or update a trade"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO trades (
                id, trade_number, symbol, direction, timeframe, entry_price, stop_price,
                target1, target2, pivot_price, pivot_type, confluence_score,
                rsi, ma_trend, volume_spike, exhaustion, atr, willr_value,
                willr_divergence, entry_distance_pct, status,
                created_at, last_update, entry_triggered, entry_triggered_at,
                current_price
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade.id,
            trade.signal.trade_number,
            trade.signal.symbol,
            trade.signal.direction.value,
            trade.signal.timeframe,
            trade.signal.entry_price,
            trade.signal.stop_price,
            trade.signal.target1,
            trade.signal.target2,
            trade.signal.pivot_price,
            trade.signal.pivot_type,
            trade.signal.confluence_score,
            trade.signal.rsi,
            trade.signal.ma_trend,
            1 if trade.signal.volume_spike else 0,
            1 if trade.signal.exhaustion else 0,
            trade.signal.atr,
            trade.signal.willr_value,
            1 if trade.signal.willr_divergence else 0,
            trade.signal.entry_distance_pct,
            trade.status.value,
            trade.created_at.isoformat(),
            trade.last_update.isoformat(),
            1 if trade.entry_triggered else 0,
            trade.entry_triggered_at.isoformat() if trade.entry_triggered_at else None,
            trade.signal.current_price
        ))

        conn.commit()
        conn.close()

    def get_active_trades(self, symbol: str = None) -> List[TrackedTrade]:
        """Get active trades (pending or open)"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = '''
            SELECT * FROM trades
            WHERE status IN ('pending', 'open', 'valid')
        '''
        if symbol:
            query += f" AND symbol = '{symbol}'"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        trades = []
        for row in rows:
            signal = PivXSignal(
                symbol=row["symbol"],
                direction=TradeDirection(row["direction"]),
                timeframe=row["timeframe"],
                entry_price=row["entry_price"],
                stop_price=row["stop_price"],
                target1=row["target1"],
                target2=row["target2"],
                pivot_price=row["pivot_price"],
                pivot_type=row["pivot_type"],
                confluence_score=row["confluence_score"],
                rsi=row["rsi"] or 50.0,
                ma_trend=row["ma_trend"] or 0,
                volume_spike=bool(row["volume_spike"]),
                exhaustion=bool(row["exhaustion"]),
                atr=row["atr"] or 0.0,
                timestamp=datetime.fromisoformat(row["created_at"]),
                current_price=row["current_price"] or row["entry_price"],
                willr_value=row["willr_value"] or 0.0,
                willr_divergence=bool(row["willr_divergence"]) if row["willr_divergence"] is not None else False,
                entry_distance_pct=row["entry_distance_pct"] or 0.0,
                trade_number=row["trade_number"] or 0
            )

            trade = TrackedTrade(
                id=row["id"],
                signal=signal,
                status=TradeStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                last_update=datetime.fromisoformat(row["last_update"]),
                entry_triggered=bool(row["entry_triggered"]),
                entry_triggered_at=datetime.fromisoformat(row["entry_triggered_at"]) if row["entry_triggered_at"] else None
            )
            trades.append(trade)

        return trades

    def has_alert_been_sent(self, trade_id: str, alert_type: str) -> bool:
        """Check if an alert has already been sent"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 1 FROM alerts_sent
            WHERE trade_id = ? AND alert_type = ?
        ''', (trade_id, alert_type))

        result = cursor.fetchone()
        conn.close()

        return result is not None

    def mark_alert_sent(self, trade_id: str, alert_type: str):
        """Mark an alert as sent"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO alerts_sent (id, trade_id, alert_type, sent_at)
            VALUES (?, ?, ?, ?)
        ''', (
            f"{trade_id}_{alert_type}",
            trade_id,
            alert_type,
            datetime.now(timezone.utc).isoformat()
        ))

        conn.commit()
        conn.close()

    def invalidate_old_trades(self, hours: int = 24):
        """Invalidate trades older than specified hours"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

        cursor.execute('''
            UPDATE trades
            SET status = 'invalid', last_update = ?
            WHERE status IN ('pending', 'valid')
            AND created_at < ?
        ''', (datetime.now(timezone.utc).isoformat(), cutoff))

        conn.commit()
        conn.close()

    def invalidate_other_trades(self, symbol: str, keep_trade_id: str):
        """Invalidate other active trades for a symbol."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE trades
            SET status = 'invalid', last_update = ?
            WHERE symbol = ?
            AND id != ?
            AND status IN ('pending', 'open', 'valid')
        ''', (datetime.now(timezone.utc).isoformat(), symbol, keep_trade_id))
        conn.commit()
        conn.close()

    def prune_active_trades(self):
        """Keep only the newest active trade per symbol."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT symbol, id, created_at
            FROM trades
            WHERE status IN ('pending', 'open', 'valid')
            ORDER BY datetime(created_at) DESC
        ''')
        rows = cursor.fetchall()
        seen = {}
        for symbol, trade_id, _created_at in rows:
            if symbol in seen:
                cursor.execute('''
                    UPDATE trades
                    SET status = 'invalid', last_update = ?
                    WHERE id = ?
                ''', (datetime.now(timezone.utc).isoformat(), trade_id))
            else:
                seen[symbol] = trade_id
        conn.commit()
        conn.close()


class PivXScanner:
    """Piv X indicator scanner"""

    def __init__(self):
        self.db = TradeDatabase()
        self.exchange_name = "kraken"

        # Initialize exchange - try multiple options
        self.exchange = None

        # Try Kraken first (works in most locations)
        try:
            self.exchange = ccxt.kraken({'enableRateLimit': True})
            # Test connection
            self.exchange.fetch_ohlcv('BTC/USD', '1h', limit=5)
            self.exchange_name = "kraken"
            logger.info("Initialized Kraken exchange")
        except Exception as e:
            logger.warning(f"Kraken failed: {e}")

            # Try Coinbase
            try:
                self.exchange = ccxt.coinbase({'enableRateLimit': True})
                self.exchange.fetch_ohlcv('BTC/USD', '1h', limit=5)
                self.exchange_name = "coinbase"
                logger.info("Initialized Coinbase exchange")
            except Exception as e2:
                logger.warning(f"Coinbase failed: {e2}")

                # Try Binance US
                try:
                    self.exchange = ccxt.binanceus({'enableRateLimit': True})
                    self.exchange.fetch_ohlcv('BTC/USD', '1h', limit=5)
                    self.exchange_name = "binanceus"
                    logger.info("Initialized Binance US exchange")
                except Exception as e3:
                    logger.error(f"All exchanges failed: {e3}")
                    self.exchange = None

    def map_symbol(self, symbol: str) -> str:
        """Map symbol for exchange"""
        base = symbol.replace("USDT", "")
        # Kraken and Coinbase use /USD format
        return f"{base}/USD"

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data"""
        if self.exchange is None:
            return None

        try:
            exchange_symbol = self.map_symbol(symbol)
            ohlcv = self.exchange.fetch_ohlcv(exchange_symbol, timeframe, limit=limit)

            if not ohlcv:
                return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)

            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            return df

        except Exception as e:
            logger.error(f"Error fetching {symbol} {timeframe}: {e}")
            return None

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)

        return true_range.rolling(window=period).mean()

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate EMA"""
        return df['close'].ewm(span=period, adjust=False).mean()

    def calculate_willr(self, df: pd.DataFrame, length: int) -> pd.Series:
        """Calculate Williams %R."""
        highest_high = df['high'].rolling(window=length).max()
        lowest_low = df['low'].rolling(window=length).min()
        willr = (highest_high - df['close']) / (highest_high - lowest_low) * -100
        return willr

    def _find_recent_pivots(self, series: pd.Series, lookback: int, is_high: bool) -> List[int]:
        """Find the two most recent pivot indices for highs or lows."""
        pivots = []
        end = len(series) - lookback - 1
        for i in range(end, lookback, -1):
            window = series[i - lookback:i + lookback + 1]
            if is_high:
                if series[i] == window.max():
                    pivots.append(i)
            else:
                if series[i] == window.min():
                    pivots.append(i)
            if len(pivots) == 2:
                break
        return pivots

    def detect_willr_divergence(self, df: pd.DataFrame, willr: pd.Series) -> Tuple[bool, bool]:
        """Detect Williams %R divergences using pivot logic."""
        if len(df) < WILLR_PIVOT_LOOKBACK * 2 + 5:
            return False, False

        price_lows = self._find_recent_pivots(df['low'], WILLR_PIVOT_LOOKBACK, is_high=False)
        price_highs = self._find_recent_pivots(df['high'], WILLR_PIVOT_LOOKBACK, is_high=True)

        bull_div = False
        bear_div = False

        if len(price_lows) == 2:
            idx_new, idx_prev = price_lows[0], price_lows[1]
            if (idx_new - idx_prev) <= WILLR_DIV_LOOKBACK_RANGE:
                if df['low'].iloc[idx_new] < df['low'].iloc[idx_prev] and willr.iloc[idx_new] > willr.iloc[idx_prev]:
                    if willr.iloc[idx_new] <= WILLR_OS_LEVEL or willr.iloc[idx_prev] <= WILLR_OS_LEVEL:
                        bull_div = True

        if len(price_highs) == 2:
            idx_new, idx_prev = price_highs[0], price_highs[1]
            if (idx_new - idx_prev) <= WILLR_DIV_LOOKBACK_RANGE:
                if df['high'].iloc[idx_new] > df['high'].iloc[idx_prev] and willr.iloc[idx_new] < willr.iloc[idx_prev]:
                    if willr.iloc[idx_new] >= WILLR_OB_LEVEL or willr.iloc[idx_prev] >= WILLR_OB_LEVEL:
                        bear_div = True

        return bull_div, bear_div

    def calculate_pivot_strength(self, atr: float, timeframe: str, mintick: float = 0.01) -> int:
        """Calculate dynamic pivot strength based on ATR and timeframe."""
        pivot_strength_raw = max(2, round(atr / mintick * ATR_MULTIPLIER))

        if timeframe == "5m":
            base_min = 4
            base_max = 15
        elif timeframe == "15m":
            base_min = 3
            base_max = 18
        elif timeframe == "1h":
            base_min = 3
            base_max = 25
        else:
            base_min = 3
            base_max = 25

        min_strength = max(3, base_min - 1) if REAL_TIME_MODE else base_min
        max_strength = max(8, base_max - 2) if REAL_TIME_MODE else base_max
        return max(min_strength, min(pivot_strength_raw, max_strength))

    def detect_pivots(self, df: pd.DataFrame, strength: int) -> Tuple[List[dict], List[dict]]:
        """Detect pivot highs and lows"""
        pivot_highs = []
        pivot_lows = []

        if len(df) < strength * 2 + 1:
            return pivot_highs, pivot_lows

        for i in range(strength, len(df) - strength):
            # Pivot High
            high_val = df.iloc[i]['high']
            is_pivot_high = True
            for j in range(1, strength + 1):
                if df.iloc[i - j]['high'] >= high_val or df.iloc[i + j]['high'] >= high_val:
                    is_pivot_high = False
                    break

            if is_pivot_high:
                pivot_highs.append({
                    'index': i,
                    'price': high_val,
                    'timestamp': df.iloc[i]['timestamp']
                })

            # Pivot Low
            low_val = df.iloc[i]['low']
            is_pivot_low = True
            for j in range(1, strength + 1):
                if df.iloc[i - j]['low'] <= low_val or df.iloc[i + j]['low'] <= low_val:
                    is_pivot_low = False
                    break

            if is_pivot_low:
                pivot_lows.append({
                    'index': i,
                    'price': low_val,
                    'timestamp': df.iloc[i]['timestamp']
                })

        return pivot_highs, pivot_lows

    def detect_exhaustion(self, df: pd.DataFrame, periods: int = 3, min_move_pct: float = 2.0) -> Tuple[bool, bool]:
        """Detect selling and buying exhaustion"""
        if len(df) < periods + 1:
            return False, False

        price_change_pct = ((df.iloc[-1]['close'] - df.iloc[-periods - 1]['close']) / df.iloc[-periods - 1]['close']) * 100

        avg_vol = df['volume'].rolling(20).mean().iloc[-1]
        vol_spike = df.iloc[-1]['volume'] > avg_vol * 1.5

        sell_exhaustion = price_change_pct <= -min_move_pct and vol_spike
        buy_exhaustion = price_change_pct >= min_move_pct and vol_spike

        return sell_exhaustion, buy_exhaustion

    def calculate_confluence_score(
        self,
        pivot_type: str,
        rsi: float,
        ma_trend: int,
        vol_spike: bool,
        exhaustion: bool,
        atr_confirmed: bool,
        htf_aligned: bool,
        willr_divergence: bool
    ) -> int:
        """Calculate confluence score for pivot quality"""
        score = 10  # Base pivot score

        # Volume confirmation (15 pts)
        if vol_spike:
            score += 15

        # HTF trend alignment (20 pts)
        if htf_aligned:
            score += 20

        # RSI conditions (25 pts)
        if pivot_type == "LOW" and rsi <= 35:
            score += 25
        elif pivot_type == "HIGH" and rsi >= 65:
            score += 25

        # Exhaustion (10 pts)
        if exhaustion:
            score += 10

        # ATR confirmation (10 pts)
        if atr_confirmed:
            score += 10

        # MA trend alignment (15 pts)
        if (pivot_type == "LOW" and ma_trend > 0) or (pivot_type == "HIGH" and ma_trend < 0):
            score += 15

        # Williams %R divergence (10 pts)
        if willr_divergence:
            score += 10

        return score

    def scan_symbol(self, symbol: str) -> List[PivXSignal]:
        """Scan a symbol for Piv X signals"""
        signals = []

        # Fetch data for primary timeframe
        df = self.fetch_ohlcv(symbol, PRIMARY_TIMEFRAME, limit=500)
        if df is None or len(df) < 100:
            logger.warning(f"Insufficient data for {symbol}")
            return signals

        # Fetch HTF data for trend alignment
        df_htf = self.fetch_ohlcv(symbol, "4h", limit=200)

        # Calculate indicators
        atr = self.calculate_atr(df)
        rsi = self.calculate_rsi(df)
        ema_fast = self.calculate_ema(df, 12)
        ema_slow = self.calculate_ema(df, 26)
        willr = self.calculate_willr(df, WILLR_LENGTH)

        current_atr = atr.iloc[-1] if not atr.empty else 0
        current_rsi = rsi.iloc[-1] if not rsi.empty else 50
        current_price = df.iloc[-1]['close']
        current_willr = willr.iloc[-1] if not willr.empty else 0.0

        # MA trend
        ma_trend = 1 if ema_fast.iloc[-1] > ema_slow.iloc[-1] else -1

        # HTF trend
        htf_trend_up = True
        if df_htf is not None and len(df_htf) > 50:
            htf_ema = self.calculate_ema(df_htf, 50)
            htf_trend_up = df_htf.iloc[-1]['close'] > htf_ema.iloc[-1]

        # Volume spike
        avg_vol = df['volume'].rolling(20).mean().iloc[-1]
        vol_spike = df.iloc[-1]['volume'] > avg_vol * 1.5

        # Exhaustion
        sell_exhaustion, buy_exhaustion = self.detect_exhaustion(df)

        # Williams %R divergence
        bull_willr_div, bear_willr_div = self.detect_willr_divergence(df, willr)

        # Detect pivots using dynamic strength
        pivot_strength = self.calculate_pivot_strength(current_atr, PRIMARY_TIMEFRAME)
        pivot_highs, pivot_lows = self.detect_pivots(df, strength=pivot_strength)

        # Pivot significance filters
        sma_length = max(1, int(round(pivot_strength * 2)))
        recent_high_avg = df['high'].rolling(sma_length).mean()
        recent_low_avg = df['low'].rolling(sma_length).mean()
        min_required_distance = current_atr * MIN_PIVOT_SIGNIFICANCE

        def pivot_passes_filters(pivot, is_high: bool) -> bool:
            idx = pivot['index']
            price = pivot['price']
            if is_high:
                if pd.isna(recent_high_avg.iloc[idx]):
                    return False
                if price < recent_high_avg.iloc[idx] + min_required_distance:
                    return False
            else:
                if pd.isna(recent_low_avg.iloc[idx]):
                    return False
                if price > recent_low_avg.iloc[idx] - min_required_distance:
                    return False
            if REQUIRE_VOLUME_CONFIRMATION:
                if df['volume'].iloc[idx] <= avg_vol:
                    return False
            return True

        pivot_highs = [p for p in pivot_highs if pivot_passes_filters(p, True)]
        pivot_lows = [p for p in pivot_lows if pivot_passes_filters(p, False)]

        # Check recent pivot lows for long setups
        for pivot in pivot_lows[-5:]:  # Check last 5 pivot lows
            pivot_price = pivot['price']
            pivot_idx = pivot['index']

            # Check if current price is near pivot zone
            zone_distance = abs(current_price - pivot_price) / current_price * 100
            if zone_distance > 3.0:  # More than 3% away, skip
                continue

            # ATR confirmation (optional)
            atr_confirmed = (not ATR_CONFIRM_ENABLED) or (
                current_price > pivot_price + (current_atr * ATR_CONFIRM_MULT)
            )

            # Calculate confluence score
            score = self.calculate_confluence_score(
                pivot_type="LOW",
                rsi=current_rsi,
                ma_trend=ma_trend,
                vol_spike=vol_spike,
                exhaustion=sell_exhaustion,
                atr_confirmed=atr_confirmed,
                htf_aligned=htf_trend_up,
                willr_divergence=bull_willr_div
            )

            # Only generate signal if score is high enough
            if score >= MIN_CONFLUENCE_SCORE:
                # Calculate entry, stop, targets (2% target, 3% max drawdown)
                entry_price = pivot_price + (current_atr * 0.1)
                stop_price = entry_price * (1 - STOP_PCT)
                target1 = entry_price * (1 + TARGET_PCT)
                target2 = entry_price * (1 + SECOND_TARGET_PCT)

                entry_distance_pct = abs((entry_price - current_price) / current_price) * 100
                signal = PivXSignal(
                    symbol=symbol,
                    direction=TradeDirection.LONG,
                    timeframe=PRIMARY_TIMEFRAME,
                    entry_price=entry_price,
                    stop_price=stop_price,
                    target1=target1,
                    target2=target2,
                    pivot_price=pivot_price,
                    pivot_type="LOW",
                    confluence_score=score,
                    rsi=current_rsi,
                    ma_trend=ma_trend,
                    volume_spike=vol_spike,
                    exhaustion=sell_exhaustion,
                    timestamp=datetime.now(timezone.utc),
                    current_price=current_price,
                    atr=current_atr,
                    willr_value=current_willr,
                    willr_divergence=bull_willr_div,
                    entry_distance_pct=entry_distance_pct
                )
                signals.append(signal)

        # Check recent pivot highs for short setups
        for pivot in pivot_highs[-5:]:  # Check last 5 pivot highs
            pivot_price = pivot['price']
            pivot_idx = pivot['index']

            # Check if current price is near pivot zone
            zone_distance = abs(current_price - pivot_price) / current_price * 100
            if zone_distance > 3.0:  # More than 3% away, skip
                continue

            # ATR confirmation (optional)
            atr_confirmed = (not ATR_CONFIRM_ENABLED) or (
                current_price < pivot_price - (current_atr * ATR_CONFIRM_MULT)
            )

            # Calculate confluence score
            score = self.calculate_confluence_score(
                pivot_type="HIGH",
                rsi=current_rsi,
                ma_trend=ma_trend,
                vol_spike=vol_spike,
                exhaustion=buy_exhaustion,
                atr_confirmed=atr_confirmed,
                htf_aligned=not htf_trend_up,
                willr_divergence=bear_willr_div
            )

            # Only generate signal if score is high enough
            if score >= MIN_CONFLUENCE_SCORE:
                # Calculate entry, stop, targets (2% target, 3% max drawdown)
                entry_price = pivot_price - (current_atr * 0.1)
                stop_price = entry_price * (1 + STOP_PCT)
                target1 = entry_price * (1 - TARGET_PCT)
                target2 = entry_price * (1 - SECOND_TARGET_PCT)

                entry_distance_pct = abs((entry_price - current_price) / current_price) * 100
                signal = PivXSignal(
                    symbol=symbol,
                    direction=TradeDirection.SHORT,
                    timeframe=PRIMARY_TIMEFRAME,
                    entry_price=entry_price,
                    stop_price=stop_price,
                    target1=target1,
                    target2=target2,
                    pivot_price=pivot_price,
                    pivot_type="HIGH",
                    confluence_score=score,
                    rsi=current_rsi,
                    ma_trend=ma_trend,
                    volume_spike=vol_spike,
                    exhaustion=buy_exhaustion,
                    timestamp=datetime.now(timezone.utc),
                    current_price=current_price,
                    atr=current_atr,
                    willr_value=current_willr,
                    willr_divergence=bear_willr_div,
                    entry_distance_pct=entry_distance_pct
                )
                signals.append(signal)

        if not signals:
            return []

        # Return only the best signal per coin per scan
        signals.sort(key=lambda s: (s.confluence_score, -s.entry_distance_pct), reverse=True)
        return [signals[0]]

    def is_same_trade(self, signal1: PivXSignal, signal2: PivXSignal, tolerance_pct: float = 1.0) -> bool:
        """Check if two signals represent the same trade"""
        if signal1.symbol != signal2.symbol:
            return False
        if signal1.direction != signal2.direction:
            return False

        # Check if pivot prices are within tolerance
        price_diff = abs(signal1.pivot_price - signal2.pivot_price) / signal1.pivot_price * 100
        return price_diff < tolerance_pct

    def generate_trade_id(self, signal: PivXSignal) -> str:
        """Generate unique trade ID"""
        return f"{signal.symbol}_{signal.direction.value}_{signal.pivot_type}_{int(signal.pivot_price)}"


class DiscordNotifier:
    """Discord notification handler"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def build_reasoning(self, signal: PivXSignal) -> str:
        """Build quick, understandable reasoning for a signal."""
        reasons = []
        if signal.volume_spike:
            reasons.append("Volume spike confirms interest")
        if signal.exhaustion:
            reasons.append("Exhaustion suggests reversal risk")
        if signal.willr_divergence:
            reasons.append("Williams %R divergence aligns")
        if signal.direction == TradeDirection.LONG and signal.rsi <= 35:
            reasons.append("RSI oversold supports bounce")
        if signal.direction == TradeDirection.SHORT and signal.rsi >= 65:
            reasons.append("RSI overbought supports pullback")
        if (signal.direction == TradeDirection.LONG and signal.ma_trend > 0) or (
            signal.direction == TradeDirection.SHORT and signal.ma_trend < 0
        ):
            reasons.append("MA trend aligns with setup")
        if not reasons:
            reasons.append("Multiple pivots align with current structure")
        return "; ".join(reasons[:3]) + "."

    def send_signal_card(
        self,
        signals: List[PivXSignal],
        trade_status: TradeStatus,
        alert_type: str = "SETUP"
    ):
        """Send a Discord embed card for signals"""
        if not signals:
            return

        # Group signals by direction
        primary_signal = signals[0]
        directions = {s.direction for s in signals}
        is_bullish = directions == {TradeDirection.LONG}
        is_bearish = directions == {TradeDirection.SHORT}

        # Colors
        trigger_alerts = {"ENTRY", "OPEN", "STOP", "TARGET1", "TARGET2"}
        if alert_type in trigger_alerts:
            color = 0xFFA500  # Orange for trigger alerts
        elif alert_type == "STILL_VALID":
            color = 0x3498DB
        elif is_bullish:
            color = 0xFFFFFF
        elif is_bearish:
            color = 0x9B59B6
        else:
            color = 0xCCCCCC

        # Direction emoji and text
        direction_emoji = "🟢" if is_bullish else "🟣" if is_bearish else "🔀"
        direction_text = "LONG" if is_bullish else "SHORT" if is_bearish else "MIXED"

        # Status emoji
        status_emoji = {
            "SETUP": "📊",
            "ENTRY": "🎯",
            "OPEN": "✅",
            "STOP": "🛑",
            "TARGET1": "🎯",
            "TARGET2": "🏁",
            "TARGET": "🎉",
            "STILL_VALID": "♻️"
        }.get(alert_type, "📊")

        # Build symbol list
        symbol_names = ", ".join([s.symbol.replace("USDT", "") for s in signals])

        # Create description
        if len(signals) == 1:
            s = signals[0]
            reasoning = self.build_reasoning(s)
            description = (
                f"**{direction_emoji} {direction_text}** | {status_emoji} {alert_type}\n\n"
                f"**Trade # {s.trade_number}**\n"
                f"**Pivot {s.pivot_type}:** ${s.pivot_price:,.2f}\n"
                f"**Entry Zone:** ${s.entry_price:,.2f}\n"
                f"**Stop Loss:** ${s.stop_price:,.2f}\n"
                f"**Target 1:** ${s.target1:,.2f}\n"
                f"**Target 2:** ${s.target2:,.2f}\n\n"
                f"**Leverage:** {LEVERAGE}x\n"
                f"**Distance to Entry:** {s.entry_distance_pct:.2f}%\n"
                f"**Plan:** TP1 {int(TARGET_PCT * 100)}%, TP2 {int(SECOND_TARGET_PCT * 100)}%, SL {int(STOP_PCT * 100)}%\n"
                f"**Current Price:** ${s.current_price:,.2f}\n"
                f"**Confluence Score:** {s.confluence_score}/100\n"
                f"**Williams %R:** {s.willr_value:.1f}\n"
                f"**RSI:** {s.rsi:.1f}\n"
                f"**Volume Spike:** {'✅' if s.volume_spike else '❌'}\n"
                f"**Exhaustion:** {'✅' if s.exhaustion else '❌'}\n\n"
                f"**Why valid:** {reasoning}\n\n"
                f"**Timeframe:** {s.timeframe}"
            )
        else:
            description = f"**{direction_emoji} {direction_text}** | {status_emoji} {alert_type}\n\n"
            long_signals = [s for s in signals if s.direction == TradeDirection.LONG]
            short_signals = [s for s in signals if s.direction == TradeDirection.SHORT]

            if long_signals:
                description += "**LONGS**\n"
                for s in long_signals:
                    coin = s.symbol.replace("USDT", "")
                    reasoning = self.build_reasoning(s)
                    description += (
                        f"- **#{s.trade_number} {coin}** | Entry ${s.entry_price:,.2f} | "
                        f"Stop ${s.stop_price:,.2f} | TP ${s.target1:,.2f}\n"
                        f"  Distance {s.entry_distance_pct:.2f}% | {reasoning}\n"
                    )
                description += "\n"

            if short_signals:
                description += "**SHORTS**\n"
                for s in short_signals:
                    coin = s.symbol.replace("USDT", "")
                    reasoning = self.build_reasoning(s)
                    description += (
                        f"- **#{s.trade_number} {coin}** | Entry ${s.entry_price:,.2f} | "
                        f"Stop ${s.stop_price:,.2f} | TP ${s.target1:,.2f}\n"
                        f"  Distance {s.entry_distance_pct:.2f}% | {reasoning}\n"
                    )

            description += (
                f"\n**Plan:** TP1 {int(TARGET_PCT * 100)}%, "
                f"TP2 {int(SECOND_TARGET_PCT * 100)}%, SL {int(STOP_PCT * 100)}%\n"
                f"**Leverage:** {LEVERAGE}x | **Timeframe:** {primary_signal.timeframe}"
            )

        # TradingView link - use KRAKEN or COINBASE format
        coin = primary_signal.symbol.replace("USDT", "")
        tv_link = f"https://www.tradingview.com/chart/?symbol=KRAKEN:{coin}USD"

        embed = {
            "title": f"Piv X Trades - {symbol_names}",
            "description": description,
            "color": color,
            "url": tv_link,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": f"Piv X Bot • {alert_type}"
            },
            "fields": [
                {
                    "name": "📈 Chart",
                    "value": f"[View on TradingView]({tv_link})",
                    "inline": True
                }
            ]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json={"embeds": [embed]},
                timeout=15
            )
            response.raise_for_status()
            logger.info(f"✅ Sent {alert_type} card for {symbol_names}")
        except Exception as e:
            logger.error(f"Error sending Discord card: {e}")

    def send_still_valid_update(self, trades: List[TrackedTrade]):
        """Send a compact 'still valid' update for existing trades"""
        if not trades:
            return

        # One trade per symbol in update
        unique_by_symbol = {}
        for trade in trades:
            sym = trade.signal.symbol
            if sym not in unique_by_symbol or trade.signal.confluence_score > unique_by_symbol[sym].signal.confluence_score:
                unique_by_symbol[sym] = trade
        trades = list(unique_by_symbol.values())

        # Group by direction
        long_trades = [t for t in trades if t.signal.direction == TradeDirection.LONG]
        short_trades = [t for t in trades if t.signal.direction == TradeDirection.SHORT]

        description = "**Active Setups Still Valid (Entry Pending):**\n\n"

        if long_trades:
            description += "🟢 **LONGS:**\n"
            for t in long_trades:
                coin = t.signal.symbol.replace("USDT", "")
                description += (
                    f"• #{t.signal.trade_number} {coin}: Entry ${t.signal.entry_price:,.2f} | "
                    f"Distance {t.signal.entry_distance_pct:.2f}% | "
                    f"Score {t.signal.confluence_score}\n"
                )

        if short_trades:
            description += "\n🟣 **SHORTS:**\n"
            for t in short_trades:
                coin = t.signal.symbol.replace("USDT", "")
                description += (
                    f"• #{t.signal.trade_number} {coin}: Entry ${t.signal.entry_price:,.2f} | "
                    f"Distance {t.signal.entry_distance_pct:.2f}% | "
                    f"Score {t.signal.confluence_score}\n"
                )

        description += f"\n*Last scan: {datetime.now(timezone.utc).strftime('%H:%M UTC')}*"

        embed = {
            "title": "♻️ Piv X - Hourly Scan Update",
            "description": description,
            "color": 0x3498DB,  # Blue for updates
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": "Piv X Bot • Hourly Update"
            }
        }

        try:
            response = requests.post(
                self.webhook_url,
                json={"embeds": [embed]},
                timeout=15
            )
            response.raise_for_status()
            logger.info("✅ Sent hourly update card")
        except Exception as e:
            logger.error(f"Error sending update card: {e}")


class PivXSignalBot:
    """Main bot class"""

    def __init__(self):
        self.scanner = PivXScanner()
        self.notifier = DiscordNotifier(DISCORD_WEBHOOK)
        self.db = TradeDatabase()

    def seconds_until_next_scan(self) -> int:
        """Calculate seconds until the next :55 scan time."""
        now = datetime.now(timezone.utc)
        target = now.replace(minute=55, second=0, microsecond=0)
        if now >= target:
            target = (now + timedelta(hours=1)).replace(minute=55, second=0, microsecond=0)
        return max(1, int((target - now).total_seconds()))

    def check_entry_triggers(self):
        """Check if any pending trades have hit entry"""
        active_trades = self.db.get_active_trades()
        entry_alerts = []
        open_alerts = []

        for trade in active_trades:
            if trade.status in [TradeStatus.PENDING, TradeStatus.STILL_VALID] and not trade.entry_triggered:
                # Fetch current price
                df = self.scanner.fetch_ohlcv(trade.signal.symbol, "5m", limit=5)
                if df is None:
                    continue

                current_price = df.iloc[-1]['close']
                entry_price = trade.signal.entry_price

                # Entry proximity alert (before trigger)
                entry_near = False
                if trade.signal.direction == TradeDirection.LONG:
                    if current_price <= entry_price * (1 + ENTRY_BUFFER_PCT):
                        entry_near = True
                else:
                    if current_price >= entry_price * (1 - ENTRY_BUFFER_PCT):
                        entry_near = True

                if entry_near and not self.db.has_alert_been_sent(trade.id, "ENTRY"):
                    trade.signal.current_price = current_price
                    trade.signal.entry_distance_pct = abs((trade.signal.entry_price - current_price) / current_price) * 100
                    self.db.mark_alert_sent(trade.id, "ENTRY")
                    entry_alerts.append(trade.signal)

                # Check if entry triggered (actual entry)
                entry_triggered = False
                if trade.signal.direction == TradeDirection.LONG:
                    # For longs, trigger when price touches or goes below entry then bounces
                    if current_price <= entry_price:
                        entry_triggered = True
                else:
                    # For shorts, trigger when price touches or goes above entry then falls
                    if current_price >= entry_price:
                        entry_triggered = True

                if entry_triggered:
                    trade.entry_triggered = True
                    trade.entry_triggered_at = datetime.now(timezone.utc)
                    trade.status = TradeStatus.OPEN
                    trade.last_update = datetime.now(timezone.utc)
                    trade.signal.entry_distance_pct = abs((trade.signal.entry_price - current_price) / current_price) * 100
                    self.db.save_trade(trade)

                    # Send OPEN alert if not already sent
                    if not self.db.has_alert_been_sent(trade.id, "OPEN"):
                        trade.signal.current_price = current_price
                        self.db.mark_alert_sent(trade.id, "OPEN")
                        open_alerts.append(trade.signal)

        if entry_alerts:
            self.notifier.send_signal_card(entry_alerts, TradeStatus.PENDING, "ENTRY")
        if open_alerts:
            self.notifier.send_signal_card(open_alerts, TradeStatus.OPEN, "OPEN")

    def check_stop_or_target(self):
        """Check if open trades hit stop or target"""
        active_trades = self.db.get_active_trades()
        stop_alerts = []
        target1_alerts = []
        target2_alerts = []

        for trade in active_trades:
            if trade.status != TradeStatus.OPEN:
                continue

            # Fetch current price
            df = self.scanner.fetch_ohlcv(trade.signal.symbol, "5m", limit=5)
            if df is None:
                continue

            current_price = df.iloc[-1]['close']
            trade.signal.entry_distance_pct = abs((trade.signal.entry_price - current_price) / current_price) * 100

            # Check stop/targets
            hit_stop = False
            hit_target1 = False
            hit_target2 = False

            if trade.signal.direction == TradeDirection.LONG:
                if current_price <= trade.signal.stop_price:
                    hit_stop = True
                elif current_price >= trade.signal.target2:
                    hit_target2 = True
                elif current_price >= trade.signal.target1:
                    hit_target1 = True
            else:
                if current_price >= trade.signal.stop_price:
                    hit_stop = True
                elif current_price <= trade.signal.target2:
                    hit_target2 = True
                elif current_price <= trade.signal.target1:
                    hit_target1 = True

            if hit_stop:
                trade.status = TradeStatus.STOPPED
                trade.last_update = datetime.now(timezone.utc)
                self.db.save_trade(trade)

                if not self.db.has_alert_been_sent(trade.id, "STOP"):
                    trade.signal.current_price = current_price
                    self.db.mark_alert_sent(trade.id, "STOP")
                    stop_alerts.append(trade.signal)

            elif hit_target2:
                trade.status = TradeStatus.TARGET_HIT
                trade.last_update = datetime.now(timezone.utc)
                self.db.save_trade(trade)

                if not self.db.has_alert_been_sent(trade.id, "TARGET2"):
                    trade.signal.current_price = current_price
                    self.db.mark_alert_sent(trade.id, "TARGET2")
                    target2_alerts.append(trade.signal)
            elif hit_target1:
                if not self.db.has_alert_been_sent(trade.id, "TARGET1"):
                    trade.signal.current_price = current_price
                    self.db.mark_alert_sent(trade.id, "TARGET1")
                    target1_alerts.append(trade.signal)

        if target1_alerts:
            self.notifier.send_signal_card(target1_alerts, TradeStatus.OPEN, "TARGET1")
        if target2_alerts:
            self.notifier.send_signal_card(target2_alerts, TradeStatus.TARGET_HIT, "TARGET2")
        if stop_alerts:
            self.notifier.send_signal_card(stop_alerts, TradeStatus.STOPPED, "STOP")

    def scan_for_signals(self):
        """Scan all symbols for new signals"""
        new_signals = []
        still_valid_trades = []
        active_trades = self.db.get_active_trades()
        active_count = len(active_trades)

        for symbol in SYMBOLS:
            logger.info(f"Scanning {symbol}...")
            signals = self.scanner.scan_symbol(symbol)
            if not signals:
                continue

            # Always enforce one trade per symbol per scan
            signal = signals[0]
            trade_id = self.scanner.generate_trade_id(signal)

            # Check if we already have this trade
            active_trades = self.db.get_active_trades(symbol)
            existing_trade = None

            for trade in active_trades:
                if self.scanner.is_same_trade(trade.signal, signal):
                    existing_trade = trade
                    break

            if existing_trade:
                # Trade still valid - update it
                existing_trade.last_update = datetime.now(timezone.utc)
                existing_trade.signal.current_price = signal.current_price
                existing_trade.signal.entry_distance_pct = signal.entry_distance_pct
                signal.trade_number = existing_trade.signal.trade_number
                existing_trade.status = TradeStatus.STILL_VALID
                self.db.save_trade(existing_trade)
                still_valid_trades.append(existing_trade)
                self.db.invalidate_other_trades(symbol, existing_trade.id)
                logger.info(f"Trade {trade_id} still valid")
            else:
                if active_count >= MAX_ACTIVE_TRADES:
                    logger.info("Max active trades reached. Skipping new trade.")
                    continue
                # New trade
                signal.trade_number = self.db.get_next_trade_number()
                trade = TrackedTrade(
                    id=trade_id,
                    signal=signal,
                    status=TradeStatus.PENDING,
                    created_at=datetime.now(timezone.utc),
                    last_update=datetime.now(timezone.utc)
                )
                self.db.save_trade(trade)
                self.db.invalidate_other_trades(symbol, trade_id)
                new_signals.append(signal)
                active_count += 1
                logger.info(f"New signal: {trade_id}")

            time.sleep(1)  # Rate limiting

        return new_signals, still_valid_trades

    def run(self):
        """Main bot loop"""
        logger.info("🚀 Piv X Signal Bot started")
        logger.info(f"Scanning: {', '.join(SYMBOLS)}")
        logger.info("Scan schedule: every hour at :55 UTC")

        if RESET_TRADES_ON_START:
            logger.info("Resetting trade tracking and numbering.")
            self.db.reset_trade_tracking()

        # Invalidate old trades on startup
        self.db.invalidate_old_trades(hours=48)
        # Remove duplicate active trades per symbol on startup
        self.db.prune_active_trades()

        while True:
            try:
                logger.info("=" * 50)
                logger.info("Starting scheduled scan...")

                # Scan for new signals
                new_signals, still_valid_trades = self.scan_for_signals()

                # Send new signal alerts (single combined card)
                if new_signals:
                    self.notifier.send_signal_card(new_signals, TradeStatus.PENDING, "SETUP")
                    for s in new_signals:
                        trade_id = self.scanner.generate_trade_id(s)
                        self.db.mark_alert_sent(trade_id, "SETUP")
                    time.sleep(1)

                # Send still valid update
                if still_valid_trades and not new_signals:
                    self.notifier.send_still_valid_update(still_valid_trades)

                # Check entry triggers
                self.check_entry_triggers()

                # Check stop/target hits
                self.check_stop_or_target()

                # Invalidate old trades
                self.db.invalidate_old_trades(hours=48)

                wait_seconds = self.seconds_until_next_scan()
                wait_minutes = max(1, wait_seconds // 60)
                logger.info(f"Scan complete. Next scan in {wait_minutes} minutes")
                logger.info("=" * 50)

                time.sleep(wait_seconds)

            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)


if __name__ == "__main__":
    bot = PivXSignalBot()
    bot.run()
