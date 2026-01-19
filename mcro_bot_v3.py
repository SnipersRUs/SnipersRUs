#!/usr/bin/env python3
"""
MCRO Bot — Enhanced Adaptive Scanner v3.0
Major improvements:
• Adaptive scanning frequency (15min to 1hr)
• Less strict parameters for better opportunity detection
• Top 150+ macro coins prioritized
• Your custom indicators integrated (VIPER, GPS, Vector Sniper)
• Silent scanning (no spam about failed scans)
"""

import os, json, time, math, traceback, requests, pytz
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import ccxt
import numpy as np
import pandas as pd
import config

# ========================= Core Configuration =========================
TZ_NY = pytz.timezone("America/New_York")
DATA_DIR = "data"
TRADES_JSON = os.path.join(DATA_DIR, "trades.json")
os.makedirs(DATA_DIR, exist_ok=True)

# Top 150 Macro Coins (prioritized for scanning)
TOP_MACRO_COINS = [
    # Tier 1: Major caps (scan every cycle)
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
    'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'MATIC/USDT', 'LINK/USDT',
    'UNI/USDT', 'ATOM/USDT', 'LTC/USDT', 'BCH/USDT', 'XLM/USDT',
    'NEAR/USDT', 'ICP/USDT', 'FIL/USDT', 'APT/USDT', 'ARB/USDT',
    'OP/USDT', 'INJ/USDT', 'TIA/USDT', 'SEI/USDT', 'SUI/USDT',
    
    # Tier 2: Strong mid-caps
    'PEPE/USDT', 'WIF/USDT', 'BONK/USDT', 'FLOKI/USDT', 'SHIB/USDT',
    'DOGE/USDT', 'RUNE/USDT', 'FTM/USDT', 'ALGO/USDT', 'VET/USDT',
    'AAVE/USDT', 'MKR/USDT', 'SNX/USDT', 'CRV/USDT', 'LDO/USDT',
    'GMX/USDT', 'DYDX/USDT', 'GRT/USDT', 'SAND/USDT', 'MANA/USDT',
    'AXS/USDT', 'GALA/USDT', 'ENJ/USDT', 'CHZ/USDT', 'IMX/USDT',
    'BLUR/USDT', 'CFX/USDT', 'MAGIC/USDT', 'JOE/USDT', 'PENDLE/USDT',
    
    # Tier 3: High volume alts
    'WLD/USDT', 'ORDI/USDT', 'PYTH/USDT', 'JTO/USDT', 'COMP/USDT',
    'YFI/USDT', 'SUSHI/USDT', '1INCH/USDT', 'BAL/USDT', 'TRX/USDT',
    'XMR/USDT', 'EOS/USDT', 'XTZ/USDT', 'THETA/USDT', 'HBAR/USDT',
    'EGLD/USDT', 'FLOW/USDT', 'KSM/USDT', 'QNT/USDT', 'ZEC/USDT',
    'DASH/USDT', 'NEO/USDT', 'WAVES/USDT', 'ZIL/USDT', 'ENS/USDT',
    'RPL/USDT', 'CAKE/USDT', 'BAKE/USDT', 'TWT/USDT', 'KAVA/USDT',
    
    # Add more as needed...
]

def now_str():
    return datetime.now(TZ_NY).strftime("%Y-%m-%d %H:%M:%S %Z")

def post_discord(content: str, embed=None):
    """Post to Discord webhook"""
    if not config.DISCORD_WEBHOOK:
        return
    try:
        payload = {"content": content} if content else {}
        if embed:
            payload["embeds"] = [embed]
        requests.post(config.DISCORD_WEBHOOK, json=payload)
    except:
        pass

