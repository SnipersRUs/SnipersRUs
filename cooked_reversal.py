#!/usr/bin/env python3
"""
REVERSAL HUNTER — Ultimate Multi-Exchange Reversal Scanner
Golden Pocket + Volume Spike + Divergence Detection System
"""

import time, json, random, requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import ccxt
import config

# ================== CONFIG ==================
class CFG:
    # Exchange selection - prioritize MEXC since you're trading there
    EXCHANGES = ["mexc", "binance", "bybit"]
    
    # Scanner settings
    TIMEFRAME = "15m"
    OHLC_LIMIT = 100
    PAIRS_TO_SCAN = 500
    DETAILED_ANALYSIS = 50
    
    # Volume filters (USD) - Higher minimum for liquid coins
    VOLUME_MIN_USD = 1_000_000  # $1M minimum for liquid coins
    VOLUME_MAX_USD = 50_000_000  # $50M maximum to avoid manipulation
    
    # Blacklist of micro-caps and new/unknown coins to avoid
    BLACKLISTED_COINS = {
        '1000RATS', '1000PEPE', '1000SATS', '1000BONK', '1000FLOKI', '1000SHIB',
        'BABYDOGE', 'BABYSHIB', 'BABYDOGE', 'BABYPEPE', 'BABYFLOKI',
        'NEW', 'NEWS', 'NEWS', 'NEWS', 'NEWS', 'NEWS',
        'TEST', 'TESTNET', 'TESTING', 'DEMO', 'FAKE',
        'MEME', 'MEMES', 'DOGE', 'SHIB', 'PEPE', 'FLOKI', 'BONK',
        'SAFE', 'SAFEMOON', 'SAFEMARS', 'SAFEGALAXY',
        'MOON', 'MOONSHOT', 'MOONSHOT', 'MOONSHOT',
        'PUMP', 'PUMPKIN', 'PUMPKIN', 'PUMPKIN',
        'RUG', 'RUGPULL', 'RUGPULL', 'RUGPULL',
        'SCAM', 'SCAMCOIN', 'SCAMCOIN', 'SCAMCOIN',
        'SHIT', 'SHITCOIN', 'SHITCOIN', 'SHITCOIN',
        'TRASH', 'TRASHCOIN', 'TRASHCOIN', 'TRASHCOIN',
        'USELESS', 'USELESS', 'USELESS', 'USELESS',
        'WORTHLESS', 'WORTHLESS', 'WORTHLESS', 'WORTHLESS'
    }
    
    # Signal thresholds
    MIN_SCORE = 50
    MIN_WATCH_SCORE = 30
    RSI_TOP = (60, 90)
    VOL_DECLINE_THRESHOLD = 0.85
    
    # Rate limiting - Only 2 priority signals
    MAX_SIGNALS_PER_SCAN = 2  # Only 2 priority signals
    MIN_SIGNALS_PER_SCAN = 1  # Minimum 1 signal per scan
    SIGNAL_COOLDOWN = 1620  # 27 minutes cooldown
    
    # Paper trading
    PAPER_BALANCE = 10_000  # $10K starting balance
    TRADE_SIZE = 300  # $300 per trade
    MAX_OPEN_TRADES = 3
    
    # Loop settings - 27 minutes for more frequent scans
    LOOP_SECONDS = 1620  # 27 minutes = 27 * 60 seconds
    
    # Discord colors - Purple for bearish signals
    C = {
        "HDR": 0xFF0000,
        "SHORT": 0x8B008B,  # Purple for bearish signals
        "WATCH": 0xFF6347,
        "INFO": 0xFFFFFF,
        "BINANCE": 0xF0B90B,
        "BYBIT": 0xFF6600,
        "MEXC": 0x00D4AA
    }

