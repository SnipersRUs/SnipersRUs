#!/usr/bin/env python3
"""
Bybit Configuration
High-performance trading bot configuration for Bybit
"""

import os

# Bybit API Configuration
BYBIT_CONFIG = {
    'api_key': os.getenv('BYBIT_API_KEY', ''),
    'api_secret': os.getenv('BYBIT_API_SECRET', ''),
    'testnet': os.getenv('BYBIT_TESTNET', 'true').lower() == 'true',
    'base_url': 'https://api.bybit.com',
    'testnet_url': 'https://api-testnet.bybit.com',
    'enable_rate_limit': True,
    'rate_limit_per_second': 10,
}

# Trading Configuration
BYBIT_TRADING_CONFIG = {
    'max_risk_per_trade': 0.02,  # 2% risk per trade
    'max_daily_loss': 0.05,      # 5% max daily loss
    'max_open_positions': 3,     # Max 3 concurrent positions
    'base_position_size': 10.0,  # $10 base position size
    'max_position_size': 50.0,   # $50 max position size
    'default_leverage': 10,      # 10x default leverage
    'max_leverage': 20,          # 20x max leverage
    'trading_fee': 0.0006,       # 0.06% trading fee
    'slippage_tolerance': 0.001, # 0.1% slippage tolerance
    'max_daily_trades': 20,      # Max 20 trades per day
    'emergency_stop_loss': 0.05, # 5% emergency stop loss
}

# Live Trading Configuration
BYBIT_LIVE_CONFIG = {
    'enabled': os.getenv('BYBIT_LIVE_TRADING', 'false').lower() == 'true',
    'max_position_size': 50.0,
    'min_position_size': 10.0,
    'trading_fee': 0.0006,
    'slippage_tolerance': 0.001,
    'max_daily_trades': 20,
    'emergency_stop_loss': 0.05,
    'paper_trading': os.getenv('BYBIT_PAPER_TRADING', 'true').lower() == 'true',
}

# Notification Configuration
BYBIT_NOTIFICATION_CONFIG = {
    'discord_webhook': os.getenv('DISCORD_WEBHOOK', ''),
    'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
    'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
    'trade_alerts': True,
    'error_alerts': True,
    'balance_alerts': True,
    'daily_summary': True,
}

# Analysis Configuration
BYBIT_ANALYSIS_CONFIG = {
    'volume_spike_threshold': 2.0,    # 2x volume spike
    'min_volume_usdt': 1000000,       # $1M minimum volume
    'price_change_threshold': 0.02,   # 2% price change threshold
    'volatility_threshold': 0.05,     # 5% volatility threshold
    'rsi_period': 14,                 # RSI period
    'rsi_oversold': 30,               # RSI oversold level
    'rsi_overbought': 70,             # RSI overbought level
    'atr_period': 14,                 # ATR period
    'atr_multiplier': 2.0,            # ATR multiplier for stops
    'golden_pocket_levels': [0.618, 0.65],  # Golden pocket retracement levels
    'divergence_threshold': 0.1,      # Divergence detection threshold
}

# Symbols to trade on Bybit
BYBIT_SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'AVAXUSDT', 
    'LINKUSDT', 'UNIUSDT', 'AAVEUSDT', 'SUSHIUSDT',
    'MATICUSDT', 'DOTUSDT', 'ATOMUSDT', 'NEARUSDT',
    'FTMUSDT', 'ALGOUSDT', 'VETUSDT', 'SUIUSDT'
]

# Symbol-specific leverage settings
SYMBOL_LEVERAGE = {
    'BTCUSDT': 10,
    'ETHUSDT': 10,
    'SOLUSDT': 15,
    'AVAXUSDT': 15,
    'LINKUSDT': 15,
    'UNIUSDT': 15,
    'AAVEUSDT': 15,
    'SUSHIUSDT': 15,
    'MATICUSDT': 15,
    'DOTUSDT': 15,
    'ATOMUSDT': 15,
    'NEARUSDT': 15,
    'FTMUSDT': 15,
    'ALGOUSDT': 15,
    'VETUSDT': 15,
    'SUIUSDT': 15,
    'DEFAULT': 10
}

# Risk Management Configuration
RISK_MANAGEMENT = {
    'max_drawdown': 0.10,           # 10% max drawdown
    'daily_loss_limit': 0.05,       # 5% daily loss limit
    'position_size_method': 'fixed', # 'fixed', 'percentage', 'kelly'
    'stop_loss_method': 'atr',      # 'atr', 'percentage', 'support_resistance'
    'take_profit_method': 'risk_reward', # 'risk_reward', 'resistance', 'trailing'
    'risk_reward_ratio': 2.0,       # 1:2 risk reward ratio
    'trailing_stop_distance': 0.02,  # 2% trailing stop distance
}

# Strategy Configuration
STRATEGY_CONFIG = {
    'strategy_name': 'golden_pocket_scalper',
    'timeframe': '1m',              # 1-minute timeframe
    'scan_interval': 60,            # 60 seconds between scans
    'max_signals_per_hour': 5,      # Max 5 signals per hour
    'signal_cooldown': 300,         # 5 minutes between signals for same symbol
    'entry_conditions': {
        'golden_pocket': True,      # Golden pocket retracement
        'divergence': True,         # RSI divergence
        'volume_spike': True,       # Volume confirmation
        'liquidity_sweep': True,    # Liquidity sweep detection
    },
    'exit_conditions': {
        'take_profit_1': 0.02,      # 2% first take profit
        'take_profit_2': 0.05,      # 5% second take profit
        'stop_loss': 0.01,          # 1% stop loss
        'trailing_stop': True,      # Enable trailing stop
    }
}

def get_symbol_leverage(symbol: str) -> int:
    """Get leverage for a specific symbol"""
    return SYMBOL_LEVERAGE.get(symbol, SYMBOL_LEVERAGE['DEFAULT'])

def get_trading_symbols() -> list:
    """Get list of trading symbols"""
    return BYBIT_SYMBOLS

def is_live_trading_enabled() -> bool:
    """Check if live trading is enabled"""
    return BYBIT_LIVE_CONFIG['enabled'] and not BYBIT_LIVE_CONFIG['paper_trading']

def get_position_size(symbol: str, account_balance: float) -> float:
    """Calculate position size based on risk management"""
    risk_amount = account_balance * BYBIT_TRADING_CONFIG['max_risk_per_trade']
    stop_loss_pct = STRATEGY_CONFIG['exit_conditions']['stop_loss']
    
    # Calculate position size based on risk
    position_size = risk_amount / stop_loss_pct
    
    # Apply limits
    max_size = BYBIT_TRADING_CONFIG['max_position_size']
    min_size = BYBIT_TRADING_CONFIG['min_position_size']
    
    return max(min_size, min(position_size, max_size))

def validate_config() -> bool:
    """Validate configuration"""
    if not BYBIT_CONFIG['api_key'] or not BYBIT_CONFIG['api_secret']:
        print("❌ Bybit API credentials not set")
        return False
    
    if BYBIT_TRADING_CONFIG['max_risk_per_trade'] > 0.05:
        print("⚠️  Warning: Risk per trade is high (>5%)")
    
    if BYBIT_TRADING_CONFIG['max_leverage'] > 20:
        print("⚠️  Warning: Maximum leverage is very high (>20x)")
    
    print("✅ Configuration validated")
    return True