# ========================= Custom Indicators (Your Indicators) =========================
def vwap_stack_detection(high, low, close, volume, timeframes=['1h', '4h', '8h', '12h']):
    """
    Detect VWAP stack from your VIPER indicator
    Returns: bullish_stack, bearish_stack, squeeze_percentage
    """
    vwaps = {}
    for tf_hours in [1, 4, 8, 12]:
        bars = tf_hours  # Simplified for this example
        tp = (high + low + close) / 3.0
        cum_pv = np.cumsum(tp * volume)
        cum_v = np.cumsum(volume)
        vwaps[f'{tf_hours}h'] = cum_pv[-1] / cum_v[-1] if cum_v[-1] > 0 else np.nan
    
    if all(not np.isnan(v) for v in vwaps.values()):
        vwap_max = max(vwaps.values())
        vwap_min = min(vwaps.values())
        squeeze_pct = (vwap_max - vwap_min) / vwap_max if vwap_max > 0 else 0
        
        # Bullish stack: 1H bottom, 12H top
        bullish = vwaps['1h'] <= vwaps['4h'] <= vwaps['8h'] <= vwaps['12h']
        # Bearish stack: 1H top, 12H bottom  
        bearish = vwaps['1h'] >= vwaps['4h'] >= vwaps['8h'] >= vwaps['12h']
        
        return bullish and squeeze_pct < 0.002, bearish and squeeze_pct < 0.002, squeeze_pct
    
    return False, False, 0

def golden_pocket_detection(high, low, current_price):
    """
    Detect if price is at golden pocket (0.618-0.65 fib) from GPS indicator
    """
    if len(high) < 50 or len(low) < 50:
        return False, None
    
    swing_high = np.max(high[-50:])
    swing_low = np.min(low[-50:])
    
    gp_high = swing_high - (swing_high - swing_low) * 0.618
    gp_low = swing_high - (swing_high - swing_low) * 0.65
    
    at_golden_pocket = gp_low <= current_price <= gp_high
    return at_golden_pocket, (gp_low, gp_high)

def vector_sniper_signals(high, low, close, volume, atr_val):
    """
    Simplified Vector Sniper logic from your indicator
    """
    if len(close) < 20:
        return False, False
    
    # Volume Z-score
    vol_mean = np.mean(volume[-20:])
    vol_std = np.std(volume[-20:])
    vol_z = (volume[-1] - vol_mean) / vol_std if vol_std > 0 else 0
    
    # ATR Z-score
    tr = high[-1] - low[-1]
    tr_z = (tr - np.mean(high[-20:] - low[-20:])) / np.std(high[-20:] - low[-20:])
    
    # Body percentage
    body = abs(close[-1] - close[-2])
    range_val = high[-1] - low[-1]
    body_pct = body / range_val if range_val > 0 else 0
    
    # Vector conditions
    bull_vector = (close[-1] > close[-2] and vol_z > 1.0 and tr_z > 1.2 and body_pct > 0.55)
    bear_vector = (close[-1] < close[-2] and vol_z > 1.0 and tr_z > 1.2 and body_pct > 0.55)
    
    return bull_vector, bear_vector

