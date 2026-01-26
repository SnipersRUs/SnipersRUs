#!/usr/bin/env python3
"""
Enhanced Bottom Scanner - Finds coins at bottoms with advanced indicators
Incorporates: Oath Keeper (Money Flow), Liquidity Hunter, GPS, Bounty Seeker, VWAP
Scans MEXC futures pairs for coins ready to move up
"""

import time
import logging
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import ccxt

# Configuration
DISCORD_WEBHOOK = ""
SCAN_INTERVAL_SEC = 1800  # 30 minutes
NUM_PICKS = 5  # Number of picks to send

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bottom_scanner_enhanced.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CoinPick:
    symbol: str
    price: float
    price_change_24h: float
    price_change_7d: float
    volume_24h: float
    rsi: float
    money_flow: float
    confluence_score: float
    confidence: float
    reasons: List[str]
    distance_from_low: float
    distance_from_high: float
    indicators: Dict[str, bool]  # Which indicators triggered

class BottomScannerEnhanced:
    def is_stock_ticker(self, symbol: str) -> bool:
        """Check if symbol is a stock ticker"""
        base = symbol.split('/')[0].split(':')[0].upper()
        if base in self.stock_tickers or 'STOCK' in base:
            return True
        for stock in self.stock_tickers:
            if base.startswith(stock) and (base == stock or base.startswith(stock + 'STOCK')):
                return True
        return False

    def is_forex_pair(self, symbol: str) -> bool:
        """Check if symbol is a forex pair"""
        base = symbol.split('/')[0].split(':')[0].upper()
        forex_codes = {
            'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 'NZD', 'SEK', 'NOK',
            'DKK', 'SGD', 'HKD', 'KRW', 'MXN', 'BRL', 'ZAR', 'INR', 'RUB', 'TRY',
            'PLN', 'CZK', 'HUF', 'RON', 'BGN', 'HRK', 'XAU', 'XAG', 'XPD', 'XPT', 'XDR'
        }
        if base in forex_codes or ('USDT' not in base and any(base.startswith(fx) for fx in forex_codes)):
            return True
        return False

    def is_crypto_only(self, symbol: str) -> bool:
        """Check if symbol is crypto only"""
        if self.is_stock_ticker(symbol) or self.is_forex_pair(symbol):
            return False
        base = symbol.split('/')[0].split(':')[0].upper()
        if 'FOREX' in base or 'FX' in base:
            return False
        return True

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.exchange = None
        self.watchlist = []
        self.last_scan_time = 0
        self.recent_picks = []
        self.pick_cooldown_hours = 24

        # Stock tickers to exclude
        self.stock_tickers = {
            'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'NFLX', 'DIS',
            'V', 'JPM', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD', 'PYPL', 'BAC', 'XOM', 'CVX',
            'ABBV', 'PFE', 'KO', 'AVGO', 'COST', 'PEP', 'TMO', 'ABT', 'MRK', 'CSCO', 'ACN',
            'ADBE', 'NKE', 'TXN', 'CMCSA', 'DHR', 'VZ', 'LIN', 'PM', 'NEE', 'RTX', 'HON',
            'UPS', 'QCOM', 'AMGN', 'T', 'LOW', 'INTU', 'SPGI', 'AMAT', 'DE', 'BKNG', 'C',
            'SBUX', 'AXP', 'ADI', 'ISRG', 'GILD', 'ADP', 'SYK', 'CL', 'MDT', 'TJX', 'ZTS',
            'GE', 'MMC', 'CI', 'APH', 'MO', 'SHW', 'ITW', 'WM', 'ETN', 'ICE', 'KLAC', 'CDNS',
            'SNPS', 'FTNT', 'MCHP', 'NXPI', 'CTAS', 'FAST', 'IDXX', 'PAYX', 'ODFL', 'CTSH',
            'AON', 'ANSS', 'KEYS', 'WDAY', 'ON', 'CDW', 'EXPD', 'FDS', 'BR', 'NDAQ', 'POOL',
            'CPRT', 'MCO', 'TTD', 'ZM', 'DOCN', 'DOCU', 'ROKU', 'PTON', 'SPOT', 'SNAP', 'TWTR',
            'SQ', 'SHOP', 'CRWD', 'OKTA', 'NET', 'DDOG', 'ZS', 'MDB', 'ESTC', 'NOW', 'TEAM',
            'PLTR', 'SNOW', 'RBLX', 'HOOD', 'COIN', 'LCID', 'RIVN', 'F', 'GM', 'FORD',
            'AMD', 'INTC', 'MU', 'LRCX', 'AMAT', 'KLAC', 'MCHP', 'SWKS', 'QRVO', 'MPWR',
            'ON', 'WOLF', 'ALGM', 'DIOD', 'POWI', 'SITM', 'CRUS', 'OLED', 'SMCI', 'SOFI', 'UPST', 'IWM', 'QQQ', 'SPY'
        }

        # Initialize MEXC exchange
        try:
            self.exchange = ccxt.mexc({
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'},
                'timeout': 10000
            })
            self.exchange.load_markets()
            logger.info("✅ MEXC exchange initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MEXC: {e}")
            raise

        # Build watchlist (crypto only)
        all_pairs = [
            s for s, m in self.exchange.markets.items()
            if (
                m.get('active', True)
                and (m.get('type') == 'swap' or m.get('swap') is True)
                and m.get('contract', True) is True
                and m.get('linear', True) is True
                and m.get('quote') == 'USDT'
            )
        ]

        self.watchlist = sorted([s for s in all_pairs if self.is_crypto_only(s)])
        excluded_count = len(all_pairs) - len(self.watchlist)
        logger.info(f"📊 Loaded {len(self.watchlist)} MEXC futures pairs (excluded {excluded_count} non-crypto pairs)")

    def calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(closes) < period + 1:
            return 50.0
        deltas = np.diff(closes[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return float(100 - (100 / (1 + rs)))

    def calculate_money_flow(self, closes: List[float], volumes: List[float], period: int = 8) -> float:
        """Oath Keeper Money Flow calculation"""
        if len(closes) < period + 1 or len(volumes) < period + 1:
            return 50.0

        up_volumes = []
        down_volumes = []

        for i in range(len(closes) - period, len(closes)):
            if closes[i] > closes[i-1]:
                up_volumes.append(volumes[i])
                down_volumes.append(0)
            elif closes[i] < closes[i-1]:
                up_volumes.append(0)
                down_volumes.append(volumes[i])
            else:
                up_volumes.append(0)
                down_volumes.append(0)

        mf_up = np.mean(up_volumes) if up_volumes else 0
        mf_down = np.mean(down_volumes) if down_volumes else 0

        if mf_up + mf_down == 0:
            return 50.0

        money_flow = 100 * mf_up / (mf_up + mf_down)
        return float(money_flow)

    def detect_liquidation(self, high: float, low: float, close: float, volume: float, avg_volume: float, atr: float) -> bool:
        """Liquidity Hunter - Detect liquidation events"""
        volume_spike = volume > avg_volume * 1.8
        wick_size = abs(high - low) > atr * 1.2
        price_jump = abs(close - (high + low) / 2) / close > 0.008
        return volume_spike and wick_size and price_jump

    def calculate_golden_pocket(self, high: float, low: float) -> Tuple[float, float]:
        """Calculate Golden Pocket zone (61.8% - 65% Fibonacci)"""
        range_size = high - low
        gp_high = high - (range_size * 0.618)
        gp_low = high - (range_size * 0.65)
        return gp_high, gp_low

    def is_near_golden_pocket(self, price: float, gp_high: float, gp_low: float) -> bool:
        """Check if price is near Golden Pocket"""
        if gp_high == gp_low:
            return False
        return gp_low <= price <= gp_high or abs(price - gp_low) / price < 0.02 or abs(price - gp_high) / price < 0.02

    def detect_order_block(self, ohlcv: List[List], idx: int, lookback: int = 20) -> bool:
        """Detect Order Block pattern"""
        if idx < lookback:
            return False

        current = ohlcv[idx]
        prev_high = max([h[2] for h in ohlcv[idx-lookback:idx]])
        prev_low = min([l[3] for l in ohlcv[idx-lookback:idx]])

        # Bullish OB: strong bearish candle followed by bullish reversal
        is_bearish = current[4] < current[1]  # close < open
        body_size = abs(current[4] - current[1])
        range_size = current[2] - current[3]

        if is_bearish and body_size > range_size * 0.42:
            # Check if price broke above this level
            if idx < len(ohlcv) - 5:
                future_high = max([h[2] for h in ohlcv[idx+1:idx+6]])
                if future_high > current[2]:
                    return True

        return False

    def detect_sweep(self, ohlcv: List[List], idx: int, lookback: int = 36) -> bool:
        """Detect liquidity sweep"""
        if idx < lookback:
            return False

        current = ohlcv[idx]
        prev_low = min([l[3] for l in ohlcv[idx-lookback:idx]])
        prev_high = max([h[2] for h in ohlcv[idx-lookback:idx]])

        atr = np.mean([abs(h[2] - h[3]) for h in ohlcv[idx-14:idx]]) if idx >= 14 else 0

        # Sweep low: price goes below previous low then closes above
        if current[3] < prev_low and current[4] > prev_low:
            wick_size = (current[3] - min(current[1], current[4])) / (current[2] - current[3])
            if wick_size >= 0.65:
                return True

        # Sweep high: price goes above previous high then closes below
        if current[2] > prev_high and current[4] < prev_high:
            wick_size = (max(current[1], current[4]) - current[2]) / (current[2] - current[3])
            if wick_size >= 0.65:
                return True

        return False

    def calculate_vwap(self, ohlcv: List[List], start_idx: int = 0) -> float:
        """Calculate VWAP from start of session"""
        if start_idx >= len(ohlcv):
            return 0.0

        cumulative_volume = 0
        cumulative_pv = 0

        for i in range(start_idx, len(ohlcv)):
            typical_price = (ohlcv[i][2] + ohlcv[i][3] + ohlcv[i][4]) / 3
            volume = ohlcv[i][5]
            cumulative_pv += typical_price * volume
            cumulative_volume += volume

        if cumulative_volume == 0:
            return 0.0

        return cumulative_pv / cumulative_volume

    def detect_divergence(self, prices: List[float], indicator: List[float], lookback: int = 20) -> Tuple[bool, bool]:
        """Detect regular bullish/bearish divergence"""
        if len(prices) < lookback or len(indicator) < lookback:
            return False, False

        # Find recent pivot lows
        recent_prices = prices[-lookback:]
        recent_indicator = indicator[-lookback:]

        # Simple divergence: price makes lower low but indicator makes higher low (bullish)
        # or price makes higher high but indicator makes lower high (bearish)
        price_low = min(recent_prices)
        price_high = max(recent_prices)
        ind_low = min(recent_indicator)
        ind_high = max(recent_indicator)

        # Find indices
        price_low_idx = recent_prices.index(price_low)
        price_high_idx = recent_prices.index(price_high)
        ind_low_idx = recent_indicator.index(ind_low)
        ind_high_idx = recent_indicator.index(ind_high)

        # Bullish divergence: price lower low, indicator higher low
        bull_div = (price_low_idx < len(recent_prices) - 5 and
                   ind_low_idx > price_low_idx and
                   recent_indicator[ind_low_idx] > recent_indicator[price_low_idx])

        # Bearish divergence: price higher high, indicator lower high
        bear_div = (price_high_idx < len(recent_prices) - 5 and
                   ind_high_idx < price_high_idx and
                   recent_indicator[ind_high_idx] < recent_indicator[price_high_idx])

        return bull_div, bear_div

    def analyze_coin(self, symbol: str) -> Optional[CoinPick]:
        """Analyze coin with all indicators"""
        try:
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=200)
            if not ohlcv or len(ohlcv) < 100:
                return None

            closes = [c[4] for c in ohlcv]
            highs = [c[2] for c in ohlcv]
            lows = [c[3] for c in ohlcv]
            opens = [c[1] for c in ohlcv]
            volumes = [c[5] for c in ohlcv]

            current_price = closes[-1]

            # Basic calculations
            rsi = self.calculate_rsi(closes, 14)
            atr = np.mean([abs(highs[i] - lows[i]) for i in range(-14, 0)]) if len(highs) >= 14 else 0
            avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else np.mean(volumes)

            # Price changes
            price_change_24h = ((closes[-1] - closes[-24]) / closes[-24] * 100) if len(closes) >= 24 else 0
            price_change_7d = ((closes[-1] - closes[-168]) / closes[-168] * 100) if len(closes) >= 168 else 0

            # EXCLUDE coins that already moved
            if abs(price_change_24h) > 8 or abs(price_change_7d) > 15:
                return None

            # Find recent high/low
            lookback = min(90 * 24, len(closes))
            recent_high = max(highs[-lookback:])
            recent_low = min(lows[-lookback:])

            distance_from_high = ((recent_high - current_price) / recent_high) * 100
            distance_from_low = ((current_price - recent_low) / recent_low) * 100

            # INDICATOR CALCULATIONS

            # 1. Oath Keeper - Money Flow
            money_flow = self.calculate_money_flow(closes, volumes, 8)
            mf_oversold = money_flow < 30
            # Calculate previous money flow for trend
            if len(closes) > 10:
                prev_mf = self.calculate_money_flow(closes[:-1], volumes[:-1], 8)
                mf_turning_up = money_flow > prev_mf
            else:
                mf_turning_up = False

            # 2. Liquidity Hunter
            liquidation = self.detect_liquidation(highs[-1], lows[-1], closes[-1], volumes[-1], avg_volume, atr)

            # 3. Golden Pocket
            gp_high, gp_low = self.calculate_golden_pocket(recent_high, recent_low)
            near_gp = self.is_near_golden_pocket(current_price, gp_high, gp_low)

            # 4. Order Block
            order_block = self.detect_order_block(ohlcv, len(ohlcv) - 1)

            # 5. Sweep
            sweep = self.detect_sweep(ohlcv, len(ohlcv) - 1)

            # 6. VWAP
            vwap = self.calculate_vwap(ohlcv, max(0, len(ohlcv) - 24))
            price_below_vwap = current_price < vwap if vwap > 0 else False

            # 7. Divergence (on Money Flow)
            mf_values = [self.calculate_money_flow(closes[:i+10], volumes[:i+10], 8)
                        for i in range(10, len(closes))]
            bull_div, bear_div = self.detect_divergence(closes[10:], mf_values, 20)

            # CONFIDENCE SCORING
            confidence = 0
            reasons = []
            indicators = {
                'money_flow_oversold': False,
                'liquidation': False,
                'golden_pocket': False,
                'order_block': False,
                'sweep': False,
                'divergence': False,
                'near_bottom': False
            }

            # Near bottom (highest priority)
            is_near_bottom = distance_from_low < 8
            if is_near_bottom:
                confidence += 35
                reasons.append("Near 90D low")
                indicators['near_bottom'] = True

            # Money Flow oversold
            if mf_oversold:
                confidence += 25
                reasons.append(f"Money Flow oversold ({money_flow:.1f})")
                indicators['money_flow_oversold'] = True

            # Golden Pocket
            if near_gp:
                confidence += 20
                reasons.append("Near Golden Pocket")
                indicators['golden_pocket'] = True

            # Liquidation detected
            if liquidation:
                confidence += 15
                reasons.append("Liquidation event")
                indicators['liquidation'] = True

            # Order Block
            if order_block:
                confidence += 15
                reasons.append("Order Block detected")
                indicators['order_block'] = True

            # Sweep
            if sweep:
                confidence += 15
                reasons.append("Liquidity sweep")
                indicators['sweep'] = True

            # Divergence
            if bull_div:
                confidence += 15
                reasons.append("Bullish divergence")
                indicators['divergence'] = True

            # RSI oversold
            if rsi < 35:
                confidence += 10
                reasons.append(f"RSI oversold ({rsi:.1f})")

            # Price below VWAP (potential bounce)
            if price_below_vwap:
                confidence += 8
                reasons.append("Below VWAP")

            # Stagnant (hasn't moved)
            if abs(price_change_24h) < 5 and abs(price_change_7d) < 10:
                confidence += 10
                reasons.append("No big moves yet")

            # Volume check
            volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1.0
            if volume_ratio > 1.2:
                confidence += 5
                reasons.append("Volume increasing")
            elif volume_ratio < 0.4:
                confidence -= 5

            # Calculate confluence score
            confluence_score = sum([
                20 if indicators['near_bottom'] else 0,
                15 if indicators['money_flow_oversold'] else 0,
                15 if indicators['golden_pocket'] else 0,
                12 if indicators['liquidation'] else 0,
                12 if indicators['order_block'] else 0,
                12 if indicators['sweep'] else 0,
                10 if indicators['divergence'] else 0,
                10 if rsi < 35 else 0,
                8 if price_below_vwap else 0
            ])

            confidence = max(0, min(100, confidence))

            # Only return high-quality picks
            if confidence >= 55:
                try:
                    ticker = self.exchange.fetch_ticker(symbol)
                    volume_24h = ticker.get('quoteVolume', 0) or 0
                except:
                    volume_24h = avg_volume * 24

                return CoinPick(
                    symbol=symbol,
                    price=current_price,
                    price_change_24h=price_change_24h,
                    price_change_7d=price_change_7d,
                    volume_24h=volume_24h,
                    rsi=rsi,
                    money_flow=money_flow,
                    confluence_score=confluence_score,
                    confidence=confidence,
                    reasons=reasons,
                    distance_from_low=distance_from_low,
                    distance_from_high=distance_from_high,
                    indicators=indicators
                )

            return None

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            return None

    def get_tradingview_link(self, symbol: str) -> str:
        """Generate TradingView link"""
        clean_symbol = symbol.split(':')[0].replace('/', '').upper()
        if not clean_symbol.endswith('USDT'):
            clean_symbol = f"{clean_symbol}USDT"
        return f"https://www.tradingview.com/chart/?symbol=MEXC:{clean_symbol}"

    def send_discord_alert(self, picks: List[CoinPick]):
        """Send Discord alert with all picks in a single card"""
        if not picks:
            return

        try:
            # Single comprehensive embed with all picks
            description_parts = [f"**Found {len(picks)} bottom setups ready to move up**\n"]

            # Add each pick to the description
            for i, pick in enumerate(picks[:NUM_PICKS], 1):
                # Format indicators
                active_indicators = [k.replace('_', ' ').title() for k, v in pick.indicators.items() if v]
                indicators_text = ", ".join(active_indicators[:3]) if active_indicators else "None"
                if len(active_indicators) > 3:
                    indicators_text += f" +{len(active_indicators)-3} more"

                tv_link = self.get_tradingview_link(pick.symbol)

                # Format price
                if pick.price < 0.01:
                    price_str = f"${pick.price:.6f}"
                elif pick.price < 1:
                    price_str = f"${pick.price:.4f}"
                else:
                    price_str = f"${pick.price:.2f}"

                # Format volume
                if pick.volume_24h >= 1_000_000:
                    volume_str = f"${pick.volume_24h/1_000_000:.2f}M"
                elif pick.volume_24h >= 1_000:
                    volume_str = f"${pick.volume_24h/1_000:.2f}K"
                else:
                    volume_str = f"${pick.volume_24h:.2f}"

                # Top reasons (limit to 3)
                top_reasons = pick.reasons[:3]

                pick_text = (
                    f"\n**#{i} {pick.symbol}** | [📈 Chart]({tv_link})\n"
                    f"💰 Price: {price_str} | 🎯 Confidence: {pick.confidence:.0f}% | ⭐ Confluence: {pick.confluence_score:.0f}%\n"
                    f"📊 24h: {pick.price_change_24h:+.2f}% | 7d: {pick.price_change_7d:+.2f}% | RSI: {pick.rsi:.1f} | MF: {pick.money_flow:.1f}\n"
                    f"📍 From Low: {pick.distance_from_low:.1f}% | From High: {pick.distance_from_high:.1f}% | Vol: {volume_str}\n"
                    f"🎯 Indicators: {indicators_text}\n"
                    f"✅ Top Reasons: {' • '.join(top_reasons)}\n"
                    f"{'─' * 50}"
                )
                description_parts.append(pick_text)

            # Create single embed
            main_embed = {
                "title": f"🔻 BOTTOM SCANNER - TOP {len(picks)} PICKS",
                "description": "".join(description_parts),
                "color": 0xff6b00,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fields": [
                    {
                        "name": "📊 Scan Summary",
                        "value": f"**Total Picks:** {len(picks)}\n**Scan Time:** {datetime.now().strftime('%H:%M:%S UTC')}\n**Next Scan:** 30 minutes",
                        "inline": True
                    },
                    {
                        "name": "🎯 Strategy",
                        "value": "Coins at bottoms with indicator confluence\n• Money Flow oversold\n• Golden Pocket zones\n• Order Blocks & Sweeps\n• VWAP positioning",
                        "inline": True
                    }
                ],
                "footer": {"text": "Enhanced Bottom Scanner • MEXC Futures • All picks in one card"}
            }

            # Send single message with all picks
            payload = {"embeds": [main_embed]}
            response = requests.post(self.webhook_url, json=payload, timeout=15)

            if response.status_code in (200, 204):
                logger.info(f"✅ All {len(picks)} picks sent in single card")
            else:
                logger.error(f"❌ Failed to send: {response.status_code}")

        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")

    def scan(self) -> List[CoinPick]:
        """Run scan"""
        logger.info("🔍 Starting enhanced bottom scan...")

        all_picks = []
        scan_list = self.watchlist[:100]  # Scan first 100 pairs

        for symbol in scan_list:
            try:
                pick = self.analyze_coin(symbol)
                if pick:
                    all_picks.append(pick)
                    logger.info(f"🎯 Found: {pick.symbol} (confidence: {pick.confidence:.0f}%, confluence: {pick.confluence_score:.0f}%)")

                time.sleep(0.1)

            except Exception as e:
                logger.debug(f"Error scanning {symbol}: {e}")
                continue

        # Sort by confluence score and confidence
        all_picks.sort(key=lambda x: (-x.confluence_score, -x.confidence))

        # Filter recent picks
        current_time = time.time()
        cooldown_seconds = self.pick_cooldown_hours * 3600

        self.recent_picks = [
            (s, t) for s, t in self.recent_picks
            if current_time - t < cooldown_seconds
        ]

        recent_symbols = {s for s, _ in self.recent_picks}
        filtered_picks = [p for p in all_picks if p.symbol not in recent_symbols]

        if len(filtered_picks) < NUM_PICKS and len(all_picks) >= NUM_PICKS:
            filtered_picks = all_picks

        top_picks = filtered_picks[:NUM_PICKS]

        for pick in top_picks:
            self.recent_picks.append((pick.symbol, current_time))

        logger.info(f"🎉 Scan complete: Found {len(all_picks)} opportunities, sending top {len(top_picks)}")

        return top_picks

    def run(self):
        """Main loop"""
        logger.info("🚀 Enhanced Bottom Scanner started")
        logger.info(f"⏰ Scan interval: {SCAN_INTERVAL_SEC / 60} minutes")
        logger.info(f"🎯 Picks per scan: {NUM_PICKS}")

        # Startup notification
        startup_embed = {
            "title": "🚀 ENHANCED BOTTOM SCANNER STARTED",
            "description": "Bot is now scanning with advanced indicators:\n• Oath Keeper (Money Flow)\n• Liquidity Hunter\n• Golden Pocket Syndicate\n• Bounty Seeker (OB/Sweeps)\n• VWAP Analysis",
            "color": 0x00ff00,
            "footer": {"text": "Enhanced Bottom Scanner • Ready to hunt bottoms!"}
        }

        try:
            requests.post(self.webhook_url, json={"embeds": [startup_embed]}, timeout=15)
        except:
            pass

        scan_count = 0
        while True:
            try:
                current_time = time.time()

                if current_time - self.last_scan_time >= SCAN_INTERVAL_SEC:
                    scan_count += 1
                    logger.info(f"\n{'='*60}\n🔍 Starting scan #{scan_count}\n{'='*60}\n")

                    picks = self.scan()

                    if picks:
                        self.send_discord_alert(picks)
                    else:
                        logger.info("⏳ No picks found this scan")

                    self.last_scan_time = current_time

                time.sleep(60)

            except KeyboardInterrupt:
                logger.info("🛑 Scanner stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Scanner error: {e}", exc_info=True)
                time.sleep(60)

def main():
    scanner = BottomScannerEnhanced(DISCORD_WEBHOOK)
    scanner.run()

if __name__ == "__main__":
    main()
