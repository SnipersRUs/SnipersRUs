#!/usr/bin/env python3
"""
Enhanced Market Maker Detection Configuration
Optimized thresholds and parameters for better accuracy
"""
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class MMThresholds:
    """Market Maker detection thresholds"""
    # Basic MM detection
    divergence_threshold: float = 15.0  # Reduced from 20 for more sensitivity
    mm_confidence_threshold: float = 35.0  # Reduced from 40 for earlier detection
    early_min_rr: float = 1.2
    m15_enabled: bool = True
    
    # Enhanced MM patterns
    iceberg_threshold: float = 0.8  # Volume spike threshold
    spoofing_threshold: float = 0.6  # Order book manipulation threshold
    layering_threshold: float = 0.7  # Layered order detection threshold
    flush_threshold: float = 0.85  # Major flush detection threshold
    
    # Volume analysis
    volume_spike_multiplier: float = 2.0  # 2x average volume
    price_stability_threshold: float = 0.005  # 0.5% price volatility
    large_order_multiplier: float = 2.0  # 2x average order size
    
    # Bias detection
    m15_momentum_threshold: float = 0.2
    h1_momentum_threshold: float = 0.5
    h4_momentum_threshold: float = 0.5
    
    # Divergence detection
    spot_pressure_threshold: float = 15.0
    futures_pressure_threshold: float = 15.0
    price_trend_threshold: float = 1.5  # 1.5% price change

@dataclass
class TradingConfig:
    """Trading system configuration"""
    # Account settings
    initial_balance: float = 10000.0
    position_size: float = 1000.0  # $1000 per trade
    max_risk_per_trade: float = 0.10  # 10% max risk per trade
    max_daily_loss: float = 0.15  # 15% max daily loss
    max_open_positions: int = 5
    
    # Leverage limits
    leverage_limits: Dict[str, int] = None
    
    def __post_init__(self):
        if self.leverage_limits is None:
            self.leverage_limits = {
                'BTC': 20,
                'ETH': 10,
                'SOL': 10,
                'DEFAULT': 10
            }
    
    # Risk management
    stop_loss_atr_multiplier: float = 2.0
    take_profit_1_multiplier: float = 1.5
    take_profit_2_multiplier: float = 3.0
    take_profit_3_multiplier: float = 5.0
    
    # Position sizing
    min_position_size: float = 100.0
    max_position_size: float = 2000.0

@dataclass
class AlertConfig:
    """Alert configuration"""
    # Flush alerts
    flush_strength_threshold: float = 70.0  # Only alert on major flushes
    flush_volume_spike: float = 2.0  # 2x volume spike for flush
    flush_price_move: float = 0.03  # 3% price move for flush
    
    # MM pattern alerts
    iceberg_confidence_threshold: float = 60.0
    spoofing_confidence_threshold: float = 60.0
    layering_confidence_threshold: float = 60.0
    
    # Trading alerts
    trade_execution_alerts: bool = True
    position_update_alerts: bool = True
    risk_management_alerts: bool = True
    
    # Discord webhook
    discord_webhook: str = "https://discord.com/api/webhooks/1417096846978842634/__rOUU6qOz_mRIRO2MUG8PpR4BMyTpmONQ9PDIpB21z47k5pKDbBbSjj3AKciiHsOCq8"
    alert_frequency_limit: int = 300  # 5 minutes between similar alerts

@dataclass
class SymbolConfig:
    """Symbol-specific configuration"""
    # Priority symbols for scanning
    priority_symbols: List[str] = None
    
    def __post_init__(self):
        if self.priority_symbols is None:
            self.priority_symbols = [
                'BTC/USDT', 'ETH/USDT', 'SOL/USDT',
                'BNB/USDT', 'XRP/USDT', 'ADA/USDT',
                'DOGE/USDT', 'AVAX/USDT', 'MATIC/USDT',
                'DOT/USDT', 'LINK/USDT', 'UNI/USDT'
            ]
    
    # Symbol-specific thresholds
    symbol_thresholds: Dict[str, Dict] = None
    
    def __post_init__(self):
        if self.symbol_thresholds is None:
            self.symbol_thresholds = {
                'BTC/USDT': {
                    'leverage': 20,
                    'min_volume': 1000000,
                    'volatility_multiplier': 1.0
                },
                'ETH/USDT': {
                    'leverage': 10,
                    'min_volume': 500000,
                    'volatility_multiplier': 1.2
                },
                'SOL/USDT': {
                    'leverage': 10,
                    'min_volume': 300000,
                    'volatility_multiplier': 1.5
                }
            }

