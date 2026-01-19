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
# Enable debug logging for signal detection
logger.setLevel(logging.DEBUG)

# ====================== CONFIGURATION ======================
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1451483953897668610/uhi0EVl81jV4B17m6tbiwZ3fOV88F7goMERBn4Vyim4_owOpDNZK1regFliw4bcl8mBF"

PAPER_TRADING_CONFIG = {
    "starting_balance": 1000.0,  # $1k starting
    "leverage": 100,              # 100x leverage (forex-optimized)
    "risk_per_trade": 0.02,        # 2% risk per trade
    "max_open_positions": 3,      # Max 3 trades
    "tp1_percent": 25,            # 25% take first TP
    "db_path": "forex_paper_trades.db",
    "max_spread_pips": 2.0,       # Skip trades if spread > 2 pips
    "pip_value_usd": 10.0         # $10 per pip for standard lots
}

SCAN_INTERVAL = 2700  # Scan every 45 minutes (45 * 60 = 2700 seconds)

# Forex session times (UTC)
FOREX_SESSIONS = {
    "tokyo": {"start": 0, "end": 9},      # 00:00 - 09:00 UTC
    "london": {"start": 8, "end": 17},    # 08:00 - 17:00 UTC
    "new_york": {"start": 13, "end": 22},  # 13:00 - 22:00 UTC
    "overlap_london_ny": {"start": 13, "end": 17}  # 13:00 - 17:00 UTC (best liquidity)
}

# ATR multipliers for forex (lower volatility)
FOREX_ATR_MULTIPLIERS = {
    "stop_loss": 1.0,    # 1.0x ATR for stops (forex-optimized)
    "tp1": 1.5,          # 1.5x ATR for TP1
    "tp2": 2.5,          # 2.5x ATR for TP2
    "tp3": 4.0           # 4.0x ATR for TP3
}

# Forex pairs to trade (only these 3 pairs)
FOREX_PAIRS = [
    "USD/JPY",
    "EUR/USD",
    "GBP/USD"
]

# ====================== FOREX UTILITIES ======================

