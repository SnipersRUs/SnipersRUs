#!/usr/bin/env python3
"""
Trade Structure Logger - Log the exact trade setups from charts
"""

import json
import time
from datetime import datetime
from typing import Dict, List

class TradeStructureLogger:
    def __init__(self):
        self.trades_file = "logged_trades.json"
        self.trades = self.load_trades()
    
    def load_trades(self) -> List[Dict]:
        """Load existing trades from file"""
        try:
            with open(self.trades_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_trades(self):
        """Save trades to file"""
        with open(self.trades_file, 'w') as f:
            json.dump(self.trades, f, indent=2)
    
    def log_trade(self, symbol: str, direction: str, entry_price: float, 
                  stop_loss: float, take_profit: float, reason: str, 
                  risk_reward_ratio: float = None, confidence: float = None):
        """Log a trade structure"""
        trade = {
            "id": len(self.trades) + 1,
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward_ratio": risk_reward_ratio,
            "confidence": confidence,
            "reason": reason,
            "status": "logged"
        }
        
        self.trades.append(trade)
        self.save_trades()
        
        print(f"✅ TRADE LOGGED:")
        print(f"  Symbol: {symbol}")
        print(f"  Direction: {direction.upper()}")
        print(f"  Entry: ${entry_price:.4f}")
        print(f"  Stop Loss: ${stop_loss:.4f}")
        print(f"  Take Profit: ${take_profit:.4f}")
        if risk_reward_ratio:
            print(f"  Risk/Reward: {risk_reward_ratio:.1f}")
        if confidence:
            print(f"  Confidence: {confidence:.1f}%")
        print(f"  Reason: {reason}")
        print()
    
    def get_trades(self) -> List[Dict]:
        """Get all logged trades"""
        return self.trades
    
    def get_trades_by_symbol(self, symbol: str) -> List[Dict]:
        """Get trades for specific symbol"""
        return [trade for trade in self.trades if trade['symbol'] == symbol]
    
    def get_recent_trades(self, count: int = 10) -> List[Dict]:
        """Get recent trades"""
        return self.trades[-count:] if self.trades else []

# Log the trades from your charts
logger = TradeStructureLogger()

print("📊 LOGGING TRADE STRUCTURES FROM YOUR CHARTS...")
print()

# ATOM/USDT Trade from your chart
logger.log_trade(
    symbol="ATOM",
    direction="long",
    entry_price=4.576,
    stop_loss=4.546,
    take_profit=4.762,
    risk_reward_ratio=6.2,
    confidence=85.0,
    reason="Golden Pocket Zone - Price pullback to support, strong bullish momentum, 6.2 R/R ratio"
)

# SOL/USDT Trade from your chart  
logger.log_trade(
    symbol="SOL",
    direction="long", 
    entry_price=240.15,
    stop_loss=238.67,
    take_profit=250.45,
    risk_reward_ratio=4.1,
    confidence=80.0,
    reason="Golden Pocket Zone - Support bounce, trend continuation, breakout retest"
)

print(f"📈 Total trades logged: {len(logger.get_trades())}")
print("✅ Trade structures saved to logged_trades.json")























































