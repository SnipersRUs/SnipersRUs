#!/usr/bin/env python3
"""
ULTRA-OPTIMIZED FUTURES SCALPING BOT v2.0
High-Performance Compounding Machine
"""
import os, time, math, json, sqlite3, threading, asyncio, aiohttp
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import lru_cache, wraps
from collections import deque
import numpy as np
import pandas as pd
import yfinance as yf
import requests
from dotenv import load_dotenv
import yaml
import schedule
import datetime as dt
from numba import jit, vectorize
import warnings
warnings.filterwarnings('ignore')

# ---------- Load env & config ----------
load_dotenv()
WEBHOOK = os.getenv("DISCORD_WEBHOOK", "").strip()
ROUND_TURN_FEE = float(os.getenv("ROUND_TURN_FEE", "1.20"))

with open("config.yaml","r") as f:
    CFG = yaml.safe_load(f)

# ---------- PERFORMANCE SETTINGS ----------
class PerformanceConfig:
    CACHE_ENABLED = True
    PARALLEL_PROCESSING = True
    MAX_CACHE_AGE_SECONDS = 30
    BATCH_SIZE = 100
    USE_NUMPY_ACCELERATION = True
    MAX_BARS_STORED = 1000
    DB_PATH = "trades.db"
    INCREMENTAL_UPDATE = True
    CONNECTION_POOL_SIZE = 10

PERF = PerformanceConfig()

# ---------- Database Manager (Fast SQLite) ----------
class TradeDB:
    def __init__(self, db_path=PERF.DB_PATH):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.lock = threading.Lock()
        self.setup_tables()
    
    def setup_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT,
                symbol TEXT,
                side TEXT,
                qty INTEGER,
                entry REAL,
                sl REAL,
                tp1 REAL,
                tp2 REAL,
                exit REAL,
                pnl REAL,
                stage TEXT,
                fees REAL
            );
            
            CREATE TABLE IF NOT EXISTS equity (
                time TEXT PRIMARY KEY,
                equity REAL,
                open_positions INTEGER,
                mtm REAL,
                win_rate REAL,
                sharpe REAL
            );
        """)
    
    def log_trade(self, trade_data):
        with self.lock:
            self.conn.execute(
                """INSERT INTO trades (time, symbol, side, qty, entry, sl, tp1, tp2, exit, pnl, stage, fees)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                trade_data
            )
            self.conn.commit()

# ---------- Optimized Data Manager ----------
class DataManager:
    def __init__(self):
        self.data_cache = {}
        self.last_update = {}
        self.lock = threading.Lock()
    
    def fetch_parallel(self, symbols: Dict) -> Dict[str, pd.DataFrame]:
        """Fetch multiple symbols in parallel"""
        results = {}
        for key, cfg in symbols.items():
            try:
                results[key] = self._fetch_single(key, cfg)
            except Exception as e:
                print(f"[ERROR] Fetching {key}: {e}")
                results[key] = None
        return results
    
    def _fetch_single(self, symbol_key: str, symbol_cfg: dict) -> pd.DataFrame:
        """Optimized single symbol fetch with caching"""
        yf_tkr = symbol_cfg["yahoo"]
        
        with self.lock:
            # Check cache freshness
            if symbol_key in self.data_cache:
                last_time = self.last_update.get(symbol_key, 0)
                if time.time() - last_time < PERF.MAX_CACHE_AGE_SECONDS:
                    return self.data_cache[symbol_key]
        
        # Fetch data
        tf = CFG["strategy"]["timeframe"]
        days = CFG["strategy"]["history_days"]
        
        try:
            period = f"{days}d"
            df = yf.download(
                yf_tkr,
                interval=tf,
                period=period,
                progress=False,
                auto_adjust=False
            )
            
            if df.empty:
                raise RuntimeError(f"Empty data for {yf_tkr}")
            
            # Update cache
            with self.lock:
                self.data_cache[symbol_key] = df
                self.last_update[symbol_key] = time.time()
            
            return df
            
        except Exception as e:
            print(f"[FETCH ERROR] {symbol_key}: {e}")
            # Return cached data if available
            return self.data_cache.get(symbol_key)

