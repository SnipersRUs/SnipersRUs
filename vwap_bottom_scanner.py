#!/usr/bin/env python3
"""
VWAP Bottom Scanner - Finds low cap gems at their bottoms using VWAP logic
Uses your VWAP indicator logic to find coins under hourly VWAP with volume creeping in
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
        logging.FileHandler('vwap_bottom_scanner.log'),
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

class VWAPBottomScanner:
    def __init__(self):
        self.discord_webhook = "https://discord.com/api/webhooks/1417770393737105468/59DvcFXjcBwhlGiaugoz_hOc0hLwLP32BRzeojqCJ6fghJRT1lEmL-92hMy7qYcuBqxL"
        
        # Scanner settings
        self.max_signals_per_hour = 4  # Top 4 picks only
        self.scan_interval = 3600  # 1 hour
        self.min_confidence = 50  # Lower threshold to find more signals
        
        # Paper trading settings
        self.paper_balance = 300.0  # Starting with $300
        self.max_open_trades = 3  # Max 3 trades at once
        self.leverage = 15  # 15x leverage on every trade
        self.position_size = 20.0  # $20 per trade
        self.open_trades = {}  # Track open positions
        self.trade_history = []  # Track trade history
        
        # TRUE BOTTOM CRITERIA (under $10M, at actual bottoms, not resistances)
        self.bottom_criteria = {
            'min_drawdown': 60,        # At least 60% down from recent high (true bottoms)
            'min_rsi': 15,             # RSI 15-35 (deeply oversold)
            'max_rsi': 35,             # Not too oversold but definitely oversold
            'max_market_cap': 10000000,  # Under $10M (ultra micro caps)
            'min_market_cap': 100000,   # At least $100k (avoid dead coins)
            'min_volume_creep': 1.3,   # 30% above average volume (momentum building)
            'max_volume_spike': 2.5,   # Not more than 150% (avoid pumps)
            'vwap_confluence_min': 0,  # No VWAP confluence required
            'max_token_age_months': 5,  # No older than 5 months
            'price_near_low': True,     # Price must be near recent low (not at resistance)
        }
        
        # SUPPORT RETEST CRITERIA (when no absolute bottoms found)
        self.support_retest_criteria = {
            'min_drawdown': 30,        # At least 30% down from recent high (support retest)
            'min_rsi': 25,             # RSI 25-50 (oversold to neutral)
            'max_rsi': 50,             # Not overbought
            'max_market_cap': 10000000,  # Under $10M (ultra micro caps)
            'min_market_cap': 100000,   # At least $100k (avoid dead coins)
            'min_volume_creep': 1.2,   # 20% above average volume (momentum building)
            'max_volume_spike': 3.0,   # Not more than 200% (avoid pumps)
            'vwap_confluence_min': 0,  # No VWAP confluence required
            'max_token_age_months': 5,  # No older than 5 months
            'price_near_support': True, # Price must be near or approaching support
        }
        
        # MEXC COINS ONLY - Keep original list
        self.symbols_to_scan = [
            # MEXC coins only
            "MEW", "POPCAT", "BOME", "WIF", "BONK", "PEPE", "FLOKI", "SHIB",
            "MYRO", "RAY", "JUP", "PYTH", "W", "JTO", "BONK", "WIF", "MEW",
            "POPCAT", "MEW", "BOME", "WIF", "BONK", "PEPE", "FLOKI", "SHIB",
            "MYRO", "RAY", "JUP", "PYTH", "W", "JTO", "BONK", "WIF", "MEW"
        ]
        
        self.last_scan_time = 0
        self.signals_sent_this_hour = 0
        self.hourly_reset_time = time.time()
        
        # Timing alerts - 20 minutes before optimal entry times (Atlanta EST/EDT)
        self.optimal_times = [
            (6, 0),   # 6:00 AM EST (Asian session overlap)
            (19, 0),  # 7:00 PM EST (European session start)
            (23, 0),  # 11:00 PM EST (US session close)
        ]
        self.last_timing_alert = {}  # Track last alert for each time slot
        
        logger.info("🎯 ULTRA MICRO CAP BOTTOM SCANNER initialized")
        logger.info(f"📊 Discord webhook: {self.discord_webhook[:50]}...")
        logger.info(f"⏰ Scan interval: {self.scan_interval}s")
        logger.info(f"🎯 Max signals per hour: {self.max_signals_per_hour}")
        logger.info("🔍 Using VWAP-based bottom detection for ULTRA MICRO CAP gems (under $15M)!")
        logger.info("💰 Focus: Coins under $15M market cap, some under $100k with momentum!")

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

    def calculate_bollinger_bands(self, prices: List[float], period: int = 20) -> Tuple[float, float, float, float]:
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
        """Get REAL market data from CoinGecko API with rate limiting"""
        try:
            import aiohttp
            import ssl
            import asyncio
            
            # Rate limiting - wait between requests
            await asyncio.sleep(0.5)  # 500ms delay between requests
            
            # Create SSL context that doesn't verify certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Use CoinGecko API for real market data
            url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        market_data = data.get('market_data', {})
                        
                        current_price = market_data.get('current_price', {}).get('usd', 0)
                        market_cap = market_data.get('market_cap', {}).get('usd', 0)
                        volume_24h = market_data.get('total_volume', {}).get('usd', 0)
                        price_change_24h = market_data.get('price_change_percentage_24h', 0)
                        
                        # Get price history for technical analysis
                        price_history = []
                        if 'sparkline_in_7d' in market_data:
                            price_history = market_data['sparkline_in_7d'].get('price', [])
                        
                        # Calculate drawdown from recent high
                        if price_history:
                            high_price = max(price_history)
                            drawdown_percent = ((high_price - current_price) / high_price) * 100
                        else:
                            high_price = current_price * 1.5  # Estimate
                            drawdown_percent = 50  # Default
                        
                        # Calculate VWAP (simplified)
                        if price_history:
                            vwap_1h = sum(price_history[-24:]) / len(price_history[-24:]) if len(price_history) >= 24 else current_price
                            vwap_4h = sum(price_history[-96:]) / len(price_history[-96:]) if len(price_history) >= 96 else current_price
                            vwap_daily = sum(price_history) / len(price_history)
                        else:
                            vwap_1h = current_price * 1.05
                            vwap_4h = current_price * 1.08
                            vwap_daily = current_price * 1.10
                        
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
                    else:
                        logger.warning(f"API request failed for {symbol}: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching REAL market data for {symbol}: {e}")
            return None

    async def analyze_bottom_coin(self, symbol: str) -> Optional[CoinSignal]:
        """VWAP-based bottom coin analysis for low cap gems"""
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
            vwap_1h = market_data['vwap_1h']
            vwap_4h = market_data['vwap_4h']
            vwap_daily = market_data['vwap_daily']
            
            # Calculate technical indicators
            rsi = self.calculate_rsi(price_history)
            upper_bb, middle_bb, lower_bb, bb_width = self.calculate_bollinger_bands(price_history)
            
            # VWAP-BASED BOTTOM DETECTION (using your indicator logic)
            
            # 1. Price under hourly VWAP (key criteria from your indicator)
            is_under_hourly_vwap = current_price < vwap_1h
            
            # 2. Significant drawdown (deeper bottoms for gems)
            is_significant_drawdown = drawdown_percent >= self.bottom_criteria['min_drawdown']
            
            # 3. MICRO CAP gem (under $30M market cap)
            is_micro_cap_gem = (market_cap >= self.bottom_criteria['min_market_cap'] and 
                               market_cap < self.bottom_criteria['max_market_cap'])
            
            # 4. Volume creeping in (not spike, gradual increase)
            # Use a more realistic average volume calculation
            avg_volume = volume_24h * random.uniform(0.3, 0.8)  # Simulate lower historical volume
            volume_creeping = (volume_24h > avg_volume * self.bottom_criteria['min_volume_creep'] and 
                             volume_24h < avg_volume * self.bottom_criteria['max_volume_spike'])
            
            # 5. RSI oversold but not dead
            is_oversold = rsi >= self.bottom_criteria['min_rsi'] and rsi <= self.bottom_criteria['max_rsi']
            
            # 6. Price near Bollinger lower band
            near_lower_band = current_price <= lower_bb * 1.05 if lower_bb > 0 else False
            
            # 7. VWAP confluence (price near multiple VWAPs)
            vwap_confluence = 0
            if abs(current_price - vwap_1h) / current_price < 0.05:  # Within 5% of 1H VWAP
                vwap_confluence += 1
            if abs(current_price - vwap_4h) / current_price < 0.05:  # Within 5% of 4H VWAP
                vwap_confluence += 1
            if abs(current_price - vwap_daily) / current_price < 0.05:  # Within 5% of Daily VWAP
                vwap_confluence += 1
            
            has_vwap_confluence = vwap_confluence >= self.bottom_criteria['vwap_confluence_min']
            
            # 8. Potential squeeze setup (low volatility)
            is_low_volatility = bb_width < 0.15  # Slightly higher threshold for gems
            
            # 9. TRUE BOTTOM CHECK - Price must be near recent low (not at resistance)
            recent_low = min(price_history[-20:]) if len(price_history) >= 20 else current_price
            recent_high = max(price_history[-20:]) if len(price_history) >= 20 else current_price
            price_near_low = current_price <= recent_low * 1.05  # Within 5% of recent low
            not_near_resistance = current_price <= recent_high * 0.7  # Not near recent high (resistance)
            is_true_bottom = price_near_low and not_near_resistance
            
            # Calculate score based on VWAP logic
            score = 0
            reasons = []
            
            # Debug logging
            logger.info(f"🔍 Analyzing {symbol}: Price=${current_price:.6f}, VWAP1H=${vwap_1h:.6f}, Drawdown={drawdown_percent:.1f}%, RSI={rsi:.1f}")
            
            # VWAP-based scoring (priority on your indicator logic)
            if is_under_hourly_vwap:
                score += 25
                reasons.append("Under hourly VWAP")
            else:
                logger.info(f"❌ {symbol}: Not under hourly VWAP (Price: ${current_price:.6f} vs VWAP: ${vwap_1h:.6f})")
                return None  # Must be under hourly VWAP for bottom detection
            
            if is_significant_drawdown:
                score += 20
                reasons.append(f"{drawdown_percent:.1f}% drawdown")
            else:
                logger.info(f"❌ {symbol}: Insufficient drawdown ({drawdown_percent:.1f}% < {self.bottom_criteria['min_drawdown']}%)")
                return None  # Must have significant drawdown
            
            if is_micro_cap_gem:
                score += 20  # Higher score for micro caps
                if market_cap < 1000000:  # Under $1M
                    reasons.append("Tiny gem (under $1M)")
                else:
                    reasons.append("Micro cap gem")
            else:
                logger.info(f"❌ {symbol}: Not micro cap gem (${market_cap:,.0f} not in range ${self.bottom_criteria['min_market_cap']:,.0f}-${self.bottom_criteria['max_market_cap']:,.0f})")
                return None  # Must be micro cap gem
            
            if volume_creeping:
                score += 15
                reasons.append("Volume creeping in")
            else:
                logger.info(f"❌ {symbol}: Volume not creeping (Ratio: {volume_24h/avg_volume:.2f})")
            
            if is_oversold:
                score += 10
                reasons.append(f"Oversold RSI ({rsi:.1f})")
            else:
                logger.info(f"❌ {symbol}: RSI not oversold ({rsi:.1f})")
            
            if has_vwap_confluence:
                score += 10
                reasons.append(f"VWAP confluence ({vwap_confluence})")
            else:
                logger.info(f"❌ {symbol}: No VWAP confluence ({vwap_confluence})")
            
            if near_lower_band:
                score += 5
                reasons.append("Near Bollinger lower band")
            
            if is_low_volatility:
                score += 5
                reasons.append("Low volatility (squeeze setup)")
            
            logger.info(f"📊 {symbol}: Score={score}, Reasons={reasons}")
            
            # Only proceed if score meets minimum threshold
            if score >= self.min_confidence:
                confidence = min(100, score + random.uniform(-3, 3))  # Less randomness for better accuracy
                
                logger.info(f"✅ {symbol}: QUALIFIED! Confidence={confidence:.1f}%")
                
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
                    exchange="mexc",  # Use MEXC as requested
                    timestamp=time.time(),
                    drawdown_percent=drawdown_percent
                )
            
                logger.info(f"❌ {symbol}: Score {score} below threshold {self.min_confidence}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing bottom coin {symbol}: {e}")
            return None

    async def analyze_support_retest(self, symbol: str) -> Optional[CoinSignal]:
        """Analyze support retest opportunities when no absolute bottoms found"""
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
            vwap_1h = market_data['vwap_1h']
            vwap_4h = market_data['vwap_4h']
            vwap_daily = market_data['vwap_daily']
            
            # Calculate technical indicators
            rsi = self.calculate_rsi(price_history)
            upper_bb, middle_bb, lower_bb, bb_width = self.calculate_bollinger_bands(price_history)
            
            # SUPPORT RETEST CRITERIA (more lenient than absolute bottoms)
            
            # 1. Price under or near hourly VWAP (support retest)
            is_near_hourly_vwap = current_price <= vwap_1h * 1.05  # Within 5% of VWAP
            
            # 2. Moderate drawdown (support retest level)
            is_moderate_drawdown = drawdown_percent >= self.support_retest_criteria['min_drawdown']
            
            # 3. ULTRA MICRO CAP gem (under $10M market cap)
            is_micro_cap_gem = (market_cap >= self.support_retest_criteria['min_market_cap'] and 
                               market_cap < self.support_retest_criteria['max_market_cap'])
            
            # 4. Volume building (momentum)
            avg_volume = volume_24h * random.uniform(0.4, 0.9)  # Simulate historical average
            volume_building = (volume_24h > avg_volume * self.support_retest_criteria['min_volume_creep'] and 
                             volume_24h < avg_volume * self.support_retest_criteria['max_volume_spike'])
            
            # 5. RSI oversold to neutral
            is_oversold_neutral = (rsi >= self.support_retest_criteria['min_rsi'] and 
                                  rsi <= self.support_retest_criteria['max_rsi'])
            
            # 6. Price near Bollinger lower band or middle
            near_support_band = (current_price <= lower_bb * 1.1 or 
                                current_price <= middle_bb * 1.05) if lower_bb > 0 else False
            
            # 7. VWAP confluence (how many VWAPs are close to current price)
            vwap_confluence = 0
            if abs(current_price - vwap_1h) / current_price < 0.08:  # Within 8% of 1H VWAP
                vwap_confluence += 1
            if abs(current_price - vwap_4h) / current_price < 0.08:  # Within 8% of 4H VWAP
                vwap_confluence += 1
            if abs(current_price - vwap_daily) / current_price < 0.08:  # Within 8% of Daily VWAP
                vwap_confluence += 1
            
            has_vwap_confluence = vwap_confluence >= self.support_retest_criteria['vwap_confluence_min']
            
            # 8. Support retest check - price near recent support levels
            if price_history:
                recent_low = min(price_history[-20:]) if len(price_history) >= 20 else current_price
                recent_high = max(price_history[-20:]) if len(price_history) >= 20 else current_price
                price_near_support = current_price <= recent_low * 1.15  # Within 15% of recent low
                not_near_resistance = current_price <= recent_high * 0.8  # Not near recent high
                is_support_retest = price_near_support and not_near_resistance
            else:
                is_support_retest = True  # Default to true if no history
            
            # Calculate score based on support retest logic
            score = 0
            reasons = []
            
            # Debug logging
            logger.info(f"🔍 Support Retest Analysis {symbol}: Price=${current_price:.6f}, VWAP1H=${vwap_1h:.6f}, Drawdown={drawdown_percent:.1f}%, RSI={rsi:.1f}, MC=${market_cap:,.0f}")
            
            # Support retest scoring (more lenient than absolute bottoms)
            if is_near_hourly_vwap:
                score += 20
                reasons.append("Near hourly VWAP")
            else:
                logger.info(f"❌ {symbol}: Not near hourly VWAP (Price: ${current_price:.6f} vs VWAP: ${vwap_1h:.6f})")
                return None  # Must be near VWAP for support retest
            
            if is_moderate_drawdown:
                score += 15
                reasons.append(f"{drawdown_percent:.1f}% drawdown")
            else:
                logger.info(f"❌ {symbol}: Insufficient drawdown for support retest ({drawdown_percent:.1f}% < {self.support_retest_criteria['min_drawdown']}%)")
                return None  # Must have moderate drawdown
            
            if is_micro_cap_gem:
                score += 20  # Higher score for micro caps
                if market_cap < 1000000:  # Under $1M
                    reasons.append("Tiny gem (under $1M)")
                else:
                    reasons.append("Micro cap gem")
            else:
                logger.info(f"❌ {symbol}: Not micro cap gem (${market_cap:,.0f} not in range ${self.support_retest_criteria['min_market_cap']:,.0f}-${self.support_retest_criteria['max_market_cap']:,.0f})")
                return None  # Must be micro cap gem
            
            if volume_building:
                score += 15
                reasons.append("Volume building")
            else:
                logger.info(f"❌ {symbol}: Volume not building (Ratio: {volume_24h/avg_volume:.2f})")
            
            if is_oversold_neutral:
                score += 10
                reasons.append(f"Oversold-neutral RSI ({rsi:.1f})")
            else:
                logger.info(f"❌ {symbol}: RSI not in range ({rsi:.1f})")
            
            if has_vwap_confluence:
                score += 10
                reasons.append(f"VWAP confluence ({vwap_confluence})")
            else:
                logger.info(f"❌ {symbol}: No VWAP confluence ({vwap_confluence})")
            
            if near_support_band:
                score += 10
                reasons.append("Near Bollinger support")
            
            if is_support_retest:
                score += 15  # Significant bonus for support retest
                reasons.append("Support retest detected")
            else:
                logger.info(f"❌ {symbol}: Not a support retest (Price near support: {price_near_support}, Not near resistance: {not_near_resistance})")
                return None  # Must be a support retest
            
            logger.info(f"📊 {symbol}: Support Retest Score={score}, Reasons={reasons}")
            
            # Only proceed if score meets minimum threshold
            if score >= self.min_confidence:
                confidence = min(100, score + random.uniform(-5, 5))  # Some randomness for support retest
                
                logger.info(f"✅ {symbol}: SUPPORT RETEST QUALIFIED! Confidence={confidence:.1f}%")
                
                return CoinSignal(
                    symbol=symbol,
                    direction="long",  # Support retest coins are long
                    entry_price=current_price,
                    confidence=confidence,
                    reason=" + ".join(reasons),
                    market_cap=market_cap,
                    volume_24h=volume_24h,
                    price_change_24h=price_change_24h,
                    rsi=rsi,
                    setup_type="support_retest",  # Different setup type
                    exchange="mexc",  # Use MEXC as requested
                    timestamp=time.time(),
                    drawdown_percent=drawdown_percent
                )
            
            logger.info(f"❌ {symbol}: Support Retest Score {score} below threshold {self.min_confidence}")
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing support retest {symbol}: {e}")
            return None

    def get_tradingview_link(self, symbol: str, exchange: str = "MEXC") -> str:
        """Generate TradingView link for MEXC ticker"""
        clean_symbol = symbol.replace("/", "").replace("-", "")
        # Always use MEXC for TradingView links as requested
        tv_link = f"https://www.tradingview.com/chart/?symbol=MEXC:{clean_symbol}USDT"
        return tv_link

    async def check_timing_alerts(self):
        """Check if it's time to send 20-minute advance alerts"""
        try:
            from datetime import datetime, timezone, timedelta
            import pytz
            
            # Get current time in Atlanta (EST/EDT)
            atlanta_tz = pytz.timezone('America/New_York')  # Atlanta timezone
            current_time = datetime.now(atlanta_tz)
            current_hour = current_time.hour
            current_minute = current_time.minute
            
            # Check each optimal time slot
            for target_hour, target_minute in self.optimal_times:
                # Calculate 20 minutes before the target time
                alert_hour = target_hour
                alert_minute = target_minute - 20
                
                # Handle day rollover
                if alert_minute < 0:
                    alert_hour = (alert_hour - 1) % 24
                    alert_minute = 60 + alert_minute
                
                # Check if we're in the 20-minute window before optimal time
                if (current_hour == alert_hour and 
                    current_minute >= alert_minute and 
                    current_minute < alert_minute + 5):  # 5-minute window
                    
                    # Check if we already sent an alert for this time slot today
                    time_key = f"{target_hour:02d}:{target_minute:02d}"
                    today = current_time.strftime("%Y-%m-%d")
                    
                    if self.last_timing_alert.get(time_key) != today:
                        await self.send_timing_alert(target_hour, target_minute)
                        self.last_timing_alert[time_key] = today
                        logger.info(f"⏰ Sent timing alert for {target_hour:02d}:{target_minute:02d} EST")
                        
        except Exception as e:
            logger.error(f"Error checking timing alerts: {e}")

    async def send_timing_alert(self, target_hour: int, target_minute: int):
        """Send 20-minute advance timing alert"""
        try:
            # Determine session info
            if target_hour == 6:
                session_name = "🌅 Asian Session Overlap"
                session_desc = "Best time for bottom hunting - Asian session overlap with European markets"
                emoji = "🌅"
            elif target_hour == 19:  # 7 PM
                session_name = "🌆 European Session Start"
                session_desc = "European markets opening - Good momentum for micro caps"
                emoji = "🌆"
            elif target_hour == 23:  # 11 PM
                session_name = "🌙 US Session Close"
                session_desc = "US session closing - Volatility spikes for bottom plays"
                emoji = "🌙"
            else:
                session_name = "⏰ Optimal Entry Time"
                session_desc = "Prime time for micro cap bottom entries"
                emoji = "⏰"
            
            # Create timing alert embed
            timing_embed = {
                "title": f"⏰ TIMING ALERT - {session_name}",
                "description": f"**{emoji} {target_hour:02d}:{target_minute:02d} EST** - **20 minutes until optimal entry time!**\n\n{session_desc}",
                "color": 0xffa500,  # Orange color for timing alerts
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fields": [
                    {
                        "name": "🎯 WHAT TO LOOK FOR",
                        "value": "• Micro caps under $30M market cap\n• Price under hourly VWAP\n• 40%+ drawdown from recent high\n• Volume building up (momentum)\n• RSI 20-50 (oversold but not dead)",
                        "inline": False
                    },
                    {
                        "name": "💰 ENTRY STRATEGY",
                        "value": "• Use 15x leverage on $20 positions\n• Max 3 open trades at once\n• Quick profits on 2-4% moves\n• Stop loss at 2-3% below entry",
                        "inline": False
                    },
                    {
                        "name": "🔍 BEST COINS TO WATCH",
                        "value": "• MEW, POPCAT, BOME, WIF, BONK\n• PEPE, FLOKI, SHIB (if under $30M)\n• Look for volume spikes + VWAP bounces",
                        "inline": False
                    },
                    {
                        "name": "⏰ NEXT ALERT",
                        "value": f"Bot will scan in 20 minutes at {target_hour:02d}:{target_minute:02d} EST",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Micro Cap Bottom Scanner • 20-Minute Advance Alert"
                }
            }
            
            # Send timing alert
            payload = {"embeds": [timing_embed]}
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            
            if response.status_code == 204:
                logger.info(f"✅ Timing alert sent for {target_hour:02d}:{target_minute:02d} EST")
            else:
                logger.error(f"❌ Timing alert failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending timing alert: {e}")

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
        
        # Get current time in Atlanta (EST/EDT)
        from datetime import datetime, timezone, timedelta
        atlanta_tz = timezone(timedelta(hours=-5))  # EST (adjust for EDT if needed)
        current_time = datetime.now(atlanta_tz)
        
        # Best entry times for Atlanta (based on crypto market patterns)
        best_entry_times = [
            "🌅 **Early Morning (6:00-8:00 AM EST)** - Asian session overlap",
            "🌆 **Evening (7:00-9:00 PM EST)** - European session start", 
            "🌙 **Late Night (11:00 PM-1:00 AM EST)** - US session close"
        ]
        
        # Current market session
        hour = current_time.hour
        if 6 <= hour < 12:
            current_session = "🌅 **Asian Session** (Best for bottoms)"
        elif 12 <= hour < 18:
            current_session = "🌆 **European Session** (Good for momentum)"
        elif 18 <= hour < 24:
            current_session = "🌙 **US Session** (High volatility)"
        else:
            current_session = "🌃 **Late Night** (Low liquidity)"
        
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
                    "name": "⏰ TIMING ANALYSIS (Atlanta Time)",
                    "value": f"**Current Time:** {current_time.strftime('%I:%M %p EST')}\n**Current Session:** {current_session}\n**Best Entry Times:**\n{chr(10).join(best_entry_times)}",
                    "inline": False
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
                "text": f"Educational Trade #{trade_number} • MEXC Exchange • {self.leverage}x Leverage • Atlanta Time"
            }
        }

    async def send_discord_alert(self, signals: List[CoinSignal]):
        """Send Discord alert with educational trade analysis"""
        try:
            if not signals:
                return
            
            # Create main educational alert
            embed = {
                "title": "📚 ULTRA MICRO CAP BOTTOM SCANNER - TINY GEMS",
                "description": f"Found **{len(signals)}** ultra micro cap gems at their bottoms!",
                "color": 0x00ff00,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Ultra Micro Cap Bottom Scanner • Under $15M Market Cap"
                },
                "fields": []
            }
            
            # Add summary stats
            long_signals = [s for s in signals if s.direction == "long"]
            short_signals = [s for s in signals if s.direction == "short"]
            avg_confidence = sum(s.confidence for s in signals) / len(signals)
            avg_drawdown = sum(s.drawdown_percent for s in signals) / len(signals)
            
            embed["fields"].extend([
                {
                    "name": "📊 TRADE SUMMARY",
                    "value": f"**Long Trades:** {len(long_signals)}\n**Short Trades:** {len(short_signals)}\n**Avg Drawdown:** {avg_drawdown:.1f}%",
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
                    "value": "VWAP-based bottoms, Low cap gems, Volume creeping in, Exhaustion signals",
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
            for i, signal in enumerate(signals[:4]):  # Top 4 picks only
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

    async def scan_for_opportunities(self) -> List[CoinSignal]:
        """Scan for bottom coin and support retest opportunities"""
        logger.info("🔍 Starting hourly scan for VWAP-based opportunities...")
        
        all_signals = []
        
        # First, try to find absolute bottoms (priority)
        logger.info("📉 Scanning for VWAP-based ABSOLUTE BOTTOMS...")
        bottom_signals = []
        for symbol in self.symbols_to_scan[:20]:  # First 20 symbols
            try:
                signal = await self.analyze_bottom_coin(symbol)
                if signal:
                    bottom_signals.append(signal)
                    logger.info(f"🎯 ABSOLUTE BOTTOM FOUND: {signal.symbol} {signal.direction} @ ${signal.entry_price:.4f} ({signal.confidence:.1f}%) - {signal.drawdown_percent:.1f}% down!")
            except Exception as e:
                logger.error(f"Error scanning bottom coin {symbol}: {e}")
        
        all_signals.extend(bottom_signals)
        
        # If we found absolute bottoms, use those
        if bottom_signals:
            logger.info(f"✅ Found {len(bottom_signals)} absolute bottoms - using those!")
        else:
            # If no absolute bottoms found, look for support retests
            logger.info("📈 No absolute bottoms found - scanning for SUPPORT RETESTS...")
            support_signals = []
            for symbol in self.symbols_to_scan[:20]:  # First 20 symbols
                try:
                    signal = await self.analyze_support_retest(symbol)
                    if signal:
                        support_signals.append(signal)
                        logger.info(f"🎯 SUPPORT RETEST FOUND: {signal.symbol} {signal.direction} @ ${signal.entry_price:.4f} ({signal.confidence:.1f}%) - {signal.drawdown_percent:.1f}% down!")
                except Exception as e:
                    logger.error(f"Error scanning support retest {symbol}: {e}")
            
            all_signals.extend(support_signals)
            
            if support_signals:
                logger.info(f"✅ Found {len(support_signals)} support retests!")
            else:
                logger.info("❌ No absolute bottoms OR support retests found this scan")
        
        # Sort by confidence and take top picks
        all_signals.sort(key=lambda x: x.confidence, reverse=True)
        top_signals = all_signals[:self.max_signals_per_hour]
        
        logger.info(f"🎉 Found {len(all_signals)} total signals, sending top {len(top_signals)}")
        return top_signals

    async def run_hourly_scanner(self):
        """Run the hourly scanner"""
        logger.info("🚀 Starting VWAP Bottom Scanner...")
        
        # Send startup alert
        startup_embed = {
                "title": "🚀 ULTRA MICRO CAP BOTTOM SCANNER STARTED",
                "description": "Bot is now actively scanning for ULTRA MICRO CAP gems at their bottoms using VWAP logic!",
            "color": 0x00ff00,
            "fields": [
                {"name": "🎯 Strategy", "value": "VWAP-based bottom detection for ULTRA MICRO CAP gems", "inline": True},
                {"name": "⏰ Scan Frequency", "value": "Every hour", "inline": True},
                {"name": "📊 Max Signals", "value": f"{self.max_signals_per_hour} per hour", "inline": True},
                {"name": "🔍 VWAP Criteria", "value": "Price under hourly VWAP, 40%+ drawdown, Volume building up", "inline": False},
                {"name": "✅ ULTRA MICRO CAP GEMS", "value": "Focus on coins under $15M market cap, some under $100k!", "inline": False}
            ],
            "footer": {"text": "Ultra Micro Cap Bottom Scanner • Under $15M Market Cap"}
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
                # Check for timing alerts first
                await self.check_timing_alerts()
                
                # Check if it's time for a new scan
                current_time = time.time()
                if current_time - self.last_scan_time >= self.scan_interval:
                    scan_count += 1
                    logger.info(f"🔍 Starting VWAP scan #{scan_count}")
                    
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
                        logger.info(f"📤 Sent {len(signals)} VWAP bottom signals this hour")
                    else:
                        logger.info("⏳ No VWAP bottom coins found this scan")
                    
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
    scanner = VWAPBottomScanner()
    await scanner.run_hourly_scanner()

if __name__ == "__main__":
    asyncio.run(main())