def rsi(series: np.ndarray, length: int = 14) -> float:
    """Calculate RSI"""
    if len(series) < length + 1:
        return 50.0
    
    delta = np.diff(series)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    
    avg_gain = np.mean(gain[-length:])
    avg_loss = np.mean(loss[-length:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def detect_divergence(price, indicator, lookback=20):
    """Detect divergences between price and indicator"""
    if len(price) < lookback or len(indicator) < lookback:
        return False, False
    
    # Find recent highs and lows
    price_high_idx = np.argmax(price[-lookback:])
    price_low_idx = np.argmin(price[-lookback:])
    
    # Bullish divergence: price makes lower low, indicator makes higher low
    bull_div = (price[-1] < price[-lookback:][price_low_idx] and 
                indicator[-1] > indicator[-lookback:][price_low_idx])
    
    # Bearish divergence: price makes higher high, indicator makes lower high
    bear_div = (price[-1] > price[-lookback:][price_high_idx] and 
                indicator[-1] < indicator[-lookback:][price_high_idx])
    
    return bull_div, bear_div

# ========================= Enhanced Scanner =========================
class AdaptiveScanner:
    def __init__(self):
        self.exchanges = {
            'mexc': ccxt.mexc(),
            'bybit': ccxt.bybit(),
            'binance': ccxt.binance(),
            'bitget': ccxt.bitget(),
        }
        
        # Load markets
        for name, ex in self.exchanges.items():
            try:
                ex.load_markets()
                print(f"[{name.upper()}] Loaded {len(ex.markets)} markets")
            except:
                pass
        
        self.last_scan_time = 0
        self.scan_interval = 3600  # Start with 1 hour
        self.no_signal_count = 0
        self.last_opportunities = []
    
    def get_best_exchange(self, symbol):
        """Find best exchange for a symbol"""
        for name, ex in self.exchanges.items():
            if symbol in ex.markets:
                return ex, name
        return None, None
    
    def scan_symbol(self, symbol):
        """Enhanced scan with your custom indicators"""
        try:
            ex, ex_name = self.get_best_exchange(symbol)
            if not ex:
                return None
            
            # Fetch data
            ohlcv_1h = ex.fetch_ohlcv(symbol, '1h', limit=100)
            if not ohlcv_1h or len(ohlcv_1h) < 50:
                return None
            
            # Convert to arrays
            ohlcv = np.array(ohlcv_1h)
            high = ohlcv[:, 2]
            low = ohlcv[:, 3]
            close = ohlcv[:, 4]
            volume = ohlcv[:, 5]
            
            current_price = close[-1]
            
            # Calculate ATR for stops
            atr = np.mean(high[-14:] - low[-14:])
            
            # Initialize confidence calculation
            confidence = 50.0  # Base confidence
            signals = []
            signal_weights = []
            
            # 1. VWAP Stack Detection (from VIPER) - High weight
            bull_stack, bear_stack, squeeze = vwap_stack_detection(high, low, close, volume)
            if bull_stack:
                confidence += 15
                signals.append("Bullish VWAP Stack")
                signal_weights.append(15)
            elif bear_stack:
                confidence += 15
                signals.append("Bearish VWAP Stack")
                signal_weights.append(15)
            
            # 2. Golden Pocket Detection (from GPS) - High weight
            at_gp, gp_levels = golden_pocket_detection(high, low, current_price)
            if at_gp:
                confidence += 12
                signals.append("At Golden Pocket")
                signal_weights.append(12)
            
            # 3. Vector Sniper Signals - High weight
            bull_vector, bear_vector = vector_sniper_signals(high, low, close, volume, atr)
            if bull_vector:
                confidence += 12
                signals.append("Bull Vector")
                signal_weights.append(12)
            elif bear_vector:
                confidence += 12
                signals.append("Bear Vector")
                signal_weights.append(12)
            
            # 4. RSI Conditions - Medium weight
            rsi_val = rsi(close)
            if rsi_val < 30:
                confidence += 8
                signals.append(f"RSI Oversold ({rsi_val:.0f})")
                signal_weights.append(8)
            elif rsi_val > 70:
                confidence += 8
                signals.append(f"RSI Overbought ({rsi_val:.0f})")
                signal_weights.append(8)
            elif rsi_val < 35:
                confidence += 5
                signals.append(f"RSI Low ({rsi_val:.0f})")
                signal_weights.append(5)
            elif rsi_val > 65:
                confidence += 5
                signals.append(f"RSI High ({rsi_val:.0f})")
                signal_weights.append(5)
            
            # 5. Support/Resistance Detection - Medium weight
            recent_high = np.max(high[-20:])
            recent_low = np.min(low[-20:])
            
            near_resistance = abs(current_price - recent_high) / current_price < 0.01
            near_support = abs(current_price - recent_low) / current_price < 0.01
            
            if near_resistance:
                confidence += 7
                signals.append("Near Resistance")
                signal_weights.append(7)
            elif near_support:
                confidence += 7
                signals.append("Near Support")
                signal_weights.append(7)
            
            # 6. Volume Spike - Medium weight
            vol_avg = np.mean(volume[-20:])
            if volume[-1] > vol_avg * 2.0:
                confidence += 10
                signals.append("Strong Volume Spike")
                signal_weights.append(10)
            elif volume[-1] > vol_avg * 1.5:
                confidence += 6
                signals.append("Volume Spike")
                signal_weights.append(6)
            
            # 7. Divergence Detection - High weight
            rsi_series = [rsi(close[:i+1]) for i in range(len(close)-20, len(close))]
            bull_div, bear_div = detect_divergence(close[-20:], rsi_series, 20)
            
            if bull_div:
                confidence += 10
                signals.append("Bullish Divergence")
                signal_weights.append(10)
            elif bear_div:
                confidence += 10
                signals.append("Bearish Divergence")
                signal_weights.append(10)
            
            # Cap confidence at 95% max
            confidence = min(95, confidence)
            
            # Minimum 60% confidence for watchlist
            if confidence < 60:
                return None
            
            # Determine trade direction
            bullish_signals = bull_stack or bull_vector or (rsi_val < 30 and near_support) or bull_div
            bearish_signals = bear_stack or bear_vector or (rsi_val > 70 and near_resistance) or bear_div
            
            if bullish_signals:
                side = "LONG"
                entry = current_price
                sl = current_price - atr * 1.5
                tp1 = current_price + atr * 2
                tp2 = current_price + atr * 4
            elif bearish_signals:
                side = "SHORT"
                entry = current_price
                sl = current_price + atr * 1.5
                tp1 = current_price - atr * 2
                tp2 = current_price - atr * 4
            else:
                return None
            
            return {
                'symbol': symbol,
                'exchange': ex_name,
                'side': side,
                'entry': entry,
                'sl': sl,
                'tp1': tp1,
                'tp2': tp2,
                'score': confidence,
                'signals': signals,
                'rsi': rsi_val,
                'volume_ratio': volume[-1] / vol_avg
            }
            
        except Exception as e:
            return None
    
    def scan_all_coins(self):
        """Scan all prioritized coins"""
        opportunities = []
        
        # Scan top macro coins first
        for symbol in TOP_MACRO_COINS:
            result = self.scan_symbol(symbol)
            if result:
                opportunities.append(result)
        
        # Then scan additional coins if needed
        all_symbols = set()
        for ex in self.exchanges.values():
            if ex.markets:
                all_symbols.update(ex.markets.keys())
        
        # Filter for USDT pairs with good volume
        additional_symbols = [s for s in all_symbols 
                            if s.endswith('/USDT') 
                            and s not in TOP_MACRO_COINS]
        
        # Scan up to 100 additional symbols
        for symbol in additional_symbols[:100]:
            if len(opportunities) >= 20:  # Limit total opportunities
                break
            
            result = self.scan_symbol(symbol)
            if result:
                opportunities.append(result)
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities
    
    def adaptive_scan(self):
        """Adaptive scanning with dynamic frequency"""
        current_time = time.time()
        
        # Check if it's time to scan
        if current_time - self.last_scan_time < self.scan_interval:
            return None
        
        # Perform scan
        opportunities = self.scan_all_coins()
        self.last_scan_time = current_time
        
        # Adjust scan frequency based on results
        if opportunities:
            # Found opportunities - reset to normal interval
            self.scan_interval = 3600  # 1 hour
            self.no_signal_count = 0
            
            # Filter by quality
            high_quality = [o for o in opportunities if o['score'] >= 70]
            watchlist = [o for o in opportunities if 50 <= o['score'] < 70]
            
            return {
                'high_quality': high_quality,
                'watchlist': watchlist,
                'total': len(opportunities)
            }
        else:
            # No opportunities - increase scan frequency
            self.no_signal_count += 1
            
            if self.no_signal_count >= 2:
                self.scan_interval = 900  # 15 minutes
            elif self.no_signal_count >= 4:
                self.scan_interval = 600  # 10 minutes
            
            return None

# ========================= Discord Formatting =========================
def create_trade_card(trade):
    """Create formatted Discord embed for trades"""
    color = 0x00ff00 if trade['side'] == 'LONG' else 0x800080
    emoji = "🟢" if trade['side'] == 'LONG' else "🟣"
    
    return {
        "title": f"{emoji} {trade['symbol']} - {trade['side']}",
        "description": f"**Score:** {trade['score']}/100\n**Exchange:** {trade['exchange']}",
        "color": color,
        "fields": [
            {
                "name": "📊 Entry",
                "value": f"${trade['entry']:.6f}",
                "inline": True
            },
            {
                "name": "🛑 Stop Loss",
                "value": f"${trade['sl']:.6f}",
                "inline": True
            },
            {
                "name": "🎯 Targets",
                "value": f"TP1: ${trade['tp1']:.6f}\nTP2: ${trade['tp2']:.6f}",
                "inline": True
            },
            {
                "name": "📈 Signals",
                "value": " + ".join(trade['signals'][:3]),
                "inline": False
            },
            {
                "name": "📊 Indicators",
                "value": f"RSI: {trade['rsi']:.0f} | Vol: {trade['volume_ratio']:.1f}x",
                "inline": False
            }
        ],
        "footer": {
            "text": f"MCRO Scanner • {trade['exchange'].upper()}"
        },
        "timestamp": datetime.now(TZ_NY).isoformat()
    }

def create_watchlist_embed(watchlist):
    """Create watchlist embed"""
    fields = []
    
    for trade in watchlist[:6]:  # Show top 6
        emoji = "🟢" if trade['side'] == 'LONG' else "🟣"
        fields.append({
            "name": f"{emoji} {trade['symbol']}",
            "value": f"Score: {trade['score']}/100\n{trade['side']} @ ${trade['entry']:.6f}",
            "inline": True
        })
    
    return {
        "title": "👀 Watchlist (6-7/10 Quality)",
        "description": "Potential setups developing",
        "color": 0xffa500,
        "fields": fields,
        "footer": {
            "text": "MCRO Scanner • Watchlist"
        },
        "timestamp": datetime.now(TZ_NY).isoformat()
    }

# ========================= Main Loop =========================
def main():
    print("🚀 MCRO Bot - Adaptive Scanner v3.0")
    print("=" * 50)
    
    scanner = AdaptiveScanner()
    
    # Silent startup - no initial notification to avoid spam
    
    last_status_update = 0
    
    while True:
        try:
            # Adaptive scanning
            scan_result = scanner.adaptive_scan()
            
            if scan_result:
                # Process high quality trades (7-10/10)
                if scan_result['high_quality']:
                    for trade in scan_result['high_quality'][:3]:
                        embed = create_trade_card(trade)
                        post_discord("", embed)
                        time.sleep(1)
                
                # Show watchlist (5-7/10)
                if scan_result['watchlist']:
                    watchlist_embed = create_watchlist_embed(scan_result['watchlist'])
                    post_discord("", watchlist_embed)
                
                print(f"[SCAN] Found {scan_result['total']} opportunities")
            
            # Status update only when significant changes occur
            current_time = time.time()
            if current_time - last_status_update > 86400:  # Only once per day
                # Only post status if there's been significant activity
                if scanner.no_signal_count > 10 or len(scanner.last_opportunities) > 0:
                    status_embed = {
                        "title": "📊 Scanner Status",
                        "description": "Active and scanning",
                        "color": 0x00bfff,
                        "fields": [
                            {
                                "name": "⏰ Current Interval",
                                "value": f"{scanner.scan_interval/60:.0f} minutes",
                                "inline": True
                            },
                            {
                                "name": "📈 Scans without signals",
                                "value": str(scanner.no_signal_count),
                                "inline": True
                            }
                        ],
                        "timestamp": datetime.now(TZ_NY).isoformat()
                    }
                    post_discord("", status_embed)
                    last_status_update = current_time
            
            # Sleep for 1 minute before next check
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Scanner stopped")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
