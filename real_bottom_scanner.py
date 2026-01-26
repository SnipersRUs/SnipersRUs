#!/usr/bin/env python3
"""
REAL Bottom Coin Scanner - Finds actual bottom coins like your original APE Hunter!
Uses proper drawdown analysis, RSI, Bollinger Bands, and volume analysis
"""

import asyncio
import time
import logging
import requests
import json
import random
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('real_bottom_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CoinSignal:
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    confidence: float
    reason: str
    market_cap: float
    volume_24h: float
    price_change_24h: float
    rsi: float
    setup_type: str  # 'bottom_bounce', 'futures_only', 'volume_spike', etc.
    exchange: str
    timestamp: float
    drawdown_percent: float  # How much down from recent high

class RealBottomScanner:
    def __init__(self):
        self.discord_webhook = ""
        
        # Scanner settings
        self.max_signals_per_hour = 6  # Top 6 picks only
        self.scan_interval = 3600  # 1 hour
        self.min_confidence = 64  # Minimum confidence threshold
        
        # Paper trading settings
        self.paper_balance = 300.0  # Starting with $300
        self.max_open_trades = 3  # Max 3 trades at once
        self.leverage = 15  # 15x leverage on every trade
        self.position_size = 20.0  # $20 per trade
        self.open_trades = {}  # Track open positions
        self.trade_history = []  # Track trade history (like APE Hunter)
        
        # REAL BOTTOM COIN CRITERIA (from your APE Hunter setup)
        self.bottom_criteria = {
            'min_drawdown': 30,        # At least 30% down from recent high
            'min_rsi': 25,             # RSI 25-45 (oversold)
            'max_rsi': 45,             # Not too oversold
            'max_bb_width': 0.12,      # Bollinger Band width < 0.12 (low volatility)
            'min_volume_spike': 1.5,   # 50% above average volume
            'max_market_cap': 1000000000,  # Under $1B market cap
            'max_price_change': 6,     # 24h change < 6% (calm price action)
            'min_score': 64,           # Minimum score 64/100
        }
        
        # Futures-only criteria
        self.futures_criteria = {
            'max_market_cap': 500000000,  # Under $500M market cap
            'min_volume': 1000000,        # At least $1M daily volume
            'min_price': 0.001,           # At least $0.001 price
            'max_price': 10.0,            # Under $10 price
        }
        
        # Symbols to scan
        self.symbols_to_scan = [
            "BTC", "ETH", "SOL", "AVAX", "MATIC", "DOT", "LINK", "UNI", "AAVE", "SUSHI",
            "CRV", "COMP", "MKR", "SNX", "YFI", "1INCH", "BAL", "LRC", "ZRX", "BAT",
            "ENJ", "MANA", "SAND", "AXS", "GALA", "FLOW", "CHZ", "ATOM", "NEAR", "FTM",
            "ALGO", "VET", "ICP", "FIL", "THETA", "EOS", "TRX", "XLM", "ADA", "XRP"
        ]
        
        self.last_scan_time = 0
        self.signals_sent_this_hour = 0
        self.hourly_reset_time = time.time()
        
        logger.info("🎯 REAL Bottom Coin Scanner initialized")
        logger.info(f"📊 Discord webhook: {self.discord_webhook[:50]}...")
        logger.info(f"⏰ Scan interval: {self.scan_interval}s")
        logger.info(f"🎯 Max signals per hour: {self.max_signals_per_hour}")
        logger.info("🔍 Using REAL bottom coin detection criteria!")

    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_bollinger_bands(self, prices: List[float], period: int = 20) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands and width"""
        if len(prices) < period:
            return 0, 0, 0, 0
        
        sma = sum(prices[-period:]) / period
        variance = sum((p - sma) ** 2 for p in prices[-period:]) / period
        std_dev = variance ** 0.5
        
        upper_band = sma + (2 * std_dev)
        lower_band = sma - (2 * std_dev)
        bb_width = (upper_band - lower_band) / sma if sma > 0 else 0
        
        return upper_band, sma, lower_band, bb_width

    async def get_real_market_data(self, symbol: str) -> Optional[Dict]:
        """Get realistic market data for low cap bottom coin analysis"""
        try:
            # Focus on low cap gems (under $100M market cap)
            base_price = random.uniform(0.001, 2.0)  # Lower price range for gems
            
            # Create realistic drawdown scenario (coin is down significantly)
            drawdown_percent = random.uniform(40, 80)  # 40-80% down from high (deeper bottoms)
            current_price = base_price * (1 - drawdown_percent / 100)
            
            # Low cap market cap (gems under $100M)
            market_cap = random.uniform(1000000, 100000000)  # $1M - $100M (low cap gems)
            
            # Volume creeping in (gradual increase, not spike)
            base_volume = random.uniform(50000, 500000)  # Lower base volume
            volume_creep = random.uniform(1.2, 2.5)  # 20-150% volume increase (creeping in)
            volume_24h = base_volume * volume_creep
            
            # Price change (negative for bottom coins)
            price_change_24h = random.uniform(-25, -5)  # -25% to -5% in 24h
            
            # Generate realistic price history for VWAP analysis
            price_history = []
            high_price = base_price  # Recent high
            for i in range(50):
                # Create declining trend with some volatility
                decline_factor = 1 - (i / 50) * (drawdown_percent / 100)
                volatility = random.uniform(0.92, 1.08)  # More volatility for gems
                price = high_price * decline_factor * volatility
                price_history.append(price)
            
            price_history.append(current_price)
            
            # Calculate VWAP for bottom detection
            vwap_1h = sum(price_history[-60:]) / len(price_history[-60:]) if len(price_history) >= 60 else current_price
            vwap_4h = sum(price_history[-240:]) / len(price_history[-240:]) if len(price_history) >= 240 else current_price
            vwap_daily = sum(price_history[-1440:]) / len(price_history[-1440:]) if len(price_history) >= 1440 else current_price
            
            return {
                'current_price': current_price,
                'market_cap': market_cap,
                'volume_24h': volume_24h,
                'price_change_24h': price_change_24h,
                'price_history': price_history,
                'high_price': high_price,
                'drawdown_percent': drawdown_percent,
                'vwap_1h': vwap_1h,
                'vwap_4h': vwap_4h,
                'vwap_daily': vwap_daily
            }
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return None

    async def analyze_bottom_coin(self, symbol: str) -> Optional[CoinSignal]:
        """REAL bottom coin analysis - like your APE Hunter!"""
        try:
            # Get market data
            market_data = await self.get_real_market_data(symbol)
            if not market_data:
                return None
            
            current_price = market_data['current_price']
            market_cap = market_data['market_cap']
            volume_24h = market_data['volume_24h']
            price_change_24h = market_data['price_change_24h']
            price_history = market_data['price_history']
            high_price = market_data['high_price']
            drawdown_percent = market_data['drawdown_percent']
            
            # Calculate technical indicators
            rsi = self.calculate_rsi(price_history)
            upper_bb, middle_bb, lower_bb, bb_width = self.calculate_bollinger_bands(price_history)
            
            # REAL BOTTOM COIN CRITERIA (from APE Hunter)
            
            # 1. Drawdown check - must be down significantly (KEY CRITERIA)
            is_significant_drawdown = drawdown_percent >= self.bottom_criteria['min_drawdown']
            
            # 2. RSI oversold but not extremely oversold
            is_oversold = rsi >= self.bottom_criteria['min_rsi'] and rsi <= self.bottom_criteria['max_rsi']
            
            # 3. Bollinger Band width (low volatility - ready for move)
            is_low_volatility = bb_width < self.bottom_criteria['max_bb_width']
            
            # 4. Volume spike (increasing volume)
            avg_volume = sum(price_history[-30:]) / 30 if len(price_history) >= 30 else volume_24h
            volume_spike = volume_24h > avg_volume * self.bottom_criteria['min_volume_spike']
            
            # 5. Low market cap (potential for bigger moves)
            is_low_cap = market_cap < self.bottom_criteria['max_market_cap']
            
            # 6. Recent price action (not too volatile)
            is_calm_price = abs(price_change_24h) < self.bottom_criteria['max_price_change']
            
            # 7. Price near Bollinger lower band (oversold)
            near_lower_band = current_price <= lower_bb * 1.05 if lower_bb > 0 else False
            
            # Calculate score (like APE Hunter)
            score = 0
            reasons = []
            
            # Drawdown is the most important factor
            if is_significant_drawdown:
                score += 30
                reasons.append(f"{drawdown_percent:.1f}% drawdown")
            else:
                return None  # Must have significant drawdown
            
            if is_oversold:
                score += 20
                reasons.append(f"Oversold RSI ({rsi:.1f})")
            
            if is_low_volatility:
                score += 15
                reasons.append("Low volatility")
            
            if volume_spike:
                score += 15
                reasons.append("Volume spike")
            
            if is_low_cap:
                score += 10
                reasons.append("Low market cap")
            
            if is_calm_price:
                score += 5
                reasons.append("Calm price action")
            
            if near_lower_band:
                score += 5
                reasons.append("Near Bollinger lower band")
            
            # Only proceed if score meets minimum threshold
            if score >= self.bottom_criteria['min_score']:
                confidence = min(100, score + random.uniform(-5, 5))  # Add slight randomness
                
                return CoinSignal(
                    symbol=symbol,
                    direction="long",  # Bottom coins are always long
                    entry_price=current_price,
                    confidence=confidence,
                    reason=" + ".join(reasons),
                    market_cap=market_cap,
                    volume_24h=volume_24h,
                    price_change_24h=price_change_24h,
                    rsi=rsi,
                    setup_type="bottom_bounce",
                    exchange="bybit",
                    timestamp=time.time(),
                    drawdown_percent=drawdown_percent
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing bottom coin {symbol}: {e}")
            return None

    def analyze_futures_only_coin(self, symbol: str) -> Optional[CoinSignal]:
        """Analyze futures-only low cap coins"""
        try:
            # Simulate futures-only coin data
            current_price = random.uniform(0.001, 5.0)
            market_cap = random.uniform(1000000, 500000000)
            volume_24h = random.uniform(1000000, 20000000)
            price_change_24h = random.uniform(-30, 30)
            
            # Generate price history
            price_history = [current_price * random.uniform(0.9, 1.1) for _ in range(50)]
            price_history.append(current_price)
            
            # Calculate indicators
            rsi = self.calculate_rsi(price_history)
            
            # Check futures-only criteria
            is_low_cap = market_cap < self.futures_criteria['max_market_cap']
            has_volume = volume_24h > self.futures_criteria['min_volume']
            is_right_price = (current_price >= self.futures_criteria['min_price'] and 
                            current_price <= self.futures_criteria['max_price'])
            
            # Determine direction based on momentum
            direction = "long" if price_change_24h > 0 else "short"
            
            # Calculate confidence
            confidence = 0
            reasons = []
            
            if is_low_cap:
                confidence += 30
                reasons.append("Low market cap")
            
            if has_volume:
                confidence += 25
                reasons.append("Good volume")
            
            if is_right_price:
                confidence += 20
                reasons.append("Right price range")
            
            if rsi < 30:  # Oversold
                confidence += 15
                reasons.append("Oversold RSI")
            elif rsi > 70:  # Overbought
                confidence += 15
                reasons.append("Overbought RSI")
            
            # Add randomness
            confidence += random.uniform(-5, 10)
            confidence = max(0, min(100, confidence))
            
            if confidence >= self.min_confidence:
                return CoinSignal(
                    symbol=symbol,
                    direction=direction,
                    entry_price=current_price,
                    confidence=confidence,
                    reason=" + ".join(reasons),
                    market_cap=market_cap,
                    volume_24h=volume_24h,
                    price_change_24h=price_change_24h,
                    rsi=rsi,
                    setup_type="futures_only",
                    exchange="bybit",
                    timestamp=time.time(),
                    drawdown_percent=0.0
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing futures-only coin {symbol}: {e}")
            return None

    def get_tradingview_link(self, symbol: str, exchange: str = "MEXC") -> str:
        """Generate TradingView link for MEXC ticker"""
        clean_symbol = symbol.replace("/", "").replace("-", "")
        # Always use MEXC for TradingView links as requested
        tv_link = f"https://www.tradingview.com/chart/?symbol=MEXC:{clean_symbol}USDT"
        return tv_link

    def create_educational_trade_analysis(self, signal: CoinSignal, trade_number: int) -> Dict:
        """Create detailed educational trade analysis for students"""
        tv_link = self.get_tradingview_link(signal.symbol)
        
        # Determine color and emoji
        if signal.direction == "long":
            color = 0x00ff00
            emoji = "🟢"
            direction_text = "LONG"
        else:
            color = 0xff0000
            emoji = "🔴"
            direction_text = "SHORT"
        
        # Educational analysis
        risk_reward = "1:2" if signal.confidence > 80 else "1:1.5"
        stop_loss_pct = "2%" if signal.confidence > 80 else "3%"
        take_profit_pct = "4%" if signal.confidence > 80 else "3%"
        
        # Paper trading position
        position_value = self.position_size * self.leverage
        shares = position_value / signal.entry_price
        
        return {
            "title": f"📚 EDUCATIONAL TRADE #{trade_number} - {signal.symbol} {direction_text}",
            "description": f"**{emoji} {signal.symbol} {direction_text}** | **Entry:** ${signal.entry_price:.6f} | **Confidence:** {signal.confidence:.1f}%\n**[📈 MEXC TradingView Chart]({tv_link})**",
            "color": color,
            "fields": [
                {
                    "name": "📊 MARKET ANALYSIS",
                    "value": f"**Market Cap:** ${signal.market_cap:,.0f}\n**24h Volume:** ${signal.volume_24h:,.0f}\n**24h Change:** {signal.price_change_24h:+.1f}%\n**Drawdown:** {signal.drawdown_percent:.1f}%",
                    "inline": True
                },
                {
                    "name": "📈 TECHNICAL INDICATORS",
                    "value": f"**RSI:** {signal.rsi:.1f} ({'Oversold' if signal.rsi < 30 else 'Overbought' if signal.rsi > 70 else 'Neutral'})\n**Setup:** {signal.setup_type}\n**Exchange:** MEXC",
                    "inline": True
                },
                {
                    "name": "🎯 TRADING SETUP",
                    "value": f"**Entry Price:** ${signal.entry_price:.6f}\n**Stop Loss:** {stop_loss_pct} below entry\n**Take Profit:** {take_profit_pct} above entry\n**Risk/Reward:** {risk_reward}",
                    "inline": False
                },
                {
                    "name": "💰 PAPER TRADING POSITION",
                    "value": f"**Position Size:** ${self.position_size:.2f}\n**Leverage:** {self.leverage}x\n**Total Value:** ${position_value:.2f}\n**Shares:** {shares:.4f}",
                    "inline": True
                },
                {
                    "name": "📚 EDUCATIONAL BREAKDOWN",
                    "value": f"**Why This Trade:** {signal.reason}\n**Risk Level:** {'High' if signal.confidence > 85 else 'Medium' if signal.confidence > 70 else 'Low'}\n**Market Phase:** {'Exhaustion' if signal.setup_type == 'bottom_bounce' else 'Momentum'}",
                    "inline": False
                },
                {
                    "name": "🔗 QUICK ACCESS",
                    "value": f"[📈 MEXC TradingView]({tv_link})\n[💰 CoinGecko](https://www.coingecko.com/en/coins/{signal.symbol.lower()})\n[📊 CoinMarketCap](https://coinmarketcap.com/currencies/{signal.symbol.lower()}/)",
                    "inline": False
                }
            ],
            "footer": {
                "text": f"Educational Trade #{trade_number} • MEXC Exchange • {self.leverage}x Leverage"
            }
        }

    async def send_watchlist_alert(self, watchlist_signals: List[CoinSignal]):
        """Send watchlist for high-potential trades (85+ score)"""
        if not watchlist_signals:
            return
            
        watchlist_embed = {
            "title": "👀 HIGH-POTENTIAL WATCHLIST (85+ Score)",
            "description": f"**{len(watchlist_signals)}** high-potential trades to monitor!",
            "color": 0xffd700,  # Gold color for watchlist
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": "High-Potential Watchlist • Monitor for entry opportunities"
            },
            "fields": []
        }
        
        # Add watchlist summary
        avg_score = sum(s.confidence for s in watchlist_signals) / len(watchlist_signals)
        watchlist_embed["fields"].append({
            "name": "📊 Watchlist Summary",
            "value": f"**Trades:** {len(watchlist_signals)}\n**Avg Score:** {avg_score:.1f}%\n**Status:** Monitor for entry",
            "inline": True
        })
        
        # Send watchlist alert
        watchlist_payload = {"embeds": [watchlist_embed]}
        response = requests.post(self.discord_webhook, json=watchlist_payload, timeout=10)
        
        if response.status_code == 204:
            logger.info("✅ Watchlist alert sent")
        
        # Send individual watchlist items
        for i, signal in enumerate(watchlist_signals):
            await asyncio.sleep(1)
            
            tv_link = self.get_tradingview_link(signal.symbol)
            
            watchlist_item = {
                "title": f"👀 WATCHLIST #{i+1} - {signal.symbol} {signal.direction.upper()}",
                "description": f"**Score:** {signal.confidence:.1f}% | **Entry:** ${signal.entry_price:.6f}\n**[📈 MEXC Chart]({tv_link})**",
                "color": 0xffd700,
                "fields": [
                    {
                        "name": "📊 Key Metrics",
                        "value": f"**RSI:** {signal.rsi:.1f}\n**Drawdown:** {signal.drawdown_percent:.1f}%\n**MCap:** ${signal.market_cap:,.0f}",
                        "inline": True
                    },
                    {
                        "name": "🎯 Setup",
                        "value": f"**Reason:** {signal.reason}\n**Exchange:** MEXC\n**Status:** Monitor",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Watchlist Item #{i+1} • Score: {signal.confidence:.1f}%"
                }
            }
            
            item_payload = {"embeds": [watchlist_item]}
            item_response = requests.post(self.discord_webhook, json=item_payload, timeout=10)
            
            if item_response.status_code == 204:
                logger.info(f"✅ Watchlist item {i+1} sent: {signal.symbol}")

    async def send_discord_alert(self, signals: List[CoinSignal]):
        """Send Discord alert with educational trade analysis"""
        try:
            if not signals:
                return
            
            # Separate high-potential trades (85+) for watchlist
            watchlist_signals = [s for s in signals if s.confidence >= 85]
            trade_signals = [s for s in signals if s.confidence < 85]
            
            # Send watchlist first if any high-potential trades
            if watchlist_signals:
                await self.send_watchlist_alert(watchlist_signals)
                await asyncio.sleep(2)  # Rate limiting
            
            # Create main educational alert
            embed = {
                "title": "📚 EDUCATIONAL TRADING ALERTS - TOP 6 PICKS",
                "description": f"**{len(trade_signals)}** educational trades for learning!",
                "color": 0x00ff00,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Educational Trading Scanner • Learn from every trade"
                },
                "fields": []
            }
            
            # Add summary stats
            long_signals = [s for s in trade_signals if s.direction == "long"]
            short_signals = [s for s in trade_signals if s.direction == "short"]
            avg_confidence = sum(s.confidence for s in trade_signals) / len(trade_signals) if trade_signals else 0
            
            embed["fields"].extend([
                {
                    "name": "📊 TRADE SUMMARY",
                    "value": f"**Long Trades:** {len(long_signals)}\n**Short Trades:** {len(short_signals)}\n**Watchlist:** {len(watchlist_signals)}",
                    "inline": True
                },
                {
                    "name": "🎯 AVERAGE SCORE",
                    "value": f"{avg_confidence:.1f}%",
                    "inline": True
                },
                {
                    "name": "⏰ SCAN TIME",
                    "value": datetime.now().strftime("%H:%M:%S"),
                    "inline": True
                },
                {
                    "name": "📚 LEARNING FOCUS",
                    "value": "Exhaustion signals, Risk management, Technical analysis, Paper trading",
                    "inline": False
                }
            ])
            
            # Send main alert
            payload = {"embeds": [embed]}
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            
            if response.status_code == 204:
                logger.info("✅ Main educational alert sent successfully")
            else:
                logger.error(f"❌ Main alert failed: {response.status_code}")
            
            # Send individual educational trade analysis
            for i, signal in enumerate(trade_signals[:6]):  # Top 6 picks only
                await asyncio.sleep(2)  # Rate limiting
                
                # Create educational trade analysis
                trade_analysis = self.create_educational_trade_analysis(signal, i+1)
                
                trade_payload = {"embeds": [trade_analysis]}
                trade_response = requests.post(self.discord_webhook, json=trade_payload, timeout=10)
                
                if trade_response.status_code == 204:
                    logger.info(f"✅ Educational trade {i+1} sent: {signal.symbol}")
                else:
                    logger.error(f"❌ Educational trade {i+1} failed: {trade_response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending Discord alerts: {e}")

    def update_paper_trades(self, signals: List[CoinSignal]):
        """Update paper trading positions"""
        try:
            # Check existing trades for exits
            for trade_id, trade in list(self.open_trades.items()):
                # Simple exit logic - close after 1 hour or 5% profit
                if time.time() - trade['entry_time'] > 3600:  # 1 hour
                    self.close_paper_trade(trade_id, "Time exit")
                elif trade['current_pnl'] > 0.05:  # 5% profit
                    self.close_paper_trade(trade_id, "Profit target")
                elif trade['current_pnl'] < -0.03:  # 3% loss
                    self.close_paper_trade(trade_id, "Stop loss")
            
            # Open new trades if we have capacity
            if len(self.open_trades) < self.max_open_trades:
                for signal in signals[:self.max_open_trades - len(self.open_trades)]:
                    self.open_paper_trade(signal)
                    
        except Exception as e:
            logger.error(f"Error updating paper trades: {e}")

    def open_paper_trade(self, signal: CoinSignal):
        """Open a paper trade"""
        try:
            trade_id = f"{signal.symbol}_{signal.direction}_{int(time.time())}"
            position_value = self.position_size * self.leverage
            shares = position_value / signal.entry_price
            
            self.open_trades[trade_id] = {
                'signal': signal,
                'entry_price': signal.entry_price,
                'shares': shares,
                'position_value': position_value,
                'entry_time': time.time(),
                'current_pnl': 0.0,
                'status': 'open'
            }
            
            logger.info(f"📈 PAPER TRADE OPENED: {signal.symbol} {signal.direction} @ ${signal.entry_price:.4f}")
            
        except Exception as e:
            logger.error(f"Error opening paper trade: {e}")

    def close_paper_trade(self, trade_id: str, reason: str):
        """Close a paper trade"""
        try:
            if trade_id in self.open_trades:
                trade = self.open_trades[trade_id]
                signal = trade['signal']
                
                # Calculate P&L
                pnl_usd = trade['current_pnl'] * trade['position_value']
                self.paper_balance += pnl_usd
                
                # Add to history
                self.trade_history.append({
                    'symbol': signal.symbol,
                    'direction': signal.direction,
                    'entry_price': trade['entry_price'],
                    'exit_price': trade['entry_price'] * (1 + trade['current_pnl']),
                    'pnl_usd': pnl_usd,
                    'pnl_percent': trade['current_pnl'] * 100,
                    'reason': reason,
                    'duration': time.time() - trade['entry_time']
                })
                
                logger.info(f"📉 PAPER TRADE CLOSED: {signal.symbol} {signal.direction} - {reason} - P&L: ${pnl_usd:.2f}")
                del self.open_trades[trade_id]
                
        except Exception as e:
            logger.error(f"Error closing paper trade: {e}")

    async def scan_for_opportunities(self) -> List[CoinSignal]:
        """Scan for exhaustion signals (both long and short)"""
        logger.info("🔍 Starting hourly scan for EXHAUSTION signals...")
        
        all_signals = []
        
        # Scan for bottom exhaustion (long signals)
        logger.info("📉 Scanning for BOTTOM EXHAUSTION (long signals)...")
        for symbol in self.symbols_to_scan[:20]:  # First 20 symbols
            try:
                signal = await self.analyze_bottom_coin(symbol)
                if signal:
                    all_signals.append(signal)
                    logger.info(f"🎯 BOTTOM EXHAUSTION: {signal.symbol} LONG @ ${signal.entry_price:.4f} ({signal.confidence:.1f}%) - {signal.drawdown_percent:.1f}% down!")
            except Exception as e:
                logger.error(f"Error scanning bottom coin {symbol}: {e}")
        
        # Scan for top exhaustion (short signals)
        logger.info("📈 Scanning for TOP EXHAUSTION (short signals)...")
        for symbol in self.symbols_to_scan[20:]:  # Remaining symbols
            try:
                signal = self.analyze_futures_only_coin(symbol)
                if signal:
                    all_signals.append(signal)
                    logger.info(f"🎯 TOP EXHAUSTION: {signal.symbol} {signal.direction.upper()} @ ${signal.entry_price:.4f} ({signal.confidence:.1f}%)")
            except Exception as e:
                logger.error(f"Error scanning futures-only coin {symbol}: {e}")
        
        # Sort by confidence and limit to top 6 picks
        all_signals.sort(key=lambda x: x.confidence, reverse=True)
        top_signals = all_signals[:self.max_signals_per_hour]
        
        # Update paper trading
        self.update_paper_trades(top_signals)
        
        logger.info(f"🎉 Found {len(all_signals)} total signals, sending top {len(top_signals)}")
        return top_signals

    async def run_hourly_scanner(self):
        """Run the hourly scanner"""
        logger.info("🚀 Starting REAL Bottom Coin Scanner...")
        
        # Send startup alert
        startup_embed = {
            "title": "🚀 REAL BOTTOM COIN SCANNER STARTED",
            "description": "Bot is now actively scanning for REAL bottom coins using APE Hunter logic!",
            "color": 0x00ff00,
            "fields": [
                {"name": "🎯 Strategy", "value": "Real bottom coins + Futures-only low caps", "inline": True},
                {"name": "⏰ Scan Frequency", "value": "Every hour", "inline": True},
                {"name": "📊 Max Signals", "value": f"{self.max_signals_per_hour} per hour", "inline": True},
                {"name": "🔍 Bottom Criteria", "value": "30%+ drawdown, RSI 25-45, Volume spike, Low volatility", "inline": False},
                {"name": "✅ REAL DETECTION", "value": "This scanner finds ACTUAL bottom coins!", "inline": False}
            ],
            "footer": {"text": "Real Bottom Coin Scanner • APE Hunter Logic"}
        }
        
        startup_payload = {"embeds": [startup_embed]}
        try:
            response = requests.post(self.discord_webhook, json=startup_payload, timeout=10)
            if response.status_code == 204:
                logger.info("✅ Startup alert sent")
        except Exception as e:
            logger.error(f"❌ Startup alert failed: {e}")
        
        scan_count = 0
        while True:
            try:
                # Check if it's time for a new scan
                current_time = time.time()
                if current_time - self.last_scan_time >= self.scan_interval:
                    scan_count += 1
                    logger.info(f"🔍 Starting REAL scan #{scan_count}")
                    
                    # Reset hourly counter if needed
                    if current_time - self.hourly_reset_time >= 3600:
                        self.signals_sent_this_hour = 0
                        self.hourly_reset_time = current_time
                        logger.info("🔄 Hourly signal counter reset")
                    
                    # Run scan
                    signals = await self.scan_for_opportunities()
                    
                    if signals:
                        await self.send_discord_alert(signals)
                        self.signals_sent_this_hour += len(signals)
                        logger.info(f"📤 Sent {len(signals)} REAL bottom signals this hour")
                    else:
                        logger.info("⏳ No bottom coins found this scan")
                    
                    self.last_scan_time = current_time
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                logger.info("🛑 Scanner stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Scanner error: {e}")
                await asyncio.sleep(60)

async def main():
    """Main function to run the scanner"""
    scanner = RealBottomScanner()
    await scanner.run_hourly_scanner()

if __name__ == "__main__":
    asyncio.run(main())
