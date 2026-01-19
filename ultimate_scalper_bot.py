#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultimate Scalper Bot - Phemex Integration
Targeting 1-2% moves with 3-4 trades per day
Based on Bounty Seeker v4 architecture
"""

import os, json, time, traceback, requests, ccxt
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UltimateScalper")

# ====================== CONFIGURATION ======================
SCALPER_CONFIG = {
    "PHEMEX_API_KEY": "2c213e33-e1bd-44ac-bf9a-44a4cd2e065a",
    "PHEMEX_SECRET": "4Q2dti8eGbr-QeADqpGA1n6hSs9K4Fb7PPNOeYUkQHhlNTg1NzdiMy0yNjkyLTRiNjEtYWU2ZS05OTA5YjljYzQ2MTc",
    "DISCORD_WEBHOOK": "https://discord.com/api/webhooks/1430429617696673852/UmIz28ug7uMqCyuVyOy7LeGXRj91sGLM9NuZicfzSZQOvYlGdfulww0WZzqRLos2I6Jz",
    "SCAN_INTERVAL_SEC": 30,  # 30 seconds for scalping
    "MAX_TOTAL_TRADES": 20,   # Maximum 20 total trades
    "MAX_OPEN_POSITIONS": 2,  # Maximum 2 open positions at once
    "TARGET_PROFIT_PCT": 1.5,  # 1.5% target profit
    "STOP_LOSS_PCT": 0.8,      # 0.8% stop loss
    "POSITION_SIZE_USDT": 5.0, # $5 per trade (10% of $52.82 account)
    "LEVERAGE": 15,             # 15x leverage
    "STARTING_BALANCE": 50.0,   # $50 starting account
    "MIN_VOLUME_USDT": 500000, # Min 24h volume
    "PAPER_TRADING": False,    # Live trading with $52.82 balance
}

# Dynamic futures pairs - will be loaded from Phemex
SCALPING_SYMBOLS = []  # Will be populated dynamically

# ====================== PHEMEX EXCHANGE CLASS ======================
class PhemexScalper:
    def __init__(self, config: dict):
        self.config = config
        self.exchange = None
        self.positions = {}
        self.daily_stats = {
            "trades_today": 0,
            "profit_today": 0.0,
            "last_reset": datetime.now(timezone.utc).date().isoformat()
        }
        self._init_phemex()

    def _init_phemex(self):
        """Initialize Phemex exchange connection"""
        try:
            self.exchange = ccxt.phemex({
                'apiKey': self.config["PHEMEX_API_KEY"],
                'secret': self.config["PHEMEX_SECRET"],
                'sandbox': self.config["PAPER_TRADING"],  # Use sandbox for paper trading
                'options': {
                    'defaultType': 'swap',
                    'test': self.config["PAPER_TRADING"]
                },
                'enableRateLimit': True,
            })
            self.exchange.load_markets()
            logger.info(f"✅ Phemex connected ({'Paper Trading' if self.config['PAPER_TRADING'] else 'Live Trading'})")

            # Load all futures pairs dynamically
            self._load_futures_pairs()
        except Exception as e:
            logger.error(f"❌ Phemex connection failed: {e}")
            raise

    def _load_futures_pairs(self):
        """Load all available futures pairs from Phemex"""
        try:
            global SCALPING_SYMBOLS
            markets = self.exchange.markets

            # Filter for USDT futures pairs only
            futures_pairs = []
            for symbol, market in markets.items():
                # More flexible filtering for futures pairs
                if (market['type'] == 'swap' and
                    market['quote'] == 'USDT' and
                    market['active'] and
                    'USDT' in symbol and
                    not symbol.endswith(':USDT:USDT')):  # Avoid double USDT
                    futures_pairs.append(symbol)

            # If no pairs found, try alternative approach
            if not futures_pairs:
                logger.warning("⚠️ No futures pairs found with strict filtering, trying alternative...")
                for symbol, market in markets.items():
                    if (market['type'] == 'swap' and
                        market['active'] and
                        'USDT' in symbol):
                        futures_pairs.append(symbol)

            # Sort by volume (if available) or alphabetically
            futures_pairs.sort()

            # Update global symbols list
            SCALPING_SYMBOLS = futures_pairs

            logger.info(f"📊 Loaded {len(futures_pairs)} futures pairs from Phemex")
            if futures_pairs:
                logger.info(f"🔍 Scanning all futures pairs: {futures_pairs[:10]}...")  # Show first 10
            else:
                logger.warning("⚠️ No futures pairs found! Using fallback pairs...")
                # Fallback to basic pairs if loading fails
                SCALPING_SYMBOLS = [
                    "BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT", "BNB/USDT:USDT",
                    "XRP/USDT:USDT", "ADA/USDT:USDT", "DOGE/USDT:USDT", "AVAX/USDT:USDT",
                    "MATIC/USDT:USDT", "DOT/USDT:USDT", "LINK/USDT:USDT", "UNI/USDT:USDT"
                ]
                logger.info(f"📊 Using fallback pairs: {len(SCALPING_SYMBOLS)} symbols")

        except Exception as e:
            logger.error(f"❌ Failed to load futures pairs: {e}")
            # Fallback to basic pairs if loading fails
            SCALPING_SYMBOLS = [
                "BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT", "BNB/USDT:USDT",
                "XRP/USDT:USDT", "ADA/USDT:USDT", "DOGE/USDT:USDT", "AVAX/USDT:USDT",
                "MATIC/USDT:USDT", "DOT/USDT:USDT", "LINK/USDT:USDT", "UNI/USDT:USDT"
            ]
            logger.info(f"📊 Using fallback pairs: {len(SCALPING_SYMBOLS)} symbols")

    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get current ticker data"""
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None

    def get_ohlcv(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> Optional[pd.DataFrame]:
        """Get OHLCV data for analysis"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            if not ohlcv:
                return None
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return None

    def place_order(self, symbol: str, side: str, amount: float, price: float = None,
                   stop_price: float = None, take_profit: float = None) -> Optional[Dict]:
        """Place a trading order"""
        if self.config["PAPER_TRADING"]:
            return self._simulate_order(symbol, side, amount, price, stop_price, take_profit)

        try:
            order_type = "market" if price is None else "limit"
            order_params = {
                "symbol": symbol,
                "type": order_type,
                "side": side.lower(),
                "amount": amount,
                "leverage": self.config["LEVERAGE"]
            }

            if price:
                order_params["price"] = price
            if stop_price:
                order_params["stopPrice"] = stop_price
            if take_profit:
                order_params["takeProfit"] = take_profit

            order = self.exchange.create_order(**order_params)
            logger.info(f"✅ Order placed: {side} {amount} {symbol} at {price or 'market'}")
            return order
        except Exception as e:
            logger.error(f"❌ Order failed: {e}")
            return None

    def _simulate_order(self, symbol: str, side: str, amount: float, price: float = None,
                       stop_price: float = None, take_profit: float = None) -> Dict:
        """Simulate order for paper trading"""
        ticker = self.get_ticker(symbol)
        if not ticker:
            return None

        entry_price = price or ticker["last"]
        order_id = f"sim_{int(time.time())}"

        # Simulate order execution
        simulated_order = {
            "id": order_id,
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "price": entry_price,
            "status": "filled",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stop_price": stop_price,
            "take_profit": take_profit
        }

        logger.info(f"📝 Simulated {side} {amount} {symbol} at ${entry_price:.6f}")
        return simulated_order

    def get_balance(self) -> Dict:
        """Get account balance"""
        if self.config["PAPER_TRADING"]:
            return {"USDT": {"free": 10000.0, "used": 0.0, "total": 10000.0}}

        try:
            return self.exchange.fetch_balance()
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return {"USDT": {"free": 0.0, "used": 0.0, "total": 0.0}}

# ====================== SCALPING SIGNAL DETECTOR ======================
class ScalpingSignalDetector:
    def __init__(self, phemex: PhemexScalper):
        self.phemex = phemex
        self.symbols = SCALPING_SYMBOLS

    def detect_scalping_signals(self) -> List[Dict]:
        """Detect high-frequency scalping opportunities"""
        signals = []

        for symbol in self.symbols:
            try:
                # Get 1-minute data for scalping
                df = self.phemex.get_ohlcv(symbol, "1m", 50)
                if df is None or len(df) < 20:
                    continue

                signal = self._analyze_scalping_opportunity(symbol, df)
                if signal:
                    signals.append(signal)

            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue

        return signals

    def _analyze_scalping_opportunity(self, symbol: str, df: pd.DataFrame) -> Optional[Dict]:
        """Analyze scalping opportunity with tight parameters"""
        if len(df) < 20:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # Calculate indicators
        df["ema_5"] = df["close"].ewm(span=5).mean()
        df["ema_10"] = df["close"].ewm(span=10).mean()
        df["rsi"] = self._calculate_rsi(df["close"], 14)
        df["volume_sma"] = df["volume"].rolling(10).mean()
        df["volume_ratio"] = df["volume"] / df["volume_sma"]

        # Price momentum
        price_change_1m = ((latest["close"] - prev["close"]) / prev["close"]) * 100
        price_change_5m = ((latest["close"] - df.iloc[-6]["close"]) / df.iloc[-6]["close"]) * 100

        # Volume spike detection
        volume_ratio = latest.get("volume_ratio", 1.0) or 1.0
        volume_spike = volume_ratio > 2.0

        # RSI conditions
        rsi = latest.get("rsi", 50.0) or 50.0  # Default to 50 if RSI not available
        rsi_oversold = rsi < 35
        rsi_overbought = rsi > 65

        # EMA crossover signals
        ema_5_latest = latest.get("ema_5", latest["close"])
        ema_10_latest = latest.get("ema_10", latest["close"])
        ema_5_prev = prev.get("ema_5", prev["close"])
        ema_10_prev = prev.get("ema_10", prev["close"])

        ema_bullish_cross = ema_5_latest > ema_10_latest and ema_5_prev <= ema_10_prev
        ema_bearish_cross = ema_5_latest < ema_10_latest and ema_5_prev >= ema_10_prev

        # Price action signals
        price_above_ema5 = latest["close"] > ema_5_latest
        price_below_ema5 = latest["close"] < ema_5_latest

        # More aggressive scalping signal detection
        confidence = 0
        direction = None
        reasons = []

        # Simple momentum-based signals (more aggressive)
        if price_change_1m > 0.2:  # 0.2% move in 1 minute
            confidence += 2
            direction = "LONG"
            reasons.append("1m momentum up")

        if price_change_1m < -0.2:  # 0.2% move down in 1 minute
            confidence += 2
            direction = "SHORT"
            reasons.append("1m momentum down")

        # Volume-based signals
        if volume_spike and price_change_1m > 0.1:
            confidence += 2
            if direction != "SHORT":
                direction = "LONG"
            reasons.append("Volume + momentum")

        if volume_spike and price_change_1m < -0.1:
            confidence += 2
            if direction != "LONG":
                direction = "SHORT"
            reasons.append("Volume + dump")

        # RSI-based signals (more lenient)
        if rsi < 40 and price_change_1m < -0.1:
            confidence += 1
            if direction != "SHORT":
                direction = "LONG"
            reasons.append("RSI oversold")

        if rsi > 60 and price_change_1m > 0.1:
            confidence += 1
            if direction != "LONG":
                direction = "SHORT"
            reasons.append("RSI overbought")

        # EMA-based signals
        if ema_bullish_cross:
            confidence += 1
            if direction != "SHORT":
                direction = "LONG"
            reasons.append("EMA bullish cross")

        if ema_bearish_cross:
            confidence += 1
            if direction != "LONG":
                direction = "SHORT"
            reasons.append("EMA bearish cross")

        # 5-minute momentum
        if abs(price_change_5m) > 0.5:
            confidence += 1
            reasons.append("5m momentum")

        # Much lower threshold for scalping
        if confidence >= 2 and direction:
            entry_price = float(latest["close"])
            stop_loss = entry_price * (0.992 if direction == "LONG" else 1.008)  # 0.8% stop
            take_profit = entry_price * (1.015 if direction == "LONG" else 0.985)  # 1.5% target

            return {
                "symbol": symbol,
                "direction": direction,
                "entry": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "confidence": min(confidence, 10),
                "reasons": reasons,
                "rsi": float(rsi),
                "volume_ratio": float(volume_ratio),
                "price_change_1m": price_change_1m,
                "price_change_5m": price_change_5m,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        return None

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

# ====================== ULTIMATE SCALPER BOT ======================
class UltimateScalperBot:
    def __init__(self):
        self.config = SCALPER_CONFIG
        self.phemex = PhemexScalper(self.config)
        self.detector = ScalpingSignalDetector(self.phemex)
        self.daily_stats = {
            "trades_today": 0,
            "total_trades": 0,
            "profit_today": 0.0,
            "last_reset": datetime.now(timezone.utc).date().isoformat()
        }
        self.active_positions = {}
        self.log("Ultimate Scalper Bot initialized")

    def log(self, msg: str):
        """Logging helper"""
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

    def reset_daily_stats(self):
        """Reset daily statistics"""
        today = datetime.now(timezone.utc).date().isoformat()
        if self.daily_stats["last_reset"] != today:
            self.daily_stats = {
                "trades_today": 0,
                "total_trades": self.daily_stats.get("total_trades", 0),  # Keep total trades
                "profit_today": 0.0,
                "last_reset": today
            }
            self.log("📊 Daily stats reset")

    def can_trade(self) -> bool:
        """Check if we can place new trades"""
        self.reset_daily_stats()

        # Check total trade limit (20 trades max)
        if self.daily_stats["total_trades"] >= self.config["MAX_TOTAL_TRADES"]:
            self.log("🛑 Maximum total trades reached (20)")
            return False

        # Check open positions limit (2 max)
        if len(self.active_positions) >= self.config["MAX_OPEN_POSITIONS"]:
            self.log("🛑 Maximum open positions reached (2)")
            return False

        # Check daily loss limit (50% of starting balance = $25)
        if self.daily_stats["profit_today"] < -25:  # $25 daily loss limit
            self.log("🛑 Daily loss limit reached ($25)")
            return False

        return True

    def calculate_position_size(self, symbol: str, entry_price: float) -> float:
        """Calculate position size based on risk management"""
        balance = self.phemex.get_balance()
        usdt_balance = balance.get("USDT", {}).get("free", 0)

        # Use fixed position size for scalping ($2.5 per trade)
        position_size_usdt = self.config["POSITION_SIZE_USDT"]

        # Adjust based on available balance
        if usdt_balance < position_size_usdt:
            position_size_usdt = usdt_balance * 0.9  # Use 90% of available balance

        # Calculate position size in base currency
        position_size = position_size_usdt / entry_price
        return position_size

    def execute_scalping_trade(self, signal: Dict) -> bool:
        """Execute a scalping trade"""
        if not self.can_trade():
            return False

        symbol = signal["symbol"]
        direction = signal["direction"]
        entry_price = signal["entry"]
        stop_loss = signal["stop_loss"]
        take_profit = signal["take_profit"]

        # Calculate position size
        position_size = self.calculate_position_size(symbol, entry_price)
        if position_size <= 0:
            self.log(f"❌ Insufficient balance for {symbol}")
            return False

        # Place order
        side = "buy" if direction == "LONG" else "sell"
        order = self.phemex.place_order(
            symbol=symbol,
            side=side,
            amount=position_size,
            price=entry_price,
            stop_price=stop_loss,
            take_profit=take_profit
        )

        if order:
            # Track position
            position_id = order["id"]
            self.active_positions[position_id] = {
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "size": position_size,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "order": order
            }

            # Update daily stats
            self.daily_stats["trades_today"] += 1
            self.daily_stats["total_trades"] += 1

            self.log(f"🎯 SCALPING TRADE: {direction} {symbol} @ ${entry_price:.6f}")
            self.log(f"   Stop: ${stop_loss:.6f} | Target: ${take_profit:.6f}")
            self.log(f"   Size: {position_size:.4f} | Total trades: {self.daily_stats['total_trades']}/20")

            # Send Discord notification
            self.send_discord_alert(signal, order)
            return True

        return False

    def send_discord_alert(self, signal: Dict, order: Dict):
        """Send Discord alert for scalping trade execution"""
        try:
            symbol = signal["symbol"]
            direction = signal["direction"]
            entry = signal["entry"]
            confidence = signal["confidence"]
            stop_loss = signal["stop_loss"]
            take_profit = signal["take_profit"]

            emoji = "🟢" if direction == "LONG" else "🔴"
            color = 0x00FF00 if direction == "LONG" else 0xFF0000

            # Calculate potential profit/loss
            potential_profit = (take_profit - entry) / entry * 100
            potential_loss = (entry - stop_loss) / entry * 100

            embed = {
                "title": f"⚡ PHEMEX SCALPING EXECUTION - {symbol}",
                "description": f"{emoji} **{direction}** {symbol} **EXECUTED**\n"
                             f"**Entry Price:** ${entry:.6f}\n"
                             f"**Stop Loss:** ${stop_loss:.6f} ({potential_loss:.2f}%)\n"
                             f"**Take Profit:** ${take_profit:.6f} ({potential_profit:.2f}%)\n"
                             f"**Leverage:** {self.config['LEVERAGE']}x\n"
                             f"**Position Size:** ${self.config['POSITION_SIZE_USDT']:.2f}",
                "color": color,
                "fields": [
                    {
                        "name": "📊 Signal Details",
                        "value": f"**Confidence:** {confidence}/10\n**Reasons:** {', '.join(signal.get('reasons', []))}\n**RSI:** {signal.get('rsi', 0):.1f}\n**Volume Ratio:** {signal.get('volume_ratio', 1):.1f}x",
                        "inline": True
                    },
                    {
                        "name": "📈 Account Status",
                        "value": f"**Total Trades:** {self.daily_stats['total_trades']}/20\n**Open Positions:** {len(self.active_positions)}/2\n**Daily P&L:** ${self.daily_stats['profit_today']:.2f}\n**Balance:** ${self.phemex.get_balance().get('USDT', {}).get('free', 0):.2f}",
                        "inline": True
                    }
                ],
                "footer": {"text": f"Ultimate Scalper Bot • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            payload = {"embeds": [embed]}
            requests.post(self.config["DISCORD_WEBHOOK"], json=payload, timeout=10)
            self.log(f"📤 Discord alert sent for {symbol} {direction}")

        except Exception as e:
            self.log(f"❌ Discord alert failed: {e}")

    def scan_for_scalping_opportunities(self):
        """Main scanning loop for scalping opportunities"""
        try:
            # Get signals
            signals = self.detector.detect_scalping_signals()

            if not signals:
                return

            # Sort by confidence
            signals.sort(key=lambda x: x["confidence"], reverse=True)

            # Execute top signal if conditions are met
            for signal in signals[:1]:  # Only take the best signal
                if signal["confidence"] >= 2:  # Minimum confidence for scalping
                    self.log(f"📊 Signal found: {signal['symbol']} {signal['direction']} (confidence: {signal['confidence']}/10)")

                    # Check if we can trade
                    if self.can_trade():
                        self.execute_scalping_trade(signal)
                    else:
                        self.log(f"⚠️ Signal found but cannot trade: {signal['symbol']} {signal['direction']}")
                    break

        except Exception as e:
            self.log(f"❌ Scan error: {e}")
            traceback.print_exc()


    def run_scalping_bot(self):
        """Main bot loop"""
        self.log("🚀 Ultimate Scalper Bot started")
        self.log(f"📊 Target: {self.config['TARGET_PROFIT_PCT']}% profit per trade")
        self.log(f"🛡️ Stop: {self.config['STOP_LOSS_PCT']}% stop loss")
        self.log(f"📈 Max total trades: {self.config['MAX_TOTAL_TRADES']}")
        self.log(f"💰 Position size: ${self.config['POSITION_SIZE_USDT']}")
        self.log(f"⚡ Leverage: {self.config['LEVERAGE']}x")


        while True:
            try:
                self.scan_for_scalping_opportunities()

                # Check if we've hit daily limits
                if not self.can_trade():
                    self.log("⏰ Daily limits reached, waiting for next day...")
                    time.sleep(3600)  # Wait 1 hour
                    continue

                # Wait for next scan
                time.sleep(self.config["SCAN_INTERVAL_SEC"])

            except KeyboardInterrupt:
                self.log("🛑 Bot stopped by user")
                break
            except Exception as e:
                self.log(f"❌ Bot error: {e}")
                time.sleep(60)  # Wait 1 minute on error

# ====================== ENTRY POINT ======================
if __name__ == "__main__":
    bot = UltimateScalperBot()
    bot.run_scalping_bot()
