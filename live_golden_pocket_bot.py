#!/usr/bin/env python3
"""
Live Golden Pocket Trading Bot
Production-ready bot for live trading on Phemex
Implements: Golden Pocket + 3-wave pullback + divergence + SFP/sweep strategy
"""

import asyncio
import time
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import os

from phemex_exchange import PhemexExchange
from phemex_config import PHEMEX_CONFIG, PHEMEX_LIVE_CONFIG, PHEMEX_TRADING_CONFIG, PHEMEX_NOTIFICATION_CONFIG
import requests

@dataclass
class LiveTradeSignal:
    """Live trade signal data"""
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    position_size: float
    leverage: int
    confidence: float
    reason: str
    is_sfp_sweep: bool = False
    timestamp: float = 0

class LiveGoldenPocketBot:
    """Live Golden Pocket trading bot for Phemex"""

    def __init__(self):
        self.exchange = PhemexExchange(paper_trading=False)  # LIVE TRADING
        self.setup_logging()

        # Live trading parameters
        self.max_trades = 3  # Max 3 trades open
        self.target_move = 0.02  # 2% target move
        self.max_move = 0.03  # 3% max move (close 75%)
        self.final_target = 0.05  # 5% final target
        self.leverage = 15  # 15x leverage as requested

        # Position sizing - Fixed $10 positions
        self.position_size = 10.0  # Fixed $10 per position

        # Cooldown system
        self.win_count = 0
        self.loss_count = 0
        self.cooldown_win_minutes = 30  # 30 min cooldown after 2 wins
        self.cooldown_loss_minutes = 60  # 60 min cooldown after 2 losses
        self.last_trade_time = 0
        self.daily_trade_count = 0
        self.last_reset_date = datetime.now().date()

        # Active trades
        self.active_trades = {}

        # Focus on smaller caps (not big caps like BTC/ETH)
        self.trading_symbols = [
            'SOL/USDT', 'SUI/USDT', 'AVAX/USDT', 'MATIC/USDT',
            'DOT/USDT', 'LINK/USDT', 'UNI/USDT', 'ATOM/USDT',
            'NEAR/USDT', 'FTM/USDT', 'ALGO/USDT', 'VET/USDT'
        ]

        # Safety limits
        self.max_daily_trades = PHEMEX_LIVE_CONFIG['max_daily_trades']
        self.emergency_stop_loss = PHEMEX_LIVE_CONFIG['emergency_stop_loss']

        # State persistence
        self.state_file = 'live_bot_state.json'
        self.load_state()

        # Discord notifications
        self.discord_webhook = PHEMEX_NOTIFICATION_CONFIG['discord_webhook']

    def setup_logging(self):
        """Setup comprehensive logging for live trading"""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)

        # Setup main logger
        self.logger = logging.getLogger('LiveGoldenPocketBot')
        self.logger.setLevel(logging.INFO)

        # File handler for all logs
        file_handler = logging.FileHandler(f'logs/live_bot_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler.setLevel(logging.INFO)

        # Console handler for critical logs
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Trade-specific logger
        self.trade_logger = logging.getLogger('TradeLogger')
        self.trade_logger.setLevel(logging.INFO)

        trade_handler = logging.FileHandler(f'logs/trades_{datetime.now().strftime("%Y%m%d")}.log')
        trade_handler.setLevel(logging.INFO)
        trade_handler.setFormatter(formatter)
        self.trade_logger.addHandler(trade_handler)

    def load_state(self):
        """Load bot state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                self.win_count = state.get('win_count', 0)
                self.loss_count = state.get('loss_count', 0)
                self.last_trade_time = state.get('last_trade_time', 0)
                self.daily_trade_count = state.get('daily_trade_count', 0)
                self.active_trades = state.get('active_trades', {})

                self.logger.info("Bot state loaded successfully")
            else:
                self.logger.info("No existing state found, starting fresh")

        except Exception as e:
            self.logger.error(f"Error loading state: {e}")

    def save_state(self):
        """Save bot state to file"""
        try:
            state = {
                'win_count': self.win_count,
                'loss_count': self.loss_count,
                'last_trade_time': self.last_trade_time,
                'daily_trade_count': self.daily_trade_count,
                'active_trades': self.active_trades,
                'last_save': time.time()
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving state: {e}")

    async def send_discord_alert(self, title: str, description: str, color: int = 0x00ff00, fields: list = None):
        """Send Discord alert"""
        try:
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Phemex Golden Pocket Bot"
                }
            }

            if fields:
                embed["fields"] = fields

            payload = {
                "embeds": [embed]
            }

            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            if response.status_code == 204:
                self.logger.info(f"Discord alert sent: {title}")
            else:
                self.logger.error(f"Discord alert failed: {response.status_code}")

        except Exception as e:
            self.logger.error(f"Error sending Discord alert: {e}")

    def reset_daily_counters(self):
        """Reset daily counters if new day"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_trade_count = 0
            self.last_reset_date = current_date
            self.logger.info("Daily counters reset for new day")

    async def get_account_balance(self) -> float:
        """Get current account balance"""
        try:
            balance = await self.exchange.get_account_balance()
            return balance.get('USDT', 0)
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return 0

    def calculate_golden_pocket(self, df: pd.DataFrame) -> Tuple[float, float]:
        """Calculate Golden Pocket levels (61.8% and 65% retracement)"""
        try:
            # Use recent high and low
            lookback = min(24, len(df))  # 24 bars for daily approximation
            high = df['high'].rolling(lookback).max().iloc[-1]
            low = df['low'].rolling(lookback).min().iloc[-1]

            range_size = high - low
            gp_high = high - (range_size * 0.618)  # 61.8% retracement
            gp_low = high - (range_size * 0.65)    # 65% retracement

            return gp_high, gp_low

        except Exception as e:
            self.logger.error(f"Error calculating Golden Pocket: {e}")
            return 0, 0

    def detect_three_wave_pullback(self, df: pd.DataFrame) -> bool:
        """Detect 3-wave pullback pattern"""
        try:
            if len(df) < 20:
                return False

            # Simple 3-wave detection
            highs = df['high'].rolling(5).max()
            lows = df['low'].rolling(5).min()

            recent_high = highs.iloc[-1]
            recent_low = lows.iloc[-1]
            current_price = df['close'].iloc[-1]

            pullback_range = recent_high - recent_low
            pullback_position = (current_price - recent_low) / pullback_range if pullback_range > 0 else 0

            # Consider it a 3-wave if price is in the 40-70% range of the pullback
            return 0.4 <= pullback_position <= 0.7

        except Exception as e:
            self.logger.error(f"Error detecting 3-wave pullback: {e}")
            return False

    def detect_divergence(self, df: pd.DataFrame) -> Tuple[bool, bool]:
        """Detect bullish and bearish divergence"""
        try:
            if len(df) < 20:
                return False, False

            # Calculate RSI
            rsi = self.calculate_rsi(df['close'], 14)

            # Find recent highs and lows
            lookback = 10
            recent_high = df['high'].rolling(lookback).max()
            recent_low = df['low'].rolling(lookback).min()

            # Check for divergence
            price_higher = df['high'].iloc[-1] > df['high'].iloc[-lookback]
            rsi_lower = rsi.iloc[-1] < rsi.iloc[-lookback]
            bearish_div = price_higher and rsi_lower

            price_lower = df['low'].iloc[-1] < df['low'].iloc[-lookback]
            rsi_higher = rsi.iloc[-1] > rsi.iloc[-lookback]
            bullish_div = price_lower and rsi_higher

            return bullish_div, bearish_div

        except Exception as e:
            self.logger.error(f"Error detecting divergence: {e}")
            return False, False

    def detect_sfp_sweep(self, df: pd.DataFrame) -> Tuple[bool, bool]:
        """Detect SFP (Stop Fake Push) and sweep patterns"""
        try:
            if len(df) < 20:
                return False, False

            current_high = df['high'].iloc[-1]
            current_low = df['low'].iloc[-1]
            current_close = df['close'].iloc[-1]

            # Look for recent swing points
            lookback = 15
            swing_high = df['high'].rolling(lookback).max().iloc[-2]
            swing_low = df['low'].rolling(lookback).min().iloc[-2]

            # Check for sweep of highs (bearish)
            sweep_high = current_high > swing_high and current_close < swing_high

            # Check for sweep of lows (bullish)
            sweep_low = current_low < swing_low and current_close > swing_low

            return sweep_low, sweep_high

        except Exception as e:
            self.logger.error(f"Error detecting SFP sweep: {e}")
            return False, False

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([50] * len(prices), index=prices.index)

    def analyze_volume_liquidations(self, df: pd.DataFrame) -> bool:
        """Check if volume and liquidations are matched for reversal"""
        try:
            if len(df) < 10:
                return False

            # Volume analysis
            avg_volume = df['volume'].rolling(10).mean()
            current_volume = df['volume'].iloc[-1]
            volume_spike = current_volume > avg_volume.iloc[-1] * 1.5

            # Price rejection (liquidation-like behavior)
            current_close = df['close'].iloc[-1]
            current_open = df['open'].iloc[-1]
            current_high = df['high'].iloc[-1]
            current_low = df['low'].iloc[-1]

            # Check for rejection wicks
            upper_wick = current_high - max(current_open, current_close)
            lower_wick = min(current_open, current_close) - current_low
            total_range = current_high - current_low

            if total_range > 0:
                upper_wick_pct = upper_wick / total_range
                lower_wick_pct = lower_wick / total_range

                # Strong rejection wick indicates liquidation
                strong_rejection = upper_wick_pct > 0.4 or lower_wick_pct > 0.4

                return volume_spike and strong_rejection

            return False

        except Exception as e:
            self.logger.error(f"Error analyzing volume/liquidations: {e}")
            return False

    def calculate_position_size(self, entry_price: float, stop_loss: float, balance: float) -> float:
        """Calculate position size - Fixed $10 positions with 15x leverage"""
        try:
            # Fixed $10 position size
            position_value = self.position_size  # $10

            # Calculate actual position size based on entry price
            position_size = position_value / entry_price

            # Apply 15x leverage
            position_size *= self.leverage

            return position_size

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0

    async def analyze_symbol(self, symbol: str) -> Optional[LiveTradeSignal]:
        """Analyze symbol for trading opportunity"""
        try:
            # Get market data
            ticker = await self.exchange.get_ticker(symbol)
            if not ticker:
                return None

            ohlcv = await self.exchange.get_ohlcv(symbol, '15m', 100)
            if ohlcv is None or len(ohlcv) < 50:
                return None

            current_price = ticker['last']

            # 1. Calculate Golden Pocket
            gp_high, gp_low = self.calculate_golden_pocket(ohlcv)
            if gp_high == 0 or gp_low == 0:
                return None

            # 2. Check if price is near Golden Pocket
            near_gp = gp_low <= current_price <= gp_high

            if not near_gp:
                return None

            # 3. Detect 3-wave pullback
            three_wave = self.detect_three_wave_pullback(ohlcv)

            # 4. Detect divergence
            bullish_div, bearish_div = self.detect_divergence(ohlcv)

            # 5. Detect SFP/sweep
            sweep_low, sweep_high = self.detect_sfp_sweep(ohlcv)

            # 6. Check volume/liquidations
            vol_liq_match = self.analyze_volume_liquidations(ohlcv)

            # 7. Determine signal
            signal = None
            confidence = 0
            reason_parts = []

            # Debug logging
            self.logger.info(f"🔍 {symbol} Analysis:")
            self.logger.info(f"  Price: ${current_price:.4f}")
            self.logger.info(f"  Near GP: {near_gp} (${gp_low:.4f} - ${gp_high:.4f})")
            self.logger.info(f"  3-Wave: {three_wave}")
            self.logger.info(f"  Bull Div: {bullish_div}, Bear Div: {bearish_div}")
            self.logger.info(f"  Sweep Low: {sweep_low}, Sweep High: {sweep_high}")
            self.logger.info(f"  Vol/Liq Match: {vol_liq_match}")

            # Get account balance for position sizing
            balance = await self.get_account_balance()
            if balance < 30:  # Minimum balance check for $10 positions
                return None

            # Bullish setup
            if (bullish_div or sweep_low) and vol_liq_match:
                if three_wave:
                    confidence += 30
                    reason_parts.append("3-wave")
                if bullish_div:
                    confidence += 25
                    reason_parts.append("Bull Div")
                if sweep_low:
                    confidence += 35
                    reason_parts.append("Sweep Low")
                    is_sfp = True
                else:
                    is_sfp = False
                if vol_liq_match:
                    confidence += 10
                    reason_parts.append("Vol/Liq")

                self.logger.info(f"  🟢 BULLISH SETUP: Confidence = {confidence}")

                if confidence >= 30:  # Lowered for test trades (was 50)
                    stop_loss = current_price * 0.99  # 1% stop for test trades
                    position_size = self.calculate_position_size(current_price, stop_loss, balance)

                    if position_size > 0:
                        signal = LiveTradeSignal(
                            symbol=symbol,
                            direction="long",
                            entry_price=current_price,
                            stop_loss=stop_loss,
                            take_profit_1=current_price * 1.02,  # 2% target
                            take_profit_2=current_price * 1.05,  # 5% target
                            position_size=position_size,
                            leverage=self.leverage,
                            confidence=confidence,
                            reason=" + ".join(reason_parts),
                            is_sfp_sweep=is_sfp,
                            timestamp=time.time()
                        )

            # Bearish setup
            elif (bearish_div or sweep_high) and vol_liq_match:
                if three_wave:
                    confidence += 30
                    reason_parts.append("3-wave")
                if bearish_div:
                    confidence += 25
                    reason_parts.append("Bear Div")
                if sweep_high:
                    confidence += 35
                    reason_parts.append("Sweep High")
                    is_sfp = True
                else:
                    is_sfp = False
                if vol_liq_match:
                    confidence += 10
                    reason_parts.append("Vol/Liq")

                self.logger.info(f"  🔴 BEARISH SETUP: Confidence = {confidence}")

                if confidence >= 30:  # Lowered for test trades (was 50)
                    stop_loss = current_price * 1.01  # 1% stop for test trades
                    position_size = self.calculate_position_size(current_price, stop_loss, balance)

                    if position_size > 0:
                        signal = LiveTradeSignal(
                            symbol=symbol,
                            direction="short",
                            entry_price=current_price,
                            stop_loss=stop_loss,
                            take_profit_1=current_price * 0.98,  # 2% target
                            take_profit_2=current_price * 0.95,  # 5% target
                            position_size=position_size,
                            leverage=self.leverage,
                            confidence=confidence,
                            reason=" + ".join(reason_parts),
                            is_sfp_sweep=is_sfp,
                            timestamp=time.time()
                        )

            if signal:
                self.logger.warning(f"🎯 SIGNAL GENERATED: {symbol} {signal.direction.upper()} - Confidence: {signal.confidence}")
                self.logger.info(f"Signal details: {signal.direction} @ ${signal.entry_price:.4f} (Size: ${signal.position_size:.2f})")
            else:
                self.logger.info(f"❌ No signal for {symbol} (confidence: {confidence})")

            return signal

        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def can_take_trade(self) -> bool:
        """Check if we can take a new trade"""
        # Reset daily counters if new day
        self.reset_daily_counters()

        # Check max trades
        if len(self.active_trades) >= self.max_trades:
            return False

        # Check daily trade limit
        if self.daily_trade_count >= self.max_daily_trades:
            return False

        # Check cooldown
        current_time = time.time()
        time_since_last = (current_time - self.last_trade_time) / 60  # minutes

        if self.loss_count >= 2 and time_since_last < self.cooldown_loss_minutes:
            return False

        if self.win_count >= 2 and time_since_last < self.cooldown_win_minutes:
            return False

        return True

    async def execute_trade(self, signal: LiveTradeSignal) -> bool:
        """Execute live trade signal"""
        try:
            if not self.can_take_trade():
                return False

            # For SFP sweeps, don't wait - execute immediately
            if not signal.is_sfp_sweep:
                # For other signals, be more selective (lowered for test trades)
                if signal.confidence < 30:  # Lowered from 80 for test trades
                    return False

            # Set leverage first
            await self.exchange.set_leverage(signal.symbol, signal.leverage)

            # Place order
            order = await self.exchange.place_order(
                symbol=signal.symbol,
                side=signal.direction,
                amount=signal.position_size,
                leverage=signal.leverage
            )

            if order:
                trade_id = f"{signal.symbol}_{int(time.time())}"
                self.active_trades[trade_id] = {
                    'signal': signal,
                    'order': order,
                    'entry_time': time.time(),
                    'status': 'open',
                    'partial_closed': False
                }

                self.last_trade_time = time.time()
                self.daily_trade_count += 1

                # Log trade
                self.trade_logger.info(f"LIVE TRADE EXECUTED: {signal.symbol} {signal.direction} @ {signal.entry_price:.4f} Size: {signal.position_size:.2f} Reason: {signal.reason}")

                # Send Discord alert
                await self.send_discord_alert(
                    title="🚀 LIVE TRADE EXECUTED",
                    description=f"**{signal.symbol}** {signal.direction.upper()} @ ${signal.entry_price:.4f}",
                    color=0x00ff00,
                    fields=[
                        {"name": "Position Size", "value": f"${signal.position_size:.2f}", "inline": True},
                        {"name": "Leverage", "value": f"{signal.leverage}x", "inline": True},
                        {"name": "Confidence", "value": f"{signal.confidence:.1f}%", "inline": True},
                        {"name": "Reason", "value": signal.reason, "inline": False},
                        {"name": "Stop Loss", "value": f"${signal.stop_loss:.4f}", "inline": True},
                        {"name": "Take Profit 1", "value": f"${signal.take_profit_1:.4f}", "inline": True},
                        {"name": "Take Profit 2", "value": f"${signal.take_profit_2:.4f}", "inline": True}
                    ]
                )

                # Save state
                self.save_state()

                self.logger.warning(f"LIVE TRADE EXECUTED: {signal.symbol} {signal.direction} @ {signal.entry_price:.4f}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to execute live trade: {e}")
            return False

    async def monitor_trades(self):
        """Monitor active trades"""
        for trade_id, trade_data in list(self.active_trades.items()):
            try:
                signal = trade_data['signal']
                current_time = time.time()

                # Get current price
                ticker = await self.exchange.get_ticker(signal.symbol)
                if not ticker:
                    continue

                current_price = ticker['last']

                # Calculate move percentage
                if signal.direction == "long":
                    move_pct = (current_price - signal.entry_price) / signal.entry_price
                else:
                    move_pct = (signal.entry_price - current_price) / signal.entry_price

                # Check exit conditions
                should_exit = False
                exit_reason = ""

                # Stop loss
                if signal.direction == "long" and current_price <= signal.stop_loss:
                    should_exit = True
                    exit_reason = "Stop Loss"
                elif signal.direction == "short" and current_price >= signal.stop_loss:
                    should_exit = True
                    exit_reason = "Stop Loss"

                # Take profit 1 (2% move)
                elif move_pct >= self.target_move:
                    should_exit = True
                    exit_reason = "Take Profit 1 (2%)"

                # Check for 3% move (close 75% if not already done)
                elif move_pct >= self.max_move and not trade_data['partial_closed']:
                    # Close 75% of position
                    await self.exchange.close_position(signal.symbol, 75)
                    trade_data['partial_closed'] = True
                    self.trade_logger.info(f"PARTIAL CLOSE: 75% of {signal.symbol} at 3% move")

                # Take profit 2 (5% move)
                elif move_pct >= self.final_target:
                    should_exit = True
                    exit_reason = "Take Profit 2 (5%)"

                # SFP sweep invalidation (if move > 1.5% against us)
                elif signal.is_sfp_sweep and move_pct <= -0.015:
                    should_exit = True
                    exit_reason = "SFP Invalidation"

                # Emergency stop loss
                elif move_pct <= -self.emergency_stop_loss:
                    should_exit = True
                    exit_reason = "Emergency Stop Loss"

                if should_exit:
                    # Close position
                    await self.exchange.close_position(signal.symbol)

                    # Calculate P&L
                    pnl_pct = move_pct * 100

                    # Update counters
                    if pnl_pct > 0:
                        self.win_count += 1
                    else:
                        self.loss_count += 1

                    # Remove from active trades
                    del self.active_trades[trade_id]

                    # Log trade result
                    self.trade_logger.info(f"TRADE CLOSED: {signal.symbol} {signal.direction} @ {current_price:.4f} P&L: {pnl_pct:.2f}% Reason: {exit_reason}")

                    # Send Discord alert
                    color = 0x00ff00 if pnl_pct > 0 else 0xff0000
                    emoji = "💰" if pnl_pct > 0 else "📉"

                    await self.send_discord_alert(
                        title=f"{emoji} TRADE CLOSED",
                        description=f"**{signal.symbol}** {signal.direction.upper()} @ ${current_price:.4f}",
                        color=color,
                        fields=[
                            {"name": "P&L", "value": f"{pnl_pct:+.2f}%", "inline": True},
                            {"name": "Exit Reason", "value": exit_reason, "inline": True},
                            {"name": "Entry Price", "value": f"${signal.entry_price:.4f}", "inline": True},
                            {"name": "Duration", "value": f"{(current_time - trade_data['entry_time'])/60:.1f} min", "inline": True},
                            {"name": "Win/Loss Count", "value": f"W: {self.win_count} L: {self.loss_count}", "inline": True}
                        ]
                    )

                    # Save state
                    self.save_state()

                    self.logger.warning(f"LIVE TRADE CLOSED: {signal.symbol} {signal.direction} @ {current_price:.4f} P&L: {pnl_pct:.2f}%")

            except Exception as e:
                self.logger.error(f"Error monitoring trade {trade_id}: {e}")

    async def scan_for_signals(self) -> List[LiveTradeSignal]:
        """Scan for trading signals"""
        signals = []

        for symbol in self.trading_symbols:
            try:
                signal = await self.analyze_symbol(symbol)
                if signal:
                    signals.append(signal)
            except Exception as e:
                self.logger.error(f"Error scanning {symbol}: {e}")

        # Sort by confidence
        signals.sort(key=lambda x: x.confidence, reverse=True)

        return signals

    async def run_live_bot(self):
        """Run the live trading bot"""
        self.logger.warning("🚀 STARTING LIVE GOLDEN POCKET BOT ON PHEMEX 🚀")

        # Send startup notification
        await self.send_discord_alert(
            title="🚀 BOT STARTED",
            description="Live Golden Pocket Bot is now running on Phemex",
            color=0x00ff00,
            fields=[
                {"name": "Leverage", "value": f"{self.leverage}x", "inline": True},
                {"name": "Max Trades", "value": str(self.max_trades), "inline": True},
                {"name": "Position Size", "value": f"${self.position_size}", "inline": True}
            ]
        )

        # Test connection first
        if not await self.exchange.test_connection():
            self.logger.error("❌ Failed to connect to Phemex. Exiting.")
            await self.send_discord_alert(
                title="❌ CONNECTION FAILED",
                description="Failed to connect to Phemex. Bot stopped.",
                color=0xff0000
            )
            return

        self.logger.warning("✅ Connected to Phemex successfully")

        # Get initial balance
        balance = await self.get_account_balance()
        self.logger.warning(f"💰 Account Balance: ${balance:.2f} USDT")

        # Send balance notification
        await self.send_discord_alert(
            title="💰 ACCOUNT STATUS",
            description=f"Connected to Phemex successfully",
            color=0x0099ff,
            fields=[
                {"name": "Balance", "value": f"${balance:.2f} USDT", "inline": True},
                {"name": "Status", "value": "Ready to trade", "inline": True}
            ]
        )

        # Main trading loop with periodic status updates
        scan_count = 0
        while True:
            try:
                # Monitor existing trades
                await self.monitor_trades()

                # Scan for new signals
                signals = await self.scan_for_signals()

                # Execute best signal if available (AUTOMATIC - no manual approval needed)
                if signals and self.can_take_trade():
                    best_signal = signals[0]
                    self.logger.warning(f"🎯 AUTO-EXECUTING TRADE: {best_signal.symbol} {best_signal.direction.upper()} (confidence: {best_signal.confidence:.1f}%)")
                    await self.execute_trade(best_signal)
                elif signals:
                    self.logger.info(f"📊 Found {len(signals)} signals but cannot trade right now (max trades or cooldown active)")
                else:
                    # Send "still looking" notification every 5 minutes (10 scans * 30 seconds)
                    scan_count += 1
                    if scan_count >= 10:  # Every 5 minutes
                        await self.send_discord_alert(
                            title="🔍 STILL SCANNING",
                            description="Bot is actively monitoring for Golden Pocket + Divergence + SFP setups",
                            color=0x0099ff,
                            fields=[
                                {"name": "⏰ Last Scan", "value": datetime.now().strftime("%H:%M:%S"), "inline": True},
                                {"name": "📊 Signals Found", "value": "0 - Waiting for perfect setup", "inline": True},
                                {"name": "🎯 Strategy", "value": "Golden Pocket + Divergence + SFP", "inline": True},
                                {"name": "💰 Balance", "value": f"${await self.get_account_balance():.2f} USDT", "inline": True},
                                {"name": "⚡ Status", "value": "ACTIVE & MONITORING", "inline": True},
                                {"name": "🔄 Next Scan", "value": "In 30 seconds", "inline": True}
                            ]
                        )
                        scan_count = 0  # Reset counter

                # Wait before next scan
                await asyncio.sleep(30)  # 30 seconds between scans

            except KeyboardInterrupt:
                self.logger.warning("🛑 Bot stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Bot error: {e}")
                await asyncio.sleep(60)

# Main execution
async def main():
    """Main function for live trading"""
    print("⚠️  WARNING: This will start LIVE TRADING on Phemex!")
    print("⚠️  Make sure you have configured your API credentials!")
    print("⚠️  Make sure you have sufficient balance!")
    print("🚀 Starting bot with AUTOMATIC trading enabled...")
    print("📊 Scanner will automatically execute trades without manual approval")

    # Automatic startup - no confirmation required
    bot = LiveGoldenPocketBot()
    await bot.run_live_bot()

if __name__ == "__main__":
    asyncio.run(main())
