#!/usr/bin/env python3
"""
Short Hunter Bot - Headless Discord Alert Bot
Scans for exhausted tops and sends Discord webhook alerts for short opportunities.
"""

import time
import logging
import requests
import json
import os
from datetime import datetime, timedelta, timezone
from collections import deque
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field

# ==========================================
# CONFIGURATION
# ==========================================
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1444925694290300938/ACddvkCxvrMz6I_LqbH7l4TOyhicCMh67g-kAtal8YPi0F-AZbXnZpYe7vzrQihJKo5X'
EXCHANGE = "OKX"
OKX_INSTRUMENTS_URL = "https://www.okx.com/api/v5/public/instruments"
OKX_CANDLES_URL = "https://www.okx.com/api/v5/market/candles"
OKX_INST_TYPE = "SWAP"
OKX_SETTLE = "USDT"
OKX_CANDLE_BAR = "15m"
OKX_CANDLE_LIMIT = 100
OKX_LOOKBACK = 96  # ~24h of 15m candles
TRADES_FILE = "active_trades.json"

# Global market data cache
market_data_cache: Dict[str, Dict] = {}

DEFAULT_ASSETS = [
    {'s': 'BTCUSDT', 'n': 'Bitcoin'},
    {'s': 'ETHUSDT', 'n': 'Ethereum'},
    {'s': 'SOLUSDT', 'n': 'Solana'},
    {'s': 'ARBUSDT', 'n': 'Arbitrum'},
    {'s': 'OPUSDT', 'n': 'Optimism'},
    {'s': 'PEPEUSDT', 'n': 'Pepe (Volatile)'},
    {'s': 'WIFUSDT', 'n': 'dogwifhat'},
    {'s': 'FETUSDT', 'n': 'Fetch.ai'}
]

# Trade limits
MAX_TRADES_PER_HOUR = 3
MAX_ACTIVE_TRADES = 3
SCAN_MINUTE = 45  # Scan at :45 of each hour (15 min before top of hour)
CARD_COLOR = 0x9b59b6  # Purple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('short_hunter_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Debug logging (NDJSON)
DEBUG_LOG_PATH = "/Users/bishop/Documents/GitHub/SnipersRUs/.cursor/debug.log"

def _debug_log(hypothesis_id: str, location: str, message: str, data: Dict):
    try:
        payload = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(DEBUG_LOG_PATH, "a") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass

def _ensure_single_instance(pid_file: str):
    # #region agent log
    _debug_log(
        "H6",
        "short_hunter_bot.py:83",
        "ensure_single_instance start",
        {
            "pid_file": pid_file,
            "pid_exists": os.path.exists(pid_file),
        },
    )
    # #endregion
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                pid_str = f.read().strip()
            if pid_str.isdigit():
                existing_pid = int(pid_str)
                if existing_pid != os.getpid():
                    try:
                        os.kill(existing_pid, 0)
                        # #region agent log
                        _debug_log(
                            "H6",
                            "short_hunter_bot.py:99",
                            "existing instance detected",
                            {"existing_pid": existing_pid},
                        )
                        # #endregion
                        logger.error(f"❌ Bot already running (PID: {existing_pid}). Exiting.")
                        raise SystemExit(1)
                    except OSError:
                        pass
        except Exception:
            pass
    try:
        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

# ==========================================
# DATA STRUCTURES
# ==========================================
@dataclass
class Signal:
    symbol: str
    price: float
    score: int
    reasons: List[str]
    stop_loss: float
    take_profit: float

@dataclass
class ActiveTrade:
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    signal_time: datetime
    reasons: List[str]
    score: int
    status: str = "ACTIVE"  # ACTIVE, CLOSED_TP, CLOSED_SL

