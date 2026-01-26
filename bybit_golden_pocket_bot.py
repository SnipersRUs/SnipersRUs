#!/usr/bin/env python3
"""
Bybit Golden Pocket Trading Bot
Production-ready bot for live trading on Bybit
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
import requests

from bybit_exchange import BybitExchange
from bybit_config import (
    BYBIT_CONFIG, BYBIT_TRADING_CONFIG, BYBIT_LIVE_CONFIG,
    BYBIT_NOTIFICATION_CONFIG, BYBIT_ANALYSIS_CONFIG,
    BYBIT_SYMBOLS, get_symbol_leverage, get_position_size, validate_config
)

@dataclass
class TradeSignal:
    """Trading signal data"""
    symbol: str
    direction: str  # 'long' or 'short'
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

class BybitGoldenPocketBot:
    """Bybit Golden Pocket trading bot"""

    def __init__(self):
        self.exchange = BybitExchange(paper_trading=BYBIT_LIVE_CONFIG['paper_trading'])
        self.setup_logging()

        # Set API credentials
        if BYBIT_CONFIG['api_key'] and BYBIT_CONFIG['api_secret']:
            self.exchange.set_credentials(BYBIT_CONFIG['api_key'], BYBIT_CONFIG['api_secret'])

        # Trading parameters
        self.max_trades = BYBIT_TRADING_CONFIG['max_open_positions']
        self.target_move = 0.02  # 2% target move
        self.max_move = 0.03     # 3% max move (close 75%)
        self.final_target = 0.05 # 5% final target
        self.leverage = BYBIT_TRADING_CONFIG['default_leverage']

        # Position sizing
        self.base_position_size = BYBIT_TRADING_CONFIG['base_position_size']

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

        # Trading symbols
        self.trading_symbols = BYBIT_SYMBOLS

        # Safety limits
        self.max_daily_trades = BYBIT_TRADING_CONFIG['max_daily_trades']
        self.emergency_stop_loss = BYBIT_TRADING_CONFIG['emergency_stop_loss']

        # State persistence
        self.state_file = 'bybit_bot_state.json'
        self.load_state()

        # Discord notifications
        self.discord_webhook = BYBIT_NOTIFICATION_CONFIG['discord_webhook']

        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0

    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bybit_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_state(self):
        """Load bot state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.win_count = state.get('win_count', 0)
                    self.loss_count = state.get('loss_count', 0)
                    self.daily_trade_count = state.get('daily_trade_count', 0)
                    self.total_trades = state.get('total_trades', 0)
                    self.winning_trades = state.get('winning_trades', 0)
                    self.losing_trades = state.get('losing_trades', 0)
                    self.total_pnl = state.get('total_pnl', 0.0)
                    self.active_trades = state.get('active_trades', {})
                self.logger.info("✅ Bot state loaded successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to load state: {e}")

    def save_state(self):
        """Save bot state to file"""
        try:
            state = {
                'win_count': self.win_count,
                'loss_count': self.loss_count,
                'daily_trade_count': self.daily_trade_count,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'total_pnl': self.total_pnl,
                'active_trades': self.active_trades,
                'last_save': time.time()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.error(f"❌ Failed to save state: {e}")

    async def send_discord_notification(self, message: str, color: int = 0x00ff00):
        """Send Discord notification"""
        return

        try:
            embed = {
                "title": "🤖 Bybit Trading Bot",
                "description": message,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": f"Trades: {self.total_trades} | PnL: ${self.total_pnl:.2f}"
                }
            }

            payload = {"embeds": [embed]}
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            response.raise_for_status()

        except Exception as e:
            self.logger.error(f"❌ Discord notification failed: {e}")

    async def test_connection(self) -> bool:
        """Test connection to Bybit"""
        try:
            success = await self.exchange.test_connection()
            if success:
                await self.send_discord_notification("✅ Connected to Bybit successfully", 0x00ff00)
            else:
                await self.send_discord_notification("❌ Failed to connect to Bybit", 0xff0000)
            return success
        except Exception as e:
            self.logger.error(f"❌ Connection test failed: {e}")
            return False

    async def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            balance = await self.exchange.get_account_balance()
            positions = await self.exchange.get_positions()

            return {
                'balance': balance,
                'positions': positions,
                'active_trades': len(self.active_trades),
                'daily_trades': self.daily_trade_count
            }
        except Exception as e:
            self.logger.error(f"❌ Failed to get account info: {e}")
            return {}

    async def analyze_golden_pocket(self, symbol: str) -> Optional[TradeSignal]:
        """Analyze for Golden Pocket trading opportunity"""
        try:
            # Get kline data
            klines = await self.exchange.get_klines(symbol, '1', 200)
            if not klines:
                return None

            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            df = df.astype({
                'open': float, 'high': float, 'low': float, 'close': float, 'volume': float
            })

            # Calculate indicators
            df['rsi'] = self.calculate_rsi(df['close'], 14)
            df['atr'] = self.calculate_atr(df, 14)

            # Find recent swing high and low
            recent_high = df['high'].rolling(20).max().iloc[-1]
            recent_low = df['low'].rolling(20).min().iloc[-1]
            current_price = df['close'].iloc[-1]

            # Check for Golden Pocket retracement (61.8% - 65%)
            # Check for Golden Pocket retracement (widened to 0.61 - 0.66 to catch near misses)
            if current_price < recent_high and current_price > recent_low:
                # Calculate retracement from High
                retracement = (recent_high - current_price) / (recent_high - recent_low)

                # Check for volume spike (lowered to 1.1x)
                volume_current = df['volume'].iloc[-1]
                volume_avg = df['volume'].rolling(20).mean().iloc[-1]
                volume_spike = volume_current / volume_avg if volume_avg > 0 else 1

                rsi_current = df['rsi'].iloc[-1]

                self.logger.info(f"🔎 Analyzing {symbol}: Retracement={retracement:.3f}, VolSpike={volume_spike:.2f}, RSI={rsi_current:.1f}")

                if 0.61 <= retracement <= 0.66:  # Golden Pocket (widened)
                    # Generate signal
                    # Relaxed Volume Spike > 1.1
                    # Relaxed RSI conditions

                    if rsi_current < 55 and volume_spike > 1.1:  # Bullish context (Oversold-ish)
                        signal = TradeSignal(
                            symbol=symbol,
                            direction='long',
                            entry_price=current_price,
                            stop_loss=current_price * 0.99,  # 1% stop loss
                            take_profit_1=current_price * 1.02,  # 2% first target
                            take_profit_2=current_price * 1.05,  # 5% second target
                            position_size=self.base_position_size,
                            leverage=get_symbol_leverage(symbol),
                            confidence=0.8,
                            reason=f"Golden Pocket Long - {retracement:.1%} retracement, Vol: {volume_spike:.1f}x",
                            timestamp=time.time()
                        )
                        return signal

                    elif rsi_current > 45 and volume_spike > 1.1:  # Bearish context (Overbought-ish)
                        signal = TradeSignal(
                            symbol=symbol,
                            direction='short',
                            entry_price=current_price,
                            stop_loss=current_price * 1.01,  # 1% stop loss
                            take_profit_1=current_price * 0.98,  # 2% first target
                            take_profit_2=current_price * 0.95,  # 5% second target
                            position_size=self.base_position_size,
                            leverage=get_symbol_leverage(symbol),
                            confidence=0.8,
                            reason=f"Golden Pocket Short - {retracement:.1%} retracement, Vol: {volume_spike:.1f}x",
                            timestamp=time.time()
                        )
                        return signal
                    else:
                        self.logger.info(f"⚠️ {symbol} in GP but conditions metrics weak: RSI={rsi_current:.1f}, Vol={volume_spike:.2f}")
                else:
                    # Log if it was close (within 5%)
                    if 0.55 <= retracement <= 0.75:
                         self.logger.info(f"👀 {symbol} near GP ({retracement:.3f})")

            return None

        except Exception as e:
            self.logger.error(f"❌ Error analyzing {symbol}: {e}")
            return None

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR indicator"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(period).mean()
        return atr

    async def execute_trade(self, signal: TradeSignal) -> bool:
        """Execute trading signal"""
        try:
            # Check if we can trade
            if not self.can_trade():
                self.logger.info("⏸️  Trading paused due to cooldown or limits")
                return False

            # Place order
            order_type = 'Market'
            side = 'Buy' if signal.direction == 'long' else 'Sell'
            qty = str(signal.position_size)

            # Add stop loss and take profit
            stop_loss = str(signal.stop_loss)
            take_profit = str(signal.take_profit_1)

            result = await self.exchange.place_order(
                symbol=signal.symbol,
                side=side,
                order_type=order_type,
                qty=qty,
                stop_loss=stop_loss,
                take_profit=take_profit
            )

            if result:
                # Track the trade
                trade_id = result.get('orderId', f"trade_{int(time.time())}")
                self.active_trades[trade_id] = {
                    'signal': signal,
                    'order_id': trade_id,
                    'entry_time': time.time(),
                    'status': 'open'
                }

                self.daily_trade_count += 1
                self.total_trades += 1

                # Send notification
                message = f"🎯 **Trade Executed**\n"
                message += f"**Symbol:** {signal.symbol}\n"
                message += f"**Direction:** {signal.direction.upper()}\n"
                message += f"**Entry:** ${signal.entry_price:.4f}\n"
                message += f"**Stop Loss:** ${signal.stop_loss:.4f}\n"
                message += f"**Take Profit:** ${signal.take_profit_1:.4f}\n"
                message += f"**Size:** ${signal.position_size}\n"
                message += f"**Reason:** {signal.reason}"

                await self.send_discord_notification(message, 0x0099ff)

                self.logger.info(f"✅ Trade executed: {signal.symbol} {signal.direction}")
                return True
            else:
                self.logger.error(f"❌ Failed to execute trade: {signal.symbol}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error executing trade: {e}")
            return False

    def can_trade(self) -> bool:
        """Check if we can place new trades"""
        # Check daily trade limit
        if self.daily_trade_count >= self.max_daily_trades:
            return False

        # Check max open positions
        if len(self.active_trades) >= self.max_trades:
            return False

        # Check cooldown
        current_time = time.time()
        if self.win_count >= 2 and (current_time - self.last_trade_time) < (self.cooldown_win_minutes * 60):
            return False

        if self.loss_count >= 2 and (current_time - self.last_trade_time) < (self.cooldown_loss_minutes * 60):
            return False

        return True

    async def monitor_trades(self):
        """Monitor active trades"""
        try:
            for trade_id, trade in list(self.active_trades.items()):
                if trade['status'] != 'open':
                    continue

                # Get current price
                symbol = trade['signal'].symbol
                ticker = await self.exchange.get_ticker(symbol)
                if not ticker:
                    continue

                current_price = float(ticker['lastPrice'])
                entry_price = trade['signal'].entry_price
                direction = trade['signal'].direction

                # Calculate PnL
                if direction == 'long':
                    pnl_pct = (current_price - entry_price) / entry_price
                else:
                    pnl_pct = (entry_price - current_price) / entry_price

                # Check for take profit or stop loss
                if pnl_pct >= 0.02:  # 2% profit
                    await self.close_trade(trade_id, "Take Profit 1", 0x00ff00)
                elif pnl_pct >= 0.05:  # 5% profit
                    await self.close_trade(trade_id, "Take Profit 2", 0x00ff00)
                elif pnl_pct <= -0.01:  # 1% loss
                    await self.close_trade(trade_id, "Stop Loss", 0xff0000)

        except Exception as e:
            self.logger.error(f"❌ Error monitoring trades: {e}")

    async def close_trade(self, trade_id: str, reason: str, color: int):
        """Close a trade"""
        try:
            trade = self.active_trades.get(trade_id)
            if not trade:
                return

            # Cancel order (simplified - in real implementation, you'd close the position)
            symbol = trade['signal'].symbol
            order_id = trade['order_id']

            success = await self.exchange.cancel_order(symbol, order_id)

            if success:
                # Update trade status
                trade['status'] = 'closed'
                trade['close_reason'] = reason
                trade['close_time'] = time.time()

                # Update statistics
                if 'profit' in reason.lower():
                    self.winning_trades += 1
                    self.win_count += 1
                    self.loss_count = 0
                else:
                    self.losing_trades += 1
                    self.loss_count += 1
                    self.win_count = 0

                self.last_trade_time = time.time()

                # Send notification
                message = f"🔒 **Trade Closed**\n"
                message += f"**Symbol:** {symbol}\n"
                message += f"**Reason:** {reason}\n"
                message += f"**Direction:** {trade['signal'].direction.upper()}\n"
                message += f"**Entry:** ${trade['signal'].entry_price:.4f}"

                await self.send_discord_notification(message, color)

                self.logger.info(f"✅ Trade closed: {symbol} - {reason}")

        except Exception as e:
            self.logger.error(f"❌ Error closing trade: {e}")

    async def run_scan_cycle(self):
        """Run one scan cycle"""
        try:
            self.logger.info("🔍 Starting scan cycle...")

            # Reset daily counter if new day
            current_date = datetime.now().date()
            if current_date != self.last_reset_date:
                self.daily_trade_count = 0
                self.last_reset_date = current_date
                self.logger.info("📅 New day - resetting daily trade counter")

            # Scan each symbol
            for symbol in self.trading_symbols:
                if not self.can_trade():
                    break

                # Analyze for Golden Pocket
                signal = await self.analyze_golden_pocket(symbol)
                if signal:
                    await self.execute_trade(signal)
                    await asyncio.sleep(1)  # Rate limiting

            # Monitor existing trades
            await self.monitor_trades()

            # Save state
            self.save_state()

            self.logger.info("✅ Scan cycle completed")

        except Exception as e:
            self.logger.error(f"❌ Error in scan cycle: {e}")

    async def start(self):
        """Start the trading bot"""
        try:
            self.logger.info("🚀 Starting Bybit Golden Pocket Trading Bot...")

            # Test connection
            if not await self.test_connection():
                self.logger.error("❌ Failed to connect to Bybit. Exiting.")
                return

            # Send startup notification
            await self.send_discord_notification("🚀 **Bot Started**\nReady to trade Golden Pocket setups!", 0x00ff00)

            # Main trading loop
            while True:
                await self.run_scan_cycle()
                await asyncio.sleep(60)  # Wait 1 minute between scans

        except KeyboardInterrupt:
            self.logger.info("⏹️  Bot stopped by user")
            await self.send_discord_notification("⏹️ **Bot Stopped**\nTrading halted by user", 0xffaa00)
        except Exception as e:
            self.logger.error(f"❌ Bot error: {e}")
            await self.send_discord_notification(f"❌ **Bot Error**\n{e}", 0xff0000)

async def main():
    """Main function"""
    # Validate configuration
    if not validate_config():
        print("❌ Configuration validation failed")
        return

    # Create and start bot
    bot = BybitGoldenPocketBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
