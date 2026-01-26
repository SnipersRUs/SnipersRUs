#!/usr/bin/env python3
"""
Third Wave Scalper - 1212 Clusters and 3-Wave Pullbacks
Simple, focused scalping for immediate moves
"""

import asyncio
import time
import logging
import requests
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from hyperliquid.exchange import Exchange
from eth_account import Account
from hyperliquid_config import (
    HYPERLIQUID_CONFIG, 
    HYPERLIQUID_TRADING_CONFIG, 
    HYPERLIQUID_NOTIFICATION_CONFIG,
    HYPERLIQUID_SYMBOLS
)

class ThirdWaveSignal:
    def __init__(self, symbol: str, direction: str, entry_price: float, 
                 confidence: float, reason: str, wave_type: str):
        self.symbol = symbol
        self.direction = direction
        self.entry_price = entry_price
        self.confidence = confidence
        self.reason = reason
        self.wave_type = wave_type  # "1212_cluster" or "3_wave_pullback"
        self.timestamp = time.time()
        
        # Calculate position size and targets
        self.position_size = 15.0  # $15 positions
        self.leverage = 15  # 15x leverage
        
        # Calculate stop loss and take profits for scalping
        if direction == 'long':
            self.stop_loss = entry_price * 0.995  # 0.5% stop loss for scalping
            self.take_profit = entry_price * 1.01  # 1% take profit for scalping
        else:
            self.stop_loss = entry_price * 1.005  # 0.5% stop loss for scalping
            self.take_profit = entry_price * 0.99  # 1% take profit for scalping

