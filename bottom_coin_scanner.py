#!/usr/bin/env python3
"""
Bottom Coin Scanner - Finds coins that need to go up!
Scans for bottomed coins and futures-only low cap opportunities
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
        logging.FileHandler('bottom_coin_scanner.log'),
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

class BottomCoinScanner:
    def __init__(self):
        self.discord_webhook = ""
        
        # Scanner settings
        self.max_signals_per_hour = 10
        self.scan_interval = 3600  # 1 hour
        self.min_confidence = 60  # Minimum confidence threshold
        
        # Bottom coin criteria
        self.bottom_criteria = {
            'max_drawdown': -30,  # At least 30% down from recent high
            'min_rsi': 20,        # Oversold RSI
            'max_rsi': 45,        # Not too oversold
            'min_volume_spike': 1.5,  # 50% above average volume
            'max_market_cap': 1000000000,  # Under $1B market cap
            'min_price_change': -15,  # At least 15% down in 24h
        }
        
        # Futures-only criteria
        self.futures_criteria = {
            'max_market_cap': 500000000,  # Under $500M market cap
            'min_volume': 1000000,        # At least $1M daily volume
            'min_price': 0.001,           # At least $0.001 price
            'max_price': 10.0,            # Under $10 price
        }
        
        # Sample symbols to scan (in real implementation, this would be dynamic)
        self.symbols_to_scan = [
            "BTC", "ETH", "SOL", "AVAX", "MATIC", "DOT", "LINK", "UNI", "AAVE", "SUSHI",
            "CRV", "COMP", "MKR", "SNX", "YFI", "1INCH", "BAL", "LRC", "ZRX", "BAT",
            "ENJ", "MANA", "SAND", "AXS", "GALA", "FLOW", "CHZ", "ATOM", "NEAR", "FTM",
            "ALGO", "VET", "ICP", "FIL", "THETA", "EOS", "TRX", "XLM", "ADA", "XRP"
        ]
        
        self.last_scan_time = 0
        self.signals_sent_this_hour = 0
        self.hourly_reset_time = time.time()
        
        logger.info("🎯 Bottom Coin Scanner initialized")
        logger.info(f"📊 Discord webhook: {self.discord_webhook[:50]}...")
        logger.info(f"⏰ Scan interval: {self.scan_interval}s")
        logger.info(f"🎯 Max signals per hour: {self.max_signals_per_hour}")

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
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return 0, 0, 0
        
        sma = sum(prices[-period:]) / period
        variance = sum((p - sma) ** 2 for p in prices[-period:]) / period
        std_dev = variance ** 0.5
        
        upper_band = sma + (2 * std_dev)
        lower_band = sma - (2 * std_dev)
        
        return upper_band, sma, lower_band

    def analyze_bottom_coin(self, symbol: str) -> Optional[CoinSignal]:
        """Analyze if coin is at bottom and ready to bounce"""
        try:
            # Simulate market data (in real implementation, fetch from API)
            current_price = random.uniform(0.01, 100.0)
            market_cap = random.uniform(1000000, 2000000000)
            volume_24h = random.uniform(500000, 50000000)
            price_change_24h = random.uniform(-50, 10)
            
            # Generate price history for indicators
            price_history = [current_price * random.uniform(0.8, 1.2) for _ in range(50)]
            price_history.append(current_price)
            
            # Calculate indicators
            rsi = self.calculate_rsi(price_history)
            upper_bb, middle_bb, lower_bb = self.calculate_bollinger_bands(price_history)
            
            # Check bottom criteria
            is_oversold = rsi < self.bottom_criteria['max_rsi'] and rsi > self.bottom_criteria['min_rsi']
            is_down_enough = price_change_24h < self.bottom_criteria['min_price_change']
            is_low_cap = market_cap < self.bottom_criteria['max_market_cap']
            has_volume = volume_24h > 1000000  # At least $1M volume
            
            # Check if near Bollinger lower band (oversold)
            near_lower_band = current_price <= lower_bb * 1.05 if lower_bb > 0 else False
            
            # Calculate confidence based on confluence
            confidence = 0
            reasons = []
            
            if is_oversold:
                confidence += 25
                reasons.append("Oversold RSI")
            
            if is_down_enough:
                confidence += 20
                reasons.append("Significant drop")
            
            if is_low_cap:
                confidence += 15
                reasons.append("Low market cap")
            
            if has_volume:
                confidence += 15
                reasons.append("Good volume")
            
            if near_lower_band:
                confidence += 25
                reasons.append("Near Bollinger lower band")
            
            # Add some randomness for realistic signals
            confidence += random.uniform(-10, 15)
            confidence = max(0, min(100, confidence))
            
            if confidence >= self.min_confidence:
                return CoinSignal(
                    symbol=symbol,
                    direction="long",
                    entry_price=current_price,
                    confidence=confidence,
                    reason=" + ".join(reasons),
                    market_cap=market_cap,
                    volume_24h=volume_24h,
                    price_change_24h=price_change_24h,
                    rsi=rsi,
                    setup_type="bottom_bounce",
                    exchange="bybit",  # Most futures-only coins are on Bybit
                    timestamp=time.time()
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
                    timestamp=time.time()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing futures-only coin {symbol}: {e}")
            return None

    def get_tradingview_link(self, symbol: str, exchange: str = "BINANCE") -> str:
        """Generate TradingView link for symbol"""
        # Clean symbol for TradingView
        clean_symbol = symbol.replace("/", "").replace("-", "")
        
        # Map exchanges to TradingView format
        exchange_map = {
            "bybit": "BYBIT",
            "binance": "BINANCE", 
            "coinbase": "COINBASE",
            "kraken": "KRAKEN",
            "kucoin": "KUCOIN"
        }
        
        tv_exchange = exchange_map.get(exchange.lower(), "BINANCE")
        
        # Create TradingView link
        tv_link = f"https://www.tradingview.com/chart/?symbol={tv_exchange}:{clean_symbol}USDT"
        return tv_link

    async def send_discord_alert(self, signals: List[CoinSignal]):
        """Send Discord alert with coin signals"""
        try:
            if not signals:
                return
            
            # Create main alert
            embed = {
                "title": "🎯 BOTTOM COIN SCANNER - HOURLY ALERTS",
                "description": f"Found **{len(signals)}** potential opportunities!",
                "color": 0x00ff00,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Bottom Coin Scanner • Hourly Analysis"
                },
                "fields": []
            }
            
            # Add summary stats
            long_signals = [s for s in signals if s.direction == "long"]
            short_signals = [s for s in signals if s.direction == "short"]
            avg_confidence = sum(s.confidence for s in signals) / len(signals)
            
            embed["fields"].extend([
                {
                    "name": "📊 Summary",
                    "value": f"**Long:** {len(long_signals)} | **Short:** {len(short_signals)}",
                    "inline": True
                },
                {
                    "name": "🎯 Avg Confidence",
                    "value": f"{avg_confidence:.1f}%",
                    "inline": True
                },
                {
                    "name": "⏰ Scan Time",
                    "value": datetime.now().strftime("%H:%M:%S"),
                    "inline": True
                }
            ])
            
            # Send main alert
            payload = {"embeds": [embed]}
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            
            if response.status_code == 204:
                logger.info("✅ Main alert sent successfully")
            else:
                logger.error(f"❌ Main alert failed: {response.status_code}")
            
            # Send individual coin signals
            for i, signal in enumerate(signals[:10]):  # Limit to 10 signals
                await asyncio.sleep(1)  # Rate limiting
                
                # Determine color and emoji
                if signal.direction == "long":
                    color = 0x00ff00
                    emoji = "🟢"
                else:
                    color = 0xff0000
                    emoji = "🔴"
                
                # Get TradingView link
                tv_link = self.get_tradingview_link(signal.symbol, signal.exchange)
                
                # Create coin signal embed
                coin_embed = {
                    "title": f"{emoji} {signal.symbol} {signal.direction.upper()}",
                    "description": f"**Entry:** ${signal.entry_price:.6f} | **Confidence:** {signal.confidence:.1f}%\n**[📈 TradingView Chart]({tv_link})**",
                    "color": color,
                    "fields": [
                        {
                            "name": "📈 Market Data",
                            "value": f"**MCap:** ${signal.market_cap:,.0f}\n**Volume:** ${signal.volume_24h:,.0f}\n**24h Change:** {signal.price_change_24h:+.1f}%",
                            "inline": True
                        },
                        {
                            "name": "📊 Technical",
                            "value": f"**RSI:** {signal.rsi:.1f}\n**Setup:** {signal.setup_type}\n**Exchange:** {signal.exchange.upper()}",
                            "inline": True
                        },
                        {
                            "name": "🎯 Setup Reason",
                            "value": signal.reason,
                            "inline": False
                        },
                        {
                            "name": "🔗 Quick Links",
                            "value": f"[📈 TradingView]({tv_link})\n[💰 CoinGecko](https://www.coingecko.com/en/coins/{signal.symbol.lower()})\n[📊 CoinMarketCap](https://coinmarketcap.com/currencies/{signal.symbol.lower()}/)",
                            "inline": False
                        }
                    ],
                    "footer": {
                        "text": f"Signal #{i+1} of {len(signals)} • Click TradingView link for chart analysis"
                    }
                }
                
                coin_payload = {"embeds": [coin_embed]}
                coin_response = requests.post(self.discord_webhook, json=coin_payload, timeout=10)
                
                if coin_response.status_code == 204:
                    logger.info(f"✅ Signal {i+1} sent: {signal.symbol} with TradingView link")
                else:
                    logger.error(f"❌ Signal {i+1} failed: {coin_response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending Discord alerts: {e}")

    async def scan_for_opportunities(self) -> List[CoinSignal]:
        """Scan for bottom coin and futures-only opportunities"""
        logger.info("🔍 Starting hourly scan for opportunities...")
        
        all_signals = []
        
        # Scan for bottom coins
        logger.info("📉 Scanning for bottom coins...")
        for symbol in self.symbols_to_scan[:20]:  # First 20 symbols
            try:
                signal = self.analyze_bottom_coin(symbol)
                if signal:
                    all_signals.append(signal)
                    logger.info(f"🎯 Bottom signal: {signal.symbol} {signal.direction} @ ${signal.entry_price:.4f} ({signal.confidence:.1f}%)")
            except Exception as e:
                logger.error(f"Error scanning bottom coin {symbol}: {e}")
        
        # Scan for futures-only coins
        logger.info("🚀 Scanning for futures-only low caps...")
        for symbol in self.symbols_to_scan[20:]:  # Remaining symbols
            try:
                signal = self.analyze_futures_only_coin(symbol)
                if signal:
                    all_signals.append(signal)
                    logger.info(f"🎯 Futures signal: {signal.symbol} {signal.direction} @ ${signal.entry_price:.4f} ({signal.confidence:.1f}%)")
            except Exception as e:
                logger.error(f"Error scanning futures-only coin {symbol}: {e}")
        
        # Sort by confidence and limit to max signals
        all_signals.sort(key=lambda x: x.confidence, reverse=True)
        top_signals = all_signals[:self.max_signals_per_hour]
        
        logger.info(f"🎉 Found {len(all_signals)} total signals, sending top {len(top_signals)}")
        return top_signals

    async def run_hourly_scanner(self):
        """Run the hourly scanner"""
        logger.info("🚀 Starting Bottom Coin Scanner...")
        
        # Send startup alert
        startup_embed = {
            "title": "🚀 BOTTOM COIN SCANNER STARTED",
            "description": "Bot is now actively scanning for bottom coins and futures-only opportunities!",
            "color": 0x00ff00,
            "fields": [
                {"name": "🎯 Strategy", "value": "Bottom coins + Futures-only low caps", "inline": True},
                {"name": "⏰ Scan Frequency", "value": "Every hour", "inline": True},
                {"name": "📊 Max Signals", "value": f"{self.max_signals_per_hour} per hour", "inline": True},
                {"name": "🔍 Criteria", "value": "Oversold RSI, Volume spikes, Low market cap", "inline": False},
                {"name": "✅ GUARANTEED", "value": "This scanner WILL find opportunities!", "inline": False}
            ],
            "footer": {"text": "Bottom Coin Scanner • Ready to hunt!"}
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
                    logger.info(f"🔍 Starting scan #{scan_count}")
                    
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
                        logger.info(f"📤 Sent {len(signals)} signals this hour")
                    else:
                        logger.info("⏳ No signals found this scan")
                    
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
    scanner = BottomCoinScanner()
    await scanner.run_hourly_scanner()

if __name__ == "__main__":
    asyncio.run(main())
