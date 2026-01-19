#!/usr/bin/env python3
"""
Trading System Integration for Enhanced MM Detector
Handles position management, risk management, and trade execution
"""
import time
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np

@dataclass
class Position:
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profits: List[float]
    position_size: float
    leverage: int
    entry_time: float
    max_loss: float
    max_gain: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    status: str = "OPEN"  # OPEN, CLOSED, STOPPED

@dataclass
class TradeResult:
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    position_size: float
    leverage: int
    pnl: float
    pnl_percent: float
    duration: float
    exit_reason: str
    entry_time: float
    exit_time: float

class TradingSystem:
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[TradeResult] = []
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        self.setup_logging()
        
        # Risk management
        self.max_risk_per_trade = 0.10  # 10% max risk per trade
        self.max_daily_loss = 0.15  # 15% max daily loss
        self.max_open_positions = 5
        self.position_size = 1000.0  # $1000 per trade
        
        # Leverage limits
        self.leverage_limits = {
            'BTC': 20,
            'ETH': 10,
            'SOL': 10,
            'DEFAULT': 10
        }

    def setup_logging(self):
        """Setup logging for trading system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trading_system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def can_open_position(self, symbol: str) -> bool:
        """Check if we can open a new position"""
        if len(self.positions) >= self.max_open_positions:
            return False
        
        if symbol in self.positions:
            return False
        
        if self.balance < self.position_size:
            return False
        
        # Check daily loss limit
        if self.daily_pnl <= -self.initial_balance * self.max_daily_loss:
            return False
        
        return True

    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> Tuple[float, int]:
        """Calculate optimal position size and leverage"""
        if entry_price <= 0 or stop_loss <= 0:
            return 0, 1
        
        # Get leverage limit for symbol
        base_symbol = symbol.split('/')[0].upper()
        max_leverage = self.leverage_limits.get(base_symbol, self.leverage_limits['DEFAULT'])
        
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit <= 0:
            return 0, 1
        
        # Calculate position size based on risk
        max_risk_amount = self.balance * self.max_risk_per_trade
        position_value = max_risk_amount / risk_per_unit
        
        # Apply leverage
        leverage = min(max_leverage, int(position_value / self.position_size)) if position_value > 0 else 1
        position_size = min(self.position_size * leverage, position_value)
        
        return position_size, leverage

    def open_position(self, symbol: str, direction: str, entry_price: float, 
                     stop_loss: float, take_profits: List[float], 
                     mm_confidence: float, setup_reason: str) -> bool:
        """Open a new position"""
        if not self.can_open_position(symbol):
            return False
        
        # Calculate position parameters
        position_size, leverage = self.calculate_position_size(symbol, entry_price, stop_loss)
        
        if position_size <= 0:
            return False
        
        # Calculate max loss and gain
        max_loss = abs(entry_price - stop_loss) * position_size / entry_price
        max_gain = abs(take_profits[1] - entry_price) * position_size / entry_price if len(take_profits) > 1 else 0
        
        # Create position
        position = Position(
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profits=take_profits,
            position_size=position_size,
            leverage=leverage,
            entry_time=time.time(),
            max_loss=max_loss,
            max_gain=max_gain,
            current_price=entry_price
        )
        
        # Deduct from balance
        self.balance -= position_size
        self.positions[symbol] = position
        
        self.logger.info(f"Position opened: {symbol} {direction} at {entry_price:.4f} "
                        f"(Size: ${position_size:.2f}, Leverage: {leverage}x)")
        
        return True

    def update_positions(self, current_prices: Dict[str, float]) -> List[TradeResult]:
        """Update all positions with current prices and check exit conditions"""
        closed_trades = []
        
        for symbol, position in list(self.positions.items()):
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            position.current_price = current_price
            
            # Calculate unrealized P&L
            position.unrealized_pnl = self.calculate_pnl(position, current_price)
            
            # Check exit conditions
            exit_result = self.check_exit_conditions(position, current_price)
            if exit_result:
                closed_trades.append(exit_result)
                self.close_position(symbol, current_price, exit_result['reason'])
        
        return closed_trades

    def check_exit_conditions(self, position: Position, current_price: float) -> Optional[dict]:
        """Check if position should be closed"""
        entry_price = position.entry_price
        stop_loss = position.stop_loss
        take_profits = position.take_profits
        direction = position.direction
        
        # Check stop loss
        if direction == "LONG" and current_price <= stop_loss:
            return {
                'reason': 'Stop Loss',
                'exit_price': current_price,
                'pnl': self.calculate_pnl(position, current_price)
            }
        elif direction == "SHORT" and current_price >= stop_loss:
            return {
                'reason': 'Stop Loss',
                'exit_price': current_price,
                'pnl': self.calculate_pnl(position, current_price)
            }
        
        # Check take profits
        for i, tp in enumerate(take_profits):
            if direction == "LONG" and current_price >= tp:
                return {
                    'reason': f'Take Profit {i+1}',
                    'exit_price': current_price,
                    'pnl': self.calculate_pnl(position, current_price)
                }
            elif direction == "SHORT" and current_price <= tp:
                return {
                    'reason': f'Take Profit {i+1}',
                    'exit_price': current_price,
                    'pnl': self.calculate_pnl(position, current_price)
                }
        
        return None

    def close_position(self, symbol: str, exit_price: float, reason: str) -> TradeResult:
        """Close a position and record the trade"""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        
        # Calculate P&L
        pnl = self.calculate_pnl(position, exit_price)
        pnl_percent = (pnl / position.position_size) * 100
        
        # Calculate duration
        duration = time.time() - position.entry_time
        
        # Create trade result
        trade_result = TradeResult(
            symbol=symbol,
            direction=position.direction,
            entry_price=position.entry_price,
            exit_price=exit_price,
            position_size=position.position_size,
            leverage=position.leverage,
            pnl=pnl,
            pnl_percent=pnl_percent,
            duration=duration,
            exit_reason=reason,
            entry_time=position.entry_time,
            exit_time=time.time()
        )
        
        # Update balance
        self.balance += position.position_size + pnl
        self.daily_pnl += pnl
        
        # Update max drawdown
        current_balance = self.balance
        if current_balance < self.initial_balance:
            drawdown = (self.initial_balance - current_balance) / self.initial_balance
            self.max_drawdown = max(self.max_drawdown, drawdown)
        
        # Record trade
        self.trade_history.append(trade_result)
        
        # Remove position
        del self.positions[symbol]
        
        self.logger.info(f"Position closed: {symbol} {position.direction} at {exit_price:.4f} "
                        f"(P&L: ${pnl:.2f}, {pnl_percent:.2f}%, Reason: {reason})")
        
        return trade_result

    def calculate_pnl(self, position: Position, current_price: float) -> float:
        """Calculate P&L for a position"""
        entry_price = position.entry_price
        position_size = position.position_size
        leverage = position.leverage
        direction = position.direction
        
        if direction == "LONG":
            pnl = (current_price - entry_price) / entry_price * position_size * leverage
        else:
            pnl = (entry_price - current_price) / entry_price * position_size * leverage
        
        return pnl

    def get_portfolio_summary(self) -> dict:
        """Get current portfolio summary"""
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_balance = self.balance + total_unrealized_pnl
        
        return {
            "balance": self.balance,
            "unrealized_pnl": total_unrealized_pnl,
            "total_balance": total_balance,
            "daily_pnl": self.daily_pnl,
            "max_drawdown": self.max_drawdown,
            "open_positions": len(self.positions),
            "total_trades": len(self.trade_history),
            "win_rate": self.calculate_win_rate(),
            "avg_pnl": self.calculate_avg_pnl()
        }

    def calculate_win_rate(self) -> float:
        """Calculate win rate percentage"""
        if not self.trade_history:
            return 0.0
        
        winning_trades = sum(1 for trade in self.trade_history if trade.pnl > 0)
        return (winning_trades / len(self.trade_history)) * 100

    def calculate_avg_pnl(self) -> float:
        """Calculate average P&L per trade"""
        if not self.trade_history:
            return 0.0
        
        total_pnl = sum(trade.pnl for trade in self.trade_history)
        return total_pnl / len(self.trade_history)

    def get_position_details(self, symbol: str) -> Optional[dict]:
        """Get detailed position information"""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        return {
            "symbol": position.symbol,
            "direction": position.direction,
            "entry_price": position.entry_price,
            "current_price": position.current_price,
            "stop_loss": position.stop_loss,
            "take_profits": position.take_profits,
            "position_size": position.position_size,
            "leverage": position.leverage,
            "unrealized_pnl": position.unrealized_pnl,
            "unrealized_pnl_percent": (position.unrealized_pnl / position.position_size) * 100,
            "entry_time": datetime.fromtimestamp(position.entry_time).isoformat(),
            "duration": time.time() - position.entry_time
        }

    def save_state(self, filename: str = "trading_state.json"):
        """Save trading system state to file"""
        state = {
            "balance": self.balance,
            "daily_pnl": self.daily_pnl,
            "max_drawdown": self.max_drawdown,
            "positions": {symbol: asdict(pos) for symbol, pos in self.positions.items()},
            "trade_history": [asdict(trade) for trade in self.trade_history[-100:]]  # Keep last 100 trades
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
        
        self.logger.info(f"Trading state saved to {filename}")

    def load_state(self, filename: str = "trading_state.json"):
        """Load trading system state from file"""
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            
            self.balance = state.get("balance", self.initial_balance)
            self.daily_pnl = state.get("daily_pnl", 0.0)
            self.max_drawdown = state.get("max_drawdown", 0.0)
            
            # Load positions
            self.positions = {}
            for symbol, pos_data in state.get("positions", {}).items():
                self.positions[symbol] = Position(**pos_data)
            
            # Load trade history
            self.trade_history = []
            for trade_data in state.get("trade_history", []):
                self.trade_history.append(TradeResult(**trade_data))
            
            self.logger.info(f"Trading state loaded from {filename}")
            
        except FileNotFoundError:
            self.logger.info(f"No existing state file found, starting fresh")
        except Exception as e:
            self.logger.error(f"Error loading state: {e}")

    def reset_daily_pnl(self):
        """Reset daily P&L (call at start of new day)"""
        self.daily_pnl = 0.0
        self.logger.info("Daily P&L reset")

    def get_trading_cards(self) -> List[dict]:
        """Get trading cards for all open positions"""
        cards = []
        
        for symbol, position in self.positions.items():
            card = {
                "symbol": position.symbol,
                "direction": position.direction,
                "entry_price": position.entry_price,
                "current_price": position.current_price,
                "stop_loss": position.stop_loss,
                "take_profits": position.take_profits,
                "position_size": position.position_size,
                "leverage": position.leverage,
                "unrealized_pnl": position.unrealized_pnl,
                "unrealized_pnl_percent": (position.unrealized_pnl / position.position_size) * 100,
                "entry_time": datetime.fromtimestamp(position.entry_time).isoformat(),
                "duration_hours": (time.time() - position.entry_time) / 3600,
                "status": position.status
            }
            cards.append(card)
        
        return cards

