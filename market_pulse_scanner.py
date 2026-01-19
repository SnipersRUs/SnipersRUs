#!/usr/bin/env python3
"""
Enhanced Market Scanner v4.0 with Paper Trading System
- Real-time price fetching with improved accuracy
- Precise entry/exit execution with live market data
- Enhanced position sizing and risk management
- Optimized performance with caching and batch operations
"""
import os, time, json, sqlite3, logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple
import pytz
import yfinance as yf
import numpy as np
from dotenv import load_dotenv
import requests
from functools import lru_cache
import threading
from collections import defaultdict

# --- logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("paper_v4")

# --- env/config ---
load_dotenv()
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "").strip()
SCAN_INTERVAL   = int(os.getenv("SCAN_INTERVAL", "300"))  # 5 minutes default
MAX_DESC        = 4096
TZ_NY           = pytz.timezone("America/New_York")
TZ_UTC          = timezone.utc

# --- paper trading constants ---
STARTING_BALANCE       = 1000.0
MAX_CONCURRENT_TRADES  = 3
POSITION_SIZE          = 300.0
MAX_RISK_PER_TRADE     = 0.02   # 2% of account

# --- Real-time price cache ---
class PriceCache:
    def __init__(self, ttl_seconds=5):
        self.cache = {}
        self.ttl = ttl_seconds
        self.lock = threading.Lock()
    
    def get(self, symbol: str) -> Optional[float]:
        with self.lock:
            if symbol in self.cache:
                price, timestamp = self.cache[symbol]
                if time.time() - timestamp < self.ttl:
                    return price
            return None
    
    def set(self, symbol: str, price: float):
        with self.lock:
            self.cache[symbol] = (price, time.time())

price_cache = PriceCache(ttl_seconds=5)

# --- market hours guard (US equities) ---
def is_us_equity_session_open(now: Optional[datetime]=None) -> bool:
    now = now or datetime.now(TZ_NY)
    wd = now.weekday()
    if wd >= 5:  # Sat/Sun
        return False
    # 09:30–16:00 ET
    open_dt  = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close_dt = now.replace(hour=16, minute=0,  second=0, microsecond=0)
    return open_dt <= now <= close_dt

# --- Enhanced real-time price fetching ---
def get_realtime_price(symbol: str, use_cache: bool = True) -> Optional[float]:
    """Get most accurate real-time price with fallback options"""
    # Check cache first
    if use_cache:
        cached = price_cache.get(symbol)
        if cached is not None:
            return cached
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Try multiple price sources in order of preference
        price_sources = [
            lambda: ticker.info.get("currentPrice"),
            lambda: ticker.info.get("regularMarketPrice"),
            lambda: ticker.info.get("previousClose"),
            lambda: ticker.history(period="1d", interval="1m")["Close"].iloc[-1] if not ticker.history(period="1d", interval="1m").empty else None
        ]
        
        for source in price_sources:
            try:
                price = source()
                if price and price > 0:
                    price = float(price)
                    price_cache.set(symbol, price)
                    return price
            except:
                continue
                
        # If all else fails, try fast_info
        if hasattr(ticker, 'fast_info'):
            price = ticker.fast_info.get('lastPrice')
            if price and price > 0:
                price = float(price)
                price_cache.set(symbol, price)
                return price
                
    except Exception as ex:
        logger.error(f"Price fetch error for {symbol}: {ex}")
    
    return None

# --- minimal Discord webhook client (embeds only) ---
class DiscordWebhook:
    def __init__(self, url: str):
        self.url = url
        self.s = requests.Session()
        self.s.headers.update({"Content-Type": "application/json", "User-Agent":"PaperScannerV4/1.0"})
    
    def send_embeds(self, embeds: List[Dict]) -> bool:
        if not self.url:
            logger.warning("No DISCORD_WEBHOOK configured.")
            return False
        # split into batches of 10 (discord limit)
        ok = True
        for i in range(0, len(embeds), 10):
            batch = embeds[i:i+10]
            # trim overlong descriptions
            for e in batch:
                if "description" in e and len(e["description"]) > MAX_DESC:
                    e["description"] = e["description"][:MAX_DESC-3] + "..."
                e.setdefault("timestamp", datetime.now(TZ_UTC).isoformat())
            try:
                r = self.s.post(self.url, json={"embeds": batch}, timeout=15)
                if r.status_code != 204:
                    logger.error(f"Discord error {r.status_code}: {r.text[:200]}")
                    ok = False
                time.sleep(0.7)  # gentle pacing
            except Exception as ex:
                logger.error(f"Discord send error: {ex}")
                ok = False
        return ok

