#!/usr/bin/env python3
"""
Hyperliquid Configuration
US-friendly decentralized exchange
"""

# Hyperliquid API Configuration
HYPERLIQUID_CONFIG = {
    'private_key': '0x0a5cfa8aeb7988073fa18623baa7a77beb6036c3202cb33e00520fb3396b7f35',
    'api_wallet': '0x40D0e1B66dAB8B61a2148467eE14cd01dC1F69Be',
    'public_wallet': '0x7aAE0f6B20a7D19DB6914bE9dad486Be5643eD6C',
    'baseUrl': 'https://api.hyperliquid.xyz',
    'sandbox': False,
    'enableRateLimit': True,
}

# Trading Configuration
HYPERLIQUID_TRADING_CONFIG = {
    'max_risk_per_trade': 0.05,
    'max_daily_loss': 0.10,
    'max_open_positions': 3,
    'base_position_size': 10.0,  # $10 per trade
    'max_position_size': 10.0,
    'default_leverage': 15,
    'max_leverage': 20,
    'symbol_leverage': {
        'SOL': 15,
        'ETH': 15,
        'BTC': 15,
        'DEFAULT': 15
    },
    'trading_fee': 0.0002,  # 0.02% - very low fees
    'slippage_tolerance': 0.001,
    'max_daily_trades': 20,
    'emergency_stop_loss': 0.05,
}

# Live Trading Configuration
HYPERLIQUID_LIVE_CONFIG = {
    'enabled': True,
    'max_position_size': 10.0,
    'min_position_size': 10.0,
    'trading_fee': 0.0002,
    'slippage_tolerance': 0.001,
    'max_daily_trades': 20,
    'emergency_stop_loss': 0.05,
}

# Notification Configuration
HYPERLIQUID_NOTIFICATION_CONFIG = {
    'discord_webhook': '',
    'trade_alerts': True,
    'error_alerts': True,
    'balance_alerts': True,
}

# Analysis Configuration
HYPERLIQUID_ANALYSIS_CONFIG = {
    'volume_spike_threshold': 2.0,
    'min_volume_usdt': 100000,
    'price_change_threshold': 0.02,
    'volatility_threshold': 0.05,
    'rsi_period': 14,
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'atr_period': 14,
    'atr_multiplier': 2.0,
}

# Symbols to trade on Hyperliquid
HYPERLIQUID_SYMBOLS = [
    'SOL', 'ETH', 'BTC', 'AVAX',
    'LINK', 'UNI', 'AAVE', 'SUSHI'
]

def get_symbol_leverage(symbol: str) -> int:
    """Get leverage for a specific symbol"""
    return HYPERLIQUID_TRADING_CONFIG['symbol_leverage'].get(symbol, HYPERLIQUID_TRADING_CONFIG['default_leverage'])

def get_symbol_config(symbol: str) -> dict:
    """Get configuration for a specific symbol"""
    return {
        'leverage': get_symbol_leverage(symbol),
        'max_position_size': HYPERLIQUID_TRADING_CONFIG['max_position_size'],
        'min_position_size': HYPERLIQUID_TRADING_CONFIG['min_position_size'],
        'trading_fee': HYPERLIQUID_TRADING_CONFIG['trading_fee'],
    }