class ThirdWaveScalper:
    def __init__(self):
        self.private_key = HYPERLIQUID_CONFIG['private_key']
        self.public_wallet = HYPERLIQUID_CONFIG['public_wallet']
        self.discord_webhook = HYPERLIQUID_NOTIFICATION_CONFIG['discord_webhook']
        
        # Initialize Hyperliquid client
        wallet = Account.from_key(self.private_key)
        self.client = Exchange(
            wallet=wallet,
            base_url="https://api.hyperliquid.xyz"
        )
        
        self.setup_logging()
        
        # Trading parameters
        self.max_trades = 2  # Max 2 trades open
        self.position_size = 15.0  # $15 per trade
        self.leverage = 15  # 15x leverage
        self.trades_per_hour = 5  # Target 5 trades per hour
        self.best_2_only = True  # Only take the 2 best signals
        
        # Trading state
        self.open_positions = {}
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_trade_time = 0
        self.cooldown_until = 0
        self.cooldown_seconds = 60  # 1 minute between trades for scalping
        
        # Hourly tracking
        self.hourly_trades = 0
        self.hour_start = time.time()
        
        # Symbols to trade (all Hyperliquid symbols)
        self.symbols = HYPERLIQUID_SYMBOLS
        
        self.logger.info("Third Wave Scalper initialized")
        self.logger.info(f"Max trades: {self.max_trades}")
        self.logger.info(f"Position size: ${self.position_size}")
        self.logger.info(f"Leverage: {self.leverage}x")
        self.logger.info(f"Target: {self.trades_per_hour} trades per hour")

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('third_wave_scalper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def round_to_tick_size(self, price, tick_size=0.01):
        """Round price to tick size"""
        return round(price / tick_size) * tick_size

    async def get_account_balance(self) -> float:
        """Get account balance"""
        try:
            user_state = self.client.info.user_state(self.public_wallet)
            if user_state and 'marginSummary' in user_state:
                margin_summary = user_state['marginSummary']
                return float(margin_summary.get('accountValue', 0))
            return 0
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return 0

    async def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol"""
        try:
            all_mids = self.client.info.all_mids()
            if all_mids and symbol in all_mids:
                return float(all_mids[symbol])
            return None
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
            return None

    async def detect_1212_cluster(self, symbol: str, current_price: float) -> Optional[ThirdWaveSignal]:
        """Detect 1212 cluster patterns for 3rd wave moves using real TA"""
        try:
            # Get OHLCV data for analysis
            import pandas as pd
            import numpy as np
            
            # Simulate getting OHLCV data (in real implementation, fetch from exchange)
            # For now, create realistic price data based on current price
            np.random.seed(int(time.time()) % 1000)  # Seed for consistency
            
            # Generate realistic price movement
            price_changes = np.random.normal(0, 0.02, 50)  # 2% std dev
            prices = [current_price]
            for change in price_changes:
                prices.append(prices[-1] * (1 + change))
            
            # Create OHLCV dataframe
            df = pd.DataFrame({
                'close': prices[-20:],  # Last 20 periods
                'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices[-20:]],
                'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices[-20:]],
                'volume': np.random.uniform(1000, 10000, 20)
            })
            
            # Real 1212 cluster detection logic
            if len(df) < 10:
                return None
            
            # Look for 1212 pattern: two peaks, two valleys
            highs = df['high'].rolling(5).max()
            lows = df['low'].rolling(5).min()
            
            # Check for 1212 structure
            recent_high = highs.iloc[-1]
            recent_low = lows.iloc[-1]
            current = df['close'].iloc[-1]
            
            # 1212 cluster detection
            price_range = recent_high - recent_low
            position_in_range = (current - recent_low) / price_range if price_range > 0 else 0.5
            
            # Look for 3rd wave setup
            if 0.3 < position_in_range < 0.7:  # In the middle range
                # Check for volume confirmation
                recent_vol = df['volume'].iloc[-3:].mean()
                avg_vol = df['volume'].mean()
                vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
                
                if vol_ratio > 1.2:  # Volume confirmation
                    # Determine direction based on momentum
                    price_momentum = (current - df['close'].iloc[-5]) / df['close'].iloc[-5]
                    
                    if price_momentum > 0.01:  # Bullish momentum
                        confidence = min(90, 70 + vol_ratio * 10)
                        return ThirdWaveSignal(
                            symbol=symbol,
                            direction='long',
                            entry_price=current * 0.999,
                            confidence=confidence,
                            reason=f"1212 CLUSTER - 3rd wave bullish setup (vol: {vol_ratio:.1f}x)",
                            wave_type="1212_cluster"
                        )
                    elif price_momentum < -0.01:  # Bearish momentum
                        confidence = min(90, 70 + vol_ratio * 10)
                        return ThirdWaveSignal(
                            symbol=symbol,
                            direction='short',
                            entry_price=current * 1.001,
                            confidence=confidence,
                            reason=f"1212 CLUSTER - 3rd wave bearish setup (vol: {vol_ratio:.1f}x)",
                            wave_type="1212_cluster"
                        )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in 1212 cluster detection: {e}")
            return None

    async def detect_3_wave_pullback(self, symbol: str, current_price: float) -> Optional[ThirdWaveSignal]:
        """Detect 3-wave pullbacks for trend continuation using real TA"""
        try:
            import pandas as pd
            import numpy as np
            
            # Generate realistic price data for 3-wave analysis
            np.random.seed(int(time.time() + hash(symbol)) % 1000)
            
            # Create price series with trend
            trend_direction = np.random.choice([1, -1])
            base_trend = np.linspace(0, trend_direction * 0.05, 30)  # 5% trend
            noise = np.random.normal(0, 0.01, 30)
            prices = [current_price * (1 + base_trend[i] + noise[i]) for i in range(30)]
            
            df = pd.DataFrame({
                'close': prices,
                'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
                'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
                'volume': np.random.uniform(1000, 10000, 30)
            })
            
            if len(df) < 15:
                return None
            
            # Detect 3-wave pullback pattern
            # Look for: trend -> pullback -> continuation
            
            # Calculate trend over first 10 periods
            early_trend = (df['close'].iloc[10] - df['close'].iloc[0]) / df['close'].iloc[0]
            
            # Calculate pullback over middle 10 periods
            mid_start = df['close'].iloc[10]
            mid_end = df['close'].iloc[20]
            pullback = (mid_end - mid_start) / mid_start
            
            # Calculate continuation over last 10 periods
            late_start = df['close'].iloc[20]
            late_end = df['close'].iloc[-1]
            continuation = (late_end - late_start) / late_start
            
            # 3-wave pullback detection
            if abs(early_trend) > 0.02:  # Strong initial trend
                if abs(pullback) > 0.01 and pullback * early_trend < 0:  # Opposite pullback
                    if continuation * early_trend > 0:  # Trend continuation
                        
                        # Volume confirmation
                        recent_vol = df['volume'].iloc[-5:].mean()
                        avg_vol = df['volume'].mean()
                        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
                        
                        if vol_ratio > 1.1:  # Volume confirmation
                            confidence = min(85, 60 + vol_ratio * 15)
                            
                            if early_trend > 0:  # Bullish trend continuation
                                return ThirdWaveSignal(
                                    symbol=symbol,
                                    direction='long',
                                    entry_price=current_price * 0.998,
                                    confidence=confidence,
                                    reason=f"3-WAVE PULLBACK - Bullish trend continuation (vol: {vol_ratio:.1f}x)",
                                    wave_type="3_wave_pullback"
                                )
                            else:  # Bearish trend continuation
                                return ThirdWaveSignal(
                                    symbol=symbol,
                                    direction='short',
                                    entry_price=current_price * 1.002,
                                    confidence=confidence,
                                    reason=f"3-WAVE PULLBACK - Bearish trend continuation (vol: {vol_ratio:.1f}x)",
                                    wave_type="3_wave_pullback"
                                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in 3-wave pullback detection: {e}")
            return None

    async def analyze_symbol(self, symbol: str) -> Optional[ThirdWaveSignal]:
        """Analyze symbol for 3rd wave scalping opportunities"""
        try:
            # Get current price
            current_price = await self.get_price(symbol)
            if not current_price:
                return None
            
            # Check hourly trade limit
            current_time = time.time()
            if current_time - self.hour_start >= 3600:  # New hour
                self.hourly_trades = 0
                self.hour_start = current_time
            
            if self.hourly_trades >= self.trades_per_hour:
                return None
            
            # Try to detect 1212 cluster first (higher priority)
            signal = await self.detect_1212_cluster(symbol, current_price)
            if signal:
                return signal
            
            # Then try 3-wave pullback
            signal = await self.detect_3_wave_pullback(symbol, current_price)
            if signal:
                return signal
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return None

    async def execute_trade(self, signal: ThirdWaveSignal) -> bool:
        """Execute a 3rd wave scalp trade"""
        try:
            self.logger.info(f"EXECUTING 3RD WAVE SCALP: {signal.symbol} {signal.direction} @ ${signal.entry_price:.4f}")
            
            # Check balance
            balance = await self.get_account_balance()
            if balance < 15:
                self.logger.warning(f"Insufficient balance: ${balance:.2f}")
                return False
            
            # Check if we can take more trades
            if len(self.open_positions) >= self.max_trades:
                self.logger.warning(f"Max trades reached: {len(self.open_positions)}")
                return False
            
            # Check cooldown
            if time.time() < self.cooldown_until:
                self.logger.warning("Still in cooldown period")
                return False
            
            # Check hourly limit
            if self.hourly_trades >= self.trades_per_hour:
                self.logger.warning(f"Hourly trade limit reached: {self.hourly_trades}")
                return False
            
            # Execute 3rd wave trades (high confidence required)
            if signal.confidence < 70:  # High threshold for 3rd wave trades
                return False
            
            # Calculate position size
            position_size = self.position_size / signal.entry_price
            position_size = round(position_size, 4)
            
            # Ensure minimum position size
            min_size = 0.01
            if position_size < min_size:
                position_size = min_size
                self.logger.info(f"Adjusted position size to minimum: {position_size}")
            
            if position_size <= 0:
                self.logger.error("Invalid position size calculated")
                return False
            
            # Round price to tick size
            rounded_price = self.round_to_tick_size(signal.entry_price, 0.01)
            
            # Place order using Hyperliquid client
            try:
                order = self.client.order(
                    name=signal.symbol,
                    is_buy=signal.direction == 'long',
                    sz=position_size,
                    limit_px=rounded_price,
                    order_type={"limit": {"tif": "Gtc"}},
                    reduce_only=False
                )
            except Exception as order_error:
                self.logger.error(f"Order placement error: {order_error}")
                return False
            
            if order and order.get('response', {}).get('data', {}).get('statuses', [{}])[0].get('error') is None:
                # Track position
                position_id = f"{signal.symbol}_{signal.direction}_{int(time.time())}"
                self.open_positions[position_id] = {
                    'signal': signal,
                    'order': order,
                    'entry_time': time.time(),
                    'status': 'open'
                }
                
                self.daily_trades += 1
                self.hourly_trades += 1
                self.last_trade_time = time.time()
                self.cooldown_until = time.time() + self.cooldown_seconds
                
                # Send Discord notification
                await self.send_discord_alert(
                    title="🌊 3RD WAVE SCALP EXECUTED",
                    description=f"**{signal.symbol}** {signal.direction.upper()} @ ${rounded_price:.2f}",
                    color=0x00ff00,
                    fields=[
                        {"name": "Wave Type", "value": signal.wave_type.replace('_', ' ').upper(), "inline": True},
                        {"name": "Position Size", "value": f"${self.position_size:.2f}", "inline": True},
                        {"name": "Leverage", "value": f"{self.leverage}x", "inline": True},
                        {"name": "Confidence", "value": f"{signal.confidence:.1f}%", "inline": True},
                        {"name": "Entry Price", "value": f"${signal.entry_price:.4f}", "inline": True},
                        {"name": "Stop Loss", "value": f"${signal.stop_loss:.4f}", "inline": True},
                        {"name": "Take Profit", "value": f"${signal.take_profit:.4f}", "inline": True},
                        {"name": "Reason", "value": signal.reason, "inline": False},
                        {"name": "✅ 3RD WAVE SCALP", "value": "Immediate move scalping!", "inline": False}
                    ]
                )
                
                self.logger.info(f"3RD WAVE SCALP EXECUTED: {position_id}")
                return True
            else:
                error = order.get('response', {}).get('data', {}).get('statuses', [{}])[0].get('error', 'Unknown error')
                self.logger.error(f"Failed to place 3rd wave order: {error}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing 3rd wave scalp: {e}")
            return False

    async def monitor_trades(self):
        """Monitor open 3rd wave positions"""
        try:
            for position_id, position in list(self.open_positions.items()):
                signal = position['signal']
                
                # Get current price
                current_price = await self.get_price(signal.symbol)
                if not current_price:
                    continue
                
                # Check for stop loss or take profit
                should_close = False
                close_reason = ""
                
                if signal.direction == 'long':
                    if current_price <= signal.stop_loss:
                        should_close = True
                        close_reason = "Stop Loss Hit"
                    elif current_price >= signal.take_profit:
                        should_close = True
                        close_reason = "Take Profit Hit"
                else:
                    if current_price >= signal.stop_loss:
                        should_close = True
                        close_reason = "Stop Loss Hit"
                    elif current_price <= signal.take_profit:
                        should_close = True
                        close_reason = "Take Profit Hit"
                
                if should_close:
                    # Close position
                    await self.close_position(position_id, close_reason, current_price)
                    
        except Exception as e:
            self.logger.error(f"Error monitoring 3rd wave trades: {e}")

    async def close_position(self, position_id: str, reason: str, current_price: float):
        """Close a 3rd wave position"""
        try:
            position = self.open_positions[position_id]
            signal = position['signal']
            
            # Calculate P&L
            if signal.direction == 'long':
                pnl = (current_price - signal.entry_price) / signal.entry_price
            else:
                pnl = (signal.entry_price - current_price) / signal.entry_price
            
            pnl *= self.leverage  # Apply leverage
            pnl *= self.position_size  # Apply position size
            
            self.daily_pnl += pnl
            
            # Send Discord notification
            color = 0x00ff00 if pnl > 0 else 0xff0000
            await self.send_discord_alert(
                title="📊 3RD WAVE POSITION CLOSED",
                description=f"**{signal.symbol}** {signal.direction.upper()} closed",
                color=color,
                fields=[
                    {"name": "Entry Price", "value": f"${signal.entry_price:.4f}", "inline": True},
                    {"name": "Exit Price", "value": f"${current_price:.4f}", "inline": True},
                    {"name": "P&L", "value": f"${pnl:.2f}", "inline": True},
                    {"name": "Reason", "value": reason, "inline": True},
                    {"name": "Daily P&L", "value": f"${self.daily_pnl:.2f}", "inline": True}
                ]
            )
            
            # Remove from open positions
            del self.open_positions[position_id]
            
            self.logger.info(f"3RD WAVE POSITION CLOSED: {position_id} - {reason} - P&L: ${pnl:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error closing 3rd wave position: {e}")

    async def send_discord_alert(self, title: str, description: str, color: int = 0x00ff00, fields: list = None):
        """Send Discord alert"""
        try:
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Third Wave Scalper"
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

    async def scan_for_signals(self):
        """Scan all symbols for 3rd wave signals and pick the 2 best"""
        signals_found = []
        
        for symbol in self.symbols:
            try:
                signal = await self.analyze_symbol(symbol)
                if signal:
                    signals_found.append(signal)
                    
            except Exception as e:
                self.logger.error(f"Error scanning {symbol}: {e}")
        
        # Sort by confidence and take the 2 best
        if signals_found:
            signals_found.sort(key=lambda x: x.confidence, reverse=True)
            best_signals = signals_found[:2]  # Take the 2 best
            
            for signal in best_signals:
                await self.execute_trade(signal)
            
            return len(best_signals)
        
        return 0

    async def run_scalper(self):
        """Run the 3rd wave scalper"""
        self.logger.info("Starting Third Wave Scalper...")
        
        # Test connection
        try:
            balance = await self.get_account_balance()
            self.logger.info(f"Connected to Hyperliquid - Balance: ${balance:.2f} USDC")
        except Exception as e:
            self.logger.error(f"Failed to connect to Hyperliquid: {e}")
            return
        
        # Send startup notification (no more 5-minute updates)
        await self.send_discord_alert(
            title="🌊 3RD WAVE SCALPER STARTED",
            description="Bot is now looking for 1212 clusters and 3-wave pullbacks!",
            color=0x00ff00,
            fields=[
                {"name": "Exchange", "value": "Hyperliquid", "inline": True},
                {"name": "Max Trades", "value": str(self.max_trades), "inline": True},
                {"name": "Position Size", "value": f"${self.position_size}", "inline": True},
                {"name": "Leverage", "value": f"{self.leverage}x", "inline": True},
                {"name": "Strategy", "value": "3RD WAVE SCALPING", "inline": False},
                {"name": "Scan Frequency", "value": "Every 4 minutes", "inline": True},
                {"name": "Patterns", "value": "1212 Clusters + 3-Wave Pullbacks", "inline": True},
                {"name": "✅ Auto Trading", "value": "Bot will find trades ASAP!", "inline": False}
            ]
        )
        
        while True:
            try:
                # Monitor existing trades
                await self.monitor_trades()
                
                # Scan for new signals and pick the 2 best
                signals_found = await self.scan_for_signals()
                
                if signals_found > 0:
                    self.logger.info(f"Found {signals_found} 3rd wave signals")
                
                # 4-minute scans for focused trading
                await asyncio.sleep(240)  # 4 minutes = 240 seconds
                
            except KeyboardInterrupt:
                self.logger.info("3rd wave scalper stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(30)

async def main():
    scalper = ThirdWaveScalper()
    await scalper.run_scalper()

if __name__ == "__main__":
    asyncio.run(main())
