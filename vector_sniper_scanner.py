#!/usr/bin/env python3
"""
Vector Sniper Pro Scanner
Advanced market scanner using Vector Sniper Pro indicator logic
Scans MEXC, Bybit, and Binance for trading opportunities
"""

import asyncio
import time
import json
import logging
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
import ccxt
from dataclasses import dataclass

# Configuration
DISCORD_WEBHOOK = ""

# Exchange configurations
EXCHANGES = {
    'mexc': {
        'class': ccxt.mexc,
        'sandbox': False,
        'rateLimit': 1000,
        'enableRateLimit': True
    },
    'bybit': {
        'class': ccxt.bybit,
        'sandbox': False,
        'rateLimit': 1000,
        'enableRateLimit': True
    },
    'binance': {
        'class': ccxt.binance,
        'sandbox': False,
        'rateLimit': 1000,
        'enableRateLimit': True
    }
}

# Vector Sniper Pro Parameters
VECTOR_PARAMS = {
    'atr_len': 14,
    'vol_len': 20,
    'tr_z_thr': 1.2,
    'vol_z_thr': 1.0,
    'ext_mult': 1.8,
    'min_body_pct': 55,
    'lb_break': 5,
    'use_break': True,
    'use_trap': True,
    'pre_min_score': 4,
    'persist_n': 2,
    'persist_window': 4,
    'cooldown_bars': 6,
    'conflict_lock': 4,
    'use_vwap': True,
    'use_ema': True,
    'ema_len': 50,
    'use_htf': False,
    'htf': '60'
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vector_sniper_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class VectorSignal:
    """Vector Sniper Pro signal data"""
    symbol: str
    exchange: str
    direction: str  # 'BULL' or 'BEAR'
    signal_type: str  # 'VECTOR', 'EXTREME', 'PRE'
    price: float
    confidence: float
    score: int
    reason: str
    tradingview_link: str
    timestamp: datetime

class VectorSniperScanner:
    """Vector Sniper Pro Scanner Implementation"""
    
    def __init__(self):
        self.exchanges = {}
        self.signals = []
        self.last_scan_time = None
        self.setup_exchanges()
        
    def setup_exchanges(self):
        """Initialize exchange connections"""
        for name, config in EXCHANGES.items():
            try:
                exchange_class = config['class']
                self.exchanges[name] = exchange_class({
                    'sandbox': config['sandbox'],
                    'rateLimit': config['rateLimit'],
                    'enableRateLimit': config['enableRateLimit']
                })
                logger.info(f"✅ {name.upper()} exchange initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {name.upper()}: {e}")
    
    def z_score(self, data: np.ndarray, window: int) -> np.ndarray:
        """Calculate Z-score"""
        if len(data) < window:
            return np.zeros(len(data))
        
        result = np.zeros(len(data))
        for i in range(window - 1, len(data)):
            window_data = data[i - window + 1:i + 1]
            mean = np.mean(window_data)
            std = np.std(window_data)
            if std == 0:
                result[i] = 0
            else:
                result[i] = (data[i] - mean) / std
        
        return result
    
    def calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        """Calculate Average True Range"""
        tr = np.maximum(
            high - low,
            np.maximum(
                np.abs(high - np.roll(close, 1)),
                np.abs(low - np.roll(close, 1))
            )
        )
        tr[0] = high[0] - low[0]  # First value
        
        atr = np.zeros(len(tr))
        atr[period-1] = np.mean(tr[:period])
        
        for i in range(period, len(tr)):
            atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
        
        return atr
    
    def calculate_vwap(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """Calculate Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        vwap = np.zeros(len(typical_price))
        
        cumulative_volume = np.cumsum(volume)
        cumulative_tp_volume = np.cumsum(typical_price * volume)
        
        for i in range(len(vwap)):
            if cumulative_volume[i] > 0:
                vwap[i] = cumulative_tp_volume[i] / cumulative_volume[i]
            else:
                vwap[i] = typical_price[i]
        
        return vwap
    
    def calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        alpha = 2.0 / (period + 1)
        ema = np.zeros(len(data))
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        
        return ema
    
    def detect_vector_signals(self, ohlcv: List[List], symbol: str, exchange: str) -> List[VectorSignal]:
        """Detect Vector Sniper Pro signals from OHLCV data"""
        if len(ohlcv) < 50:  # Need sufficient data
            return []
        
        # Convert to numpy arrays
        data = np.array(ohlcv)
        timestamps = data[:, 0]
        opens = data[:, 1]
        highs = data[:, 2]
        lows = data[:, 3]
        closes = data[:, 4]
        volumes = data[:, 5]
        
        signals = []
        
        try:
            # Calculate indicators
            atr1 = self.calculate_atr(highs, lows, closes, 1)
            atr10 = self.calculate_atr(highs, lows, closes, 10)
            atr14 = self.calculate_atr(highs, lows, closes, 14)
            
            # Z-scores
            tr_z = self.z_score(atr1, VECTOR_PARAMS['atr_len'])
            vol_z = self.z_score(volumes, VECTOR_PARAMS['vol_len'])
            
            # Price calculations
            ranges = np.maximum(highs - lows, 1e-10)
            bodies = np.abs(closes - opens)
            body_pct = (bodies / ranges) * 100.0
            
            # Volume analysis
            avg_vol = np.mean(volumes[-20:]) if len(volumes) >= 20 else np.mean(volumes)
            vol_ratio = volumes / np.maximum(avg_vol, 1e-10)
            
            # VWAP and EMA
            vwap = self.calculate_vwap(highs, lows, closes, volumes)
            ema = self.calculate_ema(closes, VECTOR_PARAMS['ema_len'])
            
            # VWAP and EMA trends
            vwap_up = vwap[-1] > vwap[-2] if len(vwap) > 1 else False
            vwap_down = vwap[-1] < vwap[-2] if len(vwap) > 1 else False
            ema_up = ema[-1] > ema[-2] if len(ema) > 1 else False
            ema_down = ema[-1] < ema[-2] if len(ema) > 1 else False
            
            # Structure breaks
            if len(highs) >= VECTOR_PARAMS['lb_break'] + 1:
                prev_high = np.max(highs[-(VECTOR_PARAMS['lb_break']+1):-1])
                prev_low = np.min(lows[-(VECTOR_PARAMS['lb_break']+1):-1])
                bull_break = highs[-1] > prev_high
                bear_break = lows[-1] < prev_low
            else:
                bull_break = bear_break = False
            
            # Traps detection
            if len(ohlcv) >= 3:
                bear_trap = (lows[-1] < lows[-2] and lows[-1] < lows[-3] and 
                           closes[-1] > highs[-2])
                bull_trap = (highs[-1] > highs[-2] and highs[-1] > highs[-3] and 
                           closes[-1] < lows[-2])
            else:
                bear_trap = bull_trap = False
            
            # Delta volume approximation
            bull_vol = volumes[-1] * (closes[-1] - lows[-1]) / ranges[-1]
            bear_vol = volumes[-1] * (highs[-1] - closes[-1]) / ranges[-1]
            delta = bull_vol - bear_vol
            delta_ratio = delta / np.maximum(volumes[-1], 1e-10)
            
            # Base vector conditions
            current_close = closes[-1]
            current_open = opens[-1]
            current_tr_z = tr_z[-1]
            current_vol_z = vol_z[-1]
            current_body_pct = body_pct[-1]
            current_vol_ratio = vol_ratio[-1]
            
            # Bull conditions
            base_bull = (current_close > current_open and 
                        current_tr_z >= VECTOR_PARAMS['tr_z_thr'] and
                        current_vol_z >= VECTOR_PARAMS['vol_z_thr'] and
                        current_body_pct >= VECTOR_PARAMS['min_body_pct'] and
                        delta_ratio > 0.2)
            
            # Bear conditions
            base_bear = (current_close < current_open and 
                        current_tr_z >= VECTOR_PARAMS['tr_z_thr'] and
                        current_vol_z >= VECTOR_PARAMS['vol_z_thr'] and
                        current_body_pct >= VECTOR_PARAMS['min_body_pct'] and
                        delta_ratio < -0.2)
            
            # Vector conditions
            bull_cond = (base_bull and (not VECTOR_PARAMS['use_break'] or bull_break)) or bear_trap
            bear_cond = (base_bear and (not VECTOR_PARAMS['use_break'] or bear_break)) or bull_trap
            
            # Extreme conditions
            ext_bull = bull_cond and (current_tr_z >= VECTOR_PARAMS['tr_z_thr'] * VECTOR_PARAMS['ext_mult'] and
                                    current_vol_z >= VECTOR_PARAMS['vol_z_thr'] * VECTOR_PARAMS['ext_mult'])
            ext_bear = bear_cond and (current_tr_z >= VECTOR_PARAMS['tr_z_thr'] * VECTOR_PARAMS['ext_mult'] and
                                    current_vol_z >= VECTOR_PARAMS['vol_z_thr'] * VECTOR_PARAMS['ext_mult'])
            
            # Pre-signal scoring
            spring = (lows[-1] < np.min(lows[-4:-1]) and closes[-1] > np.min(lows[-4:-1]) and current_vol_ratio > 1.0)
            upthrust = (highs[-1] > np.max(highs[-4:-1]) and closes[-1] < np.max(highs[-4:-1]) and current_vol_ratio > 1.0)
            
            no_supply = (closes[-1] > closes[-2] and volumes[-1] < volumes[-2] and ranges[-1] < atr10[-1] * 0.7)
            no_demand = (closes[-1] < closes[-2] and volumes[-1] < volumes[-2] and ranges[-1] < atr10[-1] * 0.7)
            
            imb_bull = delta_ratio > 0.25
            imb_bear = delta_ratio < -0.25
            
            # Side alignment
            bull_side_ok = ((not VECTOR_PARAMS['use_vwap'] or (current_close > vwap[-1] and vwap_up)) and
                          (not VECTOR_PARAMS['use_ema'] or ema_up))
            bear_side_ok = ((not VECTOR_PARAMS['use_vwap'] or (current_close < vwap[-1] and vwap_down)) and
                          (not VECTOR_PARAMS['use_ema'] or ema_down))
            
            # Calculate scores
            bull_score = sum([
                spring, no_supply, imb_bull, current_vol_ratio > 1.2, 
                bull_side_ok, current_close > current_open
            ])
            
            bear_score = sum([
                upthrust, no_demand, imb_bear, current_vol_ratio > 1.2,
                bear_side_ok, current_close < current_open
            ])
            
            # Generate signals
            current_price = closes[-1]
            
            # Create correct TradingView links based on exchange
            if exchange == 'mexc':
                # MEXC futures format - convert to TradingView format
                # SYND/USDT:USDT -> SYNDUSDT.P
                base_symbol = symbol.split('/')[0] if '/' in symbol else symbol
                tv_symbol = f"{base_symbol}USDT.P"
                tv_link = f"https://www.tradingview.com/chart/?symbol=MEXC:{tv_symbol}"
            elif exchange == 'bybit':
                tv_link = f"https://www.tradingview.com/chart/?symbol=BYBIT:{symbol}"
            elif exchange == 'binance':
                tv_link = f"https://www.tradingview.com/chart/?symbol=BINANCE:{symbol}"
            else:
                tv_link = f"https://www.tradingview.com/chart/?symbol={exchange.upper()}:{symbol}"
            
            # Bull signals
            if ext_bull:
                signals.append(VectorSignal(
                    symbol=symbol,
                    exchange=exchange,
                    direction='BULL',
                    signal_type='EXTREME',
                    price=current_price,
                    confidence=min(95, 70 + (current_tr_z * 10)),
                    score=bull_score,
                    reason=f"Extreme Bull Vector - TR Z: {current_tr_z:.2f}, Vol Z: {current_vol_z:.2f}",
                    tradingview_link=tv_link,
                    timestamp=datetime.now(timezone.utc)
                ))
            elif bull_cond:
                signals.append(VectorSignal(
                    symbol=symbol,
                    exchange=exchange,
                    direction='BULL',
                    signal_type='VECTOR',
                    price=current_price,
                    confidence=min(85, 60 + (current_tr_z * 8)),
                    score=bull_score,
                    reason=f"Bull Vector - TR Z: {current_tr_z:.2f}, Vol Z: {current_vol_z:.2f}",
                    tradingview_link=tv_link,
                    timestamp=datetime.now(timezone.utc)
                ))
            elif bull_score >= VECTOR_PARAMS['pre_min_score']:
                signals.append(VectorSignal(
                    symbol=symbol,
                    exchange=exchange,
                    direction='BULL',
                    signal_type='PRE',
                    price=current_price,
                    confidence=min(75, 50 + (bull_score * 5)),
                    score=bull_score,
                    reason=f"Pre-Bull Signal - Score: {bull_score}/7",
                    tradingview_link=tv_link,
                    timestamp=datetime.now(timezone.utc)
                ))
            
            # Bear signals
            if ext_bear:
                signals.append(VectorSignal(
                    symbol=symbol,
                    exchange=exchange,
                    direction='BEAR',
                    signal_type='EXTREME',
                    price=current_price,
                    confidence=min(95, 70 + (current_tr_z * 10)),
                    score=bear_score,
                    reason=f"Extreme Bear Vector - TR Z: {current_tr_z:.2f}, Vol Z: {current_vol_z:.2f}",
                    tradingview_link=tv_link,
                    timestamp=datetime.now(timezone.utc)
                ))
            elif bear_cond:
                signals.append(VectorSignal(
                    symbol=symbol,
                    exchange=exchange,
                    direction='BEAR',
                    signal_type='VECTOR',
                    price=current_price,
                    confidence=min(85, 60 + (current_tr_z * 8)),
                    score=bear_score,
                    reason=f"Bear Vector - TR Z: {current_tr_z:.2f}, Vol Z: {current_vol_z:.2f}",
                    tradingview_link=tv_link,
                    timestamp=datetime.now(timezone.utc)
                ))
            elif bear_score >= VECTOR_PARAMS['pre_min_score']:
                signals.append(VectorSignal(
                    symbol=symbol,
                    exchange=exchange,
                    direction='BEAR',
                    signal_type='PRE',
                    price=current_price,
                    confidence=min(75, 50 + (bear_score * 5)),
                    score=bear_score,
                    reason=f"Pre-Bear Signal - Score: {bear_score}/7",
                    tradingview_link=tv_link,
                    timestamp=datetime.now(timezone.utc)
                ))
        
        except Exception as e:
            logger.error(f"Error analyzing {symbol} on {exchange}: {e}")
        
        return signals
    
    async def get_symbols(self, exchange_name: str, limit: int = 50) -> List[str]:
        """Get trading symbols from exchange"""
        try:
            exchange = self.exchanges[exchange_name]
            markets = await asyncio.get_event_loop().run_in_executor(
                None, exchange.load_markets
            )
            
            symbols = []
            for symbol, market in markets.items():
                if exchange_name == 'mexc':
                    # For MEXC, prioritize futures contracts
                    if (market['quote'] == 'USDT' and 
                        market['active'] and 
                        market['type'] in ['future', 'swap'] and
                        'USDT' in symbol):
                        symbols.append(symbol)
                else:
                    # For other exchanges, use spot
                    if (market['quote'] == 'USDT' and 
                        market['active'] and 
                        market['type'] == 'spot' and
                        'USDT' in symbol):
                        symbols.append(symbol)
            
            return symbols[:limit]
        
        except Exception as e:
            logger.error(f"Error getting symbols from {exchange_name}: {e}")
            return []
    
    async def get_ohlcv(self, exchange_name: str, symbol: str, timeframe: str = '1m', limit: int = 100) -> List[List]:
        """Get OHLCV data from exchange"""
        try:
            exchange = self.exchanges[exchange_name]
            ohlcv = await asyncio.get_event_loop().run_in_executor(
                None, exchange.fetch_ohlcv, symbol, timeframe, None, limit
            )
            return ohlcv
        
        except Exception as e:
            logger.error(f"Error getting OHLCV for {symbol} on {exchange_name}: {e}")
            return []
    
    async def scan_exchange(self, exchange_name: str) -> List[VectorSignal]:
        """Scan single exchange for Vector Sniper signals"""
        logger.info(f"🔍 Scanning {exchange_name.upper()}...")
        all_signals = []
        
        try:
            # Get symbols - more for MEXC futures
            if exchange_name == 'mexc':
                symbols = await self.get_symbols(exchange_name, limit=100)  # More MEXC futures
            else:
                symbols = await self.get_symbols(exchange_name, limit=50)
            
            logger.info(f"📊 Found {len(symbols)} symbols on {exchange_name.upper()}")
            
            # Scan each symbol
            for symbol in symbols:
                try:
                    ohlcv = await self.get_ohlcv(exchange_name, symbol, '1m', 100)
                    if ohlcv:
                        signals = self.detect_vector_signals(ohlcv, symbol, exchange_name)
                        all_signals.extend(signals)
                        
                        if signals:
                            logger.info(f"🎯 {symbol} on {exchange_name.upper()}: {len(signals)} signals")
                
                except Exception as e:
                    logger.error(f"Error scanning {symbol} on {exchange_name}: {e}")
                    continue
                
                # Rate limiting - faster for MEXC
                if exchange_name == 'mexc':
                    await asyncio.sleep(0.05)  # Faster for MEXC
                else:
                    await asyncio.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Error scanning {exchange_name}: {e}")
        
        return all_signals
    
    async def scan_all_exchanges(self) -> List[VectorSignal]:
        """Scan all exchanges for Vector Sniper signals"""
        logger.info("🚀 Starting Vector Sniper Pro scan...")
        all_signals = []
        
        # Scan each exchange
        for exchange_name in self.exchanges.keys():
            signals = await self.scan_exchange(exchange_name)
            all_signals.extend(signals)
            logger.info(f"✅ {exchange_name.upper()}: {len(signals)} signals found")
        
        # Sort by confidence
        all_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        logger.info(f"🎯 Total signals found: {len(all_signals)}")
        return all_signals
    
    def create_discord_embed(self, signals: List[VectorSignal]) -> Dict:
        """Create Discord embed for signals"""
        if not signals:
            return {
                "embeds": [{
                    "title": "🔍 Vector Sniper Pro Scan Complete",
                    "description": "No signals found in this scan.",
                    "color": 0x808080,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }]
            }
        
        # Group signals by type
        vector_signals = [s for s in signals if s.signal_type == 'VECTOR']
        extreme_signals = [s for s in signals if s.signal_type == 'EXTREME']
        pre_signals = [s for s in signals if s.signal_type == 'PRE']
        
        embeds = []
        
        # Extreme signals (highest priority)
        if extreme_signals:
            desc = "**🚀 EXTREME VECTOR SIGNALS**\n\n"
            for signal in extreme_signals[:5]:  # Top 5
                emoji = "🟢" if signal.direction == 'BULL' else "🔴"
                desc += f"{emoji} **[{signal.symbol}]({signal.tradingview_link})** ({signal.exchange.upper()})\n"
                desc += f"   Price: ${signal.price:.4f} | Confidence: {signal.confidence:.0f}%\n"
                desc += f"   {signal.reason}\n\n"
            
            embeds.append({
                "title": "🚀 EXTREME VECTOR SIGNALS",
                "description": desc,
                "color": 0xff6b6b,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {"text": "Vector Sniper Pro - Extreme Signals"}
            })
        
        # Vector signals
        if vector_signals:
            desc = "**⚡ VECTOR SIGNALS**\n\n"
            for signal in vector_signals[:8]:  # Top 8
                emoji = "🟢" if signal.direction == 'BULL' else "🔴"
                desc += f"{emoji} **[{signal.symbol}]({signal.tradingview_link})** ({signal.exchange.upper()})\n"
                desc += f"   Price: ${signal.price:.4f} | Confidence: {signal.confidence:.0f}%\n"
                desc += f"   {signal.reason}\n\n"
            
            embeds.append({
                "title": "⚡ VECTOR SIGNALS",
                "description": desc,
                "color": 0x4ecdc4,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {"text": "Vector Sniper Pro - Vector Signals"}
            })
        
        # Pre-signals
        if pre_signals:
            desc = "**📘 PRE-SIGNALS**\n\n"
            for signal in pre_signals[:10]:  # Top 10
                emoji = "🟢" if signal.direction == 'BULL' else "🔴"
                desc += f"{emoji} **[{signal.symbol}]({signal.tradingview_link})** ({signal.exchange.upper()})\n"
                desc += f"   Price: ${signal.price:.4f} | Score: {signal.score}/7\n"
                desc += f"   {signal.reason}\n\n"
            
            embeds.append({
                "title": "📘 PRE-SIGNALS",
                "description": desc,
                "color": 0x3498db,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {"text": "Vector Sniper Pro - Pre-Signals"}
            })
        
        # Summary
        summary_desc = f"**📊 SCAN SUMMARY**\n\n"
        summary_desc += f"🔍 **Exchanges Scanned**: MEXC, Bybit, Binance\n"
        summary_desc += f"🚀 **Extreme Signals**: {len(extreme_signals)}\n"
        summary_desc += f"⚡ **Vector Signals**: {len(vector_signals)}\n"
        summary_desc += f"📘 **Pre-Signals**: {len(pre_signals)}\n"
        summary_desc += f"🎯 **Total Signals**: {len(signals)}\n\n"
        summary_desc += f"**Primary Trading Exchange**: MEXC\n"
        summary_desc += f"**TradingView Links**: Click symbol names for charts\n\n"
        summary_desc += f"⚠️ **Risk Warning**: High-risk trading. Use proper risk management."
        
        embeds.append({
            "title": "📊 Vector Sniper Pro Scan Complete",
            "description": summary_desc,
            "color": 0x00ff00,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {"text": "Vector Sniper Pro Scanner - Educational Only"}
        })
        
        return {"embeds": embeds}
    
    async def send_discord_notification(self, signals: List[VectorSignal]) -> bool:
        """Send Discord notification with signals"""
        try:
            payload = self.create_discord_embed(signals)
            
            response = requests.post(
                DISCORD_WEBHOOK,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 204:
                logger.info("✅ Discord notification sent successfully")
                return True
            else:
                logger.error(f"❌ Discord error: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error sending Discord notification: {e}")
            return False
    
    async def run_scan(self) -> List[VectorSignal]:
        """Run complete Vector Sniper Pro scan"""
        logger.info("🎯 Starting Vector Sniper Pro scan...")
        start_time = time.time()
        
        # Scan all exchanges
        signals = await self.scan_all_exchanges()
        
        # Send Discord notification
        if signals:
            await self.send_discord_notification(signals)
        else:
            # Send "no signals" notification
            await self.send_discord_notification([])
        
        scan_time = time.time() - start_time
        logger.info(f"✅ Scan completed in {scan_time:.2f} seconds")
        
        return signals

async def main():
    """Main scanner function"""
    scanner = VectorSniperScanner()
    
    try:
        # Run initial scan
        signals = await scanner.run_scan()
        
        # Run continuous scans every 30 minutes
        while True:
            logger.info("⏰ Waiting 30 minutes for next scan...")
            await asyncio.sleep(1800)  # 30 minutes
            
            signals = await scanner.run_scan()
    
    except KeyboardInterrupt:
        logger.info("🛑 Scanner stopped by user")
    except Exception as e:
        logger.error(f"❌ Scanner error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
