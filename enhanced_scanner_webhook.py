#!/usr/bin/env python3
"""
Enhanced Trading Bot Scanner with Live Price/VWAP Integration
Fixed version with proper signal detection and confidence scoring
"""
import ccxt
import pandas as pd
import numpy as np
import time
import os
import asyncio
import aiohttp
from datetime import datetime

class EnhancedScanner:
    def __init__(self):
        self.config = {
            'use_vwap_stack': True,
            'use_divergence': True,
            'use_volume_spike': True,
            'use_sfp_plays': True,
            
            # Entry Management
            'wait_for_entry': True,
            'entry_buffer_pct': 0.001,   # 0.1%
            'stop_loss_pct': 0.015,      # 1.5%
            'min_rr_ratio': 2.0,
            
            # Signal Filters
            'min_volume_multiplier': 1.5,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'min_divergence_bars': 5,
            
            # Confidence thresholds
            'min_confidence_trade': 75,  # 75% for trades
            'min_confidence_watch': 60,  # 60% for watchlist
            
            # PnL Updates
            'update_pnl_on_close_only': True,
            'status_update_hours': 12,
        }
        
        self.pending_signals = []
        self.active_positions = []
        
        # Discord webhook
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK', '')
        self.session = None
        
        # Exchange pool for live data
        self._ex_ids = ["mexc", "bybit", "bitget", "binance"]
        self._ex_map = {}
        
        # Initialize exchanges
        self._init_exchanges()
    
    async def _init_discord(self):
        """Initialize Discord session"""
        if self.discord_webhook and not self.session:
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)
    
    async def _send_discord_alert(self, title, description, color=0x3498db):
        """Send Discord alert"""
        if not self.discord_webhook or not self.session:
            return False
        
        try:
            payload = {
                "embeds": [{
                    "title": title,
                    "description": description,
                    "color": color,
                    "timestamp": datetime.now().isoformat(),
                    "footer": {"text": "Enhanced Scanner Bot"}
                }]
            }
            
            async with self.session.post(
                self.discord_webhook,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                return response.status == 204
        except Exception as e:
            print(f"[ERROR] Discord alert failed: {e}")
            return False
    
    async def _send_startup_notification(self):
        """Send startup notification to Discord"""
        await self._send_discord_alert(
            "🚀 Enhanced Scanner Started",
            f"**Status**: Online and scanning\n"
            f"**Symbols**: 12 pairs\n"
            f"**Min Trade Confidence**: {self.config['min_confidence_trade']}%\n"
            f"**Min Watch Confidence**: {self.config['min_confidence_watch']}%\n"
            f"**Scan Frequency**: Every hour",
            0x00ff00
        )
    
    async def _send_signal_alert(self, signal):
        """Send signal alert to Discord"""
        direction_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
        await self._send_discord_alert(
            f"{direction_emoji} High Confidence Signal",
            f"**Symbol**: {signal['symbol']}\n"
            f"**Direction**: {signal['direction']}\n"
            f"**Confidence**: {signal['confidence']:.0f}%\n"
            f"**Reasons**: {', '.join(signal['reasons'])}",
            0xff6b6b if signal['direction'] == 'SHORT' else 0x4ecdc4
        )
    
    async def _send_order_alert(self, order):
        """Send order execution alert to Discord"""
        direction_emoji = "🟢" if order['direction'] == 'LONG' else "🔴"
        await self._send_discord_alert(
            f"{direction_emoji} Order Executed",
            f"**Symbol**: {order['symbol']}\n"
            f"**Direction**: {order['direction']}\n"
            f"**Entry**: ${order['actual_entry']:.6f}\n"
            f"**Stop Loss**: ${order['stop_loss']:.6f}\n"
            f"**Take Profit**: ${order['take_profit']:.6f}\n"
            f"**R:R Ratio**: {order['rr_ratio']:.2f}\n"
            f"**Confidence**: {order['confidence']:.0f}%",
            0x00ff00
        )
    
    def _init_exchanges(self):
        """Initialize exchange connections"""
        for ex_id in self._ex_ids:
            try:
                ex = getattr(ccxt, ex_id)({'enableRateLimit': True})
                ex.load_markets()
                self._ex_map[ex_id] = ex
                print(f"[INFO] Connected to {ex_id}: {len(ex.markets)} markets")
            except Exception as e:
                print(f"[WARN] Failed to connect to {ex_id}: {e}")
    
    def _ex(self, ex_id):
        """Get exchange instance"""
        if ex_id not in self._ex_map:
            try:
                ex = getattr(ccxt, ex_id)({'enableRateLimit': True})
                ex.load_markets()
                self._ex_map[ex_id] = ex
            except:
                return None
        return self._ex_map.get(ex_id)
    
    def _candidates(self, symbol):
        """Generate symbol candidates for different exchanges"""
        if "/" in symbol:
            s1 = symbol
        else:
            s1 = f"{symbol}/USDT"
        return [
            s1,
            s1.replace("/USDT", "/USDT:USDT"),
            s1.replace("/", "")  # e.g., BTCUSDT
        ]
    
    def get_current_price(self, symbol):
        """Get current price from first available exchange"""
        for ex_id in self._ex_ids:
            ex = self._ex(ex_id)
            if not ex:
                continue
            for s in self._candidates(symbol):
                try:
                    if s in ex.markets:
                        t = ex.fetch_ticker(s)
                        px = float(t.get("last", t.get("close", 0)))
                        if px > 0:
                            return px
                except Exception:
                    continue
        return 0.0
    
    def get_vwap(self, symbol, timeframe='1h'):
        """Calculate VWAP from OHLCV data"""
        tf = '1h' if timeframe in ('1h', '1H', '60m') else timeframe
        
        for ex_id in self._ex_ids:
            ex = self._ex(ex_id)
            if not ex:
                continue
            for s in self._candidates(symbol):
                try:
                    if s in ex.markets:
                        ohlcv = ex.fetch_ohlcv(s, timeframe=tf, limit=60)
                        if not ohlcv:
                            continue
                        
                        df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
                        tp = (df['high'] + df['low'] + df['close']) / 3.0
                        cum_vol = df['vol'].cumsum().replace(0, pd.NA)
                        vwap = (tp * df['vol']).cumsum() / cum_vol
                        val = float(vwap.iloc[-1])
                        if val > 0:
                            return val
                except Exception:
                    continue
        
        # Fallback to current price if VWAP unavailable
        return self.get_current_price(symbol)
    
    def get_ohlcv_data(self, symbol, timeframe='1h', limit=100):
        """Get OHLCV data for analysis"""
        for ex_id in self._ex_ids:
            ex = self._ex(ex_id)
            if not ex:
                continue
            for s in self._candidates(symbol):
                try:
                    if s in ex.markets:
                        ohlcv = ex.fetch_ohlcv(s, timeframe=timeframe, limit=limit)
                        if ohlcv and len(ohlcv) > 20:
                            return pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
                except Exception:
                    continue
        return None
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50
        
        deltas = np.diff(prices)
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        if down == 0:
            return 100
        
        rs = up / down
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def check_vwap_stack(self, symbol):
        """Check for VWAP stack patterns"""
        try:
            # Get multiple VWAP timeframes
            vwap_1h = self.get_vwap(symbol, '1h')
            vwap_4h = self.get_vwap(symbol, '4h')
            current_price = self.get_current_price(symbol)
            
            if vwap_1h > 0 and vwap_4h > 0 and current_price > 0:
                # Calculate squeeze
                vwap_max = max(vwap_1h, vwap_4h)
                vwap_min = min(vwap_1h, vwap_4h)
                squeeze_pct = (vwap_max - vwap_min) / vwap_max if vwap_max > 0 else 0
                
                # Bullish: price above both VWAPs, VWAPs squeezed
                bullish_stack = current_price > vwap_1h and current_price > vwap_4h and squeeze_pct < 0.005
                
                # Bearish: price below both VWAPs, VWAPs squeezed
                bearish_stack = current_price < vwap_1h and current_price < vwap_4h and squeeze_pct < 0.005
                
                return {
                    'bullish_stack': bullish_stack,
                    'bearish_stack': bearish_stack,
                    'squeeze_pct': squeeze_pct
                }
        except:
            pass
        
        return {'bullish_stack': False, 'bearish_stack': False, 'squeeze_pct': 0.0}
    
    def check_divergence(self, symbol):
        """Check for price/RSI divergence"""
        try:
            df = self.get_ohlcv_data(symbol)
            if df is not None and len(df) > 30:
                prices = df['close'].values
                rsi = self.calculate_rsi(prices)
                
                # Simple divergence check
                price_trend = prices[-1] > prices[-10]
                rsi_trend = rsi > 50
                
                bull_div = not price_trend and rsi_trend  # Price down, RSI up
                bear_div = price_trend and not rsi_trend   # Price up, RSI down
                
                return {
                    'bull_div': bull_div,
                    'bear_div': bear_div,
                    'strength': abs(rsi - 50)
                }
        except:
            pass
        
        return {'bull_div': False, 'bear_div': False, 'strength': 0}
    
    def check_volume_spike(self, symbol):
        """Check for volume spike"""
        try:
            df = self.get_ohlcv_data(symbol)
            if df is not None and len(df) > 20:
                vol_avg = df['vol'].rolling(20).mean().iloc[-1]
                current_vol = df['vol'].iloc[-1]
                
                if vol_avg > 0:
                    ratio = current_vol / vol_avg
                    return {
                        'detected': ratio > self.config['min_volume_multiplier'],
                        'ratio': ratio
                    }
        except:
            pass
        
        return {'detected': False, 'ratio': 1.0}
    
    def check_sfp_pattern(self, symbol):
        """Check for SFP (Swing Failure Pattern)"""
        try:
            df = self.get_ohlcv_data(symbol)
            if df is not None and len(df) > 20:
                recent_high = df['high'].rolling(20).max().iloc[-1]
                recent_low = df['low'].rolling(20).min().iloc[-1]
                current_price = df['close'].iloc[-1]
                
                # Bull SFP: swept low then recovered
                bull_sfp = df['low'].iloc[-1] < recent_low and current_price > recent_low
                
                # Bear SFP: swept high then rejected
                bear_sfp = df['high'].iloc[-1] > recent_high and current_price < recent_high
                
                sweep_distance = abs(df['high'].iloc[-1] - recent_high) if bear_sfp else abs(recent_low - df['low'].iloc[-1])
                
                return {
                    'bull_sfp': bull_sfp,
                    'bear_sfp': bear_sfp,
                    'sweep_distance': sweep_distance
                }
        except:
            pass
        
        return {'bull_sfp': False, 'bear_sfp': False, 'sweep_distance': 0}
    
    def scan_for_exhaustion(self, symbol, timeframe='1h'):
        """Enhanced scan with confidence-based scoring"""
        # Base confidence starts at 50%
        confidence = 50.0
        reasons = []
        direction = None
        
        # Check each indicator
        vwap_stack = self.check_vwap_stack(symbol)
        divergence = self.check_divergence(symbol)
        volume_spike = self.check_volume_spike(symbol)
        sfp = self.check_sfp_pattern(symbol)
        
        # VWAP Stack - High weight (15%)
        if vwap_stack['bullish_stack']:
            confidence += 15
            reasons.append("Bullish VWAP Stack")
            direction = 'LONG'
        elif vwap_stack['bearish_stack']:
            confidence += 15
            reasons.append("Bearish VWAP Stack")
            direction = 'SHORT'
        
        # Divergence - High weight (12%)
        if divergence['bull_div']:
            confidence += 12
            reasons.append("Bullish Divergence")
            if not direction:
                direction = 'LONG'
        elif divergence['bear_div']:
            confidence += 12
            reasons.append("Bearish Divergence")
            if not direction:
                direction = 'SHORT'
        
        # Volume Spike - Medium weight (8-10%)
        if volume_spike['detected']:
            if volume_spike['ratio'] > 2.0:
                confidence += 10
                reasons.append(f"Strong Volume {volume_spike['ratio']:.1f}x")
            else:
                confidence += 8
                reasons.append(f"Volume Spike {volume_spike['ratio']:.1f}x")
        
        # SFP Pattern - High weight (12%)
        if sfp['bull_sfp']:
            confidence += 12
            reasons.append("Bullish SFP")
            if not direction:
                direction = 'LONG'
        elif sfp['bear_sfp']:
            confidence += 12
            reasons.append("Bearish SFP")
            if not direction:
                direction = 'SHORT'
        
        # Cap confidence at 95%
        confidence = min(95, confidence)
        
        return {
            'symbol': symbol,
            'confidence': confidence,
            'direction': direction,
            'reasons': reasons
        }
    
    def create_pending_order(self, signal):
        """Create pending order if confidence is high enough"""
        if signal['direction'] and signal['confidence'] >= self.config['min_confidence_trade']:
            entry_price = self.calculate_optimal_entry(signal)
            stop_loss = self.calculate_stop_loss(signal, entry_price)
            take_profit = self.calculate_take_profit(signal, entry_price, stop_loss)
            
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio >= self.config['min_rr_ratio']:
                order = {
                    'symbol': signal['symbol'],
                    'direction': signal['direction'],
                    'entry': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': signal['confidence'],
                    'reasons': signal['reasons'],
                    'rr_ratio': rr_ratio,
                    'status': 'PENDING',
                    'created_at': datetime.now().isoformat()
                }
                self.pending_signals.append(order)
                return order
        return None
    
    def calculate_optimal_entry(self, signal):
        """Calculate optimal entry based on VWAP"""
        current_price = self.get_current_price(signal['symbol'])
        vwap_1h = self.get_vwap(signal['symbol'], '1h')
        
        if signal['direction'] == 'LONG':
            return min(current_price, vwap_1h * (1 - self.config['entry_buffer_pct']))
        else:
            return max(current_price, vwap_1h * (1 + self.config['entry_buffer_pct']))
    
    def calculate_stop_loss(self, signal, entry_price):
        """Calculate stop loss"""
        if signal['direction'] == 'LONG':
            return entry_price * (1 - self.config['stop_loss_pct'])
        else:
            return entry_price * (1 + self.config['stop_loss_pct'])
    
    def calculate_take_profit(self, signal, entry_price, stop_loss):
        """Calculate take profit for minimum R:R"""
        risk = abs(entry_price - stop_loss)
        if signal['direction'] == 'LONG':
            return entry_price + (risk * self.config['min_rr_ratio'])
        else:
            return entry_price - (risk * self.config['min_rr_ratio'])
    
    def monitor_pending_orders(self):
        """Monitor and execute pending orders"""
        for order in self.pending_signals[:]:
            current_price = self.get_current_price(order['symbol'])
            
            if current_price > 0:
                # Check if price hit entry
                if order['direction'] == 'LONG' and current_price <= order['entry']:
                    self.execute_order(order)
                    self.pending_signals.remove(order)
                elif order['direction'] == 'SHORT' and current_price >= order['entry']:
                    self.execute_order(order)
                    self.pending_signals.remove(order)
    
    def execute_order(self, order):
        """Execute order"""
        order['status'] = 'ACTIVE'
        order['entry_time'] = datetime.now().isoformat()
        order['actual_entry'] = self.get_current_price(order['symbol'])
        self.active_positions.append(order)
        
        print(f"\n✅ EXECUTED: {order['symbol']} {order['direction']}")
        print(f"   Entry: ${order['actual_entry']:.6f}")
        print(f"   Stop: ${order['stop_loss']:.6f}")
        print(f"   Target: ${order['take_profit']:.6f}")
        print(f"   Confidence: {order['confidence']:.0f}%")
        print(f"   R:R Ratio: {order['rr_ratio']:.2f}")
        print(f"   Reasons: {', '.join(order['reasons'])}")
        
        # Send Discord notification
        if self.discord_webhook:
            asyncio.create_task(self._send_order_alert(order))

# Main scanning loop
async def main_loop():
    """Main scanning loop"""
    scanner = EnhancedScanner()
    
    # Initialize Discord
    await scanner._init_discord()
    
    # Send startup notification
    await scanner._send_startup_notification()
    
    # List of symbols to scan (add your symbols here)
    symbols_to_scan = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AVAX/USDT', 
        'MATIC/USDT', 'LINK/USDT', 'UNI/USDT', 'PEPE/USDT',
        'BAND/USDT', 'TA/USDT', 'USTC/USDT', 'ALCH/USDT'
    ]
    
    print("\n🚀 Enhanced Scanner Started")
    print(f"   Scanning {len(symbols_to_scan)} symbols")
    print(f"   Min confidence for trades: {scanner.config['min_confidence_trade']}%")
    print(f"   Min confidence for watchlist: {scanner.config['min_confidence_watch']}%")
    print("=" * 50)
    
    while True:
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scanning...")
            
            high_confidence = []
            watchlist = []
            
            for symbol in symbols_to_scan:
                signal = scanner.scan_for_exhaustion(symbol)
                
                if signal['confidence'] >= scanner.config['min_confidence_trade']:
                    high_confidence.append(signal)
                    print(f"   🎯 {symbol}: {signal['direction']} @ {signal['confidence']:.0f}% confidence")
                elif signal['confidence'] >= scanner.config['min_confidence_watch']:
                    watchlist.append(signal)
                    print(f"   👀 {symbol}: {signal['direction'] if signal['direction'] else 'NEUTRAL'} @ {signal['confidence']:.0f}% confidence")
            
            # Create orders for high confidence signals
            for signal in high_confidence:
                order = scanner.create_pending_order(signal)
                if order:
                    print(f"\n📍 PENDING ORDER: {order['symbol']} {order['direction']}")
                    print(f"   Entry: ${order['entry']:.6f}")
                    print(f"   Confidence: {order['confidence']:.0f}%")
                    
                    # Send Discord notification for high confidence signal
                    await scanner._send_signal_alert(signal)
            
            # Monitor existing pending orders
            scanner.monitor_pending_orders()
            
            # Show summary
            print(f"\n📊 Summary: {len(high_confidence)} trades, {len(watchlist)} watchlist, {len(scanner.pending_signals)} pending")
            
            # Wait before next scan
            time.sleep(3600)  # Scan every hour
            
        except KeyboardInterrupt:
            print("\n[STOPPED] Scanner terminated by user")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            time.sleep(10)

if __name__ == "__main__":
    asyncio.run(main_loop())