# ==========================================
# TRADE PERSISTENCE
# ==========================================
class TradeTracker:
    """Track active trades and assign sequential numbers"""
    def __init__(self):
        self.active_trades: Dict[str, ActiveTrade] = {}
        self.trade_counter = 0
        self._load_trades()

    def _load_trades(self):
        """Load trades from file"""
        if os.path.exists(TRADES_FILE):
            try:
                with open(TRADES_FILE, 'r') as f:
                    data = json.load(f)
                    for symbol, trade_data in data.get('active_trades', {}).items():
                        self.active_trades[symbol] = ActiveTrade(
                            symbol=symbol,
                            entry_price=trade_data['entry_price'],
                            stop_loss=trade_data['stop_loss'],
                            take_profit=trade_data['take_profit'],
                            signal_time=datetime.fromisoformat(trade_data['signal_time']),
                            reasons=trade_data['reasons'],
                            score=trade_data['score'],
                            status=trade_data.get('status', 'ACTIVE')
                        )
                    self.trade_counter = data.get('trade_counter', 0)
                    logger.info(f"📂 Loaded {len(self.active_trades)} active trades from disk")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load trades: {e}")

    def _save_trades(self):
        """Save trades to file"""
        data = {
            'active_trades': {},
            'trade_counter': self.trade_counter
        }
        for symbol, trade in self.active_trades.items():
            data['active_trades'][symbol] = {
                'entry_price': trade.entry_price,
                'stop_loss': trade.stop_loss,
                'take_profit': trade.take_profit,
                'signal_time': trade.signal_time.isoformat(),
                'reasons': trade.reasons,
                'score': trade.score,
                'status': trade.status
            }
        try:
            with open(TRADES_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Failed to save trades: {e}")

    def add_trade(self, signal: Signal, trade_number: int) -> bool:
        """Add a new active trade"""
        # #region agent log
        _debug_log(
            "H4",
            "short_hunter_bot.py:156",
            "add_trade called",
            {
                "symbol": signal.symbol,
                "trade_number": trade_number,
                "active_count": len(self.active_trades),
                "max_active": MAX_ACTIVE_TRADES,
            },
        )
        # #endregion
        if len(self.active_trades) >= MAX_ACTIVE_TRADES:
            logger.warning(f"⚠️  Max active trades ({MAX_ACTIVE_TRADES}) reached. Cannot add {signal.symbol}")
            return False

        self.trade_counter = trade_number
        self.active_trades[signal.symbol] = ActiveTrade(
            symbol=signal.symbol,
            entry_price=signal.price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            signal_time=datetime.now(),
            reasons=signal.reasons,
            score=signal.score,
            status="ACTIVE"
        )
        self._save_trades()
        logger.info(f"📝 Trade #{trade_number}: {signal.symbol} @ {signal.price:.2f} (SL: {signal.stop_loss:.2f}, TP: {signal.take_profit:.2f})")
        return True

    def update_trade_status(self, symbol: str, status: str, current_price: float) -> bool:
        """Update trade status based on price"""
        if symbol not in self.active_trades:
            return False

        trade = self.active_trades[symbol]
        closed = False

        if status == "CLOSED_TP" or (status == "ACTIVE" and current_price <= trade.take_profit):
            trade.status = "CLOSED_TP"
            closed = True
            logger.info(f"🎯 Trade #{self.trade_counter}: {symbol} CLOSED AT TP ({current_price:.2f})")
        elif status == "CLOSED_SL" or (status == "ACTIVE" and current_price >= trade.stop_loss):
            trade.status = "CLOSED_SL"
            closed = True
            logger.info(f"🛑 Trade #{self.trade_counter}: {symbol} CLOSED AT SL ({current_price:.2f})")

        if closed:
            self.active_trades[symbol] = trade
            self._save_trades()
            return True
        return False

    def get_trade_number(self, symbol: str) -> int:
        """Get the assigned trade number for a symbol"""
        if symbol in self.active_trades:
            return self.trade_counter
        return 0

    def remove_trade(self, symbol: str):
        """Remove a trade from tracking"""
        if symbol in self.active_trades:
            trade = self.active_trades[symbol]
            logger.info(f"🗑️  Removing {symbol} from tracking (status: {trade.status})")
            del self.active_trades[symbol]
            self._save_trades()

    def get_active_trades_count(self) -> int:
        return len(self.active_trades)

    def get_closed_trades_count(self) -> int:
        return self.trade_counter - len(self.active_trades)

    def get_next_trade_number(self) -> int:
        return self.trade_counter + 1


# ==========================================
# OKX API FUNCTIONS
# ==========================================
def _normalize_okx_symbol(inst_id: str) -> Optional[str]:
    if not inst_id.endswith("-SWAP"):
        return None
    parts = inst_id.split("-")
    if len(parts) != 3:
        return None
    base, quote, _ = parts
    if quote != "USDT":
        return None
    return f"{base}{quote}"


def load_okx_perps(limit: Optional[int] = None) -> List[Dict[str, str]]:
    try:
        params = {"instType": OKX_INST_TYPE}
        resp = requests.get(OKX_INSTRUMENTS_URL, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("data", [])
        symbols: List[Dict[str, str]] = []
        for item in data:
            if item.get("instType") != OKX_INST_TYPE:
                continue
            if item.get("settleCcy") != OKX_SETTLE:
                continue
            sym = _normalize_okx_symbol(item.get("instId", ""))
            if not sym:
                continue
            symbols.append({"s": sym, "n": sym.replace("USDT", "")})
        symbols = sorted(symbols, key=lambda x: x["s"])
        if limit is not None and len(symbols) > limit:
            symbols = symbols[:limit]
        logger.info(f"📊 Loaded {len(symbols)} OKX perps" + (f" (limited to {limit})" if limit else ""))
        return symbols
    except Exception as exc:
        logger.error(f"❌ Failed to load OKX perps: {exc}")
        return []


def tradingview_symbol(symbol: str) -> str:
    """Format symbol for TradingView OKX perp charts: OKX:BTCUSDT.P"""
    return f"OKX:{symbol}.P"


def _symbol_to_okx_inst(symbol: str) -> Optional[str]:
    if not symbol.endswith("USDT"):
        return None
    base = symbol[:-4]
    return f"{base}-USDT-SWAP"


def _compute_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains = []
    losses = []
    for i in range(1, period + 1):
        delta = closes[-i] - closes[-i - 1]
        if delta >= 0:
            gains.append(delta)
        else:
            losses.append(abs(delta))
    avg_gain = sum(gains) / period if gains else 0.0
    avg_loss = sum(losses) / period if losses else 0.0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


# ==========================================
# MARKET DATA ENGINE (OKX LIVE)
# ==========================================
class MarketEngine:
    def __init__(self, assets: List[Dict[str, str]]):
        self.assets = assets
        self.session = requests.Session()
        self.trade_tracker = TradeTracker()

    def _fetch_candles(self, inst_id: str) -> List[List[float]]:
        params = {"instId": inst_id, "bar": OKX_CANDLE_BAR, "limit": OKX_CANDLE_LIMIT}
        resp = self.session.get(OKX_CANDLES_URL, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("data", [])
        candles = []
        for row in data:
            try:
                # [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]
                o = float(row[1])
                h = float(row[2])
                l = float(row[3])
                c = float(row[4])
                v = float(row[5])
                candles.append([o, h, l, c, v])
            except Exception:
                continue
        candles.reverse()
        return candles

    def tick(self) -> Dict[str, Dict]:
        """Fetch real OKX 15m candles and build market snapshot"""
        data: Dict[str, Dict] = {}

        for asset in self.assets:
            symbol = asset["s"]
            inst_id = _symbol_to_okx_inst(symbol)
            if not inst_id:
                continue

            try:
                candles = self._fetch_candles(inst_id)
                if len(candles) < OKX_LOOKBACK:
                    logger.debug(f"Not enough candles for {symbol}: {len(candles)}")
                    continue

                lookback = candles[-OKX_LOOKBACK:] if len(candles) >= OKX_LOOKBACK else candles
                highs = [c[1] for c in lookback]
                lows = [c[2] for c in lookback]
                closes = [c[3] for c in lookback]
                vols = [c[4] for c in lookback]
                last_o, last_h, last_l, last_c, last_v = candles[-1]

                high = max(highs)
                low = min(lows)
                change = ((last_c - low) / low) * 100 if low > 0 else 0.0

                # VWAP approximation
                typicals = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
                vol_sum = sum(vols)
                vwap = sum(t * v for t, v in zip(typicals, vols)) / vol_sum if vol_sum > 0 else last_c

                # Deviation (std dev of closes)
                mean_close = sum(closes) / len(closes)
                variance = sum((c - mean_close) ** 2 for c in closes) / len(closes)
                std_dev = variance ** 0.5 if variance > 0 else 1.0
                dev = round((last_c - vwap) / std_dev, 2) if std_dev > 0 else 0.0

                # RSI
                rsi = _compute_rsi(closes, 14)

                # Liquidity sweep (break + reject)
                prev_high = max([c[1] for c in candles[-21:-1]]) if len(candles) > 21 else high
                is_sweep = last_h > prev_high and last_c < prev_high

                # Volume spikes (20-period MA + std dev)
                vol_slice = vols[-20:] if len(vols) >= 20 else vols
                vol_ma = sum(vol_slice) / len(vol_slice)
                vol_var = sum((v - vol_ma) ** 2 for v in vol_slice) / len(vol_slice)
                vol_std = vol_var ** 0.5
                dynamic_threshold = vol_ma + vol_std * 2.0
                extreme_threshold = vol_ma + vol_std * 3.5
                is_abnormal_volume = last_v > dynamic_threshold
                is_extreme_volume = last_v > extreme_threshold

                # Check if trade should be closed
                if symbol in self.trade_tracker.active_trades:
                    current_price = last_c
                    self.trade_tracker.update_trade_status(symbol, "ACTIVE", current_price)

                data[symbol] = {
                    "price": last_c,
                    "high": high,
                    "low": low,
                    "change": change,
                    "rsi": rsi,
                    "vwap": vwap,
                    "dev": dev,
                    "is_sweep": is_sweep,
                    "volume": last_v,
                    "vol_ma": vol_ma,
                    "vol_std": vol_std,
                    "is_abnormal_volume": is_abnormal_volume,
                    "is_extreme_volume": is_extreme_volume,
                }
                time.sleep(0.01)
            except Exception as exc:
                logger.debug(f"OKX candle fetch failed for {symbol}: {exc}")
                continue

        return data


# ==========================================
# STRATEGY LOGIC (SHORT HUNTER)
# ==========================================
def analyze_market(market_data: Dict[str, Dict], trade_tracker: TradeTracker, trades_this_hour: int):
    """Analyze market data for short opportunities and build watchlist

    Returns:
        signals: List[Signal] that qualify as full short setups
        watchlist: List[Tuple[symbol, distance_pct, gp_resist, price]]
    """
    signals: List[Signal] = []
    watch_candidates = []

    # Trade limit check
    if trades_this_hour >= MAX_TRADES_PER_HOUR:
        logger.info(f"⚠️  Hourly trade limit ({MAX_TRADES_PER_HOUR}/{MAX_TRADES_PER_HOUR}) reached. Skipping new signals.")
        return signals

    for symbol, coin in market_data.items():
        # Skip if already have active trade (unless closed)
        if symbol in trade_tracker.active_trades:
            continue

        reasons = []
        score = 0

        # 1. GPS Resistance Logic
        range_val = coin["high"] - coin["low"]
        gp_resist = coin["low"] + (range_val * 0.65)

        price = coin["price"]
        # Distance from resistance in %
        dist_pct = ((gp_resist - price) / gp_resist) * 100 if gp_resist > 0 else 0.0

        if price >= gp_resist:
            score += 30
            reasons.append(f"Price at GPS Resistance Zone ({gp_resist:.2f})")
        else:
            # Collect for watchlist if within 5% below resistance
            if 0 <= dist_pct <= 5:
                watch_candidates.append((symbol, dist_pct, gp_resist, price))

        # 2. Deviation Zones (Overextension)
        if coin["dev"] > 2.5:
            score += 40
            reasons.append("Deviation +3 Sigma Zone (Overextended)")
        elif coin["dev"] > 2.0:
            score += 20
            reasons.append("Deviation +2 Sigma Zone")

        # 3. Bearish Divergence
        price_above_vwap = coin["price"] > coin["vwap"]
        rsi_weak = coin["rsi"] < 55

        if price_above_vwap and rsi_weak:
            score += 20
            reasons.append("Bearish Divergence (Price Up, RSI Exhausted)")

        # 4. Liquidity Sweep / SFP
        if coin["is_sweep"]:
            score += 15
            reasons.append("Liquidity Sweep (SFP High)")

        # 5. Exhausted Volume
        if coin["dev"] > 2.0 and rsi_weak:
            score += 10
            reasons.append("Buyer Exhaustion Detected")

        # 6. 15m Abnormal Volume Spike (Potential Reversal)
        if coin["is_extreme_volume"]:
            score += 25
            reasons.append("15m Extreme Volume Spike (Potential Reversal)")
        elif coin["is_abnormal_volume"]:
            score += 15
            reasons.append("15m Abnormal Volume Spike (Potential Reversal)")

        # Final decision
        if score >= 70:
            signals.append(Signal(
                symbol=symbol,
                price=price,
                score=score,
                reasons=reasons,
                stop_loss=price * 1.01,  # 1% SL above
                take_profit=price * 0.97  # 3% TP below
            ))

    # Build top-3 watchlist by closest distance to resistance
    watchlist = sorted(watch_candidates, key=lambda x: x[1])[:3]
    return signals, watchlist


# ==========================================
# DISCORD WEBHOOK INTEGRATION
# ==========================================
def send_discord_alert(signals: List[Signal], trade_tracker: TradeTracker, watchlist=None) -> bool:
    """Send Discord webhook alert for short signals - all on one card, plus watchlist"""
    if not signals:
        return True

    try:
        # #region agent log
        _debug_log(
            "H5",
            "short_hunter_bot.py:388",
            "send_discord_alert start",
            {
                "signals_count": len(signals),
                "active_trades": trade_tracker.get_active_trades_count(),
            },
        )
        # #endregion
        # Format trade lines for Discord content
        trade_lines = []
        for i, signal in enumerate(signals, 1):
            trade_num = trade_tracker.get_next_trade_number() + i - 1
            tv_url = f"https://www.tradingview.com/chart/?symbol={tradingview_symbol(signal.symbol)}"
            # #region agent log
            _debug_log(
                "H7",
                "short_hunter_bot.py:414",
                "tradingview url",
                {"symbol": signal.symbol, "tv_url": tv_url},
            )
            # #endregion
            trade_lines.append(f"**#{trade_num}:** [{signal.symbol}]({tv_url})")
            trade_lines.append(f"Entry: `{signal.price:.2f}` | SL: `{signal.stop_loss:.2f}` | TP: `{signal.take_profit:.2f}`")
            trade_lines.append(f"Score: {signal.score}/100 | RSI: {market_data_cache.get(signal.symbol, {}).get('rsi', 0):.1f} | Dev: {market_data_cache.get(signal.symbol, {}).get('dev', 0):.1f}")
            trade_lines.append(f"— {', '.join(signal.reasons)}")

        trade_lines_text = '\n'.join(trade_lines)

        # Build watchlist block (top 3 coins approaching resistance)
        watchlist_lines = []
        if watchlist:
            watchlist_lines.append("**Watchlist – Approaching GPS Resistance**")
            for symbol, dist_pct, gp_resist, price in watchlist:
                tv_url = f"https://www.tradingview.com/chart/?symbol={tradingview_symbol(symbol)}"
                watchlist_lines.append(
                    f"- [{symbol}]({tv_url}) • Price: `{price:.4g}` • GP: `{gp_resist:.4g}` • Distance: `{dist_pct:.2f}%` below"
                )
        watchlist_text = "\n".join(watchlist_lines) if watchlist_lines else ""

        # Create Discord embed - ORANGE COLOR
        embed = {
            "title": f"🔴 SHORT HUNTER: {len(signals)} NEW TRADE{'S' if len(signals) > 1 else ''}",
            "description": (
                f"**TOPS HUNTED - SHORT OPPORTUNIT{'Y' if len(signals) > 1 else 'IES'} DETECTED**\n\n"
                f"{trade_lines_text}"
                + ("\n\n" + watchlist_text if watchlist_text else "")
            ),
            "color": CARD_COLOR,  # Orange
            "fields": [
                {
                    "name": f"📝 Active Trades: {trade_tracker.get_active_trades_count()}/{MAX_ACTIVE_TRADES}",
                    "value": f"Closed Today: {trade_tracker.get_closed_trades_count()}",
                    "inline": True
                },
                {
                    "name": "⏰ Signal Time",
                    "value": f"<t:{int(time.time())}:F>",
                    "inline": True
                },
            ],
            "footer": {
                "text": "Short Hunter | GPS + Deviation Top Reversal Strategy | OKX 15m Candles"
            },
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }

        payload = {
            "username": "Short Hunter",
            "embeds": [embed],
            "content": f"🚨 **SHORT ALERT{'S' if len(signals) > 1 else ''}** 🚨\n\n{len(signals)} new trade{'s' if len(signals) > 1 else ''} detected! Pin this card! 📌"
        }

        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        # #region agent log
        _debug_log(
            "H5",
            "short_hunter_bot.py:451",
            "send_discord_alert response",
            {
                "status_code": response.status_code,
                "signals_count": len(signals),
            },
        )
        # #endregion

        if response.status_code in (200, 201, 204):
            logger.info(f"✅ Discord alert sent for {len(signals)} signal(s)")
            return True
        else:
            logger.error(f"❌ Failed to send Discord alert: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Error sending Discord alert: {e}")
        return False


# ==========================================
# MAIN BOT LOOP
# ==========================================
class ShortHunterBot:
    def __init__(self):
        self.assets = load_okx_perps()
        if len(self.assets) < 100:
            logger.warning(f"⚠️  OKX perps load returned {len(self.assets)} symbols. Falling back to defaults.")
            if not self.assets:
                self.assets = DEFAULT_ASSETS
        self.engine = MarketEngine(self.assets)
        self.trade_tracker = TradeTracker()
        self.trades_this_hour = 0
        self.current_hour = datetime.now().hour
        logger.info("🚀 Short Hunter Bot initialized")

    def reset_hourly_limits(self):
        """Reset trade limits on new hour"""
        now = datetime.now()
        if now.hour != self.current_hour:
            self.current_hour = now.hour
            self.trades_this_hour = 0
            logger.info(f"⏰ Hour {self.current_hour:02d} started. Trade limit reset (0/{MAX_TRADES_PER_HOUR})")

    def should_scan(self, last_scan_minute: int) -> bool:
        """Check if it's time to scan (at :45 of each hour)"""
        now = datetime.now()
        should = now.minute == SCAN_MINUTE and now.minute != last_scan_minute
        # Log at :45 to understand scan behavior
        if now.minute == SCAN_MINUTE and now.second == 0:
            logger.info(f"🔍 should_scan: minute={now.minute}, last_scan={last_scan_minute}, result={should}")
        return should

    def run_scan(self):
        """Run market scan and send alerts"""
        global market_data_cache
        now = datetime.now()
        logger.info(f"🔍 Scanning for short opportunities at {now.strftime('%H:%M:%S')}...")

        # #region agent log
        _debug_log(
            "H1",
            "short_hunter_bot.py:560",
            "run_scan start",
            {
                "time": now.strftime("%H:%M:%S"),
                "trades_this_hour": self.trades_this_hour,
                "active_trades": self.trade_tracker.get_active_trades_count(),
            },
        )
        # #endregion

        # Update market data
        market_data_cache = self.engine.tick()
        # #region agent log
        _debug_log(
            "H2",
            "short_hunter_bot.py:571",
            "market_data_cache fetched",
            {
                "pairs_count": len(market_data_cache),
            },
        )
        # #endregion

        # #region agent log
        _debug_log(
            "H3",
            "short_hunter_bot.py:578",
            "pre market_data check",
            {
                "market_data_cache_empty": len(market_data_cache) == 0,
                "market_data_defined": "market_data" in globals(),
            },
        )
        # #endregion
        if not market_data_cache:
            logger.warning("⚠️  No market data returned from OKX. Skipping scan.")
            return

        # Log current market state
        logger.info(f"📈 Market data updated for {len(market_data_cache)} pairs")

        # Analyze for signals + watchlist
        signals, watchlist = analyze_market(market_data_cache, self.trade_tracker, self.trades_this_hour)
        # #region agent log
        _debug_log(
            "H2",
            "short_hunter_bot.py:593",
            "signals computed",
            {
                "signals_count": len(signals),
                "active_trades": self.trade_tracker.get_active_trades_count(),
            },
        )
        # #endregion

        if signals:
            logger.info(f"📊 Found {len(signals)} short signal(s)!")

            # Add all trades first (sequential numbering)
            added_signals = []
            for signal in signals:
                trade_num = self.trade_tracker.get_next_trade_number()
                if not self.trade_tracker.add_trade(signal, trade_num):
                    logger.warning(f"⚠️  Could not add trade {signal.symbol} (max active: {MAX_ACTIVE_TRADES})")
                    continue
                self.trades_this_hour += 1
                added_signals.append(signal)

            # Send single Discord alert with all trades + watchlist
            if added_signals:
                logger.info(f"📤 Sending Discord alert for {len(added_signals)} signal(s)")
                if send_discord_alert(added_signals, self.trade_tracker, watchlist):
                    logger.info(f"✅ Alert sent! Trades this hour: {self.trades_this_hour}/{MAX_TRADES_PER_HOUR}")
                else:
                    logger.error("❌ Failed to send Discord alert")
            else:
                logger.info("✓ No new trades added (all signals blocked by limits).")
        else:
            logger.info(f"✓ No short signals detected (Active: {self.trade_tracker.get_active_trades_count()}/{MAX_ACTIVE_TRADES}, Trades/hour: {self.trades_this_hour}/{MAX_TRADES_PER_HOUR})")

    def run(self):
        """Main bot loop"""
        logger.info("🎯 Short Hunter Bot started!")
        logger.info(f"📅 Scan schedule: Every hour at :{SCAN_MINUTE} (15 min before top of hour, local time)")
        sample = ", ".join([a["s"] for a in self.assets[:15]])
        logger.info(f"📊 Monitoring {len(self.assets)} OKX perps (sample: {sample})")
        logger.info(f"🔔 Discord webhook: Configured")
        logger.info(f"📝 Max active trades: {MAX_ACTIVE_TRADES} | Trade persistence: {TRADES_FILE}")

        last_scan_minute = -1

        while True:
            try:
                now = datetime.now()

                # Reset hourly limits
                self.reset_hourly_limits()

                # Check if it's scan time (:45 of each hour)
                if self.should_scan(last_scan_minute):
                    last_scan_minute = now.minute
                    logger.info(f"⏰ Scan time reached: {now.strftime('%H:%M:%S')}")
                    # #region agent log
                    _debug_log(
                        "H1",
                        "short_hunter_bot.py:631",
                        "scan trigger",
                        {
                            "minute": now.minute,
                            "second": now.second,
                        },
                    )
                    # #endregion
                    self.run_scan()
                elif now.second == 0 and now.minute % 10 == 0:
                    # Log status every 10 minutes
                    next_scan_min = SCAN_MINUTE if now.minute < SCAN_MINUTE else SCAN_MINUTE + 60
                    minutes_until_scan = next_scan_min - now.minute
                    logger.info(f"⏳ Waiting for scan time... Next scan in ~{minutes_until_scan} minutes at :{SCAN_MINUTE} | Active: {self.trade_tracker.get_active_trades_count()}/{MAX_ACTIVE_TRADES}")

                # Sleep until next second
                time.sleep(1)

            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in bot loop: {e}", exc_info=True)
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(5)  # Wait before retrying


# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == "__main__":
    _ensure_single_instance("short_hunter_bot.pid")
    bot = ShortHunterBot()
    bot.run()
