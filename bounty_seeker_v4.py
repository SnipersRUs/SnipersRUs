#!/usr/bin/env python3
"""
Bounty Seeker v4 - Real-time Scanner with Live Paper Trading
- Scans ~500 USDT-perp symbols across the configured exchanges
- Trades only 9/10 and 10/10 signals
- Shares 7–8/10 confidence signals on Watchlist
"""
import os, json, time, logging, requests, ccxt
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from paper_trader import PaperTrader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BountySeekerV4")

def tv_link(symbol: str, exchange: str) -> str:
    base = symbol.replace("/USDT","").replace(":USDT","").replace("/","")
    exch = {"bybit":"BYBIT","bitget":"BITGET","mexc":"MEXC","binance":"BINANCE"}.get(exchange.lower(),"BINANCE")
    return f"https://www.tradingview.com/chart/?symbol={exch}:{base}USDT.P"

# ------------------------- Scanner -------------------------
class RealTimeScanner:
    """Scans a large basket of perp markets and produces technical signals."""
    def __init__(self, exchanges: Dict[str, ccxt.Exchange]):
        self.exchanges = exchanges
        self.watchlist = self._build_watchlist()

    def _build_watchlist(self) -> List[Dict]:
        """Collect ~500 USDT linear swap markets across exchanges, ranked by 24h USD volume."""
        items: List[Dict] = []
        for exid, ex in self.exchanges.items():
            # grab eligible markets from the exchange's markets map
            syms = []
            for s, m in ex.markets.items():
                try:
                    if m.get("swap") and m.get("linear") and m.get("quote") == "USDT":
                        syms.append(s)
                except Exception:
                    continue

            # attempt to get 24h volume in one call
            volmap: Dict[str, float] = {}
            try:
                # many ccxt exchanges support fetch_tickers(); fallback handled by except
                tickers = ex.fetch_tickers()
                for sym, t in tickers.items():
                    if sym not in syms:
                        continue
                    last = float(t.get("last") or t.get("close") or 0) or 0.0
                    qv   = t.get("quoteVolume")
                    if qv is None:
                        # synthesize USD volume if only baseVolume is present
                        bv = float(t.get("baseVolume") or 0.0)
                        usd24 = bv * last
                    else:
                        usd24 = float(qv or 0.0)
                    volmap[sym] = usd24
            except Exception:
                # no tickers: leave volumes as 0, still include symbols
                pass

            for sym in syms:
                base = sym.split("/")[0].replace("USDT","").replace(":USDT","")
                items.append({"symbol": sym, "exchange": exid, "base": base, "usd24": float(volmap.get(sym, 0.0))})

        # sort by volume descending and cap at ~500
        items.sort(key=lambda x: x.get("usd24", 0.0), reverse=True)
        uniq, seen = [], set()
        for it in items:
            key = (it["exchange"], it["symbol"])
            if key in seen:
                continue
            uniq.append(it)
            seen.add(key)
            if len(uniq) >= 500:
                break

        logger.info(f"Built watchlist: {len(uniq)} symbols across {len(self.exchanges)} exchanges")
        return uniq

    def _get_ohlcv_data(self, ex: ccxt.Exchange, symbol: str, timeframe: str = "1h", limit: int = 120) -> Optional[pd.DataFrame]:
        try:
            ohlcv = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            if not ohlcv: return None
            df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","volume"])
            df["ts"] = pd.to_datetime(df["ts"], unit="ms")
            df.set_index("ts", inplace=True)
            return df
        except Exception:
            return None

    def _calc_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # RSI
        delta = df["close"].diff()
        gain  = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100/(1+rs))

        # MAs
        df["sma_20"] = df["close"].rolling(20).mean()
        df["sma_50"] = df["close"].rolling(50).mean()
        df["ema_12"] = df["close"].ewm(span=12).mean()
        df["ema_26"] = df["close"].ewm(span=26).mean()

        # MACD
        df["macd"] = df["ema_12"] - df["ema_26"]
        df["macd_signal"] = df["macd"].ewm(span=9).mean()

        # Bollinger
        mid = df["close"].rolling(20).mean()
        std = df["close"].rolling(20).std()
        df["bb_middle"] = mid
        df["bb_upper"]  = mid + 2*std
        df["bb_lower"]  = mid - 2*std

        # Volume
        df["volume_sma"]   = df["volume"].rolling(20).mean()
        df["volume_ratio"] = df["volume"] / df["volume_sma"]

        # Momentum
        df["price_change_1h"] = ((df["close"] - df["close"].shift(1)) / df["close"].shift(1)) * 100
        return df

    def _signal(self, df: pd.DataFrame, symbol: str, exchange: str) -> Optional[Dict]:
        if len(df) < 50:
            return None
        latest, prev = df.iloc[-1], df.iloc[-2]
        conf, direction, style, reasons = 0, None, None, []

        # RSI inflections
        if latest["rsi"] < 30 <= prev["rsi"]:
            conf += 2; direction = "LONG";  style = "reversal"; reasons.append("RSI oversold bounce")
        elif latest["rsi"] > 70 >= prev["rsi"]:
            conf += 2; direction = "SHORT"; style = "reversal"; reasons.append("RSI overbought reversal")

        # MACD cross
        if latest["macd"] > latest["macd_signal"] and prev["macd"] <= prev["macd_signal"]:
            conf += 2;
            if direction != "SHORT": direction = "LONG"; style = "momentum"
            reasons.append("MACD bullish crossover")
        elif latest["macd"] < latest["macd_signal"] and prev["macd"] >= prev["macd_signal"]:
            conf += 2;
            if direction != "LONG": direction = "SHORT"; style = "momentum"
            reasons.append("MACD bearish crossover")

        # Bollinger taps
        if latest["close"] <= latest["bb_lower"] and prev["close"] > prev["bb_lower"]:
            conf += 1;
            if direction != "SHORT": direction = "LONG"; style = "reversal"
            reasons.append("Bollinger lower touch")
        elif latest["close"] >= latest["bb_upper"] and prev["close"] < prev["bb_upper"]:
            conf += 1;
            if direction != "LONG": direction = "SHORT"; style = "reversal"
            reasons.append("Bollinger upper touch")

        # SMA20 break
        if latest["close"] > latest["sma_20"] and prev["close"] <= prev["sma_20"]:
            conf += 1;
            if direction != "SHORT": direction = "LONG"; style = "breakout"
            reasons.append("SMA20 breakout")
        elif latest["close"] < latest["sma_20"] and prev["close"] >= prev["sma_20"]:
            conf += 1;
            if direction != "LONG": direction = "SHORT"; style = "breakdown"
            reasons.append("SMA20 breakdown")

        # Volume confirm
        if latest["volume_ratio"] > 1.5: conf += 1; reasons.append("High volume")
        elif latest["volume_ratio"] > 1.2: conf += 0.5; reasons.append("Elevated volume")

        # Trend alignment
        if direction == "LONG"  and latest["close"] > latest["sma_50"] and latest["sma_20"] > latest["sma_50"]:
            conf += 1; reasons.append("Uptrend alignment")
        if direction == "SHORT" and latest["close"] < latest["sma_50"] and latest["sma_20"] < latest["sma_50"]:
            conf += 1; reasons.append("Downtrend alignment")

        if conf >= 3 and direction and len(reasons) >= 2:
            return {
                "symbol": symbol,
                "exchange": exchange,
                "direction": direction,
                "entry": float(latest["close"]),
                "confidence": min(int(conf), 10),
                "style": style or "technical",
                "base": symbol.split("/")[0],
                "reason": " + ".join(reasons),
                "rsi": float(latest["rsi"]),
                "volume_ratio": float(latest["volume_ratio"]),
                "price_change_1h": float(latest["price_change_1h"]),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        return None

    def scan_markets(self) -> List[Dict]:
        logger.info(f"Scanning {len(self.watchlist)} markets for real-time signals…")
        out: List[Dict] = []
        for item in self.watchlist:
            try:
                ex = self.exchanges[item["exchange"]]
                df = self._get_ohlcv_data(ex, item["symbol"])
                if df is None or len(df) < 50:
                    continue
                df = self._calc_indicators(df)
                sig = self._signal(df, item["symbol"], item["exchange"])
                if sig:
                    out.append(sig)
                    logger.info(f"📊 {sig['base']} {sig['direction']} ({sig['confidence']}/10) — {sig['reason']}")
                time.sleep(0.05)  # gentle rate-limit cushion
            except Exception:
                continue
        logger.info(f"Scan complete: {len(out)} signals")
        return out

# ------------------------- Bot Orchestration -------------------------
class BountySeekerV4:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.state  = self._load_state()
        self.paper_trader = PaperTrader(self.state["paper"])
        self.ex_map: Dict[str, ccxt.Exchange] = {}
        self._init_exchanges()
        self.paper_trader.bind_exchanges(self.ex_map)
        self.scanner = RealTimeScanner(self.ex_map)
        # Dynamic scan interval logic
        self.has_found_trades = self._check_if_trades_found()
        self.current_scan_interval = self._get_current_scan_interval()
        # Message cooldown to prevent spam
        self.last_message_time = 0
        self.message_cooldown_sec = int(self.config.get("MESSAGE_COOLDOWN_SEC", 300))  # 5 minutes default
        logger.info("BountySeekerV4 initialized")

    # ---- config/state ----
    def _load_config(self, path: str) -> dict:
        try:
            with open(path,"r") as f: return json.load(f)
        except FileNotFoundError:
            logger.warning("No config.json found; using defaults")
            return {"DISCORD_WEBHOOK":"", "SCAN_INTERVAL_SEC":3600, "EXCHANGES":["bybit","bitget","mexc"]}
        except Exception as e:
            logger.error(f"Config error: {e}")
            return {"DISCORD_WEBHOOK":"", "SCAN_INTERVAL_SEC":3600, "EXCHANGES":["bybit","bitget","mexc"]}

    def _load_state(self) -> dict:
        try:
            with open("state.json","r") as f: st = json.load(f)
        except FileNotFoundError:
            st = {
                "paper": {
                    "balance": 10000.0,
                    "trades": [], "history": [],
                    "stats": {"wins":0,"losses":0,"realized_pnl":0.0,"unrealized_pnl":0.0,"total_pnl":0.0,"daily_pnl":0.0,
                              "last_reset": datetime.now(timezone.utc).isoformat()}
                },
                "last_scan_time": None
            }
        except Exception as e:
            logger.error(f"State error: {e}")
            st = {"paper":{"balance":10000.0,"trades":[],"history":[],"stats":{}}}

        # Ensure paper key exists
        if "paper" not in st:
            st["paper"] = {"balance":10000.0,"trades":[],"history":[],"stats":{}}

        st["paper"].setdefault("stats", {})
        for k,v in {"wins":0,"losses":0,"realized_pnl":0.0,"unrealized_pnl":0.0,"total_pnl":0.0,"daily_pnl":0.0,"last_reset":datetime.now(timezone.utc).isoformat()}.items():
            st["paper"]["stats"].setdefault(k,v)
        return st

    def _save_state(self):
        try:
            self.state["last_scan_time"] = datetime.now(timezone.utc).isoformat()
            with open("state.json","w") as f: json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Save error: {e}")

    def _check_if_trades_found(self) -> bool:
        """Check if we have any open trades or recent trade history"""
        # Check for open trades
        if self.state.get("paper", {}).get("trades"):
            return True

        # Check for recent trade history (last 24 hours)
        history = self.state.get("paper", {}).get("history", [])
        if history:
            try:
                last_trade_time = datetime.fromisoformat(history[-1].get("exit_ts", ""))
                if (datetime.now(timezone.utc) - last_trade_time).total_seconds() < 86400:  # 24 hours
                    return True
            except Exception:
                pass

        return False

    def _get_current_scan_interval(self) -> int:
        """Get current scan interval based on whether trades have been found"""
        if self.has_found_trades:
            return int(self.config.get("SCAN_INTERVAL_AFTER_TRADES_SEC", 7200))
        else:
            return int(self.config.get("SCAN_INTERVAL_SEC", 1800))

    def _update_scan_interval(self, trades_found: bool):
        """Update scan interval based on whether trades were found in this scan"""
        if trades_found and not self.has_found_trades:
            self.has_found_trades = True
            self.current_scan_interval = int(self.config.get("SCAN_INTERVAL_AFTER_TRADES_SEC", 7200))
            logger.info(f"🔄 Trades found! Switching to {self.current_scan_interval//60} minute intervals")
        elif not trades_found and self.has_found_trades:
            # Reset to aggressive scanning if no trades found
            self.has_found_trades = False
            self.current_scan_interval = int(self.config.get("SCAN_INTERVAL_SEC", 1800))
            logger.info(f"🔍 No trades found, switching to {self.current_scan_interval//60} minute intervals")

    # ---- exchanges ----
    def _init_exchanges(self):
        for exid in self.config.get("EXCHANGES", []):
            try:
                ex = getattr(ccxt, exid)({"enableRateLimit": True})
                ex.load_markets()
                self.ex_map[exid] = ex
                logger.info(f"✅ {exid} ready ({len(ex.markets)} markets)")
            except Exception as e:
                logger.warning(f"❌ {exid} {e}")

    def _live_px(self, exchange: str, symbol: str) -> Optional[float]:
        ex = self.ex_map.get(exchange)
        if not ex: return None
        candidates = [symbol]
        if symbol.endswith("/USDT") and "/USDT:USDT" not in symbol:
            candidates.append(symbol.replace("/USDT","/USDT:USDT"))
        candidates.append(symbol.replace("/", ""))  # BTCUSDT
        for s in candidates:
            try:
                t = ex.fetch_ticker(s)
                px = float(t.get("last") or t.get("close") or 0)
                if px > 0: return px
            except Exception:
                pass
        return None

    # ---- posting ----
    def post_embeds(self, embeds: List[Dict], force: bool = False):
        # Check cooldown unless forced
        current_time = time.time()
        if not force and (current_time - self.last_message_time) < self.message_cooldown_sec:
            logger.info(f"⏳ Message cooldown active, skipping Discord post (next allowed in {int(self.message_cooldown_sec - (current_time - self.last_message_time))}s)")
            return False

        hook = self.config.get("DISCORD_WEBHOOK","")
        if not hook:
            logger.warning("No DISCORD_WEBHOOK in config.json")
            print(json.dumps({"embeds":embeds}, indent=2))
            return True

        for i in range(0, len(embeds), 10):
            r = requests.post(hook, json={"embeds": embeds[i:i+10]}, timeout=15)
            logger.info(f"Discord status: {r.status_code}")
            time.sleep(0.25)

        # Update last message time
        self.last_message_time = current_time
        return True

    # ---- selection (trade vs watchlist) ----
    def split_trades_watchlist(self, signals):
        """
        - TRADES: top 3 only, confidence >= 9
        - WATCHLIST: top 4 only, 7 <= confidence < 9
        - De-dupe by (exchange, symbol)
        - If nothing qualifies, seed watchlist with strong S/R bounce or Wave-3 setups at 7+
        """
        if not signals:
            return [], []

        # de-dupe by (exchange, symbol)
        seen = set()
        uniq = []
        for s in signals:
            k = (s.get("exchange"), s.get("symbol"))
            if k in seen:
                continue
            seen.add(k)
            uniq.append(s)

        # rank by confidence → volume_ratio → |1h change|
        ranked = sorted(
            uniq,
            key=lambda x: (x.get("confidence", 0),
                           x.get("volume_ratio", 0),
                           abs(x.get("price_change_1h", 0))),
            reverse=True,
        )

        trades = [s for s in ranked if s.get("confidence", 0) >= 8][:3]
        watch  = [s for s in ranked if 7 <= s.get("confidence", 0) < 8][:4]

        if not trades and not watch:
            # allow strong S/R or Wave-3 to display at 7+ (watchlist only)
            seed = []
            for s in ranked:
                rs = " ".join(s.get("reasons", [])).lower()
                if (("bounce support" in rs) or ("resistance" in rs) or ("wave-3" in rs) or ("wave 3" in rs)) \
                   and s.get("confidence", 0) >= 7:
                    seed.append(s)
                    if len(seed) >= 4:
                        break
            watch = seed

        return trades, watch

    # ---- cards ----
    def create_trade_card(self, trade: Dict, live_entry: float = None) -> Dict:
        symbol, direction = trade["symbol"], trade["direction"]
        entry  = float(live_entry if live_entry else (trade.get("entry") or 0.0))
        exchange = trade["exchange"]
        confidence = int(trade.get("confidence",0))
        style = trade.get("style","")
        base  = trade.get("base", symbol.split("/")[0])

        emoji = "🟢" if direction=="LONG" else "🔴"
        color = 0x00FF00 if direction=="LONG" else 0xFF0000
        conf_emoji = "💎" if confidence>=9 else "⭐" if confidence>=7 else "🔥" if confidence>=5 else "⚪"
        link = tv_link(symbol, exchange)

        desc = [
                f"**{emoji} {base} {direction}** {conf_emoji}",
                f"**Entry:** ${entry:,.6f}",
                f"**Exchange:** {exchange.upper()}",
                f"**Confidence:** {confidence}/10",
            f"**Style:** {style.title() if style else 'Technical'}",
            f"**Chart:** [TradingView]({link})"
        ]
        if trade.get("reason"): desc.append(f"**Analysis:** {trade['reason']}")
        if trade.get("rsi"): desc.append(f"**RSI:** {trade['rsi']:.1f}")
        if trade.get("volume_ratio"): desc.append(f"**Volume:** {trade['volume_ratio']:.1f}x avg")
        if trade.get("price_change_1h"): desc.append(f"**1h Change:** {trade['price_change_1h']:+.2f}%")

        return {
            "title": f"🎯 Live Signal — {base}",
            "description": "\n".join(desc),
                "color": color,
            "footer": {"text": f"Bounty Seeker v4 • Real-time • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def create_watchlist_card(self, items: List[Dict]) -> Optional[Dict]:
        if not items: return None
        lines = []
        for s in items:
            link = tv_link(s["symbol"], s["exchange"])
            dot  = "🟢" if s["direction"]=="LONG" else "🔴"
            lines.append(f"{dot} **{s['base']}** {s['direction']} • **{s['confidence']}/10** • [Chart]({link})")
        return {"title":"👀 Watchlist (7/10)", "description":"\n".join(lines), "color":0x808080}

    # ---- run one scan ----
    def run_hourly_scan(self):
        logger.info("🚀 Starting real-time scan…")
        signals = self.scanner.scan_markets()
        trades, watch = self.split_trades_watchlist(signals)

        # update PnL and open high-confidence trades only (>=9)
        self.paper_trader.update_positions()
        trades_found = False
        if trades:
            opened = self.paper_trader.open_from_signals(trades)
            logger.info(f"📈 Opened {opened} new positions (>=9/10 only)")
            trades_found = True

        # Update scan interval based on whether trades were found
        self._update_scan_interval(trades_found)
        self._save_state()

        # Only send messages if there are significant findings
        should_send = trades or watch or trades_found
        if not should_send:
            logger.info("🔍 No significant signals found, skipping Discord post")
            return []

        embeds: List[Dict] = []
        embeds.append({
            "title":"📊 Market Scan Complete",
            "description":f"**Universe:** {len(self.scanner.watchlist)} pairs\n**Signals:** {len(signals)}\n**Trades (>=8/10):** {len(trades)}\n**Watchlist (7/10):** {len(watch)}",
            "color":0x3498DB
        })

        # trade cards
        for s in trades[:6]:  # show up to 6 cards
            live_px = self._live_px(s["exchange"], s["symbol"])
            embeds.append(self.create_trade_card(s, live_px))

        # watchlist card
        wc = self.create_watchlist_card(watch)
        if wc: embeds.append(wc)

        # account + positions
        acct = self.paper_trader.account_card()
        if acct: embeds.append(acct)
        pos = self.paper_trader.positions_card(get_px=self._live_px)
        if pos: embeds.append(pos)

        # Send with cooldown check
        sent = self.post_embeds(embeds)
        if sent:
            logger.info(f"📤 Posted {len(embeds)} embeds")
        else:
            logger.info("⏳ Message skipped due to cooldown")
        return embeds

    # ---- loop ----
    def run_continuous(self):
        logger.info("🔄 Continuous mode…")
        logger.info(f"⏰ Starting with {self.current_scan_interval//60} minute intervals")
        while True:
            try:
                self.run_hourly_scan()
                logger.info(f"⏰ Next scan in {self.current_scan_interval//60} minutes…")
                time.sleep(self.current_scan_interval)
            except KeyboardInterrupt:
                logger.info("🛑 Stopping"); break
            except Exception as e:
                logger.error(f"Loop error: {e}"); time.sleep(60)

if __name__ == "__main__":
    import sys
    bot = BountySeekerV4()
    if len(sys.argv)>1 and sys.argv[1]=="continuous":
        bot.run_continuous()
    else:
        bot.run_hourly_scan()
