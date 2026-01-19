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
MIN_CONFIDENCE_SCORE = 40  # Minimum score to trigger signal (0-100) - Lowered to find more scalping opportunities
TARGET_PROFIT_PCT = 2.5  # Target 2-3% gains
STOP_LOSS_PCT = 1.0  # 1% stop loss
RISK_REWARD_RATIO = 2.5  # 2.5:1 R:R

# Technical Parameters
RSI_PERIOD = 14
VWAP_LOOKBACK = 200
VOLUME_LOOKBACK = 20
DEVIATION_2SIGMA = 2.0  # 2.0σ threshold (more sensitive)
DEVIATION_3SIGMA = 2.5  # 2.5σ threshold (preferred, lowered from 3.0)
GPS_LOW = 0.618  # Golden Pocket low (Fibonacci)
GPS_HIGH = 0.65  # Golden Pocket high

# Volume Spike Detection (VPSR Pro Logic)
VOL_MA_LENGTH = 20  # Volume MA Length
VOL_MULTIPLIER = 1.5  # Abnormal Volume Threshold (lowered from 2.0 for more signals)
VOL_EXTREME_MULTIPLIER = 2.5  # Extreme Volume Threshold (lowered from 3.5)

# Market Filters
MIN_24H_VOLUME_USD = 10000000  # $10M minimum volume
SCAN_INTERVAL_SEC = 60  # Check every minute for XX:00/30 window
ACTIVE_TRADES_COOLDOWN = 300  # 5 minutes cooldown per symbol

# Assets to monitor (Will be dynamically loaded - Top 10 by volume)
WATCHLIST_SYMBOLS = []  # Populated dynamically
WATCHLIST_UPDATE_INTERVAL = 3600  # Update watchlist every hour
WATCHLIST_SIZE = 10

# Signal routing
DISCORD_SIGNAL_BIAS = "LONG"  # LONG only for Discord alerts
SITE_SIGNAL_BIAS = "BOTH"     # BOTH for website status feed

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
    direction: str
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

def calculate_upper_gps_zone(high: float, low: float, current_price: float) -> Tuple[bool, float]:
    """
    Upper Golden Pocket (for short bias) - from high down to 0.618-0.65
    """
    range_size = high - low
    if range_size == 0:
        return False, 100.0

    gp_high_level = high - (range_size * GPS_LOW)
    gp_low_level = high - (range_size * GPS_HIGH)

    if gp_low_level <= current_price <= gp_high_level:
        return True, 0.0

    if current_price > gp_high_level:
        distance = abs(current_price - gp_high_level) / current_price * 100
    else:
        distance = abs(current_price - gp_low_level) / current_price * 100

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

