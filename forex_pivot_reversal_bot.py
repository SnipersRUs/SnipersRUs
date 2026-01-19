#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Forex Pivot Reversal Bot
Focuses on pivots and reversals using:
1. PivotX Pro - Pivot detection
2. Golden Pocket Syndicate (GPS) - Golden pocket zones
3. Tactical Deviation - VWAP deviation bands

Paper Trading:
- Starting balance: $1,000
- Leverage: 150x
- Trade size: $50 per trade
- Max 3 open positions
- 25% take first TP
"""

import os
import json
import time
import traceback
import requests
import ccxt
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import sqlite3

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ForexPivotBot")

# ====================== CONFIGURATION ======================
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1451483953897668610/uhi0EVl81jV4B17m6tbiwZ3fOV88F7goMERBn4Vyim4_owOpDNZK1regFliw4bcl8mBF"

PAPER_TRADING_CONFIG = {
    "starting_balance": 1000.0,  # $1k starting
    "leverage": 150,              # 150x leverage
    "trade_size_usd": 50.0,        # $50 per trade
    "max_open_positions": 3,      # Max 3 trades
    "tp1_percent": 25,            # 25% take first TP
    "db_path": "forex_paper_trades.db"
}

SCAN_INTERVAL = 2700  # Scan every 45 minutes (45 * 60 = 2700 seconds)

# Forex pairs to trade (only these 3 pairs)
FOREX_PAIRS = [
    "USD/JPY",
    "EUR/USD",
    "GBP/USD"
]

# ====================== INDICATOR CALCULATIONS ======================

class IndicatorCalculator:
    """Calculate PivotX, GPS, and Tactical Deviation indicators"""

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
        """Calculate ATR"""
        if len(df) < period + 1:
            return 0.001

        high = df['high'].values
        low = df['low'].values
        close = df['close'].values

        tr_list = []
        for i in range(1, len(df)):
            tr = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
            tr_list.append(tr)

        return np.mean(tr_list[-period:]) if tr_list else 0.001

    @staticmethod
    def detect_pivotx_pivots(df: pd.DataFrame, timeframe: str) -> Dict:
        """
        PivotX Pro pivot detection
        Returns: pivot_high, pivot_low, pivot_strength, exhaustion signals
        """
        if len(df) < 30:
            return {
                'pivot_high': None,
                'pivot_low': None,
                'pivot_strength': 0,
                'has_pivot': False,
                'exhaustion': None,
                'volume_spike': False
            }

        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        volume = df['volume'].values if 'volume' in df.columns else np.ones(len(df))

        # Calculate ATR
        atr = IndicatorCalculator.calculate_atr(df, 14)

        # Volume spike detection
        avg_vol = np.mean(volume[-20:]) if len(volume) >= 20 else np.mean(volume)
        vol_spike = volume[-1] > avg_vol * 1.5 if len(volume) > 0 else False

        # Determine pivot strength based on timeframe
        # 15+ on pivots are stronger, higher timeframe = stronger
        is_lower_tf = timeframe in ["5m", "3m"]
        is_higher_tf = timeframe in ["15m", "1h", "4h", "1d"]

        # Dynamic pivot strength
        atr_multiplier = 0.5
        pivot_strength_raw = max(2, int(atr / (close[-1] * 0.0001) * atr_multiplier))

        min_strength = 5 if is_lower_tf else 2
        max_strength = 15 if is_lower_tf else (20 if is_higher_tf else 50)
        pivot_strength = max(min_strength, min(pivot_strength_raw, max_strength))

        # Detect pivots
        pivot_high = None
        pivot_low = None

        if len(df) >= pivot_strength * 2 + 1:
            # Look for pivot high
            center_idx = len(df) - pivot_strength - 1
            if center_idx >= pivot_strength and center_idx < len(df) - pivot_strength:
                center_high = high[center_idx]
                is_pivot_high = True
                for i in range(center_idx - pivot_strength, center_idx + pivot_strength + 1):
                    if i != center_idx and high[i] >= center_high:
                        is_pivot_high = False
                        break
                if is_pivot_high:
                    pivot_high = center_high

            # Look for pivot low
            center_low = low[center_idx]
            is_pivot_low = True
            for i in range(center_idx - pivot_strength, center_idx + pivot_strength + 1):
                if i != center_idx and low[i] <= center_low:
                    is_pivot_low = False
                    break
            if is_pivot_low:
                pivot_low = center_low

        # Exhaustion detection
        exhaustion = None
        if len(df) >= 3:
            price_change_pct = ((close[-1] - close[-3]) / close[-3]) * 100
            if price_change_pct <= -2.0 and vol_spike:
                exhaustion = "SELLING_EXHAUSTION"  # Potential reversal up
            elif price_change_pct >= 2.0 and vol_spike:
                exhaustion = "BUYING_EXHAUSTION"  # Potential reversal down

        return {
            'pivot_high': pivot_high,
            'pivot_low': pivot_low,
            'pivot_strength': pivot_strength,
            'has_pivot': pivot_high is not None or pivot_low is not None,
            'exhaustion': exhaustion,
            'volume_spike': vol_spike,
            'atr': atr
        }

    @staticmethod
    def calculate_gps_zones(df: pd.DataFrame, timeframe: str) -> Dict:
        """
        Golden Pocket Syndicate - Calculate golden pocket zones
        Returns: Daily, Weekly, Monthly GP zones and proximity
        """
        if len(df) < 20:
            return {
                'daily_gp': None,
                'weekly_gp': None,
                'monthly_gp': None,
                'distance_to_gp': None,
                'near_gp': False
            }

        # For simplicity, we'll use the current timeframe's high/low
        # In production, you'd fetch daily/weekly/monthly data
        high = df['high'].max()
        low = df['low'].min()
        current_price = df['close'].iloc[-1]

        # Calculate GP zones (0.618 and 0.65)
        range_val = high - low
        gp_high = high - (range_val * 0.618)
        gp_low = high - (range_val * 0.65)
        gp_mid = (gp_high + gp_low) / 2

        # Calculate distance to GP
        if gp_low <= current_price <= gp_high:
            distance_to_gp = 0.0  # Inside GP
        elif current_price < gp_low:
            distance_to_gp = ((gp_low - current_price) / current_price) * 100
        else:
            distance_to_gp = ((current_price - gp_high) / current_price) * 100

        near_gp = abs(distance_to_gp) < 0.5 if distance_to_gp is not None else False

        return {
            'daily_gp_high': gp_high,
            'daily_gp_low': gp_low,
            'daily_gp_mid': gp_mid,
            'distance_to_gp': distance_to_gp,
            'near_gp': near_gp,
            'current_price': current_price
        }

    @staticmethod
    def calculate_tactical_deviation(df: pd.DataFrame) -> Optional[Dict]:
        """
        Tactical Deviation - VWAP with ±1σ, ±2σ, ±3σ bands
        Returns: deviation level and percentage
        """
        if df is None or len(df) < 20:
            return None

        # Calculate VWAP
        typical_price = (df['high'] + df['low'] + df['close']) / 3.0
        volume = df['volume'].values if 'volume' in df.columns else np.ones(len(df))

        sum_pv = (typical_price * volume).sum()
        sum_v = volume.sum()
        sum_pv2 = ((typical_price ** 2) * volume).sum()

        if sum_v == 0:
            return None

        vwap = sum_pv / sum_v
        variance = (sum_pv2 / sum_v) - (vwap ** 2)
        std_dev = np.sqrt(max(variance, 0))

        if std_dev == 0:
            return None

        current_price = df['close'].iloc[-1]

        # Deviation bands
        upper_1 = vwap + (std_dev * 1.0)
        lower_1 = vwap - (std_dev * 1.0)
        upper_2 = vwap + (std_dev * 2.0)
        lower_2 = vwap - (std_dev * 2.0)
        upper_3 = vwap + (std_dev * 3.0)
        lower_3 = vwap - (std_dev * 3.0)

        # Get deviation level
        dev_percent = ((current_price - vwap) / std_dev) if std_dev > 0 else 0

        level = 0
        if current_price >= upper_3 or current_price <= lower_3:
            level = 3  # ±3σ = A+ setup
        elif current_price >= upper_2 or current_price <= lower_2:
            level = 2  # ±2σ = A- setup
        elif current_price >= upper_1 or current_price <= lower_1:
            level = 1

        return {
            "vwap": vwap,
            "std_dev": std_dev,
            "deviation_level": level,
            "deviation_percent": dev_percent,
            "current_price": current_price,
            "upper_2": upper_2,
            "lower_2": lower_2,
            "upper_3": upper_3,
            "lower_3": lower_3
        }

# ====================== PAPER TRADING ACCOUNT ======================

class PaperTradingAccount:
    """Paper trading account with $1k, 150x leverage, $50 trades"""

    def __init__(self):
        self.db_path = PAPER_TRADING_CONFIG["db_path"]
        self.init_database()
        self.load_state()

    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Trades table
        c.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                quantity REAL NOT NULL,
                leverage INTEGER NOT NULL,
                margin REAL NOT NULL,
                tp1 REAL,
                tp2 REAL,
                tp3 REAL,
                stop_loss REAL,
                tp1_hit BOOLEAN DEFAULT 0,
                opened_at TEXT NOT NULL,
                closed_at TEXT,
                exit_price REAL,
                pnl REAL,
                exit_reason TEXT
            )
        ''')

        # Account state table
        c.execute('''
            CREATE TABLE IF NOT EXISTS account_state (
                id INTEGER PRIMARY KEY,
                balance REAL NOT NULL,
                last_updated TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()

    def load_state(self):
        """Load account state from database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('SELECT balance FROM account_state WHERE id = 1')
        row = c.fetchone()

        if row:
            self.balance = row[0]
        else:
            self.balance = PAPER_TRADING_CONFIG["starting_balance"]
            c.execute('INSERT INTO account_state (id, balance, last_updated) VALUES (1, ?, ?)',
                     (self.balance, datetime.now(timezone.utc).isoformat()))
            conn.commit()

        conn.close()

    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT * FROM trades WHERE closed_at IS NULL
        ''')
        rows = c.fetchall()
        conn.close()

        columns = ['id', 'symbol', 'direction', 'entry_price', 'quantity', 'leverage',
                  'margin', 'tp1', 'tp2', 'tp3', 'stop_loss', 'tp1_hit', 'opened_at',
                  'closed_at', 'exit_price', 'pnl', 'exit_reason']

        return [dict(zip(columns, row)) for row in rows]

    def can_open_position(self) -> bool:
        """Check if we can open a new position"""
        open_positions = self.get_open_positions()
        return len(open_positions) < PAPER_TRADING_CONFIG["max_open_positions"]

    def open_position(self, symbol: str, direction: str, entry_price: float,
                     tp1: float, tp2: float, tp3: float, stop_loss: float) -> Optional[int]:
        """Open a new position"""
        if not self.can_open_position():
            return None

        leverage = PAPER_TRADING_CONFIG["leverage"]
        trade_size_usd = PAPER_TRADING_CONFIG["trade_size_usd"]
        margin = trade_size_usd
        notional = margin * leverage
        quantity = notional / entry_price

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO trades (symbol, direction, entry_price, quantity, leverage,
                              margin, tp1, tp2, tp3, stop_loss, opened_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, direction, entry_price, quantity, leverage, margin,
              tp1, tp2, tp3, stop_loss, datetime.now(timezone.utc).isoformat()))

        trade_id = c.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"✅ Opened {direction} position: {symbol} @ ${entry_price:.5f}")
        return trade_id

    def update_positions(self, current_prices: Dict[str, float]):
        """Update positions and check for TP/SL hits"""
        open_positions = self.get_open_positions()

        for position in open_positions:
            symbol = position['symbol']
            current_price = current_prices.get(symbol)

            if current_price is None:
                continue

            direction = position['direction']
            entry_price = position['entry_price']
            tp1 = position['tp1']
            tp2 = position['tp2']
            tp3 = position['tp3']
            stop_loss = position['stop_loss']
            tp1_hit = position['tp1_hit']

            # Check TP/SL
            if direction == "LONG":
                # Check stop loss
                if current_price <= stop_loss:
                    self.close_position(position['id'], current_price, "STOP_LOSS")
                    continue

                # Check TP1 (25% take profit)
                if not tp1_hit and current_price >= tp1:
                    # Close 25% of position
                    self.partial_close(position['id'], current_price, tp1, 0.25)
                    continue

                # Check TP2
                if tp1_hit and current_price >= tp2:
                    self.close_position(position['id'], current_price, "TAKE_PROFIT_2")
                    continue

                # Check TP3
                if tp1_hit and current_price >= tp3:
                    self.close_position(position['id'], current_price, "TAKE_PROFIT_3")
                    continue

            else:  # SHORT
                # Check stop loss
                if current_price >= stop_loss:
                    self.close_position(position['id'], current_price, "STOP_LOSS")
                    continue

                # Check TP1 (25% take profit)
                if not tp1_hit and current_price <= tp1:
                    self.partial_close(position['id'], current_price, tp1, 0.25)
                    continue

                # Check TP2
                if tp1_hit and current_price <= tp2:
                    self.close_position(position['id'], current_price, "TAKE_PROFIT_2")
                    continue

                # Check TP3
                if tp1_hit and current_price <= tp3:
                    self.close_position(position['id'], current_price, "TAKE_PROFIT_3")
                    continue

    def partial_close(self, trade_id: int, exit_price: float, tp_level: float, percent: float):
        """Close a percentage of the position"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
        position = c.fetchone()

        if not position:
            conn.close()
            return

        direction = position[2]
        entry_price = position[3]
        quantity = position[4]
        margin = position[6]

        # Calculate PnL for partial close
        side = 1 if direction == "LONG" else -1
        pnl = (exit_price - entry_price) * side * quantity * percent

        # Update balance
        c.execute('SELECT balance FROM account_state WHERE id = 1')
        balance = c.fetchone()[0]
        new_balance = balance + pnl

        c.execute('UPDATE account_state SET balance = ?, last_updated = ? WHERE id = 1',
                 (new_balance, datetime.now(timezone.utc).isoformat()))

        # Mark TP1 as hit
        c.execute('UPDATE trades SET tp1_hit = 1 WHERE id = ?', (trade_id,))

        conn.commit()
        conn.close()

        self.balance = new_balance
        logger.info(f"💰 Partial TP1 hit: {position[1]} - Closed 25% @ ${exit_price:.5f}, PnL: ${pnl:.2f}")

    def close_position(self, trade_id: int, exit_price: float, reason: str):
        """Close a position completely"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
        position = c.fetchone()

        if not position:
            conn.close()
            return

        direction = position[2]
        entry_price = position[3]
        quantity = position[4]

        # Calculate PnL
        side = 1 if direction == "LONG" else -1
        pnl = (exit_price - entry_price) * side * quantity

        # Update balance
        c.execute('SELECT balance FROM account_state WHERE id = 1')
        balance = c.fetchone()[0]
        new_balance = balance + pnl

        c.execute('UPDATE account_state SET balance = ?, last_updated = ? WHERE id = 1',
                 (new_balance, datetime.now(timezone.utc).isoformat()))

        # Close trade
        c.execute('''
            UPDATE trades SET closed_at = ?, exit_price = ?, pnl = ?, exit_reason = ?
            WHERE id = ?
        ''', (datetime.now(timezone.utc).isoformat(), exit_price, pnl, reason, trade_id))

        conn.commit()
        conn.close()

        self.balance = new_balance
        logger.info(f"🔒 Closed {direction} position: {position[1]} @ ${exit_price:.5f}, PnL: ${pnl:.2f}, Reason: {reason}")

# ====================== DISCORD ALERTS ======================

def send_discord_alert(embed: Dict):
    """Send Discord alert"""
    if not DISCORD_WEBHOOK:
        return

    try:
        payload = {"embeds": [embed]}
        response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
        response.raise_for_status()
        logger.info("✅ Discord alert sent")
    except Exception as e:
        logger.error(f"❌ Discord alert failed: {e}")

def create_gp_proximity_card(symbol: str, gps_data: Dict, current_price: float) -> Dict:
    """Create golden pocket proximity alert card"""
    distance = gps_data.get('distance_to_gp', 0)
    near_gp = gps_data.get('near_gp', False)

    if near_gp:
        title = f"🎯 APPROACHING GOLDEN POCKET - {symbol}"
        color = 0xFFD700  # Gold
        description = f"**Price is near Golden Pocket zone!**\n\n"
    else:
        title = f"📍 GOLDEN POCKET PROXIMITY - {symbol}"
        color = 0xFFA500  # Orange
        description = f"**Distance to Golden Pocket:** {abs(distance):.3f}%\n\n"

    description += (
        f"**Current Price:** ${current_price:.5f}\n"
        f"**GP Zone:** ${gps_data.get('daily_gp_low', 0):.5f} - ${gps_data.get('daily_gp_high', 0):.5f}\n"
        f"**GP Mid:** ${gps_data.get('daily_gp_mid', 0):.5f}\n\n"
        f"*Watch for reversal signals at this level*"
    )

    return {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def create_deviation_card(symbol: str, deviation_data: Dict, timeframe: str, grade: str) -> Dict:
    """Create A- deviation setup card"""
    level = deviation_data.get('deviation_level', 0)
    dev_pct = deviation_data.get('deviation_percent', 0)
    current_price = deviation_data.get('current_price', 0)
    vwap = deviation_data.get('vwap', 0)

    # A- setup (2σ deviation)
    if level == 2:
        title = f"📊 A- DEVIATION SETUP - {symbol}"
        # Green for longs (bull), purple for bearish (short)
        if dev_pct < 0:
            color = 0x00FF00  # Green (bull)
            direction = "LONG"
            emoji = "🟢"
        else:
            color = 0x9B59B6  # Purple (bear)
            direction = "SHORT"
            emoji = "🔴"

        description = (
            f"{emoji} **{direction} Setup** - A- Grade\n\n"
            f"**Timeframe:** {timeframe}\n"
            f"**Current Price:** ${current_price:.5f}\n"
            f"**VWAP:** ${vwap:.5f}\n"
            f"**Deviation:** {abs(dev_pct):.2f}σ ({level}σ level)\n\n"
            f"*Price is at ±2σ deviation - Good reversal setup*"
        )

    else:
        return None

    return {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def create_aplus_card(symbol: str, signal_data: Dict, timeframe: str) -> Dict:
    """Create A+ setup card"""
    direction = signal_data.get('direction', 'LONG')
    entry = signal_data.get('entry', 0)
    tp1 = signal_data.get('tp1', 0)
    tp2 = signal_data.get('tp2', 0)
    tp3 = signal_data.get('tp3', 0)
    stop_loss = signal_data.get('stop_loss', 0)

    # Green for longs (bull), purple for bearish (short)
    if direction == "LONG":
        color = 0x00FF00  # Green (bull)
        emoji = "🟢"
    else:  # SHORT
        color = 0x9B59B6  # Purple (bear)
        emoji = "🔴"

    description = (
        f"{emoji} **{direction} SETUP** - A+ Grade\n\n"
        f"**Timeframe:** {timeframe}\n"
        f"**Entry:** ${entry:.5f}\n"
        f"**Stop Loss:** ${stop_loss:.5f}\n"
        f"**Take Profit 1:** ${tp1:.5f} (25%)\n"
        f"**Take Profit 2:** ${tp2:.5f}\n"
        f"**Take Profit 3:** ${tp3:.5f}\n\n"
        f"**Confluence Factors:**\n"
    )

    # Add confluence reasons
    reasons = signal_data.get('reasons', [])
    for reason in reasons[:5]:  # Limit to 5 reasons
        description += f"• {reason}\n"

    return {
        "title": f"⭐ A+ SETUP - {symbol}",
        "description": description,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": f"Forex Pivot Reversal Bot • {timeframe}"
        }
    }

# ====================== MAIN BOT ======================

class ForexPivotReversalBot:
    """Main forex trading bot"""

    def __init__(self):
        self.exchange = None
        self.paper_account = PaperTradingAccount()
        self.init_exchange()
        self.last_scan_time = {}
        self.last_gp_alert = {}  # Track last GP proximity alert per symbol

    def init_exchange(self):
        """Initialize exchange for data fetching"""
        try:
            # Use a free exchange API for forex data (e.g., Alpha Vantage, Yahoo Finance via yfinance)
            # For now, we'll use a simple approach with ccxt
            self.exchange = ccxt.oanda({
                'enableRateLimit': True,
                'apiKey': os.getenv('OANDA_API_KEY', ''),
                'secret': os.getenv('OANDA_SECRET', ''),
            })
            logger.info("✅ Exchange initialized")
        except Exception as e:
            logger.warning(f"Exchange init warning: {e}")
            # Fallback: we'll use mock data or another data source
            self.exchange = None

    def fetch_ohlcv(self, symbol: str, timeframe: str = "15m", limit: int = 200) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data"""
        try:
            # Map forex symbols for exchange
            mapped_symbol = symbol.replace("/", "")

            if self.exchange:
                ohlcv = self.exchange.fetch_ohlcv(mapped_symbol, timeframe, limit=limit)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                return df
            else:
                # Mock data for testing
                logger.warning(f"Using mock data for {symbol}")
                return self._generate_mock_data(symbol, limit)
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None

    def _generate_mock_data(self, symbol: str, limit: int) -> pd.DataFrame:
        """Generate mock OHLCV data for testing"""
        dates = pd.date_range(end=datetime.now(timezone.utc), periods=limit, freq='15min')
        np.random.seed(hash(symbol) % 1000)
        base_price = 1.1000 if "EUR" in symbol else 1.2500

        prices = []
        current = base_price
        for _ in range(limit):
            change = np.random.uniform(-0.001, 0.001)
            current += change
            high = current + abs(np.random.uniform(0, 0.0005))
            low = current - abs(np.random.uniform(0, 0.0005))
            prices.append({
                'timestamp': dates[len(prices)],
                'open': current,
                'high': high,
                'low': low,
                'close': current + np.random.uniform(-0.0002, 0.0002),
                'volume': np.random.uniform(1000, 10000)
            })
            current = prices[-1]['close']

        df = pd.DataFrame(prices)
        return df

    def scan_symbol(self, symbol: str) -> Optional[Dict]:
        """Scan a symbol for trading signals"""
        try:
            # Fetch data for multiple timeframes
            df_5m = self.fetch_ohlcv(symbol, "5m", 200)
            df_15m = self.fetch_ohlcv(symbol, "15m", 200)

            if df_5m is None or df_15m is None or len(df_5m) < 30 or len(df_15m) < 30:
                return None

            current_price = df_15m['close'].iloc[-1]

            # 1. Calculate PivotX Pro pivots
            pivotx_5m = IndicatorCalculator.detect_pivotx_pivots(df_5m, "5m")
            pivotx_15m = IndicatorCalculator.detect_pivotx_pivots(df_15m, "15m")

            # 2. Calculate GPS zones
            gps_data = IndicatorCalculator.calculate_gps_zones(df_15m, "15m")

            # 3. Calculate Tactical Deviation
            deviation_data = IndicatorCalculator.calculate_tactical_deviation(df_15m)

            # Determine signal grade
            # A+ setups: 15m+ timeframes with strong confluence
            # A- setups: 5m timeframes or 2σ deviations
            grade = None
            direction = None
            reasons = []
            confluence_score = 0

            # Check for A+ setup (15m+ with strong confluence)
            if pivotx_15m['has_pivot'] and deviation_data and deviation_data['deviation_level'] >= 2:
                if gps_data['near_gp']:
                    grade = "A+"
                    confluence_score += 30
                    reasons.append("✅ Near Golden Pocket")

                if deviation_data['deviation_level'] >= 3:
                    grade = "A+"
                    confluence_score += 30
                    reasons.append(f"✅ ±3σ deviation ({deviation_data['deviation_percent']:.2f}σ)")
                elif deviation_data['deviation_level'] >= 2:
                    grade = "A-"
                    confluence_score += 20
                    reasons.append(f"✅ ±2σ deviation ({deviation_data['deviation_percent']:.2f}σ)")

                if pivotx_15m['exhaustion']:
                    confluence_score += 15
                    reasons.append(f"✅ {pivotx_15m['exhaustion']}")

                # Determine direction
                if pivotx_15m['pivot_low'] and deviation_data['deviation_percent'] < 0:
                    direction = "LONG"
                elif pivotx_15m['pivot_high'] and deviation_data['deviation_percent'] > 0:
                    direction = "SHORT"

            # Check for A- setup (5m timeframe)
            elif pivotx_5m['has_pivot'] and deviation_data and deviation_data['deviation_level'] >= 2:
                grade = "A-"
                confluence_score += 15
                reasons.append("✅ 5m pivot detected")
                reasons.append(f"✅ ±2σ deviation ({deviation_data['deviation_percent']:.2f}σ)")

                if pivotx_5m['pivot_low'] and deviation_data['deviation_percent'] < 0:
                    direction = "LONG"
                elif pivotx_5m['pivot_high'] and deviation_data['deviation_percent'] > 0:
                    direction = "SHORT"

            if grade and direction:
                # Calculate entry, TP, SL
                atr = pivotx_15m.get('atr', 0.001) if pivotx_15m.get('atr') else pivotx_5m.get('atr', 0.001)

                if direction == "LONG":
                    entry = current_price
                    stop_loss = entry - (atr * 1.5)
                    tp1 = entry + (atr * 2.5)
                    tp2 = entry + (atr * 4.0)
                    tp3 = entry + (atr * 6.0)
                else:  # SHORT
                    entry = current_price
                    stop_loss = entry + (atr * 1.5)
                    tp1 = entry - (atr * 2.5)
                    tp2 = entry - (atr * 4.0)
                    tp3 = entry - (atr * 6.0)

                return {
                    'symbol': symbol,
                    'direction': direction,
                    'grade': grade,
                    'entry': entry,
                    'stop_loss': stop_loss,
                    'tp1': tp1,
                    'tp2': tp2,
                    'tp3': tp3,
                    'timeframe': "15m" if grade == "A+" else "5m",
                    'reasons': reasons,
                    'confluence_score': confluence_score,
                    'gps_data': gps_data,
                    'deviation_data': deviation_data,
                    'pivotx_data': pivotx_15m if grade == "A+" else pivotx_5m
                }

            return None

        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            traceback.print_exc()
            return None

    def check_gp_proximity(self, symbol: str, gps_data: Dict):
        """Check and alert on golden pocket proximity"""
        if not gps_data.get('near_gp') and gps_data.get('distance_to_gp') is None:
            return

        # Alert if approaching GP (within 1%)
        distance = abs(gps_data.get('distance_to_gp', 999))
        if distance < 1.0:
            # Rate limit: alert once per hour per symbol
            last_alert = self.last_gp_alert.get(symbol, 0)
            if time.time() - last_alert > 3600:
                card = create_gp_proximity_card(symbol, gps_data, gps_data.get('current_price', 0))
                send_discord_alert(card)
                self.last_gp_alert[symbol] = time.time()

    def run_scan(self):
        """Run one scan cycle"""
        logger.info("🔍 Starting scan cycle...")

        # Update existing positions
        current_prices = {}
        for symbol in FOREX_PAIRS:
            df = self.fetch_ohlcv(symbol, "15m", 10)
            if df is not None and len(df) > 0:
                current_prices[symbol] = df['close'].iloc[-1]

        self.paper_account.update_positions(current_prices)

        # Scan for new signals
        signals = []
        for symbol in FOREX_PAIRS:
            signal = self.scan_symbol(symbol)
            if signal:
                signals.append(signal)

                # Check GP proximity
                if signal.get('gps_data'):
                    self.check_gp_proximity(symbol, signal['gps_data'])

                # Send alerts based on grade
                grade = signal.get('grade')
                if grade == "A+":
                    card = create_aplus_card(symbol, signal, signal.get('timeframe', '15m'))
                    send_discord_alert(card)
                elif grade == "A-":
                    if signal.get('deviation_data'):
                        card = create_deviation_card(symbol, signal['deviation_data'],
                                                    signal.get('timeframe', '5m'), grade)
                        if card:
                            send_discord_alert(card)

        # Execute trades for A+ signals only
        if signals:
            aplus_signals = [s for s in signals if s.get('grade') == 'A+']
            for signal in aplus_signals[:PAPER_TRADING_CONFIG["max_open_positions"]]:
                if self.paper_account.can_open_position():
                    trade_id = self.paper_account.open_position(
                        signal['symbol'],
                        signal['direction'],
                        signal['entry'],
                        signal['tp1'],
                        signal['tp2'],
                        signal['tp3'],
                        signal['stop_loss']
                    )
                    if trade_id:
                        logger.info(f"✅ Opened trade: {signal['symbol']} {signal['direction']}")

        logger.info(f"✅ Scan complete. Found {len(signals)} signals, {len(aplus_signals) if signals else 0} A+")

    def run(self):
        """Main bot loop"""
        logger.info("🚀 Forex Pivot Reversal Bot started")
        logger.info(f"💰 Starting balance: ${PAPER_TRADING_CONFIG['starting_balance']:.2f}")
        logger.info(f"⚙️  Leverage: {PAPER_TRADING_CONFIG['leverage']}x")
        logger.info(f"📊 Trade size: ${PAPER_TRADING_CONFIG['trade_size_usd']:.2f}")
        logger.info(f"🔢 Max positions: {PAPER_TRADING_CONFIG['max_open_positions']}")

        while True:
            try:
                self.run_scan()
                time.sleep(SCAN_INTERVAL)
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                traceback.print_exc()
                time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    bot = ForexPivotReversalBot()
    bot.run()


