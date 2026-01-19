#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bounty Seeker - Reversal Sniper Bot
Finds pure bottoms for reversal trades targeting 2-3% gains
Strategy: GPS Zones + Deviation Bands (2.5σ-3σ) + SFP Reversals
Exchange: Binance Futures (Best Liquidity)
Self-Learning: Adjusts parameters based on win/loss performance
"""

import os
import json
import time
import sqlite3
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import ccxt
import logging

# ====================== CONFIGURATION ======================
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1432976746692612147/SLf6oNcxTZfnmt1LmGLv-asGHwi-BnR2T8XIneUr7zM1tTbsSMncMZgzytvTFiAHmpcr"

# Exchange: OKX (Best Liquidity & Access)
# Falls back to OKX if Binance is restricted
EXCHANGE_NAME = "okx"
EXCHANGE_CONFIG = {
    'apiKey': os.getenv('OKX_API_KEY', ''),
    'secret': os.getenv('OKX_SECRET', ''),
    'password': os.getenv('OKX_PASSPHRASE', ''),
    'options': {'defaultType': 'swap'},  # Use swap (perpetual futures)
    'enableRateLimit': True,
    'sandbox': False
}

# Data storage
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
TRADES_DB = os.path.join(DATA_DIR, "bounty_seeker_trades.db")
LEARNING_DB = os.path.join(DATA_DIR, "bounty_seeker_learning.db")
STATE_FILE = os.path.join(DATA_DIR, "bounty_seeker_state.json")
STATUS_FILE = "bounty_seeker_status.json"

# Trading Parameters
MIN_CONFIDENCE_SCORE = 50  # Minimum score to trigger signal (0-100) - Lowered to find more signals
TARGET_PROFIT_PCT = 2.5  # Target 2-3% gains
STOP_LOSS_PCT = 1.0  # 1% stop loss
RISK_REWARD_RATIO = 2.5  # 2.5:1 R:R

# Technical Parameters
RSI_PERIOD = 14
VWAP_LOOKBACK = 200
VOLUME_LOOKBACK = 20
DEVIATION_2SIGMA = 2.5  # 2.5σ threshold
DEVIATION_3SIGMA = 3.0  # 3σ threshold (preferred)
GPS_LOW = 0.618  # Golden Pocket low (Fibonacci)
GPS_HIGH = 0.65  # Golden Pocket high

# Volume Spike Detection (VPSR Pro Logic)
VOL_MA_LENGTH = 20  # Volume MA Length
VOL_MULTIPLIER = 2.0  # Abnormal Volume Threshold
VOL_EXTREME_MULTIPLIER = 3.5  # Extreme Volume Threshold

# Market Filters
MIN_24H_VOLUME_USD = 10000000  # $10M minimum volume (to get closer to 50 coins)
SCAN_INTERVAL_SEC = 60  # Check every minute for XX:45 window
ACTIVE_TRADES_COOLDOWN = 300  # 5 minutes cooldown per symbol

# Assets to monitor (Will be dynamically loaded - Top 50 by volume)
WATCHLIST_SYMBOLS = []  # Populated dynamically
WATCHLIST_UPDATE_INTERVAL = 3600  # Update watchlist every hour

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bounty_seeker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ====================== DATACLASSES ======================
@dataclass
class Signal:
    """Trading signal data"""
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence_score: int
    reasons: List[str]
    rsi: float
    deviation: float
    in_gps_zone: bool
    timestamp: datetime
    timeframe: str = "15m"
    tradingview_link: str = ""
    trade_number: int = 0

@dataclass
class TradeResult:
    """Trade outcome for learning"""
    symbol: str
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    pnl_pct: float
    was_winner: bool
    confidence_score: int
    reasons: List[str]

# ====================== DATABASE SETUP ======================
def init_databases():
    """Initialize SQLite databases"""
    # Trades database
    conn = sqlite3.connect(TRADES_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_number INTEGER,
            symbol TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL NOT NULL,
            take_profit REAL NOT NULL,
            confidence_score INTEGER NOT NULL,
            reasons TEXT,
            entry_time TEXT NOT NULL,
            exit_time TEXT,
            exit_price REAL,
            pnl_pct REAL,
            exit_reason TEXT,
            status TEXT DEFAULT 'open'
        )
    ''')
    # Ensure columns exist for upgrades
    c.execute("PRAGMA table_info(trades)")
    cols = {row[1] for row in c.fetchall()}
    if "trade_number" not in cols:
        c.execute("ALTER TABLE trades ADD COLUMN trade_number INTEGER")
    if "exit_reason" not in cols:
        c.execute("ALTER TABLE trades ADD COLUMN exit_reason TEXT")
    conn.commit()
    conn.close()

    # Learning database (for self-learning)
    conn = sqlite3.connect(LEARNING_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS performance_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            total_trades INTEGER DEFAULT 0,
            winners INTEGER DEFAULT 0,
            losers INTEGER DEFAULT 0,
            avg_confidence_winner REAL,
            avg_confidence_loser REAL,
            avg_pnl_winner REAL,
            avg_pnl_loser REAL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS parameter_adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            parameter_name TEXT NOT NULL,
            old_value REAL,
            new_value REAL,
            reason TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS strategy_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_component TEXT NOT NULL,
            win_rate REAL,
            avg_pnl REAL,
            total_trades INTEGER,
            last_updated TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ====================== TECHNICAL INDICATORS ======================
def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculate RSI indicator"""
    if len(prices) < period + 1:
        return 50.0
    deltas = np.diff(prices[-period-1:])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_vwap_and_deviation(ohlcv: List) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Calculate VWAP and standard deviation
    Returns: (vwap, std_dev, current_deviation_sigma)
    """
    if len(ohlcv) < 50:
        return None, None, None

    # Calculate VWAP
    total_pv = 0.0
    total_volume = 0.0
    prices = []

    for candle in ohlcv:
        price = float(candle[4])  # Close
        vol = float(candle[5])  # Volume
        total_pv += price * vol
        total_volume += vol
        prices.append(price)

    if total_volume == 0:
        return None, None, None

    vwap = total_pv / total_volume
    current_price = prices[-1]

    # Calculate standard deviation
    price_array = np.array(prices)
    std_dev = np.std(price_array)

    if std_dev == 0:
        return vwap, None, None

    # Calculate how many sigmas away from VWAP
    deviation_sigma = (current_price - vwap) / std_dev

    return vwap, std_dev, deviation_sigma

def calculate_gps_zone(high: float, low: float, current_price: float) -> Tuple[bool, float]:
    """
    Check if price is in Golden Pocket zone (0.618 - 0.65 retracement)
    Returns: (is_in_zone, distance_to_zone_pct)
    """
    range_size = high - low
    if range_size == 0:
        return False, 100.0

    gp_low_level = low + (range_size * GPS_LOW)
    gp_high_level = low + (range_size * GPS_HIGH)

    if gp_low_level <= current_price <= gp_high_level:
        return True, 0.0

    # Calculate distance to zone
    if current_price < gp_low_level:
        distance = abs(current_price - gp_low_level) / current_price * 100
    else:
        distance = abs(current_price - gp_high_level) / current_price * 100

    return False, distance

def detect_sfp_reversal(ohlcv: List) -> bool:
    """
    Detect Swing Failure Pattern (SFP) - price sweeps low then reverses
    """
    if len(ohlcv) < 5:
        return False

    # Get last 3 candles
    recent = ohlcv[-3:]
    lows = [float(c[3]) for c in recent]  # Low prices
    closes = [float(c[4]) for c in recent]  # Close prices

    # SFP: Lower low followed by higher close (reversal)
    if lows[0] > lows[1] and closes[1] < closes[2]:
        # Check for wick (liquidity grab)
        last_candle = ohlcv[-1]
        low = float(last_candle[3])
        close = float(last_candle[4])
        open_price = float(last_candle[1])
        high = float(last_candle[2])

        # Lower wick indicates rejection
        lower_wick = min(open_price, close) - low
        body = abs(close - open_price)
        if lower_wick > body * 0.5:  # Significant lower wick
            return True

    return False

def calculate_volume_spike_metrics(ohlcv: List) -> Tuple[float, float, float, bool, bool, bool]:
    """
    Calculate volume spike metrics using VPSR Pro logic
    Returns: (vol_ma, vol_stddev, volume_ratio, is_abnormal, is_extreme, is_reversal_signal)
    """
    if len(ohlcv) < VOL_MA_LENGTH + 1:
        return 0.0, 0.0, 1.0, False, False, False

    # Get volumes
    volumes = [float(c[5]) for c in ohlcv]
    current_volume = volumes[-1]
    prev_volume = volumes[-2] if len(volumes) > 1 else current_volume

    # Calculate Volume EMA (using exponential moving average)
    vol_ema = np.mean(volumes[-VOL_MA_LENGTH:])  # Start with SMA
    # Then apply EMA smoothing
    alpha = 2.0 / (VOL_MA_LENGTH + 1.0)
    for vol in volumes[-VOL_MA_LENGTH:]:
        vol_ema = alpha * vol + (1 - alpha) * vol_ema

    # Calculate standard deviation
    vol_stddev = np.std(volumes[-VOL_MA_LENGTH:])

    # Calculate thresholds
    dynamic_threshold = vol_ema + (vol_stddev * VOL_MULTIPLIER)
    extreme_threshold = vol_ema + (vol_stddev * VOL_EXTREME_MULTIPLIER)

    # Classifications
    volume_ratio = current_volume / vol_ema if vol_ema > 0 else 1.0
    is_abnormal = current_volume > dynamic_threshold
    is_extreme = current_volume > extreme_threshold

    # Reversal Signal: Previous bar had extreme volume + current bar is bullish (reversal)
    prev_was_extreme = prev_volume > extreme_threshold if len(volumes) > 1 else False
    current_candle = ohlcv[-1]
    current_is_bullish = float(current_candle[4]) > float(current_candle[1])  # Close > Open

    # For bottom reversals, we want extreme volume followed by bullish reversal
    is_reversal_signal = prev_was_extreme and current_is_bullish

    return vol_ema, vol_stddev, volume_ratio, is_abnormal, is_extreme, is_reversal_signal

# ====================== SELF-LEARNING SYSTEM ======================
class LearningSystem:
    """Self-learning system that adjusts parameters based on performance"""

    def __init__(self):
        self.conn = sqlite3.connect(LEARNING_DB)
        self.init_tables()

    def init_tables(self):
        """Initialize learning tables if needed"""
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS trade_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                entry_time TEXT,
                exit_time TEXT,
                entry_price REAL,
                exit_price REAL,
                pnl_pct REAL,
                confidence_score INTEGER,
                was_winner INTEGER,
                reasons TEXT,
                deviation REAL,
                in_gps INTEGER,
                had_sfp INTEGER
            )
        ''')
        self.conn.commit()

    def record_trade_outcome(self, trade: TradeResult, signal: Signal):
        """Record trade outcome for learning"""
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO trade_outcomes
            (symbol, entry_time, exit_time, entry_price, exit_price, pnl_pct,
             confidence_score, was_winner, reasons, deviation, in_gps, had_sfp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade.symbol,
            trade.entry_time.isoformat(),
            trade.exit_time.isoformat(),
            trade.entry_price,
            trade.exit_price,
            trade.pnl_pct,
            trade.confidence_score,
            1 if trade.was_winner else 0,
            json.dumps(trade.reasons),
            signal.deviation,
            1 if signal.in_gps_zone else 0,
            1 if 'SFP' in ' '.join(signal.reasons) else 0
        ))
        self.conn.commit()

    def analyze_performance(self) -> Dict:
        """Analyze recent performance and suggest adjustments"""
        c = self.conn.cursor()

        # Get last 50 trades
        c.execute('''
            SELECT was_winner, confidence_score, pnl_pct, deviation, in_gps, had_sfp
            FROM trade_outcomes
            ORDER BY exit_time DESC
            LIMIT 50
        ''')
        results = c.fetchall()

        if len(results) < 10:
            return {}  # Not enough data

        winners = [r for r in results if r[0] == 1]
        losers = [r for r in results if r[0] == 0]

        win_rate = len(winners) / len(results) if results else 0

        analysis = {
            'win_rate': win_rate,
            'total_trades': len(results),
            'winners': len(winners),
            'losers': len(losers),
            'avg_winner_confidence': np.mean([w[1] for w in winners]) if winners else 0,
            'avg_loser_confidence': np.mean([l[1] for l in losers]) if losers else 0,
            'avg_winner_pnl': np.mean([w[2] for w in winners]) if winners else 0,
            'avg_loser_pnl': np.mean([l[2] for l in losers]) if losers else 0,
        }

        # Strategy component analysis
        gps_winners = [r for r in winners if r[4] == 1]
        gps_losers = [r for r in losers if r[4] == 1]
        gps_win_rate = len(gps_winners) / (len(gps_winners) + len(gps_losers)) if (gps_winners or gps_losers) else 0

        sfp_winners = [r for r in winners if r[5] == 1]
        sfp_losers = [r for r in losers if r[5] == 1]
        sfp_win_rate = len(sfp_winners) / (len(sfp_winners) + len(sfp_losers)) if (sfp_winners or sfp_losers) else 0

        analysis['gps_win_rate'] = gps_win_rate
        analysis['sfp_win_rate'] = sfp_win_rate

        return analysis

    def get_adjusted_parameters(self) -> Dict:
        """Get adjusted parameters based on learning"""
        analysis = self.analyze_performance()

        if not analysis or analysis['total_trades'] < 10:
            return {}  # Use defaults

        adjustments = {}

        # If win rate is low, increase minimum confidence
        if analysis['win_rate'] < 0.5:
            if analysis['avg_loser_confidence'] > 0:
                # Losers had high confidence, need to be more selective
                adjustments['min_confidence'] = min(85, MIN_CONFIDENCE_SCORE + 5)
        elif analysis['win_rate'] > 0.7:
            # High win rate, can be slightly more aggressive
            adjustments['min_confidence'] = max(65, MIN_CONFIDENCE_SCORE - 5)

        # Adjust GPS weight based on performance
        if analysis.get('gps_win_rate', 0) > 0.65:
            adjustments['gps_weight'] = 1.2  # Increase GPS importance
        elif analysis.get('gps_win_rate', 0) < 0.45:
            adjustments['gps_weight'] = 0.8  # Decrease GPS importance

        # Adjust SFP weight
        if analysis.get('sfp_win_rate', 0) > 0.65:
            adjustments['sfp_weight'] = 1.2
        elif analysis.get('sfp_win_rate', 0) < 0.45:
            adjustments['sfp_weight'] = 0.8

        return adjustments

    def close(self):
        """Close database connection"""
        self.conn.close()

# ====================== MAIN BOT CLASS ======================
class BountySeekerBot:
    """Bounty Seeker - Reversal Sniper Bot"""

    def __init__(self):
        self.exchange = None
        self.learning = LearningSystem()
        self.active_trades = {}  # symbol -> entry_time
        self.state = self.load_state()
        self.adjusted_params = {}
        self.watchlist = []
        self.watchlist_last_update = None
        self.trade_counter = self.state.get("trade_counter", 0)
        self.last_status_minute = None
        self.init_exchange()
        self.load_top_50_watchlist()
        self.reset_trades_if_needed()

    def reset_trades_if_needed(self):
        """Reset trades and counters (one-time)"""
        if self.state.get("trades_reset_v2"):
            return
        try:
            conn = sqlite3.connect(TRADES_DB)
            c = conn.cursor()
            c.execute("DELETE FROM trades")
            conn.commit()
            conn.close()
            self.trade_counter = 0
            self.active_trades = {}
            self.state["trade_counter"] = 0
            self.state["trades_reset_v2"] = True
            self.save_state()
            logger.info("🧹 Trades reset: cleared history and trade numbers restarted")
        except Exception as e:
            logger.error(f"Failed to reset trades: {e}")

    def get_next_trade_number(self) -> int:
        """Get the next trade number and persist it"""
        self.trade_counter += 1
        self.state["trade_counter"] = self.trade_counter
        self.save_state()
        return self.trade_counter

    def get_open_trades(self) -> List[Dict]:
        """Fetch open trades from database"""
        conn = sqlite3.connect(TRADES_DB)
        c = conn.cursor()
        c.execute("""
            SELECT id, trade_number, symbol, entry_price, stop_loss, take_profit, entry_time
            FROM trades WHERE status = 'open'
        """)
        rows = c.fetchall()
        conn.close()
        trades = []
        for r in rows:
            trades.append({
                "id": r[0],
                "trade_number": r[1],
                "symbol": r[2],
                "entry_price": r[3],
                "stop_loss": r[4],
                "take_profit": r[5],
                "entry_time": r[6]
            })
        return trades

    def close_trade(self, trade_id: int, exit_price: float, exit_reason: str, entry_price: float):
        """Close trade with P&L calculation"""
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price else 0.0
        conn = sqlite3.connect(TRADES_DB)
        c = conn.cursor()
        c.execute("""
            UPDATE trades
            SET exit_time = ?, exit_price = ?, pnl_pct = ?, exit_reason = ?, status = 'closed'
            WHERE id = ?
        """, (
            datetime.now(timezone.utc).isoformat(),
            exit_price,
            pnl_pct,
            exit_reason,
            trade_id
        ))
        conn.commit()
        conn.close()
        logger.info(f"✅ Trade closed: #{trade_id} {exit_reason} @ {exit_price:.4f} ({pnl_pct:.2f}%)")

    def check_open_trades(self):
        """Check open trades for TP/SL hit and close them"""
        open_trades = self.get_open_trades()
        for trade in open_trades:
            try:
                ticker = self.exchange.fetch_ticker(trade["symbol"])
                current_price = float(ticker.get("last", 0) or ticker.get("close", 0) or 0)
                if current_price <= 0:
                    continue
                if current_price <= trade["stop_loss"]:
                    self.close_trade(trade["id"], current_price, "stop_loss", trade["entry_price"])
                    if trade["symbol"] in self.active_trades:
                        del self.active_trades[trade["symbol"]]
                elif current_price >= trade["take_profit"]:
                    self.close_trade(trade["id"], current_price, "take_profit", trade["entry_price"])
                    if trade["symbol"] in self.active_trades:
                        del self.active_trades[trade["symbol"]]
            except Exception as e:
                logger.error(f"Failed to check trade {trade.get('symbol')}: {e}")

    def count_open_trades(self) -> int:
        """Count open trades"""
        return len(self.get_open_trades())

    def init_exchange(self):
        """Initialize OKX exchange (perpetual futures)"""
        try:
            self.exchange = ccxt.okx(EXCHANGE_CONFIG)
            self.exchange.load_markets()
            logger.info("✅ OKX Futures connected")
        except Exception as e:
            logger.error(f"❌ Exchange init failed: {e}")
            # Try Binance as fallback
            try:
                logger.info("🔄 Trying Binance as fallback...")
                self.exchange = ccxt.binance({
                    'options': {'defaultType': 'future'},
                    'enableRateLimit': True
                })
                self.exchange.load_markets()
                logger.info("✅ Binance Futures connected (fallback)")
            except Exception as e2:
                logger.error(f"❌ Both exchanges failed. Binance error: {e2}")
                raise

    def get_tradingview_link(self, symbol: str) -> str:
        """Generate TradingView link for symbol - Format: BTC/USDT (no exchange name)"""
        try:
            # Convert OKX format (BTC/USDT:USDT) to TradingView format (BTC/USDT)
            # Remove :USDT suffix if present, keep /USDT format
            if '/USDT:USDT' in symbol:
                # BTC/USDT:USDT -> BTC/USDT
                clean_symbol = symbol.replace(':USDT', '')
            elif '/USDT' in symbol:
                # BTC/USDT -> BTC/USDT (already correct)
                clean_symbol = symbol
            elif ':USDT' in symbol:
                # BTC:USDT -> BTC/USDT
                base = symbol.split(':')[0]
                clean_symbol = f"{base}/USDT"
            else:
                # Just BTC -> BTC/USDT
                base = symbol.split('/')[0] if '/' in symbol else symbol
                clean_symbol = f"{base}/USDT"

            # TradingView format: symbol=BTC/USDT (no exchange name)
            return f"https://www.tradingview.com/chart/?symbol={clean_symbol}"
        except Exception as e:
            # Fallback: try to extract base and add /USDT
            base = symbol.split('/')[0] if '/' in symbol else symbol.split(':')[0]
            return f"https://www.tradingview.com/chart/?symbol={base}/USDT"

    def load_top_50_watchlist(self):
        """Load top 50 perpetual futures USDT pairs by 24h volume"""
        try:
            logger.info("📊 Loading top 50 coins by volume...")

            # Get all swap (perpetual futures) markets
            all_swap_pairs = []
            for market_id, market in self.exchange.markets.items():
                # OKX swap markets: type='swap', quote='USDT'
                if (market.get('type') == 'swap' and
                    market.get('quote') == 'USDT' and
                    market.get('active', True)):
                    all_swap_pairs.append(market_id)

            if not all_swap_pairs:
                logger.warning("⚠️ No swap pairs found, using fallback list")
                self.watchlist = WATCHLIST_SYMBOLS if WATCHLIST_SYMBOLS else []
                return

            logger.info(f"📊 Found {len(all_swap_pairs)} swap pairs, fetching volumes...")

            # Fetch tickers to get volumes
            try:
                tickers = self.exchange.fetch_tickers()
            except Exception as e:
                logger.error(f"Failed to fetch tickers: {e}")
                # Fallback to first 50 pairs
                self.watchlist = all_swap_pairs[:50]
                logger.info(f"📊 Using first 50 pairs as fallback")
                return

            # Get volumes for each pair
            symbol_volumes = []
            for symbol in all_swap_pairs:
                ticker = tickers.get(symbol, {})
                # Try different volume fields
                volume = (ticker.get('quoteVolume') or
                         ticker.get('baseVolume') or
                         ticker.get('info', {}).get('volCcy24h') or
                         0)
                try:
                    volume = float(volume)
                except (ValueError, TypeError):
                    volume = 0.0

                if volume >= MIN_24H_VOLUME_USD:  # Filter by minimum volume
                    symbol_volumes.append((symbol, volume))

            # Sort by volume descending
            symbol_volumes.sort(key=lambda x: x[1], reverse=True)

            # Get top 50
            self.watchlist = [s[0] for s in symbol_volumes[:50]]
            self.watchlist_last_update = datetime.now(timezone.utc)

            # Log top 10 for verification
            top_10_names = [s.split('/')[0] if '/' in s else s.split(':')[0] for s in self.watchlist[:10]]
            logger.info(f"✅ Loaded top 50 coins: {', '.join(top_10_names)}... (Total: {len(self.watchlist)})")

        except Exception as e:
            logger.error(f"❌ Failed to load watchlist: {e}")
            # Fallback to common pairs
            self.watchlist = [
                'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'BNB/USDT:USDT',
                'XRP/USDT:USDT', 'ADA/USDT:USDT', 'AVAX/USDT:USDT', 'DOGE/USDT:USDT',
                'TRX/USDT:USDT', 'LINK/USDT:USDT', 'MATIC/USDT:USDT', 'DOT/USDT:USDT',
                'UNI/USDT:USDT', 'LTC/USDT:USDT', 'ATOM/USDT:USDT', 'ETC/USDT:USDT',
                'ARB/USDT:USDT', 'OP/USDT:USDT', 'SUI/USDT:USDT', 'APT/USDT:USDT',
                'INJ/USDT:USDT', 'TIA/USDT:USDT', 'SEI/USDT:USDT', 'WLD/USDT:USDT'
            ]
            logger.info(f"📊 Using fallback watchlist ({len(self.watchlist)} pairs)")

    def should_update_watchlist(self) -> bool:
        """Check if watchlist should be updated"""
        if not self.watchlist_last_update:
            return True
        elapsed = (datetime.now(timezone.utc) - self.watchlist_last_update).total_seconds()
        return elapsed >= WATCHLIST_UPDATE_INTERVAL

    def load_state(self) -> Dict:
        """Load bot state from file"""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_state(self):
        """Save bot state to file"""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def get_next_scan_time_utc(self) -> datetime:
        """Next scan time at XX:45 UTC"""
        now = datetime.now(timezone.utc)
        next_scan = now.replace(second=0, microsecond=0)
        if next_scan.minute < 45:
            next_scan = next_scan.replace(minute=45)
        else:
            next_scan = (next_scan + timedelta(hours=1)).replace(minute=45)
        return next_scan

    def write_status(self, status: str, signals: Optional[List[Signal]] = None):
        """Write bot status to JSON for the website"""
        try:
            open_trades = self.get_open_trades()
            payload = {
                "status": status,
                "exchange": EXCHANGE_NAME,
                "watchlist_size": len(self.watchlist),
                "last_scan_time": self.state.get("last_scan_time"),
                "next_scan_time": self.get_next_scan_time_utc().isoformat(),
                "open_trades": open_trades,
                "signals": []
            }

            if signals:
                payload["signals"] = [
                    {
                        "symbol": s.symbol,
                        "entry_price": s.entry_price,
                        "stop_loss": s.stop_loss,
                        "take_profit": s.take_profit,
                        "confidence_score": s.confidence_score,
                        "reasons": s.reasons[:3],
                        "rsi": s.rsi,
                        "deviation": s.deviation,
                        "in_gps_zone": s.in_gps_zone,
                        "timestamp": s.timestamp.isoformat(),
                        "tradingview_link": s.tradingview_link
                    }
                    for s in signals
                ]

            with open(STATUS_FILE, 'w') as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write status file: {e}")

    def is_scan_time(self) -> bool:
        """Check if it's time to scan (XX:45 - 15 minutes before hour)"""
        now = datetime.now(timezone.utc)
        return now.minute == 45 and now.second < 5

    def analyze_symbol(self, symbol: str) -> Optional[Signal]:
        """Analyze a symbol for reversal signals"""
        try:
            # Fetch 15m candles
            timeframe = '15m'
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=200)

            if len(ohlcv) < 50:
                return None

            # Get current data
            current_candle = ohlcv[-1]
            current_price = float(current_candle[4])  # Close
            high = float(current_candle[2])
            low = float(current_candle[3])
            volume = float(current_candle[5])

            # Get daily range for GPS
            daily_ohlcv = self.exchange.fetch_ohlcv(symbol, '1d', limit=1)
            if daily_ohlcv:
                daily_high = float(daily_ohlcv[-1][2])
                daily_low = float(daily_ohlcv[-1][3])
            else:
                # Use recent candles to estimate daily range
                daily_high = max([float(c[2]) for c in ohlcv[-96:]])  # Last 24h of 15m candles
                daily_low = min([float(c[3]) for c in ohlcv[-96:]])

            # Calculate indicators
            closes = [float(c[4]) for c in ohlcv]
            rsi = calculate_rsi(closes, RSI_PERIOD)
            vwap, std_dev, deviation_sigma = calculate_vwap_and_deviation(ohlcv)
            in_gps, gps_distance = calculate_gps_zone(daily_high, daily_low, current_price)
            has_sfp = detect_sfp_reversal(ohlcv)

            if vwap is None or std_dev is None or deviation_sigma is None:
                return None

            # Calculate volume spike metrics (VPSR Pro logic)
            vol_ma, vol_stddev, volume_ratio, is_abnormal_vol, is_extreme_vol, is_vol_reversal = calculate_volume_spike_metrics(ohlcv)

            # Score the signal
            score = 0
            reasons = []

            # 1. Deviation Zone (2.5σ - 3σ) - Most important
            if deviation_sigma <= -DEVIATION_3SIGMA:
                score += 40
                reasons.append(f"Deviation Zone -3 Sigma (Mean Reversion)")
            elif deviation_sigma <= -DEVIATION_2SIGMA:
                score += 30
                reasons.append(f"Deviation Zone -2.5 Sigma")
            elif deviation_sigma <= -1.5:  # More lenient - catch more opportunities
                score += 20
                reasons.append(f"Deviation Zone -1.5 Sigma (Oversold)")

            # 2. GPS Zone (Golden Pocket)
            if in_gps:
                gps_weight = self.adjusted_params.get('gps_weight', 1.0)
                score += int(30 * gps_weight)
                reasons.append(f"Price in Daily Golden Pocket (0.618-0.65)")
            elif gps_distance < 1.0:  # More lenient - within 1%
                score += 20
                reasons.append(f"Near GPS Zone ({gps_distance:.2f}% away)")
            elif gps_distance < 2.0:  # Even more lenient
                score += 10
                reasons.append(f"Approaching GPS Zone ({gps_distance:.2f}% away)")

            # 3. RSI Divergence - More lenient
            if rsi < 40 and rsi > 20:  # Wider range
                score += 20
                reasons.append(f"RSI Oversold ({rsi:.1f})")
            elif rsi < 30:
                score += 15
                reasons.append(f"RSI Extreme Oversold ({rsi:.1f})")
            elif rsi < 50:  # Even more lenient
                score += 10
                reasons.append(f"RSI Below Midline ({rsi:.1f})")

            # 4. SFP Reversal
            if has_sfp:
                sfp_weight = self.adjusted_params.get('sfp_weight', 1.0)
                score += int(15 * sfp_weight)
                reasons.append("SFP Reversal Detected (Sweeping Lows)")

            # 5. Volume Spike Detection (VPSR Pro Logic) - High Priority
            if is_vol_reversal:
                # Extreme volume on previous bar + bullish reversal = strong signal
                score += 25
                reasons.append(f"Volume Reversal Signal (Extreme Vol + Bullish Reversal)")
            elif is_extreme_vol:
                # Extreme volume spike (3.5x threshold)
                score += 20
                reasons.append(f"Extreme Volume Spike ({volume_ratio:.1f}x - {VOL_EXTREME_MULTIPLIER}x threshold)")
            elif is_abnormal_vol:
                # Abnormal volume spike (2.0x threshold)
                score += 15
                reasons.append(f"Abnormal Volume Spike ({volume_ratio:.1f}x - {VOL_MULTIPLIER}x threshold)")
            elif volume_ratio > 1.5:
                # Standard volume confirmation
                score += 10
                reasons.append(f"Volume Spike ({volume_ratio:.1f}x average)")
            elif volume_ratio > 1.2:  # Lower threshold
                score += 5
                reasons.append(f"Volume Above Average ({volume_ratio:.1f}x)")

            # 6. Price near daily low (additional signal)
            price_from_low = ((current_price - daily_low) / (daily_high - daily_low)) * 100 if (daily_high - daily_low) > 0 else 50
            if price_from_low < 20:  # Bottom 20% of daily range
                score += 15
                reasons.append(f"Price Near Daily Low ({price_from_low:.1f}% from low)")
            elif price_from_low < 35:  # Bottom 35% of daily range
                score += 10
                reasons.append(f"Price in Lower Range ({price_from_low:.1f}% from low)")

            # Apply adjusted minimum confidence (but don't go below 45)
            min_confidence = max(45, self.adjusted_params.get('min_confidence', MIN_CONFIDENCE_SCORE))

            # Debug logging for near-misses
            if score >= min_confidence - 10 and score < min_confidence:
                logger.debug(f"Near miss: {symbol} - Score: {score}/{min_confidence}, Deviation: {deviation_sigma:.2f}σ, RSI: {rsi:.1f}, GPS: {in_gps}")

            if score >= min_confidence:
                # Calculate stop loss and take profit
                stop_loss = current_price * (1 - STOP_LOSS_PCT / 100)
                take_profit = current_price * (1 + TARGET_PROFIT_PCT / 100)

                # Generate TradingView link
                tv_link = self.get_tradingview_link(symbol)

                return Signal(
                    symbol=symbol,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence_score=score,
                    reasons=reasons,
                    rsi=rsi,
                    deviation=deviation_sigma,
                    in_gps_zone=in_gps,
                    timestamp=datetime.now(timezone.utc),
                    tradingview_link=tv_link
                )

            return None

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def send_top_picks_discord(self, picks: List[Signal]):
        """Send top picks to Discord in a single card"""
        try:
            if not picks:
                return

            time_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

            # Single orange card with all trades
            fields = []
            for i, signal in enumerate(picks, 1):
                rank_emoji = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"#{i}"
                title = f"{rank_emoji} TRADE #{signal.trade_number} • {signal.symbol}"
                value_lines = [
                    f"**Entry**: ${signal.entry_price:.4f}",
                    f"**Stop**: ${signal.stop_loss:.4f}",
                    f"**TP**: ${signal.take_profit:.4f}",
                    f"**Confidence**: {signal.confidence_score}/100",
                    f"**RSI**: {signal.rsi:.1f} | **Dev**: {signal.deviation:.2f}σ",
                    f"**Status**: EXECUTED",
                    f"**Why**: {', '.join(signal.reasons[:3])}",
                    f"**Chart**: [Open TradingView]({signal.tradingview_link})"
                ]
                fields.append({
                    "name": title,
                    "value": "\n".join(value_lines),
                    "inline": False
                })

            embed = {
                "title": f"🟧 BOUNTY ALERTS • {len(picks)} TRADE(S)",
                "description": "Top reversal setups (15m scan). Trades are numbered and executed.",
                "color": 0xF39C12,  # Orange
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fields": fields,
                "footer": {
                    "text": f"Bounty Seeker // Reversal Sniper • {time_str}"
                }
            }

            payload = {"embeds": [embed]}
            response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)

            if response.status_code in (200, 201, 204):
                symbols_str = ", ".join([s.symbol for s in picks])
                logger.info(f"✅ Discord alert sent for top {len(picks)} picks: {symbols_str}")
                return True
            else:
                logger.error(f"Discord error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def send_discord_alert(self, signal: Signal):
        """Send Discord webhook alert immediately - Green card style"""
        try:
            # Format timestamp
            time_str = signal.timestamp.strftime("%H:%M:%S UTC")

            # Create rich embed matching HTML style
            embed = {
                "title": f"{signal.symbol} // REVERSAL ALERT",
                "description": "Targeting local bottom for mean reversion bounce.",
                "color": 0x0ecb81,  # Green (#0ecb81)
                "timestamp": signal.timestamp.isoformat(),
                "fields": [
                    {
                        "name": "ENTRY",
                        "value": f"${signal.entry_price:.4f}",
                        "inline": True
                    },
                    {
                        "name": "STOP LOSS",
                        "value": f"${signal.stop_loss:.4f}",
                        "inline": True
                    },
                    {
                        "name": "TAKE PROFIT",
                        "value": f"${signal.take_profit:.4f}",
                        "inline": True
                    },
                    {
                        "name": "CONFIDENCE",
                        "value": f"{signal.confidence_score}/100",
                        "inline": True
                    },
                    {
                        "name": "RSI",
                        "value": f"{signal.rsi:.1f}",
                        "inline": True
                    },
                    {
                        "name": "DEVIATION",
                        "value": f"{signal.deviation:.2f}σ",
                        "inline": True
                    },
                    {
                        "name": "Why This Trade?",
                        "value": "\n".join([f"✅ {r}" for r in signal.reasons]),
                        "inline": False
                    },
                    {
                        "name": "📊 TradingView Chart",
                        "value": f"[Open Chart →]({signal.tradingview_link})",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": f"Bounty Seeker // Reversal Sniper • {time_str}"
                }
            }

            # Send immediately
            payload = {"embeds": [embed]}
            response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)

            if response.status_code in (200, 201, 204):
                logger.info(f"✅ Discord alert sent for {signal.symbol} (Score: {signal.confidence_score})")
                return True
            else:
                logger.error(f"Discord error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def save_trade(self, signal: Signal):
        """Save trade to database"""
        try:
            conn = sqlite3.connect(TRADES_DB)
            c = conn.cursor()
            c.execute('''
                INSERT INTO trades
                (trade_number, symbol, entry_price, stop_loss, take_profit, confidence_score, reasons, entry_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal.trade_number,
                signal.symbol,
                signal.entry_price,
                signal.stop_loss,
                signal.take_profit,
                signal.confidence_score,
                json.dumps(signal.reasons),
                signal.timestamp.isoformat(),
                'open'
            ))
            conn.commit()
            conn.close()
            logger.info(f"✅ Trade executed: #{signal.trade_number} {signal.symbol} @ {signal.entry_price:.4f}")
        except Exception as e:
            logger.error(f"Failed to save trade: {e}")

    def scan_markets(self):
        """Scan all watchlist symbols for signals"""
        logger.info("🔍 Scanning markets for reversal opportunities...")

        # Update watchlist if needed
        if self.should_update_watchlist():
            logger.info("🔄 Updating watchlist...")
            self.load_top_50_watchlist()

        if not self.watchlist:
            logger.warning("⚠️ No symbols in watchlist, skipping scan")
            return []

        # Check open trades for TP/SL
        self.check_open_trades()

        # Enforce max open trades
        open_trades = self.count_open_trades()
        if open_trades >= 3:
            logger.info(f"⛔ Max open trades reached ({open_trades}/3). Waiting for TP/SL.")
            return []

        signals_found = []
        for symbol in self.watchlist:
            # Check cooldown
            if symbol in self.active_trades:
                elapsed = (datetime.now(timezone.utc) - self.active_trades[symbol]).total_seconds()
                if elapsed < ACTIVE_TRADES_COOLDOWN:
                    continue

            # Analyze symbol
            signal = self.analyze_symbol(symbol)
            if signal:
                signals_found.append(signal)
                logger.info(f"✅ Signal found: {signal.symbol} (Score: {signal.confidence_score}) - Reasons: {', '.join(signal.reasons[:2])}")

            # Rate limiting
            time.sleep(0.3)  # Slightly faster since we're scanning more

        if not signals_found:
            logger.info("⏳ No signals found this scan")
            return []

        # Sort by confidence score (highest first)
        signals_found.sort(key=lambda x: x.confidence_score, reverse=True)

        # Get top 3 picks (or all if less than 3)
        top_picks = signals_found[:3] if len(signals_found) >= 3 else signals_found

        # Send picks to Discord (only if we have at least 1)
        if top_picks:
            # Assign trade numbers
            for signal in top_picks:
                signal.trade_number = self.get_next_trade_number()
            logger.info(f"🎯 Found {len(signals_found)} signals, sending top {len(top_picks)} picks...")
            self.send_top_picks_discord(top_picks)

            # Save all picks to database and mark as active
            for signal in top_picks:
                self.save_trade(signal)
                self.active_trades[signal.symbol] = signal.timestamp
        else:
            # Debug: Log why no signals found
            logger.info(f"⏳ No signals found - Scanned {len(self.watchlist)} symbols, confidence threshold: {self.adjusted_params.get('min_confidence', MIN_CONFIDENCE_SCORE)}")

        return top_picks

    def update_learning(self):
        """Update learning system with recent performance"""
        try:
            # Get adjusted parameters
            self.adjusted_params = self.learning.get_adjusted_parameters()
            if self.adjusted_params:
                logger.info(f"🧠 Learning adjustments: {self.adjusted_params}")
        except Exception as e:
            logger.error(f"Learning update failed: {e}")

    def send_startup_notification(self):
        """Send startup notification to Discord - DISABLED (only send signals)"""
        # Removed - user has HTML interface, only send signals
        logger.info("✅ Bot started (Discord notifications disabled for startup)")

    def run(self):
        """Main bot loop"""
        logger.info("🚀 Bounty Seeker Bot Started")
        logger.info(f"📊 Monitoring {len(self.watchlist)} symbols (Top 50 by volume)")
        logger.info("⏰ Scanning at XX:45 (15 minutes before hour)")
        logger.info("🔕 Discord: Only sending signals (no scanning messages)")

        # Startup notification disabled - user has HTML interface
        self.send_startup_notification()
        self.write_status("ACTIVE")

        last_scan_minute = -1
        last_scan_hour = -1

        while True:
            try:
                now = datetime.now(timezone.utc)

                # Scan ONLY at XX:45 (15 minutes before the hour) - once per hour
                if now.minute == 45 and now.second < 5:
                    # Make sure we don't scan twice in the same minute/hour
                    if now.minute != last_scan_minute or now.hour != last_scan_hour:
                        logger.info(f"⏰ Scan time: {now.strftime('%H:%M:%S UTC')} (15 min before hour)")
                        self.write_status("SCANNING")
                        self.update_learning()  # Update parameters based on performance
                        signals = self.scan_markets()
                        last_scan_minute = now.minute
                        last_scan_hour = now.hour
                        self.state["last_scan_time"] = now.isoformat()
                        self.save_state()
                        if signals:
                            logger.info(f"✅ Scan complete: Found {len(signals)} signals, sent to Discord")
                        else:
                            logger.info(f"⏳ Scan complete: No signals found")
                        self.write_status("ACTIVE", signals=signals)

                # Update learning every hour
                if now.minute == 0 and now.second < 5:
                    self.update_learning()

                # Heartbeat status update every minute
                if self.last_status_minute != now.minute:
                    self.last_status_minute = now.minute
                    self.write_status("ACTIVE")

                time.sleep(1)  # Check every second

            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)

        self.learning.close()
        logger.info("👋 Bounty Seeker Bot Stopped")

# ====================== MAIN ======================
if __name__ == "__main__":
    init_databases()
    bot = BountySeekerBot()
    bot.run()
