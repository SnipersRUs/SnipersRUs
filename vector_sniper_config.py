#!/usr/bin/env python3
"""
Vector Sniper Pro Configuration
Configuration settings for the Vector Sniper Pro scanner
"""

# Discord Configuration
DISCORD_WEBHOOK = ""

# Exchange Configuration
EXCHANGES = {
    'mexc': {
        'name': 'MEXC',
        'primary': True,  # Primary trading exchange
        'rate_limit': 1000,
        'symbols_limit': 50
    },
    'bybit': {
        'name': 'Bybit',
        'primary': False,
        'rate_limit': 1000,
        'symbols_limit': 50
    },
    'binance': {
        'name': 'Binance',
        'primary': False,
        'rate_limit': 1000,
        'symbols_limit': 50
    }
}

# Vector Sniper Pro Indicator Parameters
VECTOR_PARAMS = {
    # Core Parameters
    'atr_len': 14,
    'vol_len': 20,
    'tr_z_thr': 1.2,
    'vol_z_thr': 1.0,
    'ext_mult': 1.8,
    
    # Vector Filters
    'min_body_pct': 55,
    'lb_break': 5,
    'use_break': True,
    'use_trap': True,
    
    # Pre-Signal Filter
    'pre_min_score': 4,
    'persist_n': 2,
    'persist_window': 4,
    'cooldown_bars': 6,
    'conflict_lock': 4,
    
    # Trend Alignment
    'use_vwap': True,
    'use_ema': True,
    'ema_len': 50,
    'use_htf': False,
    'htf': '60'
}

# Scanner Configuration
SCANNER_CONFIG = {
    'scan_interval': 1800,  # 30 minutes
    'max_signals_per_type': {
        'EXTREME': 5,
        'VECTOR': 8,
        'PRE': 10
    },
    'min_confidence': 50,
    'timeframe': '1m',
    'ohlcv_limit': 100
}

# Trading Configuration
TRADING_CONFIG = {
    'primary_exchange': 'mexc',
    'max_position_size': 100.0,  # USD
    'risk_per_trade': 0.02,  # 2%
    'leverage': 1,  # Spot trading
    'stop_loss_pct': 0.02,  # 2%
    'take_profit_pct': 0.04  # 4%
}

# Discord Embed Colors
COLORS = {
    'EXTREME': 0xff6b6b,  # Red
    'VECTOR': 0x4ecdc4,   # Teal
    'PRE': 0x3498db,      # Blue
    'SUMMARY': 0x00ff00,  # Green
    'NO_SIGNALS': 0x808080  # Gray
}

# TradingView Configuration
TRADINGVIEW_CONFIG = {
    'base_url': 'https://www.tradingview.com/chart/?symbol=',
    'exchanges': {
        'mexc': 'MEXC',
        'bybit': 'BYBIT',
        'binance': 'BINANCE'
    }
}



















