# ================== PAPER TRADING ==================
class PaperTrading:
    def __init__(self):
        self.balance = CFG.PAPER_BALANCE
        self.positions = {}  # symbol -> position data
        self.trade_history = []
        self.load_state()
    
    def load_state(self):
        """Load trading state from file"""
        try:
            with open('trading_state.json', 'r') as f:
                data = json.load(f)
                self.balance = data.get('balance', CFG.PAPER_BALANCE)
                self.positions = data.get('positions', {})
                self.trade_history = data.get('trade_history', [])
        except:
            pass
    
    def save_state(self):
        """Save trading state to file"""
        try:
            with open('trading_state.json', 'w') as f:
                json.dump({
                    'balance': self.balance,
                    'positions': self.positions,
                    'trade_history': self.trade_history[-100:]  # Keep last 100 trades
                }, f, indent=2)
        except:
            pass
    
    def can_open_trade(self) -> bool:
        """Check if we can open a new trade"""
        return (len(self.positions) < CFG.MAX_OPEN_TRADES and 
                self.balance >= CFG.TRADE_SIZE)
    
    def open_position(self, signal: Dict) -> bool:
        """Open a new short position"""
        if not self.can_open_trade():
            return False
        
        symbol = signal['symbol']
        entry_price = signal['price']
        size_usd = CFG.TRADE_SIZE
        size_units = size_usd / entry_price
        
        position = {
            'symbol': symbol,
            'base': signal['base'],
            'exchange': signal['exchange'],
            'side': 'short',
            'entry_price': entry_price,
            'size_usd': size_usd,
            'size_units': size_units,
            'entry_time': utcnow().isoformat(),
            'score': signal['score'],
            'tp1': signal['tp1'],
            'tp2': signal['tp2'],
            'tp3': signal['tp3'],
            'sl': signal['sl']
        }
        
        self.positions[symbol] = position
        self.balance -= size_usd
        
        # Log trade
        self.trade_history.append({
            'action': 'OPEN',
            'timestamp': utcnow().isoformat(),
            'position': position
        })
        
        self.save_state()
        return True
    
    def update_positions(self, current_prices: Dict[str, float]):
        """Update position PnL with current prices"""
        closed_positions = []
        
        for symbol, position in list(self.positions.items()):
            if symbol in current_prices:
                current_price = current_prices[symbol]
                pnl_pct = (position['entry_price'] - current_price) / position['entry_price']
                pnl_usd = position['size_usd'] * pnl_pct
                
                # Update position
                position['current_price'] = current_price
                position['pnl_pct'] = pnl_pct
                position['pnl_usd'] = pnl_usd
                
                # Check for TP/SL
                should_close = False
                close_reason = ""
                
                if current_price <= position['tp1']:
                    should_close = True
                    close_reason = "TP1 Hit"
                elif current_price <= position['tp2']:
                    should_close = True
                    close_reason = "TP2 Hit"
                elif current_price <= position['tp3']:
                    should_close = True
                    close_reason = "TP3 Hit"
                elif current_price >= position['sl']:
                    should_close = True
                    close_reason = "SL Hit"
                
                if should_close:
                    self.close_position(symbol, current_price, close_reason)
                    closed_positions.append(position)
        
        return closed_positions
    
    def close_position(self, symbol: str, exit_price: float, reason: str):
        """Close a position"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        pnl_pct = (position['entry_price'] - exit_price) / position['entry_price']
        pnl_usd = position['size_usd'] * pnl_pct
        
        # Update balance
        self.balance += position['size_usd'] + pnl_usd
        
        # Log closure
        self.trade_history.append({
            'action': 'CLOSE',
            'timestamp': utcnow().isoformat(),
            'symbol': symbol,
            'exit_price': exit_price,
            'pnl_pct': pnl_pct,
            'pnl_usd': pnl_usd,
            'reason': reason,
            'position': position
        })
        
        # Remove position
        del self.positions[symbol]
        self.save_state()
    
    def get_summary(self) -> Dict:
        """Get trading summary"""
        # Calculate unrealized PnL from open positions
        unrealized_pnl = sum(pos.get('pnl_usd', 0) for pos in self.positions.values())
        
        # Calculate realized PnL from closed trades
        realized_pnl = sum(t.get('pnl_usd', 0) for t in self.trade_history if t.get('action') == 'CLOSE')
        
        total_pnl = unrealized_pnl + realized_pnl
        total_trades = len([t for t in self.trade_history if t.get('action') == 'CLOSE'])
        winning_trades = len([t for t in self.trade_history if t.get('action') == 'CLOSE' and t.get('pnl_usd', 0) > 0])
        
        return {
            'balance': self.balance,
            'open_positions': len(self.positions),
            'total_pnl': total_pnl,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': winning_trades / max(1, total_trades) * 100
        }

# ================== UTILS ==================
def utcnow(): 
    return datetime.now(timezone.utc)

def safe_upper(s):
    """Safely convert to uppercase"""
    if s is None:
        return ""
    return str(s).upper()

def safe_float(v, default=0.0):
    """Safely convert to float"""
    try:
        return float(v) if v is not None else default
    except:
        return default

def post_embeds(embeds: List[Dict]):
    try:
        r = requests.post(config.DISCORD_WEBHOOK, json={"embeds": embeds[:10]}, timeout=10)
        if r.status_code not in (200, 204):
            print(f"Webhook HTTP {r.status_code}")
    except Exception as e:
        print(f"Webhook error: {e}")

# ================== INDICATORS ==================
def rsi(series: pd.Series, period=14):
    """Calculate RSI"""
    if len(series) < period + 1:
        return 50.0  # Default neutral RSI
    d = series.diff()
    up = d.clip(lower=0).rolling(period).mean()
    dn = (-d.clip(upper=0)).rolling(period).mean()
    rs = up / dn.replace(0, np.nan)
    return float(100 - (100/(1+rs)).iloc[-1])

def detect_golden_pocket(df: pd.DataFrame) -> Dict:
    """Detect Golden Pocket zones (61.8% - 65% retracement)"""
    try:
        c, h, l = df["close"], df["high"], df["low"]
        
        # Daily, Weekly, Monthly Golden Pockets
        daily_high = h.rolling(24).max().iloc[-1] if len(h) >= 24 else h.max()
        daily_low = l.rolling(24).min().iloc[-1] if len(l) >= 24 else l.min()
        daily_range = daily_high - daily_low
        
        # Golden Pocket calculations
        gp_high = daily_high - (daily_range * 0.618)  # 61.8% retracement
        gp_low = daily_high - (daily_range * 0.65)   # 65% retracement
        
        current_price = c.iloc[-1]
        
        # Check if price is in Golden Pocket zone
        in_gp_zone = gp_low <= current_price <= gp_high
        
        # Calculate distance to GP
        gp_distance = min(abs(current_price - gp_high), abs(current_price - gp_low))
        gp_distance_pct = (gp_distance / current_price) * 100 if current_price > 0 else 100
        
        return {
            "in_gp_zone": in_gp_zone,
            "gp_high": float(gp_high),
            "gp_low": float(gp_low),
            "gp_distance_pct": float(gp_distance_pct),
            "near_gp": gp_distance_pct < 2.0  # Within 2% of GP
        }
    except Exception as e:
        print(f"    Golden Pocket calc error: {e}")
        return {
            "in_gp_zone": False,
            "gp_high": 0.0,
            "gp_low": 0.0,
            "gp_distance_pct": 100.0,
            "near_gp": False
        }

def detect_volume_spike(df: pd.DataFrame) -> Dict:
    """Detect high volume spikes on 15m+ timeframes"""
    try:
        v = df["volume"]
        
        # Volume analysis
        v_ma20 = v.rolling(20).mean().iloc[-1] if len(v) >= 20 else v.mean()
        v_ma50 = v.rolling(50).mean().iloc[-1] if len(v) >= 50 else v.mean()
        
        # Current volume vs averages
        vol_ratio_20 = float(v.iloc[-1] / max(1e-12, v_ma20))
        vol_ratio_50 = float(v.iloc[-1] / max(1e-12, v_ma50))
        
        # Volume spike detection
        extreme_spike = vol_ratio_20 > 3.0  # 3x average volume
        high_spike = vol_ratio_20 > 2.0     # 2x average volume
        liquidity_spike = vol_ratio_50 > 1.5  # 1.5x 50-period average
        
        # Volume trend analysis
        recent_vol = v.iloc[-5:].mean() if len(v) >= 5 else v.iloc[-1]
        vol_trend_up = recent_vol > v_ma20 * 1.2
        
        return {
            "extreme_spike": extreme_spike,
            "high_spike": high_spike,
            "liquidity_spike": liquidity_spike,
            "vol_ratio_20": vol_ratio_20,
            "vol_ratio_50": vol_ratio_50,
            "vol_trend_up": vol_trend_up
        }
    except Exception as e:
        print(f"    Volume spike calc error: {e}")
        return {
            "extreme_spike": False,
            "high_spike": False,
            "liquidity_spike": False,
            "vol_ratio_20": 1.0,
            "vol_ratio_50": 1.0,
            "vol_trend_up": False
        }

def detect_exhaustion(df: pd.DataFrame) -> Dict:
    """Detect volume exhaustion and price overextension with enhanced logic"""
    try:
        c, v = df["close"], df["volume"]
        
        # Volume analysis
        v_ma20 = v.rolling(20).mean().iloc[-1] if len(v) >= 20 else v.mean()
        v_recent = v.iloc[-5:].mean() if len(v) >= 5 else v.iloc[-1]
        vol_declining = v_recent < v_ma20 * CFG.VOL_DECLINE_THRESHOLD
        vol_ratio = float(v_recent / max(1e-12, v_ma20))
        
        # Price extension
        ema21 = c.ewm(span=21, adjust=False).mean().iloc[-1]
        price_extension = (c.iloc[-1] - ema21) / max(1e-12, ema21) * 100
        
        # RSI
        rsi_val = rsi(c)
        
        # Enhanced divergence detection
        price_higher = c.iloc[-1] > c.iloc[-10] if len(c) >= 10 else False
        rsi_prev = rsi(c.iloc[:-1]) if len(c) > 15 else rsi_val
        bearish_div = price_higher and rsi_val < rsi_prev
        
        # Volume spike detection
        vol_std = v.rolling(20).std().iloc[-1] if len(v) >= 20 else 0
        extreme_vol = v.iloc[-1] > v_ma20 + (vol_std * 3.5) if vol_std > 0 else False
        
        # Money flow analysis (oversold + losing momentum)
        money_flow_leaving = (rsi_val > 70 and vol_ratio < 0.8) or (price_extension > 15 and vol_declining)
        
        return {
            "vol_declining": vol_declining,
            "vol_ratio": vol_ratio,
            "price_extension": float(price_extension),
            "rsi": rsi_val,
            "bearish_divergence": bearish_div,
            "extreme_vol_spike": extreme_vol,
            "money_flow_leaving": money_flow_leaving
        }
    except Exception as e:
        print(f"    Exhaustion calc error: {e}")
        return {
            "vol_declining": False,
            "vol_ratio": 1.0,
            "price_extension": 0.0,
            "rsi": 50.0,
            "bearish_divergence": False,
            "extreme_vol_spike": False,
            "money_flow_leaving": False
        }

def calculate_vwaps(df: pd.DataFrame) -> Dict:
    """Calculate multi-timeframe VWAPs"""
    try:
        c, v = df["close"], df["volume"]
        
        # VWAPs
        vwap = (c * v).sum() / v.sum() if v.sum() > 0 else c.mean()
        vwap_1h = ((c.iloc[-4:] * v.iloc[-4:]).sum() / v.iloc[-4:].sum() 
                   if len(c) >= 4 and v.iloc[-4:].sum() > 0 else vwap)
        vwap_4h = ((c.iloc[-16:] * v.iloc[-16:]).sum() / v.iloc[-16:].sum() 
                   if len(c) >= 16 and v.iloc[-16:].sum() > 0 else vwap)
        vwap_daily = ((c.iloc[-96:] * v.iloc[-96:]).sum() / v.iloc[-96:].sum() 
                      if len(c) >= 96 and v.iloc[-96:].sum() > 0 else vwap)
        
        last_price = float(c.iloc[-1])
        
        above_1h = last_price > vwap_1h
        above_4h = last_price > vwap_4h
        above_daily = last_price > vwap_daily
        
        return {
            "price": last_price,
            "vwap_1h": float(vwap_1h),
            "vwap_4h": float(vwap_4h),
            "vwap_daily": float(vwap_daily),
            "above_all_vwaps": above_1h and above_4h and above_daily,
            "above_count": int(above_1h) + int(above_4h) + int(above_daily)
        }
    except Exception as e:
        print(f"    VWAP calc error: {e}")
        return {
            "price": 0.0,
            "vwap_1h": 0.0,
            "vwap_4h": 0.0,
            "vwap_daily": 0.0,
            "above_all_vwaps": False,
            "above_count": 0
        }

def score_short(exh: Dict, vwap: Dict, gp: Dict, vol_spike: Dict) -> int:
    """Calculate enhanced short score 0-100 with Golden Pocket logic"""
    s = 0
    
    # Golden Pocket zone (25 points) - HIGHEST PRIORITY
    if gp["in_gp_zone"]: s += 25
    elif gp["near_gp"]: s += 15
    
    # Volume spike + divergence combo (30 points)
    if vol_spike["extreme_spike"] and exh["bearish_divergence"]: s += 30
    elif vol_spike["high_spike"] and exh["bearish_divergence"]: s += 20
    elif vol_spike["liquidity_spike"] and exh["bearish_divergence"]: s += 15
    
    # Volume exhaustion (20 points)
    if exh["vol_declining"]: s += 15
    if exh["vol_ratio"] < 0.7: s += 5
    
    # Price overextension (15 points)
    if exh["price_extension"] > 15: s += 15
    elif exh["price_extension"] > 10: s += 10
    
    # RSI conditions (10 points)
    if exh["rsi"] > 75: s += 10
    elif exh["rsi"] > 70: s += 5
    
    # Money flow leaving (10 points)
    if exh["money_flow_leaving"]: s += 10
    
    # VWAP positioning (5 points)
    if vwap["above_all_vwaps"]: s += 5
    
    return min(100, s)

def get_market_analysis(signal: Dict) -> str:
    """Generate market analysis summary for the signal"""
    try:
        base = signal['base']
        price = signal['price']
        rsi = signal['exh']['rsi']
        vol_ratio = signal['exh']['vol_ratio']
        price_ext = signal['exh']['price_extension']
        
        analysis_parts = []
        
        # Market condition
        if rsi > 75:
            analysis_parts.append("🔴 **OVERSOLD** - RSI at extreme levels")
        elif rsi > 70:
            analysis_parts.append("🟡 **OVERBOUGHT** - RSI showing weakness")
        
        # Volume analysis
        if vol_ratio > 2.0:
            analysis_parts.append("📈 **MASSIVE VOLUME SPIKE** - Institutional activity")
        elif vol_ratio > 1.5:
            analysis_parts.append("📊 **HIGH VOLUME** - Strong selling pressure")
        
        # Price extension
        if price_ext > 15:
            analysis_parts.append("⚡ **EXTREME OVEREXTENSION** - Price stretched beyond normal")
        elif price_ext > 10:
            analysis_parts.append("📏 **OVEREXTENDED** - Price showing exhaustion")
        
        # Golden Pocket
        if signal.get('gp', {}).get('in_gp_zone', False):
            analysis_parts.append("🎯 **GOLDEN POCKET ZONE** - Perfect reversal area")
        elif signal.get('gp', {}).get('near_gp', False):
            analysis_parts.append("📍 **NEAR GOLDEN POCKET** - Approaching reversal zone")
        
        # Money flow
        if signal['exh'].get('money_flow_leaving', False):
            analysis_parts.append("💰 **MONEY FLOW LEAVING** - Smart money exiting")
        
        if not analysis_parts:
            analysis_parts.append("📊 **MARKET ANALYSIS** - Standard bearish setup detected")
        
        return " | ".join(analysis_parts)
        
    except Exception as e:
        return "📊 **MARKET ANALYSIS** - Bearish reversal setup detected"

# ================== EXCHANGE HANDLER ==================
class ExchangeHandler:
    def __init__(self, exchange_name: str):
        self.name = exchange_name.lower()
        self.exchange = None
        self.futures_symbols = []
        
    def init(self):
        """Initialize exchange connection with proper error handling"""
        try:
            print(f"Initializing {self.name.upper()}...")
            
            if self.name == "binance":
                self.exchange = ccxt.binance({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'future'},
                    'timeout': 10000
                })
            elif self.name == "bybit":
                self.exchange = ccxt.bybit({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'linear'},
                    'timeout': 10000
                })
            elif self.name == "mexc":
                self.exchange = ccxt.mexc({
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'swap',
                        'fetchOHLCV': {'limit': 100}
                    },
                    'timeout': 10000,
                    'rateLimit': 100  # Slower rate limit for MEXC
                })
            else:
                return False
            
            # Load markets with error handling
            self.exchange.load_markets()
            self._load_futures_symbols()
            return True
            
        except Exception as e:
            print(f"❌ Error initializing {self.name}: {e}")
            return False
    
    def _load_futures_symbols(self):
        """Load futures symbols with proper parsing"""
        try:
            for symbol, market in self.exchange.markets.items():
                try:
                    # Ensure we're dealing with strings
                    symbol = str(symbol)
                    
                    # Check if it's a futures/perpetual market
                    is_futures = False
                    
                    if self.name == "binance":
                        # For Binance, we want perpetual contracts, not dated futures
                        is_futures = (market.get('type') == 'swap' and 
                                    market.get('linear') == True)
                    elif self.name == "bybit":
                        is_futures = (market.get('linear') == True and 
                                    market.get('swap') == True)
                    elif self.name == "mexc":
                        is_futures = (market.get('swap') == True and 
                                    market.get('linear') == True)
                    
                    # Check quote currency
                    quote = safe_upper(market.get('quote'))
                    if is_futures and quote == 'USDT' and market.get('active'):
                        self.futures_symbols.append(symbol)
                        
                except Exception as e:
                    # Skip problematic symbols
                    continue
                    
            print(f"✅ {self.name.upper()} loaded {len(self.futures_symbols)} futures")
            
        except Exception as e:
            print(f"Error loading {self.name} symbols: {e}")
    
    def fetch_ticker(self, symbol: str) -> Optional[Dict]:
        """Fetch ticker with error handling"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            
            # Parse base currency safely
            base = symbol.split('/')[0] if '/' in symbol else symbol.split(':')[0]
            
            return {
                'symbol': symbol,
                'base': base,
                'price': safe_float(ticker.get('last')),
                'volume_24h': safe_float(ticker.get('quoteVolume')),
                'change_24h': safe_float(ticker.get('percentage'))
            }
        except Exception as e:
            return None
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = "15m", limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch OHLCV with error handling"""
        try:
            # Add retry logic for MEXC
            retries = 2 if self.name == "mexc" else 1
            
            for attempt in range(retries):
                try:
                    ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                    if ohlcv and len(ohlcv) >= 20:
                        return pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
                except Exception as e:
                    if attempt < retries - 1:
                        time.sleep(0.5)
                    else:
                        raise e
            return None
            
        except Exception:
            return None
    
    def scan_for_shorts(self) -> List[Dict]:
        """Scan with robust error handling"""
        results = []
        
        try:
            # Get symbols to scan
            symbols_to_scan = self.futures_symbols[:CFG.PAIRS_TO_SCAN]
            if not symbols_to_scan:
                print(f"  No symbols to scan for {self.name}")
                return []
            
            print(f"  Scanning {len(symbols_to_scan)} pairs on {self.name.upper()}...")
            
            # Phase 1: Quick ticker scan
            candidates = []
            errors = 0
            
            for i, symbol in enumerate(symbols_to_scan):
                if i % 50 == 0 and i > 0:
                    print(f"    Progress: {i}/{len(symbols_to_scan)} (Errors: {errors})")
                
                try:
                    ticker = self.fetch_ticker(symbol)
                    if ticker and CFG.VOLUME_MIN_USD <= ticker['volume_24h'] <= CFG.VOLUME_MAX_USD:
                        # Check if coin is blacklisted (micro-cap or new/unknown)
                        base_symbol = ticker['symbol'].split('/')[0] if '/' in ticker['symbol'] else ticker['symbol']
                        if base_symbol not in CFG.BLACKLISTED_COINS:
                            candidates.append(ticker)
                except Exception:
                    errors += 1
                    
                # Rate limiting
                time.sleep(0.02 if self.name != "mexc" else 0.1)
            
            print(f"  Found {len(candidates)} in volume range (Errors: {errors})")
            
            # Phase 2: Detailed analysis
            analyzed = 0
            for ticker in candidates[:CFG.DETAILED_ANALYSIS]:
                try:
                    df = self.fetch_ohlcv(ticker['symbol'], CFG.TIMEFRAME, CFG.OHLC_LIMIT)
                    if df is None or len(df) < 30:
                        continue
                    
                    # Calculate all indicators
                    exh = detect_exhaustion(df)
                    vwap = calculate_vwaps(df)
                    gp = detect_golden_pocket(df)
                    vol_spike = detect_volume_spike(df)
                    
                    # Enhanced conditions with Golden Pocket
                    strict_ok = (
                        (gp["in_gp_zone"] or gp["near_gp"]) and
                        (vol_spike["high_spike"] or vol_spike["extreme_spike"]) and
                        (exh["bearish_divergence"] or exh["money_flow_leaving"]) and
                        CFG.RSI_TOP[0] <= exh["rsi"] <= CFG.RSI_TOP[1]
                    )
                    
                    watch_ok = (
                        (gp["near_gp"] or vwap["above_count"] >= 2) and
                        (exh["rsi"] >= 62 or exh["price_extension"] >= 7.5) and
                        (vol_spike["liquidity_spike"] or exh["vol_declining"])
                    )
                    
                    # Calculate enhanced score
                    score = score_short(exh, vwap, gp, vol_spike)
                    
                    # Build enhanced result
                    result = {
                        'exchange': self.name,
                        'base': ticker['base'],
                        'symbol': ticker['symbol'],
                        'price': ticker['price'],
                        'vol_24h': ticker['volume_24h'],
                        'change_24h': ticker['change_24h'],
                        'score': score,
                        'exh': exh,
                        'vwap': vwap,
                        'gp': gp,
                        'vol_spike': vol_spike,
                        'strict_ok': strict_ok,
                        'watch_ok': watch_ok,
                        'tp1': ticker['price'] * 0.95,
                        'tp2': ticker['price'] * 0.90,
                        'tp3': ticker['price'] * 0.80,
                        'sl': ticker['price'] * 1.05
                    }
                    results.append(result)
                    analyzed += 1
                    
                    if analyzed % 10 == 0:
                        print(f"    Analyzed {analyzed}/{min(len(candidates), CFG.DETAILED_ANALYSIS)}")
                        
                except Exception as e:
                    continue
                
                # Rate limiting
                time.sleep(0.05 if self.name != "mexc" else 0.15)
            
            print(f"  Completed {self.name}: {len(results)} signals found")
            
        except Exception as e:
            print(f"  Major error scanning {self.name}: {e}")
            
        return results

# ================== SCANNER ==================
class MultiExchangeScanner:
    def __init__(self):
        self.handlers = {}
        self.paper_trading = PaperTrading()
        self.last_signals = []  # Track recent signals for rate limiting
        self.active_signals = {}  # Track active signals to avoid duplicates
        
    def init(self):
        """Initialize all exchanges"""
        for exchange_name in CFG.EXCHANGES:
            handler = ExchangeHandler(exchange_name)
            if handler.init():
                self.handlers[exchange_name] = handler
            else:
                print(f"Skipping {exchange_name} due to initialization failure")
    
    def scan_all(self) -> Tuple[List[Dict], List[Dict]]:
        """Scan all exchanges with rate limiting and paper trading"""
        all_results = []
        
        for name, handler in self.handlers.items():
            results = handler.scan_for_shorts()
            all_results.extend(results)
        
        # Filter signals
        signals = [r for r in all_results if r['strict_ok'] and r['score'] >= CFG.MIN_SCORE]
        signals = sorted(signals, key=lambda x: x['score'], reverse=True)
        
        # Smart signal validation - avoid duplicates
        current_time = time.time()
        new_signals = []
        
        for signal in signals:
            signal_key = f"{signal['base']}_{signal['exchange']}"
            
            # Check if this signal is already active
            if signal_key in self.active_signals:
                existing_signal = self.active_signals[signal_key]
                # Only add if entry price is significantly different (>2%)
                price_diff = abs(signal['price'] - existing_signal['price']) / existing_signal['price']
                if price_diff > 0.02:  # 2% price difference
                    new_signals.append(signal)
                    print(f"🔄 Updated signal: {signal['base']} (Price changed {price_diff:.1%})")
                else:
                    print(f"⏭️ Skipping duplicate: {signal['base']} (Same entry)")
            else:
                new_signals.append(signal)
                self.active_signals[signal_key] = signal
        
        # Clean up old signals
        self.active_signals = {k: v for k, v in self.active_signals.items() 
                              if current_time - v.get('timestamp', 0) < CFG.SIGNAL_COOLDOWN}
        
        signals = new_signals[:CFG.MAX_SIGNALS_PER_SCAN]
        
        # Ensure minimum signals per scan
        if len(signals) < CFG.MIN_SIGNALS_PER_SCAN:
            # Add more signals from watchlist if needed
            additional_needed = CFG.MIN_SIGNALS_PER_SCAN - len(signals)
            watch_candidates = [r for r in all_results if r not in signals and r['watch_ok']]
            additional_signals = watch_candidates[:additional_needed]
            signals.extend(additional_signals)
            print(f"📈 Added {len(additional_signals)} additional signals to meet minimum")
        
        # Paper trading - open positions for new signals
        new_entries = []
        for signal in signals:
            if self.paper_trading.can_open_trade():
                if self.paper_trading.open_position(signal):
                    print(f"📈 Opened paper trade: {signal['base']} @ ${signal['price']:.8f}")
                    new_entries.append(signal)
        
        # Update existing positions with current prices
        current_prices = {r['symbol']: r['price'] for r in all_results}
        closed_positions = self.paper_trading.update_positions(current_prices)
        
        for pos in closed_positions:
            print(f"📉 Closed position: {pos['base']} - {pos.get('close_reason', 'Manual')}")
        
        # Watchlist (rest of qualifying signals)
        watch_candidates = [r for r in all_results if r not in signals and r['watch_ok']]
        watch = sorted(watch_candidates, key=lambda x: x['score'], reverse=True)[:10]
        
        return signals, watch, new_entries

# ================== UI ==================
def header_embed(handlers_count: int, signals_count: int, trading_summary: Dict = None):
    exchanges_str = ", ".join([h.upper() for h in CFG.EXCHANGES])
    
    desc = f"Scan: {utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
    desc += f"Active: {handlers_count} exchanges\n"
    desc += f"Signals: {signals_count}"
    
    if trading_summary:
        desc += f"\n\n💰 **Paper Trading:**\n"
        desc += f"Balance: ${trading_summary['balance']:,.0f}\n"
        desc += f"Open Positions: {trading_summary['open_positions']}/{CFG.MAX_OPEN_TRADES}\n"
        desc += f"Total PnL: ${trading_summary['total_pnl']:,.0f}\n"
        desc += f"Win Rate: {trading_summary['win_rate']:.1f}%"
    
    return {
        "title": "🎯 REVERSAL HUNTER — Ultimate Reversal Scanner",
        "description": desc,
        "color": CFG.C["HDR"]
    }

def get_tradingview_link(base: str) -> str:
    """Get the best TradingView link for a symbol"""
    ticker = f"{base}/USDT"
    
    # Use the most reliable format - BINANCE with proper symbol format
    return f"https://www.tradingview.com/chart/?symbol=BINANCE:{ticker}"

def signal_embed(sig: Dict, i: int):
    exchange_color = CFG.C.get(safe_upper(sig['exchange']), CFG.C["SHORT"])
    
    # TradingView links - use smart fallback system
    ticker_symbol = f"{sig['base']}/USDT"
    tv_link = get_tradingview_link(sig['base'])
    
    # Get market analysis
    market_analysis = get_market_analysis(sig)
    
    # Golden Pocket info
    gp_info = ""
    if sig.get('gp', {}).get('in_gp_zone', False):
        gp_info = "🎯 **IN GOLDEN POCKET ZONE**"
    elif sig.get('gp', {}).get('near_gp', False):
        gp_info = "📍 **NEAR GOLDEN POCKET**"
    
    # Volume spike info
    vol_info = ""
    if sig.get('vol_spike', {}).get('extreme_spike', False):
        vol_info = "📈 **EXTREME VOLUME SPIKE**"
    elif sig.get('vol_spike', {}).get('high_spike', False):
        vol_info = "📊 **HIGH VOLUME SPIKE**"
    
    desc = (
        f"**Exchange:** {safe_upper(sig['exchange'])}\n"
        f"**Entry:** ${sig['price']:.8f}\n"
        f"**Volume:** ${sig['vol_24h']:,.0f}\n"
        f"**Score:** {sig['score']}/100\n\n"
        f"{market_analysis}\n\n"
        f"{gp_info}\n{vol_info}\n"
        f"📊 RSI: {sig['exh']['rsi']:.1f} • Ext: {sig['exh']['price_extension']:.1f}%\n"
        f"🎯 TP1: ${sig['tp1']:.8f} • TP2: ${sig['tp2']:.8f} • TP3: ${sig['tp3']:.8f}\n"
        f"📈 [**{ticker_symbol}**]({tv_link})\n\n"
        f"⚠️ **NOT FINANCIAL ADVICE** - DYOR!"
    )
    
    return {
        "title": f"#{i} 🎯 REVERSAL HUNT — {sig['base']}/USDT",
        "description": desc,
        "color": exchange_color
    }

def entry_notification_embed(signal: Dict):
    """Separate notification for when we take an entry"""
    exchange_color = CFG.C.get(safe_upper(signal['exchange']), CFG.C["SHORT"])
    
    # TradingView link - use smart fallback system
    ticker_symbol = f"{signal['base']}/USDT"
    tv_link = get_tradingview_link(signal['base'])
    
    desc = (
        f"🚨 **ENTRY TAKEN** 🚨\n\n"
        f"**Symbol:** [{ticker_symbol}]({tv_link})\n"
        f"**Exchange:** {safe_upper(signal['exchange'])}\n"
        f"**Entry Price:** ${signal['price']:.8f}\n"
        f"**Trade Size:** $300\n"
        f"**Score:** {signal['score']}/100\n\n"
        f"📊 **Analysis:**\n"
        f"• RSI: {signal['exh']['rsi']:.1f}\n"
        f"• Price Extension: {signal['exh']['price_extension']:.1f}%\n"
        f"• Volume Ratio: {signal['exh']['vol_ratio']:.2f}\n\n"
        f"🎯 **Targets:**\n"
        f"• TP1: ${signal['tp1']:.8f} (-5%)\n"
        f"• TP2: ${signal['tp2']:.8f} (-10%)\n"
        f"• TP3: ${signal['tp3']:.8f} (-20%)\n"
        f"• SL: ${signal['sl']:.8f} (+5%)"
    )
    
    return {
        "title": f"🎯 REVERSAL HUNT ENTRY — {signal['base']}/USDT",
        "description": desc,
        "color": exchange_color,
        "timestamp": utcnow().isoformat()
    }

def watchlist_embed(watch: List[Dict]):
    if not watch:
        return {
            "title": "👀 Oversold Watchlist",
            "description": "No oversold coins losing momentum detected",
            "color": CFG.C["WATCH"]
        }
    
    lines = []
    for w in watch[:5]:
        # Add TradingView links to watchlist items
        ticker_symbol = f"{w['base']}/USDT"
        tv_link = get_tradingview_link(w['base'])
        
        # Add market condition info
        condition = ""
        if w.get('exh', {}).get('money_flow_leaving', False):
            condition = "💰 Money leaving"
        elif w.get('exh', {}).get('vol_declining', False):
            condition = "📉 Volume declining"
        elif w.get('exh', {}).get('rsi', 50) > 70:
            condition = "🔴 Oversold"
        
        lines.append(f"• **[{w['base']}]({tv_link})** ({safe_upper(w['exchange'])}) — Score {w['score']} {condition}")
    
    return {
        "title": "👀 Oversold Watchlist - Coins Losing Momentum",
        "description": "\n".join(lines),
        "color": CFG.C["WATCH"]
    }

# ================== MAIN ==================
def run(loop=True, interval=CFG.LOOP_SECONDS):
    scanner = MultiExchangeScanner()
    scanner.init()
    
    if not scanner.handlers:
        print("❌ No exchanges initialized")
        return
    
    while True:
        try:
            print(f"\n{'='*50}")
            print(f"Starting scan at {utcnow().strftime('%H:%M:%S UTC')}")
            
            signals, watch, new_entries = scanner.scan_all()
            
            # Get trading summary
            trading_summary = scanner.paper_trading.get_summary()
            
            # Send separate entry notifications first
            if new_entries:
                for entry in new_entries:
                    entry_embed = entry_notification_embed(entry)
                    post_embeds([entry_embed])
                    print(f"📤 Sent entry notification for {entry['base']}")
            
            # Build main Discord message
            embeds = [header_embed(len(scanner.handlers), len(signals), trading_summary)]
            
            if signals:
                for i, sig in enumerate(signals, 1):
                    embeds.append(signal_embed(sig, i))
            else:
                embeds.append({
                    "title": "No Shorts Found",
                    "description": "Market not showing exhaustion",
                    "color": CFG.C["INFO"]
                })
            
            embeds.append(watchlist_embed(watch))
            post_embeds(embeds)
            
            print(f"✅ Complete: {len(signals)} signals, {len(watch)} watch")
            
            if not loop:
                break
            
            print(f"Next scan in {interval//60} minutes...")
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n⏹ Stopped")
            break
        except Exception as e:
            print(f"Main loop error: {e}")
            if not loop:
                break
            time.sleep(30)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=CFG.LOOP_SECONDS)
    ap.add_argument("--exchanges", nargs="+", help="Exchanges to scan")
    args = ap.parse_args()
    
    if args.exchanges:
        CFG.EXCHANGES = [e.lower() for e in args.exchanges]
    
    run(loop=args.loop, interval=args.interval)
