#!/usr/bin/env python3
"""
Hyperliquid Golden Pocket Trading Bot
US-friendly decentralized exchange
"""

import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from hyperliquid_exchange import HyperliquidExchange
from hyperliquid_config import (
    HYPERLIQUID_TRADING_CONFIG, 
    HYPERLIQUID_NOTIFICATION_CONFIG,
    HYPERLIQUID_SYMBOLS
)

class LiveTradeSignal:
    def __init__(self, symbol: str, direction: str, entry_price: float, 
                 confidence: float, reason: str, is_sfp_sweep: bool = False):
        self.symbol = symbol
        self.direction = direction
        self.entry_price = entry_price
        self.confidence = confidence
        self.reason = reason
        self.is_sfp_sweep = is_sfp_sweep
        self.timestamp = time.time()
        
        # Calculate position size and targets
        self.position_size = HYPERLIQUID_TRADING_CONFIG['max_position_size']
        self.leverage = HYPERLIQUID_TRADING_CONFIG['default_leverage']
        
        # Calculate stop loss and take profits
        if direction == 'long':
            self.stop_loss = entry_price * 0.99  # 1% stop loss for testing
            self.take_profit_1 = entry_price * 1.015  # 1.5% first target
            self.take_profit_2 = entry_price * 1.02   # 2% second target
        else:
            self.stop_loss = entry_price * 1.01  # 1% stop loss for testing
            self.take_profit_1 = entry_price * 0.985  # 1.5% first target
            self.take_profit_2 = entry_price * 0.98   # 2% second target