class MMConfig:
    """Main configuration class"""
    
    def __init__(self):
        self.thresholds = MMThresholds()
        self.trading = TradingConfig()
        self.alerts = AlertConfig()
        self.symbols = SymbolConfig()
        
        # Load from external config if available
        self._load_external_config()
    
    def _load_external_config(self):
        """Load configuration from external file if available"""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("cfg", "config/config.py")
            if spec and spec.loader:
                cfg = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(cfg)
                
                # Override with external config values
                if hasattr(cfg, 'SENSITIVITY'):
                    sens = cfg.SENSITIVITY
                    self.thresholds.divergence_threshold = sens.get('DIVERGENCE_THRESHOLD', self.thresholds.divergence_threshold)
                    self.thresholds.mm_confidence_threshold = sens.get('MM_CONF_FOR_IDEA', self.thresholds.mm_confidence_threshold)
                    self.thresholds.early_min_rr = sens.get('EARLY_MIN_RR', self.thresholds.early_min_rr)
                    self.thresholds.m15_enabled = sens.get('M15_ENABLED', self.thresholds.m15_enabled)
                
                if hasattr(cfg, 'DISCORD_WEBHOOK'):
                    self.alerts.discord_webhook = cfg.DISCORD_WEBHOOK
                    
        except Exception as e:
            print(f"Could not load external config: {e}")
    
    def get_symbol_config(self, symbol: str) -> Dict:
        """Get symbol-specific configuration"""
        base_symbol = symbol.split('/')[0].upper()
        return self.symbols.symbol_thresholds.get(symbol, 
            self.symbols.symbol_thresholds.get(f'{base_symbol}/USDT', {}))
    
    def update_threshold(self, category: str, key: str, value: float):
        """Update a specific threshold"""
        if category == 'thresholds':
            setattr(self.thresholds, key, value)
        elif category == 'trading':
            setattr(self.trading, key, value)
        elif category == 'alerts':
            setattr(self.alerts, key, value)
        elif category == 'symbols':
            setattr(self.symbols, key, value)
    
    def get_optimized_thresholds(self) -> Dict:
        """Get optimized thresholds based on market conditions"""
        return {
            'divergence_threshold': self.thresholds.divergence_threshold,
            'mm_confidence_threshold': self.thresholds.mm_confidence_threshold,
            'iceberg_threshold': self.thresholds.iceberg_threshold,
            'spoofing_threshold': self.thresholds.spoofing_threshold,
            'layering_threshold': self.thresholds.layering_threshold,
            'flush_threshold': self.thresholds.flush_threshold,
            'volume_spike_multiplier': self.thresholds.volume_spike_multiplier,
            'price_stability_threshold': self.thresholds.price_stability_threshold
        }
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return any issues"""
        issues = []
        
        # Check thresholds
        if self.thresholds.divergence_threshold < 5 or self.thresholds.divergence_threshold > 50:
            issues.append("Divergence threshold should be between 5 and 50")
        
        if self.thresholds.mm_confidence_threshold < 20 or self.thresholds.mm_confidence_threshold > 80:
            issues.append("MM confidence threshold should be between 20 and 80")
        
        # Check trading config
        if self.trading.max_risk_per_trade > 0.20:
            issues.append("Max risk per trade should not exceed 20%")
        
        if self.trading.max_daily_loss > 0.30:
            issues.append("Max daily loss should not exceed 30%")
        
        # Check leverage limits
        for symbol, leverage in self.trading.leverage_limits.items():
            if leverage > 50:
                issues.append(f"Leverage for {symbol} should not exceed 50x")
        
        return issues

# Global configuration instance
config = MMConfig()

# Export commonly used values
DIV_TH = config.thresholds.divergence_threshold
MM_CONF = config.thresholds.mm_confidence_threshold
EARLY_RR = config.thresholds.early_min_rr
USE_M15 = config.thresholds.m15_enabled

# Trading constants
ACCOUNT_BALANCE = config.trading.initial_balance
TRADE_SIZE = config.trading.position_size
MAX_LEVERAGE_BTC = config.trading.leverage_limits['BTC']
MAX_LEVERAGE_ETH = config.trading.leverage_limits['ETH']
MAX_LEVERAGE_SOL = config.trading.leverage_limits['SOL']
RISK_PER_TRADE = config.trading.max_risk_per_trade

# Enhanced MM Detection Thresholds
ICEBERG_THRESHOLD = config.thresholds.iceberg_threshold
SPOOFING_THRESHOLD = config.thresholds.spoofing_threshold
LAYERING_THRESHOLD = config.thresholds.layering_threshold
FLUSH_THRESHOLD = config.thresholds.flush_threshold