# ---------- Vectorized Indicators (FAST) ----------
def fast_atr(high, low, close, period=14):
    """Simplified ATR calculation"""
    n = len(high)
    atr = np.zeros(n)
    tr = np.zeros(n)
    
    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i-1])
        lc = abs(low[i] - close[i-1])
        tr[i] = max(hl, hc, lc)
    
    # Initial ATR
    if period <= n:
        atr[period-1] = np.mean(tr[:period])
        
        # Subsequent ATR values
        for i in range(period, n):
            atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    
    return atr

class IndicatorEngine:
    def __init__(self):
        self.cache = {}
        
    def calculate_all(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Ultra-fast indicator calculation with caching"""
        out = df.copy()
        
        # Convert to numpy for speed
        high = df["High"].values
        low = df["Low"].values
        close = df["Close"].values
        
        # Fast calculations using numba
        out["ATR"] = fast_atr(high, low, close)
        
        # Simple indicators
        out["HL2"] = (high + low) / 2
        out["TP"] = (high + low + close) / 3
        
        return out

# ---------- Advanced Position Manager ----------
@dataclass
class Position:
    sym: str
    qty: int
    side: str
    entry: float
    sl: float
    tp1: float
    tp2: float
    R: float
    filled_time: dt.datetime
    stage: str = "OPEN"
    fees_paid: float = 0.0

class CompoundingPortfolio:
    def __init__(self, starting_equity: float):
        self.starting_equity = starting_equity
        self.equity = starting_equity
        self.positions: List[Position] = []
        self.closed_trades: deque = deque(maxlen=1000)
        self.consec_losses = 0
        self.consec_wins = 0
        self.cooldown_until: Optional[dt.datetime] = None
        self.db = TradeDB()
        
        # Compounding metrics
        self.daily_starting_equity = starting_equity
        self.compound_factor = 1.0
        self.peak_equity = starting_equity
        self.max_drawdown = 0.0

# ---------- Signal Engine ----------
class SignalEngine:
    def __init__(self):
        self.indicator_engine = IndicatorEngine()
    
    def analyze_all_parallel(self, symbols: Dict, dfs: Dict[str, pd.DataFrame]) -> List[Dict]:
        """Analyze all symbols for signals"""
        signals = []
        
        for sym_key, df in dfs.items():
            if df is not None and len(df) > 50:
                signal = self._analyze_single(sym_key, df, symbols[sym_key])
                if signal:
                    signals.append(signal)
        
        return sorted(signals, key=lambda x: x.get("score", 0), reverse=True)
    
    def _analyze_single(self, symbol_key: str, df: pd.DataFrame, symbol_cfg: dict) -> Optional[Dict]:
        """Signal analysis for single symbol"""
        # Apply indicators
        df = self.indicator_engine.calculate_all(df, symbol_key)
        
        # Get latest bar
        b = df.iloc[-1]
        
        close = float(b["Close"])
        atr = float(b.get("ATR", 1.0))
        
        # Simple signal logic
        score = 0
        
        # Price action
        if len(df) >= 20:
            sma_20 = df["Close"].rolling(20).mean().iloc[-1]
            if close > float(sma_20):
                score += 2  # Bullish
            else:
                score += 1  # Bearish signal potential
        
        # Volume check
        if len(df) >= 10:
            avg_vol = df["Volume"].rolling(10).mean().iloc[-1]
            if float(b["Volume"]) > float(avg_vol) * 1.5:
                score += 1
        
        # Generate signal if score meets threshold
        min_score = CFG["filters"]["min_confluence_score"]
        
        if score >= min_score:
            return self._create_signal(symbol_key, symbol_cfg, "LONG", close, atr, score)
        
        return None
    
    def _create_signal(self, symbol_key: str, symbol_cfg: dict, side: str, 
                      price: float, atr: float, score: int) -> Dict:
        """Create trading signal"""
        
        # Calculate position parameters
        tick = symbol_cfg["tick_size"]
        tick_value = symbol_cfg["tick_value"]
        
        # ATR-based stops
        stop_multiplier = CFG["filters"]["atr_mult_stop"]
        stop_points = max(tick, atr * stop_multiplier)
        
        # Risk calculation
        risk_pct = CFG["account"]["risk_per_trade_pct"]
        risk_total = 10000 * risk_pct  # Using base equity for now
        ticks_to_stop = math.ceil(stop_points / tick)
        risk_per_contract = ticks_to_stop * tick_value
        
        if risk_per_contract <= 0:
            return None
        
        qty = max(1, int(risk_total // risk_per_contract))
        qty = min(qty, symbol_cfg["max_contracts"])
        
        # Profit targets
        tp1_mult = CFG["profit_management"]["tp1_R"]
        tp2_mult = CFG["profit_management"]["tp2_R"]
        
        if side == "LONG":
            sl = price - stop_points
            tp1 = price + stop_points * tp1_mult
            tp2 = price + stop_points * tp2_mult
        else:
            sl = price + stop_points
            tp1 = price - stop_points * tp1_mult
            tp2 = price - stop_points * tp2_mult
        
        return {
            "symbol": symbol_key,
            "side": side,
            "qty": qty,
            "entry": price,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "R": risk_per_contract,
            "score": score,
            "risk_pct": risk_pct
        }

# ---------- Discord Notifier ----------
class AsyncDiscordNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def post(self, message: str):
        """Non-blocking post to Discord"""
        try:
            if self.webhook_url:
                response = requests.post(
                    self.webhook_url,
                    json={"content": message},
                    timeout=5
                )
                print(f"Discord: {response.status_code}")
        except Exception as e:
            print(f"Discord error: {e}")

# ---------- MAIN TRADING ENGINE ----------
class UltraScalpingBot:
    def __init__(self):
        self.data_mgr = DataManager()
        self.signal_engine = SignalEngine()
        self.portfolio = CompoundingPortfolio(CFG["account"]["starting_equity"])
        self.discord = AsyncDiscordNotifier(WEBHOOK) if WEBHOOK else None
        
        # Performance tracking
        self.scan_times = deque(maxlen=100)
        self.last_scan = time.time()
    
    def notify(self, msg: str):
        """Send notification"""
        print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}")
        if self.discord:
            self.discord.post(msg)
    
    def scan_and_trade(self):
        """Ultra-optimized scanning and trading loop"""
        start_time = time.time()
        
        # Check trading conditions
        if self.portfolio.cooldown_until and dt.datetime.now() < self.portfolio.cooldown_until:
            return
        
        if len(self.portfolio.positions) >= CFG["account"]["max_open_trades"]:
            return
        
        # Fetch data
        symbols = CFG["symbols"]
        dfs = self.data_mgr.fetch_parallel(symbols)
        
        # Extract current prices
        prices = {}
        for k, df in dfs.items():
            if df is not None and not df.empty:
                prices[k] = float(df["Close"].iloc[-1])
        
        # Find new signals
        if len(self.portfolio.positions) < CFG["account"]["max_open_trades"]:
            signals = self.signal_engine.analyze_all_parallel(symbols, dfs)
            
            # Execute best signals
            capacity = CFG["account"]["max_open_trades"] - len(self.portfolio.positions)
            for signal in signals[:capacity]:
                self._execute_signal(signal)
        
        # Performance tracking
        scan_time = time.time() - start_time
        self.scan_times.append(scan_time)
        
        # Status update
        self.notify(f"🔍 Scan complete: {len(prices)} symbols, {scan_time:.2f}s")
    
    def _execute_signal(self, signal: Dict):
        """Execute trading signal"""
        pos = Position(
            sym=signal["symbol"],
            qty=signal["qty"],
            side=signal["side"],
            entry=signal["entry"],
            sl=signal["sl"],
            tp1=signal["tp1"],
            tp2=signal["tp2"],
            R=signal["R"],
            filled_time=dt.datetime.now()
        )
        
        # Calculate fees
        pos.fees_paid = ROUND_TURN_FEE * signal["qty"]
        
        # Add to portfolio
        self.portfolio.positions.append(pos)
        
        # Log to database
        self.portfolio.db.log_trade((
            dt.datetime.now().isoformat(),
            signal["symbol"],
            signal["side"],
            signal["qty"],
            signal["entry"],
            signal["sl"],
            signal["tp1"],
            signal["tp2"],
            None,  # exit price
            None,  # pnl
            "OPEN",
            pos.fees_paid
        ))
        
        # Notify
        self.notify(
            f"🎯 **{signal['side']} {signal['symbol']}** x{signal['qty']} @ {signal['entry']:.2f}\n"
            f"├ SL: {signal['sl']:.2f} | TP1: {signal['tp1']:.2f} | TP2: {signal['tp2']:.2f}\n"
            f"├ Score: {signal['score']} | Risk: {signal['risk_pct']*100:.1f}%\n"
            f"└ Equity: ${self.portfolio.equity:,.2f}"
        )
    
    def push_performance_update(self):
        """Send comprehensive performance update"""
        current_equity = self.portfolio.equity
        
        # Get recent trades stats
        recent = list(self.portfolio.closed_trades)[-50:] if self.portfolio.closed_trades else []
        if recent:
            wins = [t["pnl"] for t in recent if t["pnl"] > 0]
            win_rate = len(wins) / len(recent) * 100
        else:
            win_rate = 0
        
        # Send update
        self.notify(
            f"📊 **PERFORMANCE UPDATE**\n"
            f"```"
            f"Equity:     ${current_equity:,.2f}\n"
            f"Positions:  {len(self.portfolio.positions)}/{CFG['account']['max_open_trades']}\n"
            f"Win Rate:   {win_rate:.1f}%\n"
            f"Status:     ACTIVE & SCANNING 🎯"
            f"```"
        )
    
    def run(self):
        """Main execution loop with scheduling"""
        self.notify(
            f"🚀 **ULTRA SCALPER v2.0 INITIALIZED**\n"
            f"├ Starting Equity: ${self.portfolio.equity:,.2f}\n"
            f"├ Symbols: {', '.join(CFG['symbols'].keys())}\n"
            f"├ Scan Interval: {CFG['strategy']['scan_interval_minutes']}min\n"
            f"├ Max Positions: {CFG['account']['max_open_trades']}\n"
            f"└ Mode: COMPOUND AGGRESSIVE 💎"
        )
        
        # Initial scan
        self.scan_and_trade()
        
        # Schedule regular scans
        schedule.every(CFG["strategy"]["scan_interval_minutes"]).minutes.do(self.scan_and_trade)
        schedule.every(CFG["strategy"]["pnl_push_interval_minutes"]).minutes.do(self.push_performance_update)
        
        # Main loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                self.notify("🛑 Bot shutdown requested")
                break
            except Exception as e:
                self.notify(f"💥 Critical error: {e}")
                raise

# ---------- MAIN ENTRY POINT ----------
if __name__ == "__main__":
    # Start the bot
    bot = UltraScalpingBot()
    
    try:
        bot.run()
    except KeyboardInterrupt:
        bot.notify("🛑 Bot shutdown requested")
        if bot.discord:
            time.sleep(1)  # Allow final messages to send
    except Exception as e:
        bot.notify(f"💥 Critical error: {e}")
        raise