def detect_sfp_reversal_high(ohlcv: List) -> bool:
    """
    Detect Swing Failure Pattern (SFP) - price sweeps high then reverses
    """
    if len(ohlcv) < 5:
        return False

    recent = ohlcv[-3:]
    highs = [float(c[2]) for c in recent]
    closes = [float(c[4]) for c in recent]

    # SFP: Higher high followed by lower close (reversal)
    if highs[0] < highs[1] and closes[1] > closes[2]:
        last_candle = ohlcv[-1]
        low = float(last_candle[3])
        close = float(last_candle[4])
        open_price = float(last_candle[1])
        high = float(last_candle[2])

        upper_wick = high - max(open_price, close)
        body = abs(close - open_price)
        if upper_wick > body * 0.5:
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

        # If win rate is low, increase minimum confidence (but keep it reasonable for scalping)
        if analysis['win_rate'] < 0.5:
            if analysis['avg_loser_confidence'] > 0:
                # Losers had high confidence, need to be more selective but still allow scalping
                adjustments['min_confidence'] = min(55, MIN_CONFIDENCE_SCORE + 5)
        elif analysis['win_rate'] > 0.7:
            # High win rate, can be more aggressive for scalping
            adjustments['min_confidence'] = max(35, MIN_CONFIDENCE_SCORE - 5)

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
        self.trending_coins = []
        self.standout_coin = None
        self.top_gainers = []
        self.top_losers = []
        self.watchlist_candidates = []
        self.trade_counter = self.state.get("trade_counter", 0)
        self.signal_counter = self.state.get("signal_counter", 0)
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
        """Load top 10 perpetual futures USDT pairs by 24h volume"""
        try:
            logger.info("📊 Loading top 10 coins by volume...")

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
                # Fallback to first 10 pairs
                self.watchlist = all_swap_pairs[:WATCHLIST_SIZE]
                logger.info("📊 Using first 10 pairs as fallback")
                return

            def safe_float(value, default=0.0):
                try:
                    if value is None:
                        return default
                    return float(value)
                except (ValueError, TypeError):
                    return default

            def compute_change_pct(ticker):
                pct = ticker.get('percentage')
                pct = safe_float(pct, None)

                if pct is None:
                    info = ticker.get('info', {}) or {}
                    last = safe_float(ticker.get('last') or info.get('last'))
                    open_24h = safe_float(
                        ticker.get('open') or info.get('open24h') or info.get('sodUtc0') or info.get('sodUtc8')
                    )
                    if open_24h > 0:
                        pct = ((last - open_24h) / open_24h) * 100
                    else:
                        pct = 0.0

                # Heuristic: if pct looks like a ratio (0.02), convert to percent
                if abs(pct) < 1:
                    info = ticker.get('info', {}) or {}
                    last = safe_float(ticker.get('last') or info.get('last'))
                    open_24h = safe_float(
                        ticker.get('open') or info.get('open24h') or info.get('sodUtc0') or info.get('sodUtc8')
                    )
                    if open_24h > 0:
                        calc_pct = ((last - open_24h) / open_24h) * 100
                        if abs(calc_pct) >= 1:
                            pct = calc_pct
                    else:
                        pct = pct * 100

                return pct

            # Get volumes for each pair
            symbol_volumes = []
            symbol_changes = []
            for symbol in all_swap_pairs:
                ticker = tickers.get(symbol, {})
                # Try different volume fields
                volume = (ticker.get('quoteVolume') or
                         ticker.get('baseVolume') or
                         ticker.get('info', {}).get('volCcy24h') or
                         0)
                volume = safe_float(volume)
                pct_change = compute_change_pct(ticker)

                if volume >= MIN_24H_VOLUME_USD:  # Filter by minimum volume
                    symbol_volumes.append((symbol, volume))
                    symbol_changes.append((symbol, pct_change, volume))

            # Sort by volume descending
            symbol_volumes.sort(key=lambda x: x[1], reverse=True)

            # Get top 10
            self.watchlist = [s[0] for s in symbol_volumes[:WATCHLIST_SIZE]]
            self.watchlist_last_update = datetime.now(timezone.utc)

            # Log top 10 for verification
            top_10_names = [s.split('/')[0] if '/' in s else s.split(':')[0] for s in self.watchlist[:10]]
            logger.info(f"✅ Loaded top 10 coins: {', '.join(top_10_names)} (Total: {len(self.watchlist)})")

            # Top movers from 24h % change
            gainers_sorted = sorted(symbol_changes, key=lambda x: x[1], reverse=True)
            losers_sorted = sorted(symbol_changes, key=lambda x: x[1])

            self.trending_coins = [
                {"symbol": s, "change_pct": pct, "volume": vol}
                for s, pct, vol in gainers_sorted[:5]
            ]
            self.top_gainers = [
                {"symbol": s, "change_pct": pct, "volume": vol}
                for s, pct, vol in gainers_sorted[:5]
            ]
            self.top_losers = [
                {"symbol": s, "change_pct": pct, "volume": vol}
                for s, pct, vol in losers_sorted[:5]
            ]

            # Standout coin (highest absolute % change)
            if symbol_changes:
                standout = max(symbol_changes, key=lambda x: abs(x[1]))
                self.standout_coin = {
                    "symbol": standout[0],
                    "change_pct": standout[1],
                    "volume": standout[2],
                    "reason": "Top 24h mover"
                }

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

    def increment_signal_counter(self, count: int):
        """Increment and persist total signals count"""
        self.signal_counter += count
        self.state["signal_counter"] = self.signal_counter
        self.save_state()

    def get_next_scan_time_utc(self) -> datetime:
        """Next scan time at XX:00 or XX:30 UTC"""
        now = datetime.now(timezone.utc)
        next_scan = now.replace(second=0, microsecond=0)
        if next_scan.minute < 30:
            next_scan = next_scan.replace(minute=30)
        else:
            next_scan = (next_scan + timedelta(hours=1)).replace(minute=0)
        return next_scan

    def write_status(self, status: str, signals: Optional[List[Signal]] = None):
        """Write bot status to JSON for the website"""
        try:
            open_trades = self.get_open_trades()
            last_signals = self.state.get("last_signals", [])

            def serialize_signals(items: List[Signal]):
                return [
                    {
                        "symbol": s.symbol,
                        "direction": s.direction,
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
                    for s in items
                ]

            payload = {
                "status": status,
                "exchange": EXCHANGE_NAME,
                "watchlist_size": len(self.watchlist),
                "signal_count": self.signal_counter,
                "last_scan_time": self.state.get("last_scan_time"),
                "next_scan_time": self.get_next_scan_time_utc().isoformat(),
                "open_trades": open_trades,
                "signals": [],
                "last_signals": last_signals,
                "watchlist_candidates": self.watchlist_candidates,
                "trending_coins": self.trending_coins,
                "spotlight": self.standout_coin,
                "top_gainers": self.top_gainers,
                "top_losers": self.top_losers
            }

            if signals:
                payload["signals"] = serialize_signals(signals)
                payload["last_signals"] = payload["signals"]
                self.state["last_signals"] = payload["signals"]
                self.save_state()

            with open(STATUS_FILE, 'w') as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write status file: {e}")

    def is_scan_time(self) -> bool:
        """Check if it's time to scan (XX:45 - 15 minutes before hour)"""
        now = datetime.now(timezone.utc)
        return now.minute == 45 and now.second < 5

    def analyze_symbol(self, symbol: str, bias: str = "both") -> Optional[Signal]:
        """Analyze a symbol for reversal signals (long + short)"""
        try:
            timeframe = '15m'
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=200)

            if len(ohlcv) < 50:
                return None

            current_candle = ohlcv[-1]
            current_open = float(current_candle[1])
            current_price = float(current_candle[4])

            daily_ohlcv = self.exchange.fetch_ohlcv(symbol, '1d', limit=1)
            if daily_ohlcv:
                daily_high = float(daily_ohlcv[-1][2])
                daily_low = float(daily_ohlcv[-1][3])
            else:
                daily_high = max([float(c[2]) for c in ohlcv[-96:]])
                daily_low = min([float(c[3]) for c in ohlcv[-96:]])

            closes = [float(c[4]) for c in ohlcv]
            rsi = calculate_rsi(closes, RSI_PERIOD)
            vwap, std_dev, deviation_sigma = calculate_vwap_and_deviation(ohlcv)

            in_gps_long, gps_dist_long = calculate_gps_zone(daily_high, daily_low, current_price)
            in_gps_short, gps_dist_short = calculate_upper_gps_zone(daily_high, daily_low, current_price)
            has_sfp_long = detect_sfp_reversal(ohlcv)
            has_sfp_short = detect_sfp_reversal_high(ohlcv)

            if vwap is None or std_dev is None or deviation_sigma is None:
                return None

            vol_ma, vol_stddev, volume_ratio, is_abnormal_vol, is_extreme_vol, is_vol_reversal = calculate_volume_spike_metrics(ohlcv)
            is_bullish = current_price > current_open
            is_bearish = current_price < current_open
            vol_reversal_short = is_extreme_vol and is_bearish

            # Apply adjusted minimum confidence (but don't go below 35 for scalping)
            min_confidence = max(35, self.adjusted_params.get('min_confidence', MIN_CONFIDENCE_SCORE))

            def build_signal(direction: str, score: int, reasons: List[str], in_gps_zone: bool) -> Signal:
                if direction == "LONG":
                    stop_loss = current_price * (1 - STOP_LOSS_PCT / 100)
                    take_profit = current_price * (1 + TARGET_PROFIT_PCT / 100)
                else:
                    stop_loss = current_price * (1 + STOP_LOSS_PCT / 100)
                    take_profit = current_price * (1 - TARGET_PROFIT_PCT / 100)

                tv_link = self.get_tradingview_link(symbol)
                return Signal(
                    symbol=symbol,
                    direction=direction,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence_score=score,
                    reasons=reasons,
                    rsi=rsi,
                    deviation=deviation_sigma,
                    in_gps_zone=in_gps_zone,
                    timestamp=datetime.now(timezone.utc),
                    tradingview_link=tv_link
                )

            # Long scoring
            long_score = 0
            long_reasons = []

            if deviation_sigma <= -DEVIATION_3SIGMA:
                long_score += 40
                long_reasons.append("Deviation Zone -2.5 Sigma (Mean Reversion)")
            elif deviation_sigma <= -DEVIATION_2SIGMA:
                long_score += 30
                long_reasons.append("Deviation Zone -2.0 Sigma")
            elif deviation_sigma <= -1.5:
                long_score += 20
                long_reasons.append("Deviation Zone -1.5 Sigma (Oversold)")
            elif deviation_sigma <= -1.0:
                long_score += 15
                long_reasons.append("Deviation Zone -1.0 Sigma (Slightly Oversold)")

            if in_gps_long:
                gps_weight = self.adjusted_params.get('gps_weight', 1.0)
                long_score += int(30 * gps_weight)
                long_reasons.append("Price in Daily Golden Pocket (0.618-0.65)")
            elif gps_dist_long < 1.0:
                long_score += 20
                long_reasons.append(f"Near GPS Zone ({gps_dist_long:.2f}% away)")
            elif gps_dist_long < 2.0:
                long_score += 15
                long_reasons.append(f"Approaching GPS Zone ({gps_dist_long:.2f}% away)")
            elif gps_dist_long < 3.0:
                long_score += 10
                long_reasons.append(f"Getting Close to GPS Zone ({gps_dist_long:.2f}% away)")

            if rsi < 40 and rsi > 20:
                long_score += 20
                long_reasons.append(f"RSI Oversold ({rsi:.1f})")
            elif rsi < 30:
                long_score += 15
                long_reasons.append(f"RSI Extreme Oversold ({rsi:.1f})")
            elif rsi < 50:
                long_score += 12
                long_reasons.append(f"RSI Below Midline ({rsi:.1f})")
            elif rsi < 55:
                long_score += 8
                long_reasons.append(f"RSI Slightly Below Midline ({rsi:.1f})")

            if has_sfp_long:
                sfp_weight = self.adjusted_params.get('sfp_weight', 1.0)
                long_score += int(15 * sfp_weight)
                long_reasons.append("SFP Reversal Detected (Sweeping Lows)")

            if is_vol_reversal and is_bullish:
                long_score += 25
                long_reasons.append("Volume Reversal (Extreme Vol + Bullish Reversal)")
            elif is_extreme_vol:
                long_score += 20
                long_reasons.append(f"Extreme Volume Spike ({volume_ratio:.1f}x)")
            elif is_abnormal_vol:
                long_score += 15
                long_reasons.append(f"Abnormal Volume Spike ({volume_ratio:.1f}x)")
            elif volume_ratio > 1.5:
                long_score += 10
                long_reasons.append(f"Volume Spike ({volume_ratio:.1f}x avg)")
            elif volume_ratio > 1.2:
                long_score += 8
                long_reasons.append(f"Volume Above Average ({volume_ratio:.1f}x)")
            elif volume_ratio > 1.0:
                long_score += 5
                long_reasons.append(f"Volume Slightly Above Average ({volume_ratio:.1f}x)")

            price_from_low = ((current_price - daily_low) / (daily_high - daily_low)) * 100 if (daily_high - daily_low) > 0 else 50
            if price_from_low < 20:
                long_score += 15
                long_reasons.append(f"Price Near Daily Low ({price_from_low:.1f}% from low)")
            elif price_from_low < 35:
                long_score += 12
                long_reasons.append(f"Price in Lower Range ({price_from_low:.1f}% from low)")
            elif price_from_low < 45:
                long_score += 8
                long_reasons.append(f"Price in Lower Half ({price_from_low:.1f}% from low)")

            # Short scoring
            short_score = 0
            short_reasons = []

            if deviation_sigma >= DEVIATION_3SIGMA:
                short_score += 40
                short_reasons.append("Deviation Zone +2.5 Sigma (Mean Reversion)")
            elif deviation_sigma >= DEVIATION_2SIGMA:
                short_score += 30
                short_reasons.append("Deviation Zone +2.0 Sigma")
            elif deviation_sigma >= 1.5:
                short_score += 20
                short_reasons.append("Deviation Zone +1.5 Sigma (Overbought)")
            elif deviation_sigma >= 1.0:
                short_score += 15
                short_reasons.append("Deviation Zone +1.0 Sigma (Slightly Overbought)")

            if in_gps_short:
                gps_weight = self.adjusted_params.get('gps_weight', 1.0)
                short_score += int(30 * gps_weight)
                short_reasons.append("Price in Upper Golden Pocket (0.618-0.65)")
            elif gps_dist_short < 1.0:
                short_score += 20
                short_reasons.append(f"Near Upper GPS Zone ({gps_dist_short:.2f}% away)")
            elif gps_dist_short < 2.0:
                short_score += 15
                short_reasons.append(f"Approaching Upper GPS Zone ({gps_dist_short:.2f}% away)")
            elif gps_dist_short < 3.0:
                short_score += 10
                short_reasons.append(f"Getting Close to Upper GPS Zone ({gps_dist_short:.2f}% away)")

            if rsi > 60 and rsi < 80:
                short_score += 20
                short_reasons.append(f"RSI Overbought ({rsi:.1f})")
            elif rsi > 70:
                short_score += 15
                short_reasons.append(f"RSI Extreme Overbought ({rsi:.1f})")
            elif rsi > 50:
                short_score += 12
                short_reasons.append(f"RSI Above Midline ({rsi:.1f})")
            elif rsi > 45:
                short_score += 8
                short_reasons.append(f"RSI Slightly Above Midline ({rsi:.1f})")

            if has_sfp_short:
                sfp_weight = self.adjusted_params.get('sfp_weight', 1.0)
                short_score += int(15 * sfp_weight)
                short_reasons.append("SFP Reversal Detected (Sweeping Highs)")

            if vol_reversal_short:
                short_score += 25
                short_reasons.append("Volume Reversal (Extreme Vol + Bearish Reversal)")
            elif is_extreme_vol:
                short_score += 20
                short_reasons.append(f"Extreme Volume Spike ({volume_ratio:.1f}x)")
            elif is_abnormal_vol:
                short_score += 15
                short_reasons.append(f"Abnormal Volume Spike ({volume_ratio:.1f}x)")
            elif volume_ratio > 1.5:
                short_score += 10
                short_reasons.append(f"Volume Spike ({volume_ratio:.1f}x avg)")
            elif volume_ratio > 1.2:
                short_score += 8
                short_reasons.append(f"Volume Above Average ({volume_ratio:.1f}x)")
            elif volume_ratio > 1.0:
                short_score += 5
                short_reasons.append(f"Volume Slightly Above Average ({volume_ratio:.1f}x)")

            price_from_high = ((daily_high - current_price) / (daily_high - daily_low)) * 100 if (daily_high - daily_low) > 0 else 50
            if price_from_high < 20:
                short_score += 15
                short_reasons.append(f"Price Near Daily High ({price_from_high:.1f}% from high)")
            elif price_from_high < 35:
                short_score += 12
                short_reasons.append(f"Price in Upper Range ({price_from_high:.1f}% from high)")
            elif price_from_high < 45:
                short_score += 8
                short_reasons.append(f"Price in Upper Half ({price_from_high:.1f}% from high)")

            long_ok = long_score >= min_confidence
            short_ok = short_score >= min_confidence

            if bias.lower() == "long":
                if long_ok:
                    return build_signal("LONG", long_score, long_reasons, in_gps_long)
                return None
            if bias.lower() == "short":
                if short_ok:
                    return build_signal("SHORT", short_score, short_reasons, in_gps_short)
                return None

            if long_ok and short_ok:
                if long_score >= short_score:
                    return build_signal("LONG", long_score, long_reasons, in_gps_long)
                return build_signal("SHORT", short_score, short_reasons, in_gps_short)
            if long_ok:
                return build_signal("LONG", long_score, long_reasons, in_gps_long)
            if short_ok:
                return build_signal("SHORT", short_score, short_reasons, in_gps_short)

            return None

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def compute_watchlist_candidates(self) -> List[dict]:
        """Build watchlist candidates near GPS/support/resistance zones"""
        candidates = []
        for symbol in self.watchlist:
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, '15m', limit=96)
                if len(ohlcv) < 20:
                    continue
                current = ohlcv[-1]
                current_price = float(current[4])

                daily_ohlcv = self.exchange.fetch_ohlcv(symbol, '1d', limit=1)
                if daily_ohlcv:
                    daily_high = float(daily_ohlcv[-1][2])
                    daily_low = float(daily_ohlcv[-1][3])
                else:
                    daily_high = max([float(c[2]) for c in ohlcv])
                    daily_low = min([float(c[3]) for c in ohlcv])

                in_gps_long, gps_dist_long = calculate_gps_zone(daily_high, daily_low, current_price)
                in_gps_short, gps_dist_short = calculate_upper_gps_zone(daily_high, daily_low, current_price)

                lows = [float(c[3]) for c in ohlcv[-50:]]
                highs = [float(c[2]) for c in ohlcv[-50:]]
                support = min(lows)
                resistance = max(highs)
                support_dist = abs(current_price - support) / current_price * 100
                resistance_dist = abs(resistance - current_price) / current_price * 100

                price_from_low = ((current_price - daily_low) / (daily_high - daily_low)) * 100 if (daily_high - daily_low) > 0 else 50
                price_from_high = ((daily_high - current_price) / (daily_high - daily_low)) * 100 if (daily_high - daily_low) > 0 else 50

                reasons = []
                distance = None

                if in_gps_long or gps_dist_long < 1.0:
                    reasons.append(f"Near GPS (Long) {gps_dist_long:.2f}%")
                    distance = gps_dist_long
                if in_gps_short or gps_dist_short < 1.0:
                    reasons.append(f"Near GPS (Short) {gps_dist_short:.2f}%")
                    distance = min(distance, gps_dist_short) if distance is not None else gps_dist_short
                if support_dist < 0.8:
                    reasons.append(f"Near Support {support_dist:.2f}%")
                    distance = min(distance, support_dist) if distance is not None else support_dist
                if resistance_dist < 0.8:
                    reasons.append(f"Near Resistance {resistance_dist:.2f}%")
                    distance = min(distance, resistance_dist) if distance is not None else resistance_dist
                if price_from_low < 20:
                    reasons.append(f"Lower Range {price_from_low:.1f}%")
                if price_from_high < 20:
                    reasons.append(f"Upper Range {price_from_high:.1f}%")

                if reasons:
                    candidates.append({
                        "symbol": symbol,
                        "price": current_price,
                        "distance": distance if distance is not None else 0,
                        "reasons": reasons[:3]
                    })
            except Exception as e:
                logger.error(f"Watchlist candidate error for {symbol}: {e}")
                continue

        candidates.sort(key=lambda x: x["distance"])
        return candidates[:12]

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
                title = f"{rank_emoji} TRADE #{signal.trade_number} • {signal.symbol} • {signal.direction}"
                value_lines = [
                    f"**Bias**: {signal.direction}",
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
                "title": f"🟩 BOUNTY ALERTS • {len(picks)} TRADE(S)",
                "description": "Top reversal setups (15m scan). Trades are numbered and executed.",
                "color": 0x0ecb81,  # Green
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fields": fields,
                "footer": {
                    "text": f"Bounty Seeker // Reversal Sniper • {time_str}"
                }
            }

            # Watchlist card (Top 3 coins) - Orange
            watchlist = self.watchlist[:3]
            watchlist_lines = []
            for idx, sym in enumerate(watchlist, 1):
                tv_link = self.get_tradingview_link(sym)
                watchlist_lines.append(f"{idx}. **{sym}** — [Chart]({tv_link})")

            watchlist_embed = {
                "title": "🟧 WATCHLIST • TOP 3 COINS",
                "description": "Quick watchlist for the next hour.",
                "color": 0xF39C12,  # Orange
                "fields": [
                    {
                        "name": "Watchlist",
                        "value": "\n".join(watchlist_lines) if watchlist_lines else "No coins available",
                        "inline": False
                    }
                ],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            payload = {"embeds": [embed, watchlist_embed]}
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
            signal = self.analyze_symbol(symbol, bias=SITE_SIGNAL_BIAS)
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

        if top_picks:
            # Assign trade numbers
            for signal in top_picks:
                signal.trade_number = self.get_next_trade_number()

            # Send picks to Discord (long-only per DISCORD_SIGNAL_BIAS)
            discord_picks = [s for s in top_picks if s.direction == DISCORD_SIGNAL_BIAS]
            if discord_picks:
                logger.info(f"🎯 Found {len(signals_found)} signals, sending {len(discord_picks)} {DISCORD_SIGNAL_BIAS} picks...")
                self.send_top_picks_discord(discord_picks)
            else:
                logger.info(f"ℹ️ Signals found but no {DISCORD_SIGNAL_BIAS} picks to send to Discord")

            self.increment_signal_counter(len(top_picks))

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

    def send_status_discord(self, status: str, details: dict = None):
        """Send bot status/heartbeat to Discord"""
        try:
            now = datetime.now(timezone.utc)

            # Color based on status
            colors = {
                "STARTUP": 0x00f3ff,    # Cyan
                "SCANNING": 0xF39C12,   # Orange
                "ACTIVE": 0x0ecb81,     # Green
                "SIGNALS": 0x0ecb81,    # Green
                "NO_SIGNALS": 0x848e9c, # Gray
                "ERROR": 0xff0055,      # Red
                "SHUTDOWN": 0x9c27b0,   # Purple
            }
            color = colors.get(status, 0x848e9c)

            # Build fields
            fields = [
                {"name": "Status", "value": status, "inline": True},
                {"name": "Time (UTC)", "value": now.strftime('%H:%M:%S'), "inline": True},
                {"name": "Watchlist", "value": f"{len(self.watchlist)} coins", "inline": True},
            ]

            if details:
                if "signals_found" in details:
                    fields.append({"name": "Signals Found", "value": str(details["signals_found"]), "inline": True})
                if "open_trades" in details:
                    fields.append({"name": "Open Trades", "value": f"{details['open_trades']}/3", "inline": True})
                if "top_gainers" in details and details["top_gainers"]:
                    gainers = details["top_gainers"][:3]
                    gainer_text = "\n".join([f"{g['symbol']}: +{g['change_pct']:.2f}%" for g in gainers])
                    fields.append({"name": "Top Gainers", "value": gainer_text or "N/A", "inline": True})
                if "top_losers" in details and details["top_losers"]:
                    losers = details["top_losers"][:3]
                    loser_text = "\n".join([f"{l['symbol']}: {l['change_pct']:.2f}%" for l in losers])
                    fields.append({"name": "Top Losers", "value": loser_text or "N/A", "inline": True})
                if "error" in details:
                    fields.append({"name": "Error", "value": str(details["error"])[:200], "inline": False})
                if "message" in details:
                    fields.append({"name": "Info", "value": str(details["message"])[:200], "inline": False})

            embed = {
                "title": f"🤖 BOUNTY SEEKER • {status}",
                "color": color,
                "timestamp": now.isoformat(),
                "fields": fields,
                "footer": {"text": "Bounty Seeker Bot • Live Status"}
            }

            payload = {"embeds": [embed]}
            response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)

            if response.status_code != 204:
                logger.warning(f"Discord status ping returned {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to send status to Discord: {e}")

    def send_startup_notification(self):
        """Send startup notification to Discord"""
        self.send_status_discord("STARTUP", {
            "message": f"Bot initialized. Scanning top {len(self.watchlist)} coins every 30 minutes.",
            "open_trades": self.count_open_trades()
        })
        logger.info("✅ Bot started - Discord startup notification sent")

    def run(self):
        """Main bot loop"""
        logger.info("🚀 Bounty Seeker Bot Started")
        logger.info(f"📊 Monitoring {len(self.watchlist)} symbols (Top 10 by volume)")
        logger.info("⏰ Scanning at XX:00 and XX:30 (every 30 minutes)")
        logger.info("📢 Discord: Sending status updates + signals")

        # Startup notification to Discord
        self.send_startup_notification()
        self.write_status("ACTIVE")

        last_scan_minute = -1
        last_scan_hour = -1
        last_hourly_ping = -1

        while True:
            try:
                now = datetime.now(timezone.utc)

                # Scan ONLY at XX:00 and XX:30 - once per half-hour
                if now.minute in (0, 30) and now.second < 5:
                    # Make sure we don't scan twice in the same minute/hour
                    if now.minute != last_scan_minute or now.hour != last_scan_hour:
                        logger.info(f"⏰ Scan time: {now.strftime('%H:%M:%S UTC')} (30‑min interval)")

                        # Send scanning status to Discord
                        self.send_status_discord("SCANNING", {
                            "message": f"Starting 30-min scan at {now.strftime('%H:%M UTC')}",
                            "open_trades": self.count_open_trades()
                        })

                        self.write_status("SCANNING")
                        self.update_learning()  # Update parameters based on performance
                        signals = self.scan_markets()
                        self.watchlist_candidates = self.compute_watchlist_candidates()
                        last_scan_minute = now.minute
                        last_scan_hour = now.hour
                        self.state["last_scan_time"] = now.isoformat()
                        self.save_state()

                        # Send scan results to Discord
                        if signals:
                            logger.info(f"✅ Scan complete: Found {len(signals)} signals, sent to Discord")
                            self.send_status_discord("SIGNALS", {
                                "signals_found": len(signals),
                                "open_trades": self.count_open_trades(),
                                "top_gainers": self.top_gainers[:3] if self.top_gainers else [],
                                "top_losers": self.top_losers[:3] if self.top_losers else [],
                                "message": f"Found {len(signals)} trade setups"
                            })
                        else:
                            logger.info(f"⏳ Scan complete: No signals found")
                            self.send_status_discord("NO_SIGNALS", {
                                "signals_found": 0,
                                "open_trades": self.count_open_trades(),
                                "top_gainers": self.top_gainers[:3] if self.top_gainers else [],
                                "top_losers": self.top_losers[:3] if self.top_losers else [],
                                "message": "No setups met criteria this scan"
                            })

                        self.write_status("ACTIVE", signals=signals)

                # Update learning every hour
                if now.minute == 0 and now.second < 5:
                    self.update_learning()

                # Hourly heartbeat ping to Discord (on the hour, different from scans)
                if now.hour != last_hourly_ping and now.minute == 0 and now.second >= 10 and now.second < 15:
                    last_hourly_ping = now.hour
                    self.send_status_discord("ACTIVE", {
                        "message": f"Hourly heartbeat - bot running normally",
                        "open_trades": self.count_open_trades(),
                        "top_gainers": self.top_gainers[:3] if self.top_gainers else [],
                        "top_losers": self.top_losers[:3] if self.top_losers else []
                    })

                # Heartbeat status update every minute (for website JSON)
                if self.last_status_minute != now.minute:
                    self.last_status_minute = now.minute
                    self.write_status("ACTIVE")

                time.sleep(1)  # Check every second

            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                self.send_status_discord("SHUTDOWN", {"message": "Bot stopped by user"})
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                self.send_status_discord("ERROR", {"error": str(e)})
                time.sleep(5)

        self.learning.close()
        logger.info("👋 Bounty Seeker Bot Stopped")

# ====================== MAIN ======================
if __name__ == "__main__":
    init_databases()
    bot = BountySeekerBot()
    bot.run()