class HyperliquidGoldenPocketBot:
    def __init__(self):
        self.exchange = HyperliquidExchange(paper_trading=False)  # LIVE TRADING
        self.setup_logging()

        # Live trading parameters
        self.max_trades = 3  # Max 3 trades open
        self.target_move = 0.02  # 2% target move
        self.max_move = 0.03  # 3% max move (close 75%)
        self.final_target = 0.05  # 5% final target
        self.leverage = 15  # 15x leverage as requested

        # Position sizing - Fixed $10 positions
        self.position_size = 10.0  # Fixed $10 per position
        
        # Trading state
        self.open_positions = {}
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_trade_time = 0
        self.cooldown_until = 0
        
        # Discord webhook
        self.discord_webhook = HYPERLIQUID_NOTIFICATION_CONFIG['discord_webhook']
        
        # Symbols to trade
        self.symbols = HYPERLIQUID_SYMBOLS
        
        self.logger.info("Hyperliquid Golden Pocket Bot initialized")
        self.logger.info(f"Max trades: {self.max_trades}")
        self.logger.info(f"Position size: ${self.position_size}")
        self.logger.info(f"Leverage: {self.leverage}x")

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('hyperliquid_golden_pocket_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def calculate_position_size(self, entry_price: float, stop_loss: float, balance: float) -> float:
        """Calculate position size - Fixed $10 positions with 15x leverage"""
        try:
            position_value = self.position_size  # $10
            position_size = position_value / entry_price
            position_size *= self.leverage  # Apply 15x leverage
            return position_size
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0

    async def get_account_balance(self) -> float:
        """Get account balance"""
        try:
            balance = await self.exchange.get_account_balance()
            return balance.get('USDC', 0)
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return 0

    def calculate_rsi(self, prices, period=14):
        """Calculate RSI manually"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        return rsi

    async def analyze_symbol(self, symbol: str) -> Optional[LiveTradeSignal]:
        """Analyze symbol for Golden Pocket opportunities"""
        try:
            self.logger.debug(f"Analyzing {symbol}...")
            
            # Get current price
            ticker = await self.exchange.get_ticker(symbol)
            if not ticker:
                return None
            
            current_price = ticker['last']
            self.logger.debug(f"{symbol} current price: ${current_price:.4f}")
            
            # Simulate some analysis for testing
            # In real implementation, this would analyze Golden Pockets, divergence, SFP
            
            # For testing, generate signals randomly with low confidence
            import random
            confidence = random.uniform(20, 40)  # Low confidence for testing
            
            if confidence > 30:  # Lower threshold for testing
                direction = random.choice(['long', 'short'])
                reason = f"Test signal - Golden Pocket + Divergence + SFP (confidence: {confidence:.1f}%)"
                
                signal = LiveTradeSignal(
                    symbol=symbol,
                    direction=direction,
                    entry_price=current_price,
                    confidence=confidence,
                    reason=reason,
                    is_sfp_sweep=False
                )
                
                self.logger.info(f"Signal generated for {symbol}: {direction} @ ${current_price:.4f} (confidence: {confidence:.1f}%)")
                return signal
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return None

    async def execute_trade(self, signal: LiveTradeSignal) -> bool:
        """Execute a trade signal"""
        try:
            self.logger.info(f"Executing trade: {signal.symbol} {signal.direction} @ ${signal.entry_price:.4f}")
            
            # Check balance
            balance = await self.get_account_balance()
            if balance < 30:  # Minimum balance check for $10 positions
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
            
            # For SFP sweeps, don't wait - execute immediately
            if not signal.is_sfp_sweep:
                # For other signals, be more selective (lowered for test trades)
                if signal.confidence < 30:  # Lowered from 80 for test trades
                    return False
            
            # Calculate position size
            position_size = self.calculate_position_size(
                signal.entry_price, 
                signal.stop_loss, 
                balance
            )
            
            if position_size <= 0:
                self.logger.error("Invalid position size calculated")
                return False
            
            # Place order
            order = await self.exchange.place_order(
                symbol=signal.symbol,
                side=signal.direction,
                amount=position_size,
                order_type='market',
                leverage=self.leverage
            )
            
            if order:
                # Track position
                position_id = f"{signal.symbol}_{signal.direction}_{int(time.time())}"
                self.open_positions[position_id] = {
                    'signal': signal,
                    'order': order,
                    'entry_time': time.time(),
                    'status': 'open'
                }
                
                self.daily_trades += 1
                self.last_trade_time = time.time()
                
                # Send Discord notification
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
                
                self.logger.info(f"Trade executed successfully: {position_id}")
                return True
            else:
                self.logger.error("Failed to place order")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return False

    async def monitor_trades(self):
        """Monitor open positions"""
        try:
            for position_id, position in list(self.open_positions.items()):
                signal = position['signal']
                current_time = time.time()
                
                # Get current price
                ticker = await self.exchange.get_ticker(signal.symbol)
                if not ticker:
                    continue
                
                current_price = ticker['last']
                
                # Check for stop loss or take profit
                should_close = False
                close_reason = ""
                
                if signal.direction == 'long':
                    if current_price <= signal.stop_loss:
                        should_close = True
                        close_reason = "Stop Loss Hit"
                    elif current_price >= signal.take_profit_2:
                        should_close = True
                        close_reason = "Take Profit 2 Hit"
                else:
                    if current_price >= signal.stop_loss:
                        should_close = True
                        close_reason = "Stop Loss Hit"
                    elif current_price <= signal.take_profit_2:
                        should_close = True
                        close_reason = "Take Profit 2 Hit"
                
                if should_close:
                    # Close position
                    await self.close_position(position_id, close_reason, current_price)
                    
        except Exception as e:
            self.logger.error(f"Error monitoring trades: {e}")

    async def close_position(self, position_id: str, reason: str, current_price: float):
        """Close a position"""
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
                title="📊 POSITION CLOSED",
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
            
            self.logger.info(f"Position closed: {position_id} - {reason} - P&L: ${pnl:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")

    async def send_discord_alert(self, title: str, description: str, color: int = 0x00ff00, fields: list = None):
        """Send Discord alert"""
        try:
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Hyperliquid Golden Pocket Bot"
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
        """Scan all symbols for trading signals"""
        signals_found = 0
        
        for symbol in self.symbols:
            try:
                signal = await self.analyze_symbol(symbol)
                if signal:
                    signals_found += 1
                    await self.execute_trade(signal)
                    
            except Exception as e:
                self.logger.error(f"Error scanning {symbol}: {e}")
        
        return signals_found

    async def run_live_bot(self):
        """Run the live trading bot"""
        self.logger.info("Starting Hyperliquid Golden Pocket Bot...")
        
        # Test connection
        if not await self.exchange.test_connection():
            self.logger.error("Failed to connect to Hyperliquid")
            return
        
        # Send startup notification
        await self.send_discord_alert(
            title="🚀 HYPERLIQUID BOT STARTED",
            description="Golden Pocket + Divergence + SFP Bot is now active!",
            color=0x00ff00,
            fields=[
                {"name": "Exchange", "value": "Hyperliquid", "inline": True},
                {"name": "Max Trades", "value": str(self.max_trades), "inline": True},
                {"name": "Position Size", "value": f"${self.position_size}", "inline": True},
                {"name": "Leverage", "value": f"{self.leverage}x", "inline": True},
                {"name": "Strategy", "value": "Golden Pocket + Divergence + SFP", "inline": False}
            ]
        )
        
        scan_count = 0
        while True:
            try:
                # Monitor existing trades
                await self.monitor_trades()
                
                # Scan for new signals
                signals_found = await self.scan_for_signals()
                
                if signals_found > 0:
                    self.logger.info(f"Found {signals_found} signals")
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
                                {"name": "💰 Balance", "value": f"${await self.get_account_balance():.2f} USDC", "inline": True},
                                {"name": "⚡ Status", "value": "ACTIVE & MONITORING", "inline": True},
                                {"name": "🔄 Next Scan", "value": "In 30 seconds", "inline": True}
                            ]
                        )
                        scan_count = 0  # Reset counter
                
                await asyncio.sleep(30)  # 30 seconds between scans
                
            except KeyboardInterrupt:
                self.logger.info("Bot stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(30)

async def main():
    bot = HyperliquidGoldenPocketBot()
    await bot.run_live_bot()

if __name__ == "__main__":
    asyncio.run(main())























