class TradeStatus(Enum):
    PENDING   = "PENDING"
    ACTIVE    = "ACTIVE"
    CLOSED    = "CLOSED"
    CANCELLED = "CANCELLED"
    STOPPED   = "STOPPED"
    TARGET1   = "TARGET1"
    TARGET2   = "TARGET2"
    TARGET3   = "TARGET3"

@dataclass
class Signal:
    id: str
    symbol: str
    direction: str  # CALL or PUT
    entry_price: float
    stop_price: float
    tp1: float
    tp2: float
    tp3: float
    confidence: float
    reason: str
    signal_time: datetime
    expiry_time: datetime
    chart_url: str = ""

@dataclass
class Trade:
    id: str
    signal_id: str
    symbol: str
    direction: str
    entry_price: float
    actual_entry: float
    stop_price: float
    tp1: float
    tp2: float
    tp3: float
    position_size: float
    shares: int
    entry_time: datetime
    exit_time: Optional[datetime]=None
    exit_price: Optional[float]=None
    status: str = TradeStatus.PENDING.value
    pnl: float = 0.0
    pnl_percent: float = 0.0
    max_profit: float = 0.0
    max_loss: float = 0.0
    exit_reason: str = ""

class PaperTradingAccount:
    def __init__(self, db_path: str = "paper_trading.db"):
        self.db_path = db_path
        self.init_database()
        self.load_account_state()

    # ---------- DB ----------
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS account_state (
            id INTEGER PRIMARY KEY,
            balance REAL, starting_balance REAL,
            total_trades INTEGER, winning_trades INTEGER, losing_trades INTEGER,
            last_updated TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS signals (
            id TEXT PRIMARY KEY, symbol TEXT, direction TEXT,
            entry_price REAL, stop_price REAL, tp1 REAL, tp2 REAL, tp3 REAL,
            confidence REAL, reason TEXT, signal_time TIMESTAMP, expiry_time TIMESTAMP,
            chart_url TEXT, triggered INTEGER DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY, signal_id TEXT, symbol TEXT, direction TEXT,
            entry_price REAL, actual_entry REAL, stop_price REAL,
            tp1 REAL, tp2 REAL, tp3 REAL, position_size REAL, shares INTEGER,
            entry_time TIMESTAMP, exit_time TIMESTAMP, exit_price REAL,
            status TEXT, pnl REAL, pnl_percent REAL, max_profit REAL, max_loss REAL,
            exit_reason TEXT, FOREIGN KEY(signal_id) REFERENCES signals(id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT, trade_id TEXT, timestamp TIMESTAMP,
            event TEXT, price REAL, notes TEXT, FOREIGN KEY(trade_id) REFERENCES trades(id))""")
        conn.commit()
        conn.close()

    def load_account_state(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT balance, starting_balance, total_trades, winning_trades, losing_trades FROM account_state ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if row:
            self.balance, self.starting_balance, self.total_trades, self.winning_trades, self.losing_trades = row
        else:
            self.balance = self.starting_balance = STARTING_BALANCE
            self.total_trades = self.winning_trades = self.losing_trades = 0
            self.save_account_state()
        conn.close()

    def save_account_state(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""INSERT INTO account_state (balance, starting_balance, total_trades, winning_trades, losing_trades, last_updated)
                     VALUES (?,?,?,?,?,?)""",
                  (self.balance, self.starting_balance, self.total_trades, self.winning_trades, self.losing_trades, datetime.now(TZ_UTC)))
        conn.commit()
        conn.close()

    # ---------- Signals ----------
    def add_signal(self, s: Signal) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("""INSERT INTO signals (id,symbol,direction,entry_price,stop_price,tp1,tp2,tp3,confidence,reason,signal_time,expiry_time,chart_url)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (s.id,s.symbol,s.direction,s.entry_price,s.stop_price,s.tp1,s.tp2,s.tp3,s.confidence,s.reason,s.signal_time,s.expiry_time,s.chart_url))
            conn.commit()
            logger.info(f"📝 Added signal: {s.symbol} {s.direction} @ {s.entry_price:.4f}")
            return True
        except Exception as ex:
            logger.error(f"Add signal failed: {ex}")
            return False
        finally:
            conn.close()

    # ---------- Trading rules ----------
    def get_active_trades_count(self)->int:
        conn=sqlite3.connect(self.db_path)
        c=conn.cursor()
        c.execute("SELECT COUNT(*) FROM trades WHERE status=?", (TradeStatus.ACTIVE.value,))
        n=c.fetchone()[0]
        conn.close()
        return n

    def can_enter_trade(self)->bool:
        return (self.get_active_trades_count() < MAX_CONCURRENT_TRADES) and (self.balance >= POSITION_SIZE)

    def enter_trade(self, sig: Signal, current_price: float) -> Optional[Trade]:
        # guard: only stocks during RTH
        if not is_us_equity_session_open():
            logger.info("⏸ Market closed — deferring stock entry.")
            return None
        if not self.can_enter_trade():
            logger.warning(f"Cannot enter trade. Active={self.get_active_trades_count()} Balance=${self.balance:.2f}")
            return None

        # Get fresh real-time price for entry
        fresh_price = get_realtime_price(sig.symbol, use_cache=False)
        if fresh_price:
            current_price = fresh_price

        risk_per_share = abs(current_price - sig.stop_price)
        max_risk_amt   = self.balance * MAX_RISK_PER_TRADE
        shares_risk    = int(max_risk_amt / risk_per_share) if risk_per_share > 0 else 0
        shares_cap     = int(POSITION_SIZE / current_price)
        shares         = min(shares_risk, shares_cap)
        
        if shares <= 0:
            logger.warning(f"Position too small for {sig.symbol}")
            return None

        pos_val = shares * current_price
        trade = Trade(
            id=f"T{int(time.time())}_{sig.symbol}",
            signal_id=sig.id,
            symbol=sig.symbol,
            direction=sig.direction,
            entry_price=sig.entry_price,
            actual_entry=current_price,
            stop_price=sig.stop_price,
            tp1=sig.tp1,
            tp2=sig.tp2,
            tp3=sig.tp3,
            position_size=pos_val,
            shares=shares,
            entry_time=datetime.now(TZ_UTC),
            status=TradeStatus.ACTIVE.value
        )

        conn=sqlite3.connect(self.db_path)
        c=conn.cursor()
        c.execute("""INSERT INTO trades (id,signal_id,symbol,direction,entry_price,actual_entry,stop_price,tp1,tp2,tp3,position_size,shares,entry_time,status)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (trade.id, trade.signal_id, trade.symbol, trade.direction, trade.entry_price, trade.actual_entry,
                   trade.stop_price, trade.tp1, trade.tp2, trade.tp3, trade.position_size, trade.shares, trade.entry_time, trade.status))
        c.execute("UPDATE signals SET triggered=1 WHERE id=?", (sig.id,))
        c.execute("""INSERT INTO journal(trade_id,timestamp,event,price,notes)
                    VALUES (?,?,?,?,?)""", (trade.id, datetime.now(TZ_UTC), "TRADE_ENTERED", current_price,
                                            f"Entered {shares} shares at ${current_price:.4f}"))
        conn.commit()
        conn.close()

        self.balance -= pos_val
        self.save_account_state()
        logger.info(f"✅ ENTERED: {trade.symbol} {trade.direction} {shares} @ ${current_price:.4f}")
        self.send_trade_notification(trade, "ENTRY")
        return trade

    def update_trade(self, trade_id: str, current_price: float) -> Optional[str]:
        conn=sqlite3.connect(self.db_path)
        c=conn.cursor()
        c.execute("SELECT * FROM trades WHERE id=? AND status=?", (trade_id, TradeStatus.ACTIVE.value))
        row=c.fetchone()
        if not row:
            conn.close()
            return None

        symbol=row[2]
        direction=row[3]
        actual_entry=row[5]
        stop=row[6]
        tp1, tp2, tp3 = row[7], row[8], row[9]
        shares=row[11]
        pos_val=row[10]

        # Get fresh real-time price for exit check
        fresh_price = get_realtime_price(symbol, use_cache=False)
        if fresh_price:
            current_price = fresh_price

        exit_reason=None
        exit_status=None
        
        if (direction=="CALL" and current_price<=stop) or (direction=="PUT" and current_price>=stop):
            exit_reason="STOP_LOSS"
            exit_status=TradeStatus.STOPPED
        elif direction=="CALL":
            if   current_price>=tp3:
                exit_reason="TARGET_3"
                exit_status=TradeStatus.TARGET3
            elif current_price>=tp2:
                exit_reason="TARGET_2"
                exit_status=TradeStatus.TARGET2
            elif current_price>=tp1:
                exit_reason="TARGET_1"
                exit_status=TradeStatus.TARGET1
        else:  # PUT
            if   current_price<=tp3:
                exit_reason="TARGET_3"
                exit_status=TradeStatus.TARGET3
            elif current_price<=tp2:
                exit_reason="TARGET_2"
                exit_status=TradeStatus.TARGET2
            elif current_price<=tp1:
                exit_reason="TARGET_1"
                exit_status=TradeStatus.TARGET1

        pnl = (current_price - actual_entry)*shares if direction=="CALL" else (actual_entry - current_price)*shares
        pnl_pct = (pnl/pos_val)*100

        c.execute("SELECT max_profit,max_loss FROM trades WHERE id=?", (trade_id,))
        mp, ml = c.fetchone()
        mp = max(mp or 0, pnl)
        ml = min(ml or 0, pnl)

        if exit_reason:
            self.balance += (pos_val + pnl)
            self.total_trades += 1
            if pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            self.save_account_state()
            c.execute("""UPDATE trades SET exit_time=?, exit_price=?, status=?, pnl=?, pnl_percent=?, max_profit=?, max_loss=?, exit_reason=? WHERE id=?""",
                      (datetime.now(TZ_UTC), current_price, exit_status.value, pnl, pnl_pct, mp, ml, exit_reason, trade_id))
            c.execute("""INSERT INTO journal(trade_id,timestamp,event,price,notes)
                         VALUES (?,?,?,?,?)""", (trade_id, datetime.now(TZ_UTC), "TRADE_CLOSED", current_price,
                         f"Closed at ${current_price:.4f} - P&L ${pnl:.2f} ({pnl_pct:.1f}%) - {exit_reason}"))
            logger.info(f"💰 CLOSED {symbol}: P&L ${pnl:.2f} ({pnl_pct:.1f}%) - {exit_reason}")
        else:
            c.execute("UPDATE trades SET max_profit=?, max_loss=? WHERE id=?", (mp, ml, trade_id))

        conn.commit()
        conn.close()
        return exit_reason

    def check_pending_signals(self):
        """Check untriggered signals with real-time prices"""
        conn=sqlite3.connect(self.db_path)
        c=conn.cursor()
        c.execute("SELECT * FROM signals WHERE triggered=0 AND expiry_time>?", (datetime.now(TZ_UTC),))
        rows=c.fetchall()
        conn.close()
        
        for r in rows:
            sig=Signal(id=r[0], symbol=r[1], direction=r[2], entry_price=r[3], stop_price=r[4],
                       tp1=r[5], tp2=r[6], tp3=r[7], confidence=r[8], reason=r[9],
                       signal_time=r[10], expiry_time=r[11], chart_url=r[12])
            try:
                cur = get_realtime_price(sig.symbol)
                if not cur:
                    continue
                
                hit=False
                # Use tighter entry tolerance for better accuracy
                if sig.direction=="CALL" and cur <= sig.entry_price*1.0005:  # 0.05% tolerance
                    hit=True
                if sig.direction=="PUT"  and cur >= sig.entry_price*0.9995:
                    hit=True
                    
                if hit and self.can_enter_trade():
                    self.enter_trade(sig, cur)
            except Exception as ex:
                logger.error(f"Signal check error {sig.symbol}: {ex}")

    def update_active_trades(self):
        """Update all active trades with real-time prices"""
        conn=sqlite3.connect(self.db_path)
        c=conn.cursor()
        c.execute("SELECT id,symbol FROM trades WHERE status=?", (TradeStatus.ACTIVE.value,))
        active=c.fetchall()
        conn.close()
        
        # Batch fetch prices for efficiency
        symbols = [sym for _, sym in active]
        prices = {}
        
        for sym in symbols:
            price = get_realtime_price(sym)
            if price:
                prices[sym] = price
        
        for tid, sym in active:
            if sym in prices:
                reason=self.update_trade(tid, prices[sym])
                if reason:
                    self.send_trade_notification(None, "EXIT", trade_id=tid)

    # --- account stats & notifications ---
    def get_active_trades_value(self)->float:
        """Calculate current value of active positions with real-time prices"""
        conn=sqlite3.connect(self.db_path)
        c=conn.cursor()
        c.execute("SELECT symbol, shares, actual_entry FROM trades WHERE status=?", (TradeStatus.ACTIVE.value,))
        positions = c.fetchall()
        conn.close()
        
        total_value = 0.0
        for symbol, shares, entry_price in positions:
            current = get_realtime_price(symbol)
            if current:
                total_value += shares * current
            else:
                # Fallback to entry price if can't get current
                total_value += shares * entry_price
        
        return total_value

    def get_account_stats(self)->Dict:
        conn=sqlite3.connect(self.db_path)
        c=conn.cursor()
        win_rate = (self.winning_trades/self.total_trades*100) if self.total_trades>0 else 0.0
        c.execute("SELECT AVG(pnl),AVG(pnl_percent) FROM trades WHERE status!=?", (TradeStatus.PENDING.value,))
        avg_pnl, avg_pnl_pct = c.fetchone()
        avg_pnl=avg_pnl or 0.0
        avg_pnl_pct=avg_pnl_pct or 0.0
        c.execute("SELECT MAX(pnl), MIN(pnl) FROM trades WHERE status!=?", (TradeStatus.PENDING.value,))
        best, worst = c.fetchone()
        best=best or 0.0
        worst=worst or 0.0
        active_val = self.get_active_trades_value()
        conn.close()
        total_ret=((self.balance-STARTING_BALANCE)/STARTING_BALANCE*100)
        return {"balance":self.balance,"starting_balance":STARTING_BALANCE,"total_equity":self.balance+active_val,
                "total_return":total_ret,"total_trades":self.total_trades,"winning_trades":self.winning_trades,
                "losing_trades":self.losing_trades,"win_rate":win_rate,"avg_pnl":avg_pnl,"avg_pnl_percent":avg_pnl_pct,
                "best_trade":best,"worst_trade":worst,"active_trades":self.get_active_trades_count(),
                "active_positions_value":active_val}

    def send_trade_notification(self, trade: Optional[Trade], event: str, trade_id: Optional[str]=None):
        if not DISCORD_WEBHOOK:
            return
        wh=DiscordWebhook(DISCORD_WEBHOOK)
        if event=="ENTRY" and trade:
            embed={"title":f"📈 Trade Entered: {trade.symbol}",
                   "color":0x00FF00 if trade.direction=="CALL" else 0xFF0000,
                   "description":(f"**Direction**: {trade.direction}\n"
                                  f"**Entry**: ${trade.actual_entry:.4f}\n"
                                  f"**Shares**: {trade.shares}\n"
                                  f"**Stop**: ${trade.stop_price:.4f}\n"
                                  f"**Targets**: ${trade.tp1:.4f} → ${trade.tp2:.4f} → ${trade.tp3:.4f}\n"),
                   "timestamp":datetime.now(TZ_UTC).isoformat()}
            wh.send_embeds([embed])
            return
        if event=="EXIT" and trade_id:
            conn=sqlite3.connect(self.db_path)
            c=conn.cursor()
            c.execute("SELECT symbol,pnl,pnl_percent,exit_reason FROM trades WHERE id=?", (trade_id,))
            row=c.fetchone()
            conn.close()
            if not row:
                return
            sym,pnl,pct,reason=row
            embed={"title":f"💰 Trade Closed: {sym}",
                   "color":0x00FF00 if (pnl or 0)>0 else 0xFF0000,
                   "description":f"**P&L**: ${pnl:.2f} ({pct:.1f}%)\n**Reason**: {reason}\n**Balance**: ${self.balance:.2f}"}
            wh.send_embeds([embed])

    def generate_daily_report(self)->str:
        s=self.get_account_stats()
        return (f"📊 **Daily Trading Report**\n"
                f"========================\n\n"
                f"**Starting**: ${s['starting_balance']:.2f}\n"
                f"**Balance**: ${s['balance']:.2f}\n"
                f"**Equity**: ${s['total_equity']:.2f}\n"
                f"**Return**: {s['total_return']:.2f}%\n\n"
                f"**Trades**: {s['total_trades']} | **Win rate**: {s['win_rate']:.1f}%\n"
                f"**Avg P&L**: ${s['avg_pnl']:.2f} ({s['avg_pnl_percent']:.1f}%)\n"
                f"**Best/Worst**: ${s['best_trade']:.2f} / ${s['worst_trade']:.2f}\n"
                f"**Active**: {s['active_trades']}/{MAX_CONCURRENT_TRADES} (${s['active_positions_value']:.2f})\n")

# --- Enhanced momentum scanner with real-time data ---
def scan_and_track(symbols: List[str], account: PaperTradingAccount) -> List[Dict]:
    """Enhanced scanner with real-time price accuracy"""
    out = []
    
    # Batch download for efficiency
    try:
        tickers = yf.Tickers(' '.join(symbols))
        data = {}
        
        for sym in symbols:
            try:
                ticker = tickers.tickers[sym]
                df = ticker.history(period="5d", interval="1h")
                if len(df) >= 2:
                    data[sym] = df
            except:
                pass
    except:
        # Fallback to individual fetching
        data = {}
        for sym in symbols:
            try:
                df = yf.Ticker(sym).history(period="5d", interval="1h")
                if len(df) >= 2:
                    data[sym] = df
            except:
                pass
    
    for sym, df in data.items():
        try:
            # Get real-time current price
            cur = get_realtime_price(sym)
            if not cur:
                cur = float(df["Close"].iloc[-1])
            
            prev = float(df["Close"].iloc[-2])
            
            # Calculate momentum indicators
            returns = df["Close"].pct_change()
            volatility = returns.std()
            momentum = (cur - prev) / prev
            
            # Enhanced signal generation
            signal_generated = False
            
            if momentum > 0.002:  # 0.2% positive momentum
                # Bullish signal
                # Dynamic stop based on volatility
                stop_distance = max(cur * 0.02, cur * volatility * 2)
                
                sig = Signal(
                    id=f"S{int(time.time()*1000)}_{sym}",
                    symbol=sym,
                    direction="CALL",
                    entry_price=cur * 0.9995,  # Tighter entry
                    stop_price=cur - stop_distance,
                    tp1=cur * 1.01,
                    tp2=cur * 1.02,
                    tp3=cur * 1.03,
                    confidence=min(9.0, 7.5 + momentum * 100),  # Dynamic confidence
                    reason=f"Bullish momentum {momentum:.2%}, volatility {volatility:.2%}",
                    signal_time=datetime.now(TZ_UTC),
                    expiry_time=datetime.now(TZ_UTC) + timedelta(hours=4),
                    chart_url=f"https://www.tradingview.com/chart/?symbol={sym}&interval=60"
                )
                account.add_signal(sig)
                signal_generated = True
                
            elif momentum < -0.002:  # 0.2% negative momentum
                # Bearish signal
                stop_distance = max(cur * 0.02, cur * volatility * 2)
                
                sig = Signal(
                    id=f"S{int(time.time()*1000)}_{sym}",
                    symbol=sym,
                    direction="PUT",
                    entry_price=cur * 1.0005,  # Tighter entry
                    stop_price=cur + stop_distance,
                    tp1=cur * 0.99,
                    tp2=cur * 0.98,
                    tp3=cur * 0.97,
                    confidence=min(9.0, 7.5 + abs(momentum) * 100),
                    reason=f"Bearish momentum {momentum:.2%}, volatility {volatility:.2%}",
                    signal_time=datetime.now(TZ_UTC),
                    expiry_time=datetime.now(TZ_UTC) + timedelta(hours=4),
                    chart_url=f"https://www.tradingview.com/chart/?symbol={sym}&interval=60"
                )
                account.add_signal(sig)
                signal_generated = True
            
            if signal_generated:
                out.append({
                    "symbol": sym,
                    "direction": sig.direction,
                    "current_price": cur,
                    "entry": sig.entry_price,
                    "stop": sig.stop_price,
                    "tp1": sig.tp1,
                    "tp2": sig.tp2,
                    "tp3": sig.tp3,
                    "chart_url": sig.chart_url,
                    "confidence": sig.confidence,
                    "reason": sig.reason
                })
                
        except Exception as ex:
            logger.error(f"Scan error {sym}: {ex}")
    
    return out

def enhanced_main_loop():
    """Main trading loop with optimized performance and real-time accuracy"""
    logger.info("🚀 Starting Enhanced Market Scanner v4.0 with Paper Trading")
    acct = PaperTradingAccount()
    
    # Send startup notification
    if DISCORD_WEBHOOK:
        DiscordWebhook(DISCORD_WEBHOOK).send_embeds([{
            "title": "✅ Scanner Started (Paper Trading v4.0)",
            "description": f"Balance: ${acct.balance:.2f} | Max open: {MAX_CONCURRENT_TRADES} | Pos size: ${POSITION_SIZE:.0f}",
            "color": 0x00FF00,
            "fields": [
                {"name": "Market Status", "value": "🟢 Open" if is_us_equity_session_open() else "🔴 Closed", "inline": True},
                {"name": "Starting Balance", "value": f"${STARTING_BALANCE:.2f}", "inline": True},
                {"name": "Risk Per Trade", "value": f"{MAX_RISK_PER_TRADE*100:.1f}%", "inline": True}
            ]
        }])
    
    last_report = None
    last_scan = 0
    iter_no = 0
    
    # Define watchlist with more symbols for better opportunities
    watchlist = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'META', 'AMZN', 'GOOGL', 
                 'JPM', 'V', 'WMT', 'PG', 'JNJ', 'UNH', 'HD', 'DIS',
                 'MA', 'BAC', 'XOM', 'CVX', 'ABBV']
    
    while True:
        try:
            iter_no += 1
            start_time = time.time()
            
            logger.info(f"━━━ Iteration {iter_no} ━━━")
            
            # Check market status
            market_open = is_us_equity_session_open()
            logger.info(f"Market: {'🟢 OPEN' if market_open else '🔴 CLOSED'}")
            
            # Always update active trades with real-time prices
            logger.info("📊 Updating active trades...")
            acct.update_active_trades()
            
            # Check pending signals (only enters during market hours)
            if market_open:
                logger.info("🎯 Checking pending signals...")
                acct.check_pending_signals()
            
            # Scan for new signals based on interval
            current_time = time.time()
            if current_time - last_scan >= SCAN_INTERVAL:
                logger.info(f"🔍 Scanning {len(watchlist)} symbols...")
                new_signals = scan_and_track(watchlist, acct)
                logger.info(f"📝 Found {len(new_signals)} new signals")
                
                # Send summary of new signals
                if new_signals and DISCORD_WEBHOOK:
                    embeds = []
                    for sig in new_signals[:5]:  # Limit to 5 to avoid spam
                        embeds.append({
                            "title": f"🎯 New Signal: {sig['symbol']}",
                            "color": 0x00FF00 if sig['direction'] == "CALL" else 0xFF0000,
                            "fields": [
                                {"name": "Direction", "value": sig['direction'], "inline": True},
                                {"name": "Current", "value": f"${sig['current_price']:.2f}", "inline": True},
                                {"name": "Entry", "value": f"${sig['entry']:.2f}", "inline": True},
                                {"name": "Stop", "value": f"${sig['stop']:.2f}", "inline": True},
                                {"name": "Targets", "value": f"${sig['tp1']:.2f} → ${sig['tp2']:.2f} → ${sig['tp3']:.2f}", "inline": False},
                                {"name": "Confidence", "value": f"{sig['confidence']:.1f}/10", "inline": True},
                                {"name": "Reason", "value": sig['reason'][:100], "inline": False}
                            ],
                            "footer": {"text": f"Chart: {sig['chart_url']}"}
                        })
                    if embeds:
                        DiscordWebhook(DISCORD_WEBHOOK).send_embeds(embeds)
                
                last_scan = current_time
            
            # End-of-day report (at 4:00 PM ET)
            now = datetime.now(TZ_NY)
            if now.hour == 16 and now.minute < 5 and last_report != now.date():
                rep = acct.generate_daily_report()
                logger.info("\n" + rep)
                
                if DISCORD_WEBHOOK:
                    # Get detailed stats for the report
                    stats = acct.get_account_stats()
                    DiscordWebhook(DISCORD_WEBHOOK).send_embeds([{
                        "title": "📊 Daily Trading Report",
                        "description": rep,
                        "color": 0x3498DB,
                        "fields": [
                            {"name": "📈 Performance", "value": f"{stats['total_return']:.2f}%", "inline": True},
                            {"name": "🎯 Win Rate", "value": f"{stats['win_rate']:.1f}%", "inline": True},
                            {"name": "💼 Active Trades", "value": f"{stats['active_trades']}/{MAX_CONCURRENT_TRADES}", "inline": True}
                        ],
                        "footer": {"text": f"Generated at {now.strftime('%Y-%m-%d %H:%M:%S ET')}"}
                    }])
                last_report = now.date()
            
            # Performance metrics
            loop_time = time.time() - start_time
            logger.info(f"⏱ Loop completed in {loop_time:.2f}s")
            
            # Dynamic sleep based on market status
            if market_open:
                sleep_time = max(30, 60 - loop_time)  # More frequent during market hours
            else:
                sleep_time = max(60, 300 - loop_time)  # Less frequent after hours
            
            logger.info(f"💤 Sleeping for {sleep_time:.0f}s...")
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            logger.info("🛑 Graceful shutdown initiated...")
            
            # Final report
            final_stats = acct.get_account_stats()
            logger.info(f"\n📊 Final Stats:")
            logger.info(f"  Balance: ${final_stats['balance']:.2f}")
            logger.info(f"  Total Return: {final_stats['total_return']:.2f}%")
            logger.info(f"  Win Rate: {final_stats['win_rate']:.1f}%")
            logger.info(f"  Total Trades: {final_stats['total_trades']}")
            
            if DISCORD_WEBHOOK:
                DiscordWebhook(DISCORD_WEBHOOK).send_embeds([{
                    "title": "🛑 Scanner Stopped",
                    "description": f"**Final Balance**: ${final_stats['balance']:.2f}\n"
                                   f"**Total Return**: {final_stats['total_return']:.2f}%\n"
                                   f"**Win Rate**: {final_stats['win_rate']:.1f}%\n"
                                   f"**Total Trades**: {final_stats['total_trades']}",
                    "color": 0xFF0000
                }])
            break
            
        except Exception as ex:
            logger.error(f"❌ Loop error: {ex}")
            time.sleep(60)

# --- Quick test function ---
def test_realtime_prices():
    """Test real-time price fetching accuracy"""
    test_symbols = ['AAPL', 'MSFT', 'TSLA']
    logger.info("Testing real-time price fetching...")
    
    for sym in test_symbols:
        price = get_realtime_price(sym)
        cached_price = get_realtime_price(sym, use_cache=True)
        logger.info(f"{sym}: Fresh=${price:.2f}, Cached=${cached_price:.2f}")
    
    logger.info("✅ Price testing complete")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_realtime_prices()
    else:
        enhanced_main_loop()