class ForexUtils:
    """Forex-specific utility functions"""

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """Normalize forex symbols (e.g., 'EUR/USD')"""
        if '/' in symbol:
            return symbol  # Already normalized
        elif symbol.endswith('USD'):
            return f"{symbol[:-3]}/USD"
        elif len(symbol) == 6:  # EURUSD format
            return f"{symbol[:3]}/{symbol[3:]}"
        return symbol

    @staticmethod
    def price_to_pips(price_diff: float, symbol: str) -> float:
        """Convert price difference to pips"""
        # For XXX/USD pairs, 1 pip = 0.0001
        # For XXX/JPY pairs, 1 pip = 0.01
        if "JPY" in symbol:
            return abs(price_diff) * 100  # JPY pairs
        else:
            return abs(price_diff) * 10000  # Standard pairs

    @staticmethod
    def pips_to_price(pips: float, symbol: str) -> float:
        """Convert pips to price difference"""
        if "JPY" in symbol:
            return pips / 100
        else:
            return pips / 10000

    @staticmethod
    def is_psychological_level(price: float, threshold: float = 0.0005) -> bool:
        """Check if price is near a psychological level (round numbers)"""
        # Check if price is near round numbers (e.g., 1.0000, 1.0500, 1.1000)
        rounded = round(price, 2)  # Round to 2 decimals
        diff = abs(price - rounded)
        return diff <= threshold

    @staticmethod
    def get_current_session() -> str:
        """Get current forex session"""
        now = datetime.now(timezone.utc)
        hour = now.hour

        if 13 <= hour < 17:
            return "overlap_london_ny"  # Best liquidity
        elif 8 <= hour < 17:
            return "london"
        elif 13 <= hour < 22:
            return "new_york"
        elif 0 <= hour < 9:
            return "tokyo"
        else:
            return "low_liquidity"  # Outside main sessions

    @staticmethod
    def is_market_open() -> bool:
        """Check if forex market is open (24/5 - closed weekends)"""
        now = datetime.now(timezone.utc)
        weekday = now.weekday()  # 0=Monday, 6=Sunday

        # Forex is closed on weekends (Saturday = 5, Sunday = 6)
        if weekday >= 5:
            return False

        # Check if it's Friday after close (22:00 UTC) or Sunday before open
        if weekday == 4 and now.hour >= 22:  # Friday after 22:00 UTC
            return False
        if weekday == 6:  # Sunday
            return False

        return True

    @staticmethod
    def is_news_event_near() -> bool:
        """Check if high-impact news is within 30 mins (placeholder for news API)"""
        # TODO: Integrate with Forex Factory API or similar
        # For now, return False (no news filter)
        return False

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
    def calculate_gps_zones(df: pd.DataFrame, timeframe: str, symbol: str) -> Dict:
        """
        Golden Pocket Syndicate - Calculate golden pocket zones
        Enhanced for forex: combines GP with psychological levels
        Returns: Daily, Weekly, Monthly GP zones and proximity
        """
        if len(df) < 20:
            return {
                'daily_gp_high': None,
                'daily_gp_low': None,
                'daily_gp_mid': None,
                'distance_to_gp': None,
                'near_gp': False,
                'at_psychological_level': False,
                'psychological_level': None
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

        # Check for psychological levels (round numbers)
        at_psychological = ForexUtils.is_psychological_level(current_price)
        psychological_level = round(current_price, 2) if at_psychological else None

        # Calculate distance to GP in pips
        if gp_low <= current_price <= gp_high:
            distance_to_gp_pips = 0.0  # Inside GP
        elif current_price < gp_low:
            distance_to_gp_pips = ForexUtils.price_to_pips(gp_low - current_price, symbol)
        else:
            distance_to_gp_pips = ForexUtils.price_to_pips(current_price - gp_high, symbol)

        # Near GP if within 10 pips
        near_gp = distance_to_gp_pips <= 10.0

        return {
            'daily_gp_high': gp_high,
            'daily_gp_low': gp_low,
            'daily_gp_mid': gp_mid,
            'distance_to_gp_pips': distance_to_gp_pips,
            'distance_to_gp': (distance_to_gp_pips / 100) if "JPY" not in symbol else (distance_to_gp_pips / 10),  # Percentage
            'near_gp': near_gp,
            'current_price': current_price,
            'at_psychological_level': at_psychological,
            'psychological_level': psychological_level
        }

    @staticmethod
    def calculate_session_vwap(df: pd.DataFrame, session: str = "london") -> Optional[Dict]:
        """
        Calculate session-based VWAP for forex (London/New York/Tokyo sessions)
        Forex respects session boundaries more than daily levels
        """
        if df is None or len(df) < 20:
            return None

        # Filter by session hours (UTC)
        session_hours = FOREX_SESSIONS.get(session, FOREX_SESSIONS["london"])
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour

        # Filter data for session
        if session == "overlap_london_ny":
            df_session = df[(df['hour'] >= 13) & (df['hour'] < 17)]
        else:
            df_session = df[(df['hour'] >= session_hours["start"]) & (df['hour'] < session_hours["end"])]

        if len(df_session) < 10:
            # Fallback to all data if session data insufficient
            df_session = df

        # Calculate VWAP
        typical_price = (df_session['high'] + df_session['low'] + df_session['close']) / 3.0
        volume = df_session['volume'].values if 'volume' in df_session.columns else np.ones(len(df_session))

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
            "lower_3": lower_3,
            "session": session
        }

    @staticmethod
    def calculate_tactical_deviation(df: pd.DataFrame) -> Optional[Dict]:
        """
        Tactical Deviation - Session-based VWAP with ±1σ, ±2σ, ±3σ bands
        Uses current session (London/New York overlap preferred)
        Returns: deviation level and percentage
        """
        # Use session-based VWAP for forex
        current_session = ForexUtils.get_current_session()
        if current_session == "low_liquidity":
            current_session = "london"  # Fallback to London

        return IndicatorCalculator.calculate_session_vwap(df, current_session)

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

    def calculate_position_size_pips(self, entry_price: float, stop_loss: float,
                                     symbol: str, balance: float) -> float:
        """Calculate forex position size in lots based on pip risk"""
        stop_pips = ForexUtils.price_to_pips(abs(entry_price - stop_loss), symbol)
        if stop_pips == 0:
            stop_pips = 20  # Default 20 pips if calculation fails

        risk_amount = balance * PAPER_TRADING_CONFIG["risk_per_trade"]
        pip_value = PAPER_TRADING_CONFIG["pip_value_usd"]

        # Calculate lot size: (Risk Amount / Stop Loss in Pips) / Pip Value
        lot_size = (risk_amount / stop_pips) / pip_value

        # Cap at 20% of balance
        max_lot_size = (balance * 0.20) / (entry_price * pip_value * 100)  # Approximate
        lot_size = min(lot_size, max_lot_size)

        # Convert lots to quantity (1 standard lot = 100,000 units for XXX/USD)
        if "JPY" in symbol:
            quantity = lot_size * 100000  # Standard lot for JPY pairs
        else:
            quantity = lot_size * 100000  # Standard lot for XXX/USD pairs

        return quantity

    def open_position(self, symbol: str, direction: str, entry_price: float,
                     tp1: float, tp2: float, tp3: float, stop_loss: float) -> Optional[int]:
        """Open a new position with pip-based position sizing"""
        if not self.can_open_position():
            return None

        leverage = PAPER_TRADING_CONFIG["leverage"]

        # Calculate position size based on pip risk
        quantity = self.calculate_position_size_pips(entry_price, stop_loss, symbol, self.balance)

        # Calculate margin (notional / leverage)
        notional = quantity * entry_price
        margin = notional / leverage

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

        stop_pips = ForexUtils.price_to_pips(abs(entry_price - stop_loss), symbol)
        logger.info(f"✅ Opened {direction} position: {symbol} @ ${entry_price:.5f} | Stop: {stop_pips:.1f} pips")
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
    """Create golden pocket proximity alert card with pip-based metrics"""
    distance_pips = gps_data.get('distance_to_gp_pips', 0)
    near_gp = gps_data.get('near_gp', False)
    at_psych = gps_data.get('at_psychological_level', False)
    psych_level = gps_data.get('psychological_level')

    if near_gp:
        title = f"🎯 APPROACHING GOLDEN POCKET - {symbol}"
        color = 0xFFD700  # Gold
        description = f"**Price is near Golden Pocket zone!**\n\n"
    else:
        title = f"📍 GOLDEN POCKET PROXIMITY - {symbol}"
        color = 0xFFA500  # Orange
        description = f"**Distance to Golden Pocket:** {distance_pips:.1f} pips\n\n"

    description += (
        f"**Current Price:** {current_price:.5f}\n"
        f"**GP Zone:** {gps_data.get('daily_gp_low', 0):.5f} - {gps_data.get('daily_gp_high', 0):.5f}\n"
        f"**GP Mid:** {gps_data.get('daily_gp_mid', 0):.5f}\n"
    )

    if at_psych:
        description += f"**🎯 At Psychological Level:** {psych_level}\n"

    description += f"\n*Watch for reversal signals at this level*"

    return {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def create_deviation_card(symbol: str, deviation_data: Dict, timeframe: str, grade: str) -> Dict:
    """Create A- deviation setup card with pip-based metrics"""
    level = deviation_data.get('deviation_level', 0)
    dev_pct = deviation_data.get('deviation_percent', 0)
    current_price = deviation_data.get('current_price', 0)
    vwap = deviation_data.get('vwap', 0)
    session = deviation_data.get('session', 'london')

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

        # Calculate distance from VWAP in pips
        vwap_distance_pips = ForexUtils.price_to_pips(abs(current_price - vwap), symbol)

        description = (
            f"{emoji} **{direction} Setup** - A- Grade\n\n"
            f"**Timeframe:** {timeframe}\n"
            f"**Session:** {session.upper()}\n"
            f"**Current Price:** {current_price:.5f}\n"
            f"**Session VWAP:** {vwap:.5f}\n"
            f"**Distance from VWAP:** {vwap_distance_pips:.1f} pips\n"
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
    """Create A+ setup card with pip-based metrics"""
    direction = signal_data.get('direction', 'LONG')
    entry = signal_data.get('entry', 0)
    tp1 = signal_data.get('tp1', 0)
    tp2 = signal_data.get('tp2', 0)
    tp3 = signal_data.get('tp3', 0)
    stop_loss = signal_data.get('stop_loss', 0)
    session = signal_data.get('session', 'london')

    # Green for longs (bull), purple for bearish (short)
    if direction == "LONG":
        color = 0x00FF00  # Green (bull)
        emoji = "🟢"
    else:  # SHORT
        color = 0x9B59B6  # Purple (bear)
        emoji = "🔴"

    # Calculate pip distances
    stop_pips = ForexUtils.price_to_pips(abs(entry - stop_loss), symbol)
    tp1_pips = ForexUtils.price_to_pips(abs(tp1 - entry), symbol)
    tp2_pips = ForexUtils.price_to_pips(abs(tp2 - entry), symbol)
    tp3_pips = ForexUtils.price_to_pips(abs(tp3 - entry), symbol)

    description = (
        f"{emoji} **{direction} SETUP** - A+ Grade\n\n"
        f"**Timeframe:** {timeframe}\n"
        f"**Session:** {session.upper()}\n"
        f"**Entry:** {entry:.5f}\n"
        f"**Stop Loss:** {stop_loss:.5f} ({stop_pips:.1f} pips)\n"
        f"**Take Profit 1:** {tp1:.5f} ({tp1_pips:.1f} pips) - 25%\n"
        f"**Take Profit 2:** {tp2:.5f} ({tp2_pips:.1f} pips)\n"
        f"**Take Profit 3:** {tp3:.5f} ({tp3_pips:.1f} pips)\n\n"
        f"**Risk/Reward:** 1:{tp1_pips/stop_pips:.2f} (TP1)\n\n"
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
            "text": f"Forex Pivot Reversal Bot • {timeframe} • {session.upper()}"
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
        self.last_premarket_day = None  # Track last premarket update day
        self.last_premarket_week = None  # Track last premarket update week

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

    def get_spread(self, symbol: str) -> float:
        """Get current spread in pips (placeholder - would use real broker API)"""
        # TODO: Integrate with broker API to get real spread
        # For now, return a mock spread (typically 1-2 pips for major pairs)
        return 1.5  # Mock spread in pips

    def scan_symbol(self, symbol: str) -> Optional[Dict]:
        """Scan a symbol for trading signals with FX-specific filters"""
        try:
            # 1. Check market hours (24/5 - closed weekends)
            if not ForexUtils.is_market_open():
                logger.debug(f"Market closed for {symbol}")
                return None

            # 2. Check news filter (avoid high-impact events)
            if ForexUtils.is_news_event_near():
                logger.debug(f"High-impact news event near - skipping {symbol}")
                return None

            # 3. Check spread filter
            spread_pips = self.get_spread(symbol)
            if spread_pips > PAPER_TRADING_CONFIG["max_spread_pips"]:
                logger.debug(f"Spread too wide ({spread_pips:.1f} pips) for {symbol}")
                return None

            # Fetch data for multiple timeframes
            df_5m = self.fetch_ohlcv(symbol, "5m", 200)
            df_15m = self.fetch_ohlcv(symbol, "15m", 200)

            if df_5m is None or df_15m is None or len(df_5m) < 30 or len(df_15m) < 30:
                return None

            current_price = df_15m['close'].iloc[-1]

            # 1. Calculate PivotX Pro pivots
            pivotx_5m = IndicatorCalculator.detect_pivotx_pivots(df_5m, "5m")
            pivotx_15m = IndicatorCalculator.detect_pivotx_pivots(df_15m, "15m")

            # 2. Calculate GPS zones (with psychological levels)
            gps_data = IndicatorCalculator.calculate_gps_zones(df_15m, "15m", symbol)

            # 3. Calculate Tactical Deviation (session-based VWAP)
            deviation_data = IndicatorCalculator.calculate_tactical_deviation(df_15m)

            # Debug logging
            logger.debug(f"{symbol}: Pivot 5m={pivotx_5m['has_pivot']}, 15m={pivotx_15m['has_pivot']}, "
                        f"Deviation={deviation_data['deviation_level'] if deviation_data else 'None'}, "
                        f"Near GP={gps_data.get('near_gp', False)}")

            # Determine signal grade
            # A+ setups: 15m+ timeframes with strong confluence
            # A- setups: 5m timeframes or 2σ deviations
            grade = None
            direction = None
            reasons = []
            confluence_score = 0

            # SWING TRADES (A+): 15m+ timeframes - Higher timeframe moves
            # Check for A+ setup (15m+ with strong confluence) - SWING OPPORTUNITIES
            swing_signal = False
            # Relaxed: Allow signals with pivot OR deviation (not requiring both)
            if (pivotx_15m['has_pivot'] or (deviation_data and deviation_data['deviation_level'] >= 2)) and deviation_data:
                # Swing trade: Strong confluence on 15m+
                if deviation_data['deviation_level'] >= 2:
                    swing_signal = True
                    if gps_data['near_gp']:
                        grade = "A+"
                        confluence_score += 30
                        reasons.append("✅ Near Golden Pocket (SWING)")

                    if deviation_data['deviation_level'] >= 3:
                        grade = "A+"
                        confluence_score += 30
                        reasons.append(f"✅ ±3σ deviation ({deviation_data['deviation_percent']:.2f}σ) - SWING")
                    elif deviation_data['deviation_level'] >= 2:
                        if not grade:  # Don't downgrade if already A+
                            grade = "A-"
                        confluence_score += 20
                        reasons.append(f"✅ ±2σ deviation ({deviation_data['deviation_percent']:.2f}σ)")

                    if pivotx_15m['exhaustion']:
                        confluence_score += 15
                        reasons.append(f"✅ {pivotx_15m['exhaustion']} - SWING")

                    # Determine direction for SWING (more flexible)
                    if deviation_data['deviation_percent'] < 0:
                        # Oversold - potential LONG
                        if pivotx_15m['pivot_low'] or not pivotx_15m['has_pivot']:
                            direction = "LONG"
                    elif deviation_data['deviation_percent'] > 0:
                        # Overbought - potential SHORT
                        if pivotx_15m['pivot_high'] or not pivotx_15m['has_pivot']:
                            direction = "SHORT"

            # SCALP TRADES (A-): 5m timeframe - Quick in/out moves
            # Check for A- setup (5m timeframe) - SCALP OPPORTUNITIES
            scalp_signal = False
            # Relaxed: Allow signals with pivot OR deviation (not requiring both)
            if not swing_signal and (pivotx_5m['has_pivot'] or (deviation_data and deviation_data['deviation_level'] >= 1)) and deviation_data:
                # Lower threshold for scalps: 1σ deviation is acceptable
                if deviation_data['deviation_level'] >= 1:
                    scalp_signal = True
                    grade = "A-"
                    confluence_score += 15
                    reasons.append("✅ 5m pivot detected (SCALP)")
                    reasons.append(f"✅ ±2σ deviation ({deviation_data['deviation_percent']:.2f}σ) - SCALP")

                    # Check for additional scalp confirmations
                    if pivotx_5m['exhaustion']:
                        confluence_score += 10
                        reasons.append(f"✅ {pivotx_5m['exhaustion']} - SCALP")

                    if gps_data['near_gp']:
                        confluence_score += 15
                        reasons.append("✅ Near Golden Pocket (SCALP)")

                    # Determine direction for SCALP (more flexible)
                    if deviation_data['deviation_percent'] < 0:
                        # Oversold - potential LONG
                        if pivotx_5m['pivot_low'] or not pivotx_5m['has_pivot']:
                            direction = "LONG"
                    elif deviation_data['deviation_percent'] > 0:
                        # Overbought - potential SHORT
                        if pivotx_5m['pivot_high'] or not pivotx_5m['has_pivot']:
                            direction = "SHORT"

            if grade and direction:
                # Calculate entry, TP, SL using forex-optimized ATR multipliers
                atr = pivotx_15m.get('atr', 0.001) if pivotx_15m.get('atr') else pivotx_5m.get('atr', 0.001)
                current_session = ForexUtils.get_current_session()

                # Use forex-optimized multipliers (lower volatility)
                if direction == "LONG":
                    entry = current_price
                    stop_loss = entry - (atr * FOREX_ATR_MULTIPLIERS["stop_loss"])
                    tp1 = entry + (atr * FOREX_ATR_MULTIPLIERS["tp1"])
                    tp2 = entry + (atr * FOREX_ATR_MULTIPLIERS["tp2"])
                    tp3 = entry + (atr * FOREX_ATR_MULTIPLIERS["tp3"])
                else:  # SHORT
                    entry = current_price
                    stop_loss = entry + (atr * FOREX_ATR_MULTIPLIERS["stop_loss"])
                    tp1 = entry - (atr * FOREX_ATR_MULTIPLIERS["tp1"])
                    tp2 = entry - (atr * FOREX_ATR_MULTIPLIERS["tp2"])
                    tp3 = entry - (atr * FOREX_ATR_MULTIPLIERS["tp3"])

                # Add psychological level info if present
                if gps_data.get('at_psychological_level'):
                    reasons.append(f"✅ At psychological level: {gps_data.get('psychological_level')}")

                # Add session info
                if deviation_data:
                    reasons.append(f"✅ Session VWAP: {deviation_data.get('session', 'london').upper()}")

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
                    'pivotx_data': pivotx_15m if grade == "A+" else pivotx_5m,
                    'session': current_session,
                    'spread_pips': spread_pips
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

    def send_premarket_update(self, update_type: str = "daily"):
        """Send premarket update to Discord at start of new day/week"""
        now = datetime.now(timezone.utc)
        current_day = now.date()
        current_week = now.isocalendar()[1]  # Week number

        # Check if we've already sent today's/week's update
        if update_type == "daily" and self.last_premarket_day == current_day:
            return
        if update_type == "weekly" and self.last_premarket_week == current_week:
            return

        # Get account stats
        open_positions = self.paper_account.get_open_positions()
        balance = self.paper_account.balance

        # Get current session
        current_session = ForexUtils.get_current_session()
        session_emoji = "🔥" if current_session == "overlap_london_ny" else "📊"

        if update_type == "weekly":
            title = "📅 WEEKLY PREMARKET UPDATE"
            description = (
                f"**New Trading Week Starting!**\n\n"
                f"**Current Session:** {session_emoji} {current_session.upper()}\n"
                f"**Account Balance:** ${balance:.2f}\n"
                f"**Open Positions:** {len(open_positions)}/{PAPER_TRADING_CONFIG['max_open_positions']}\n\n"
                f"**Trading Pairs:**\n"
                f"• USD/JPY\n"
                f"• EUR/USD\n"
                f"• GBP/USD\n\n"
                f"**Bot Status:** ✅ Active\n"
                f"**Scan Interval:** Every 45 minutes\n"
                f"**Market Hours:** 24/5 (Closed weekends)\n\n"
                f"*Ready to hunt for A+ setups!*"
            )
        else:  # daily
            title = "🌅 DAILY PREMARKET UPDATE"
            description = (
                f"**New Trading Day Starting!**\n\n"
                f"**Current Session:** {session_emoji} {current_session.upper()}\n"
                f"**Account Balance:** ${balance:.2f}\n"
                f"**Open Positions:** {len(open_positions)}/{PAPER_TRADING_CONFIG['max_open_positions']}\n\n"
                f"**Today's Focus:**\n"
                f"• Session-based VWAP deviations\n"
                f"• Golden Pocket + Psychological levels\n"
                f"• Pivot reversals on 15m+\n\n"
                f"*Looking for A+ setups with 3+ confirmations!*"
            )

        embed = {
            "title": title,
            "description": description,
            "color": 0x00FF00,
            "timestamp": now.isoformat(),
            "footer": {
                "text": "Forex Pivot Reversal Bot • FX-Optimized"
            }
        }

        send_discord_alert(embed)

        # Update tracking
        if update_type == "daily":
            self.last_premarket_day = current_day
        else:
            self.last_premarket_week = current_week

        logger.info(f"✅ Sent {update_type} premarket update")

    def run_scan(self):
        """Run one scan cycle with FX-specific checks"""
        # Check if market is open
        if not ForexUtils.is_market_open():
            logger.info("⏸️  Market closed (weekend) - skipping scan")
            return

        # Check for new day/week and send premarket update
        now = datetime.now(timezone.utc)
        current_day = now.date()
        current_week = now.isocalendar()[1]
        current_hour = now.hour

        # Send weekly update on Monday at market open (00:00 UTC or 08:00 UTC for London)
        if (self.last_premarket_week != current_week and
            (current_hour == 0 or current_hour == 8)):
            self.send_premarket_update("weekly")

        # Send daily update at start of new trading day (00:00 UTC or 08:00 UTC for London)
        if (self.last_premarket_day != current_day and
            (current_hour == 0 or current_hour == 8)):
            self.send_premarket_update("daily")

        current_session = ForexUtils.get_current_session()
        logger.info(f"🔍 Starting scan cycle... (Session: {current_session.upper()})")
        logger.info(f"🎯 Looking for: SCALPS (5m) & SWINGS (15m+) on {len(FOREX_PAIRS)} pairs")

        # Update existing positions
        current_prices = {}
        for symbol in FOREX_PAIRS:
            df = self.fetch_ohlcv(symbol, "15m", 10)
            if df is not None and len(df) > 0:
                current_prices[symbol] = df['close'].iloc[-1]

        self.paper_account.update_positions(current_prices)

        # Scan for new signals (SCALPS & SWINGS)
        signals = []
        scalp_count = 0
        swing_count = 0

        for symbol in FOREX_PAIRS:
            signal = self.scan_symbol(symbol)
            if signal:
                signals.append(signal)
                if signal.get('grade') == 'A+':
                    swing_count += 1
                    logger.info(f"📈 SWING opportunity: {symbol} {signal.get('direction')} - {signal.get('timeframe')}")
                elif signal.get('grade') == 'A-':
                    scalp_count += 1
                    logger.info(f"⚡ SCALP opportunity: {symbol} {signal.get('direction')} - {signal.get('timeframe')}")

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

        aplus_signals = [s for s in signals if s.get('grade') == 'A+']
        logger.info(f"✅ Scan complete: {len(signals)} total signals ({scalp_count} scalps, {swing_count} swings)")
        if aplus_signals:
            logger.info(f"🎯 {len(aplus_signals)} A+ SWING setups ready for auto-trading")

    def run(self):
        """Main bot loop - only runs during trading hours"""
        logger.info("🚀 Forex Pivot Reversal Bot started")
        logger.info(f"💰 Starting balance: ${PAPER_TRADING_CONFIG['starting_balance']:.2f}")
        logger.info(f"⚙️  Leverage: {PAPER_TRADING_CONFIG['leverage']}x")
        logger.info(f"📊 Risk per trade: {PAPER_TRADING_CONFIG['risk_per_trade']*100}%")
        logger.info(f"🔢 Max positions: {PAPER_TRADING_CONFIG['max_open_positions']}")
        logger.info(f"⏰ Market hours: 24/5 (Closed weekends)")

        # Send initial premarket update if market is open
        if ForexUtils.is_market_open():
            now = datetime.now(timezone.utc)
            current_week = now.isocalendar()[1]
            self.last_premarket_week = current_week
            self.last_premarket_day = now.date()
            self.send_premarket_update("daily")

        while True:
            try:
                # Only run during trading hours
                if ForexUtils.is_market_open():
                    self.run_scan()
                    time.sleep(SCAN_INTERVAL)
                else:
                    # Market is closed - wait and check again
                    logger.info("⏸️  Market closed - waiting 1 hour before checking again...")
                    time.sleep(3600)  # Wait 1 hour before checking again
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






