#!/usr/bin/env python3
"""
Professional Market Scanner v2.6
2-hour scans + VWAP + TradingView links + paper trading + safe Discord posting
"""

import os
import sys
import time
import json
import sqlite3
import logging
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import yfinance as yf
from zoneinfo import ZoneInfo

# =================== CONFIGURATION ===================
# Database
DB_PATH = "scanner.db"

# Discord
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "https://discord.com/api/webhooks/1418463511490596894/IMmM_B4uw9BcHR8jGDngm66ariSOZVojs1yQuRKX8xJP0Nsg2DAPhSVOcY0Rl1Ru9YBQ")
WEBULL_REF_LINK = os.getenv("WEBULL_REF_LINK", "")

# Twitter
TWITTER_BEARER = os.getenv("TWITTER_BEARER_TOKEN", "")
TWITTER_HANDLES = ["@elonmusk", "@cz_binance", "@VitalikButerin"]

# Trading
SCAN_INTERVAL = 7200  # 2 hours in seconds
MAX_DESC = 4000
MAX_EMBEDS_PER_POST = 10

# Colors
RED = 0xff0000
GREEN = 0x00ff00
BLUE = 0x0000ff
YELLOW = 0xffff00
PURPLE = 0x800080
GOLD = 0xffd700
GRAY = 0x808080

# Timezone
TZ_UTC = timezone.utc
TZ_NY = ZoneInfo("America/New_York")

# =================== LOGGING ===================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =================== UTILITY FUNCTIONS ===================
def ny_now():
    """Get current time in NY timezone"""
    return datetime.now(TZ_NY)

def get_market_session():
    """Get current market session"""
    now = ny_now()
    hour = now.hour
    
    if 9 <= hour < 16:
        return ["RTH"]  # Regular Trading Hours
    elif 4 <= hour < 9:
        return ["PRE"]  # Pre-market
    elif 16 <= hour < 20:
        return ["AH"]   # After-hours
    else:
        return ["CLOSED"]

def linkify(text: str, url: str) -> str:
    """Create markdown link"""
    return f"[{text}]({url})"

def tv_link(symbol: str) -> str:
    """Create TradingView link"""
    return f"[{symbol}](https://www.tradingview.com/chart/?symbol={symbol})"

# =================== DATABASE FUNCTIONS ===================
def init_db():
    """Initialize database tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Paper account table
    c.execute("""
        CREATE TABLE IF NOT EXISTS paper_account (
            id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 10000.0,
            equity REAL DEFAULT 10000.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Paper positions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS paper_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            direction TEXT NOT NULL,
            entry REAL NOT NULL,
            qty REAL NOT NULL,
            stop REAL NOT NULL,
            tp1 REAL NOT NULL,
            status TEXT DEFAULT 'OPEN',
            opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_price REAL,
            closed_at TIMESTAMP
        )
    """)
    
    # Trades table
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            type TEXT DEFAULT 'STOCK',
            direction TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_price REAL NOT NULL,
            tp1 REAL NOT NULL,
            tp2 REAL,
            tp3 REAL,
            invalidation REAL,
            reason TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # News tracking table
    c.execute("""
        CREATE TABLE IF NOT EXISTS seen_news (
            id TEXT PRIMARY KEY,
            seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Initialize paper account if not exists
    c.execute("SELECT COUNT(*) FROM paper_account WHERE id=1")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO paper_account (id, balance, equity) VALUES (1, 10000.0, 10000.0)")
    
    conn.commit()
    conn.close()

def _seen_news_ids() -> set:
    """Get set of seen news IDs"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM seen_news")
    ids = {row[0] for row in c.fetchall()}
    conn.close()
    return ids

def _mark_news_ids(ids: List[str]):
    """Mark news IDs as seen"""
    if not ids:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for news_id in ids:
        c.execute("INSERT OR IGNORE INTO seen_news (id) VALUES (?)", (news_id,))
    conn.commit()
    conn.close()

# =================== NEWS FUNCTIONS ===================
def fetch_global_news(max_items: int = 8, max_age_minutes: int = 120) -> List[Dict]:
    """Fetch global market news"""
    try:
        # This is a placeholder - you would implement actual news fetching
        # For now, return some sample news
        sample_news = [
            {
                "id": f"news_{int(time.time())}",
                "title": "Market Update: Major indices showing mixed signals",
                "link": "https://example.com/news1",
                "source": "MarketWatch",
                "important": True
            },
            {
                "id": f"news_{int(time.time()) + 1}",
                "title": "Fed officials signal potential rate adjustments",
                "link": "https://example.com/news2", 
                "source": "Reuters",
                "important": False
            }
        ]
        return sample_news[:max_items]
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return []

# =================== SCANNING FUNCTIONS ===================
def scan_stocks_hourly() -> List[Dict]:
    """Scan for hourly stock options plays"""
    try:
        # This is a placeholder - you would implement actual scanning logic
        # For now, return some sample trades
        sample_trades = [
            {
                "symbol": "AAPL",
                "direction": "CALL",
                "entry": 150.0,
                "stop": 145.0,
                "tp1": 155.0,
                "tp2": 160.0,
                "tp3": 165.0,
                "invalidation": 140.0,
                "risk_reward": 2.0,
                "confidence": 8,
                "reason": "Breakout above resistance with volume",
                "chart_url": "https://www.tradingview.com/chart/?symbol=AAPL",
                "news": [{"title": "Apple earnings beat expectations", "link": "https://example.com"}]
            }
        ]
        return sample_trades
    except Exception as e:
        logger.error(f"Error scanning hourly stocks: {e}")
        return []

def scan_stocks_daily() -> List[Dict]:
    """Scan for daily stock options plays"""
    try:
        # This is a placeholder - you would implement actual scanning logic
        sample_trades = [
            {
                "symbol": "TSLA",
                "direction": "PUT",
                "entry": 200.0,
                "stop": 210.0,
                "tp1": 190.0,
                "tp2": 180.0,
                "tp3": 170.0,
                "invalidation": 220.0,
                "risk_reward": 1.5,
                "confidence": 7,
                "reason": "Rejection at key resistance level",
                "chart_url": "https://www.tradingview.com/chart/?symbol=TSLA"
            }
        ]
        return sample_trades
    except Exception as e:
        logger.error(f"Error scanning daily stocks: {e}")
        return []

def scan_futures() -> List[Dict]:
    """Scan for futures setups"""
    try:
        # This is a placeholder - you would implement actual scanning logic
        sample_trades = [
            {
                "symbol": "MNQ",
                "name": "Micro E-mini NASDAQ-100",
                "direction": "LONG",
                "entry": 15000.0,
                "stop": 14800.0,
                "tp1": 15200.0,
                "tp2": 15400.0,
                "tp3": 15600.0,
                "reason": "Bullish divergence on 4H chart",
                "chart_url": "https://www.tradingview.com/chart/?symbol=MNQ"
            }
        ]
        return sample_trades
    except Exception as e:
        logger.error(f"Error scanning futures: {e}")
        return []

def scan_forex() -> List[Dict]:
    """Scan for forex setups"""
    try:
        # This is a placeholder - you would implement actual scanning logic
        sample_trades = [
            {
                "symbol": "EURUSD",
                "name": "Euro/US Dollar",
                "direction": "LONG",
                "entry": 1.0850,
                "stop": 1.0800,
                "tp1": 1.0900,
                "tp2": 1.0950,
                "tp3": 1.1000,
                "reason": "Support bounce with RSI oversold",
                "chart_url": "https://www.tradingview.com/chart/?symbol=EURUSD"
            }
        ]
        return sample_trades
    except Exception as e:
        logger.error(f"Error scanning forex: {e}")
        return []

# ---------- paper trader ----------
class PaperTrader:
    def __init__(self, db_path:str, start_balance:float=10000.0, max_open:int=4, risk_pct:float=0.02):
        self.db_path=db_path; self.max_open=max_open; self.risk_pct=risk_pct

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _account(self):
        with self._conn() as conn:
            bal, eq = conn.execute("SELECT balance, equity FROM paper_account WHERE id=1").fetchone()
        return bal, eq

    def _open_count(self):
        with self._conn() as conn:
            (n,) = conn.execute("SELECT COUNT(*) FROM paper_positions WHERE status='OPEN'").fetchone()
        return n

    def _list_open(self):
        with self._conn() as conn:
            rows = conn.execute("SELECT symbol, direction, entry, qty, stop, tp1, last_price FROM paper_positions WHERE status='OPEN'").fetchall()
        return rows

    def update_and_open(self, candidates:List[Dict])->Optional[Dict]:
        # update open positions
        bal, eq = self._account()
        opens = self._list_open()
        pnl_total = 0.0
        summaries=[]
        with self._conn() as conn:
            for sym, direction, entry, qty, stop, tp1, last_price in opens:
                try:
                    cur = float(yf.Ticker(sym).history(period='1d', interval='5m')["Close"].iloc[-1])
                except Exception:
                    cur = last_price or entry
                long = direction in ("LONG","CALL")
                pnl = (cur-entry) * qty if long else (entry-cur) * qty
                pnl_total += pnl
                status = "OPEN"
                # auto-close if invalidated or TP1 hit
                if (long and (cur <= stop or cur >= tp1)) or ((not long) and (cur >= stop or cur <= tp1)):
                    bal += pnl
                    status = "CLOSED"
                conn.execute("UPDATE paper_positions SET last_price=?, status=? WHERE symbol=? AND status='OPEN'", (cur, status, sym))
                summaries.append(f"{sym} {direction} qty {int(qty)} | {cur:.2f} | P/L {pnl:+.2f}")
            eq = bal + pnl_total
            conn.execute("UPDATE paper_account SET balance=?, equity=?, updated_at=? WHERE id=1", (bal, eq, datetime.now(TZ_UTC)))

            # open new positions up to max 4
            room = self.max_open - self._open_count()
            for t in (candidates or [])[:max(0, room)]:
                sym = t["symbol"]
                direction = "LONG" if t["direction"] in ("LONG","CALL") else "SHORT"
                entry = float(t["entry"]); stop=float(t["stop"]); tp1=float(t["tp1"])
                risk_per = (entry-stop) if direction=="LONG" else (stop-entry)
                if risk_per<=0: continue
                # 2% of equity per idea
                alloc_risk = eq * self.risk_pct
                qty = max(1, int(alloc_risk / risk_per))
                conn.execute("""INSERT INTO paper_positions (symbol, direction, entry, qty, stop, tp1, status, opened_at, last_price)
                                VALUES (?,?,?,?,?,?, 'OPEN', ?, ?)""",
                             (sym, direction, entry, float(qty), stop, tp1, datetime.now(TZ_UTC), entry))
                summaries.append(f"OPEN {sym} {direction} qty {int(qty)} @ {entry:.2f}")

        # build embed
        bal, eq = self._account()
        desc = (f"**Paper Account**\nBalance: ${bal:,.2f} | Equity: ${eq:,.2f} | Max open: 4 | Risk/trade: 2%\n\n" +
                "\n".join(summaries[:30]) if summaries else "No changes.")
        return {"title":"📄 Paper Trading Update","color":GOLD,"description":desc[:MAX_DESC],
                "timestamp":datetime.now(TZ_UTC).isoformat()}

# ---------- embeds ----------
def create_news_embed(global_news:List[Dict], tweets:List[Dict])->List[Dict]:
    embeds=[]
    if global_news:
        seen=_seen_news_ids(); new=[]; lines=[]
        for it in global_news:
            mark="🟡 " if it.get("important") else "• "
            lines.append(f"{mark}{linkify(it['title'][:120], it['link'])} — *{it['source']}*")
            if it["id"] not in seen: new.append(it["id"])
        _mark_news_ids(new)
        embeds.append({"title":"🟡 Market Headlines (last ~2h)","color":YELLOW,
                       "description":"\n".join(lines)[:MAX_DESC],
                       "timestamp":datetime.now(TZ_UTC).isoformat(),
                       "footer":{"text":"Auto-updates every 2 hours"}})
    if WEBULL_REF_LINK:
        embeds.append({"title":"🟢 Get set up to trade","color":GREEN,
                       "description":f"Need an account? Try **Webull**: {WEBULL_REF_LINK}",
                       "timestamp":datetime.now(TZ_UTC).isoformat()})
    return embeds

def _options_embed_block(trades:List[Dict], title:str, color:int)->Dict:
    desc=f"**{title}**\n\n"
    for i,t in enumerate(trades,1):
        emoji="🟢" if t["direction"]=="CALL" else "🔴"
        conf="💎" if t["confidence"]>=9 else "⭐" if t["confidence"]>=7 else "⚪"
        desc += f"{i}. {emoji} **{tv_link(t['symbol'])}** — {t['direction']} {conf}\n"
        desc += f"   Entry ${t['entry']} | Stop ${t['stop']} | Targets ${t['tp1']} → ${t['tp2']} → {t['tp3']}\n"
        desc += f"   Invalidate ${t.get('invalidation', 'N/A')} | R:R {t.get('risk_reward', 'N/A')}\n"
        desc += f"   [Chart]({t['chart_url']})\n"
        if t.get('news'): desc += f"   📰 {linkify(t['news'][0]['title'][:60], t['news'][0]['link'])}\n"
        desc += f"   **Why**: {t['reason']}\n\n"
        if len(desc) > MAX_DESC-500:  # prevent overrun
            desc += "…"
            break
    return {"title":title,"color":color,"description":desc[:MAX_DESC],
            "timestamp":datetime.now(TZ_UTC).isoformat(),
            "footer":{"text":"Educational only. Not financial advice."}}

def create_futures_embed(trades:List[Dict])->Dict:
    desc="**Futures Setups**\n\n"
    for t in trades:
        emoji="🟢" if t["direction"]=="LONG" else "🔴"
        desc += f"{emoji} **{tv_link(t['symbol'])}** — {t['name']}\n"
        desc += f"   Entry {t['entry']} | Stop {t['stop']} | Targets {t['tp1']} → {t['tp2']} → {t['tp3']}\n"
        desc += f"   [Chart]({t['chart_url']})\n"
        desc += f"   **Why**: {t['reason']}\n\n"
        if len(desc) > MAX_DESC-300:
            desc += "…"; break
    return {"title":"🔵 FUTURES (incl. MNQ)","color":BLUE,
            "description":desc[:MAX_DESC],"timestamp":datetime.now(TZ_UTC).isoformat()}

def create_forex_embed(trades:List[Dict])->Dict:
    desc="**Major Forex Pairs**\n\n"
    for t in trades:
        emoji="🟢" if t["direction"]=="LONG" else "🔴"
        desc += f"{emoji} **{tv_link(t['symbol'])}** ({t['name']})\n"
        desc += f"   Entry {t['entry']} | Stop {t['stop']} | Targets {t['tp1']} → {t['tp2']} → {t['tp3']}\n"
        desc += f"   **Why**: {t['reason']}\n\n"
        if len(desc) > MAX_DESC-300: desc += "…"; break
    return {"title":"🟢 FOREX","color":GREEN,
            "description":desc[:MAX_DESC],"timestamp":datetime.now(TZ_UTC).isoformat()}

def create_disclaimer_embed()->Dict:
    return {"title":"⚠️ IMPORTANT DISCLAIMER","color":GRAY,
            "description":"Educational tool only. Risk 1–2% per trade, use stops, take profits at TP1. Options involve high risk.",
            "timestamp":datetime.now(TZ_UTC).isoformat()}

# ---------- storage ----------
def store_trades(trades:List[Dict]):
    conn=sqlite3.connect(DB_PATH); c=conn.cursor()
    for t in trades:
        c.execute("SELECT id FROM trades WHERE symbol=? AND status='PENDING'", (t['symbol'],))
        if not c.fetchone():
            c.execute("""INSERT INTO trades (symbol,type,direction,entry_price,stop_price,tp1,tp2,tp3,invalidation,reason,status,created_at,updated_at)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?, ?, ?)""",
                      (t['symbol'], t.get('type','STOCK'), t['direction'], t['entry'], t['stop'], t['tp1'], t.get('tp2'), t.get('tp3'),
                       t.get('invalidation'), t['reason'], 'PENDING', datetime.now(TZ_UTC), datetime.now(TZ_UTC)))
    conn.commit(); conn.close()

# ---------- safe Discord poster ----------
def _embed_len(e:Dict)->int:
    total = len(e.get("title","")) + len(e.get("description","") or "")
    ft = e.get("footer",{}).get("text","")
    return total + len(ft)

def _split_if_needed(e:Dict)->List[Dict]:
    if _embed_len(e) <= 5800: return [e]
    desc = e.get("description","")
    lines = desc.split("\n")
    parts=[]; buf=""
    for line in lines:
        if len(buf) + len(line) + 1 > MAX_DESC:
            part = dict(e); part["description"]=buf; part["title"]=e["title"] + " (cont.)"
            parts.append(part); buf=""
        buf += (line + "\n")
    if buf:
        part = dict(e); part["description"]=buf; part["title"]=e["title"] + " (cont.)"
        parts.append(part)
    return parts

def post_embeds(embeds:List[Dict]):
    if not DISCORD_WEBHOOK:
        logger.warning("No DISCORD_WEBHOOK set. Printing embeds locally.")
        for e in embeds: logger.info(f"\n== {e['title']} ==\n{(e.get('description') or '')[:500]}")
        return
    # pre-split any too-large embed
    safe=[]
    for e in embeds:
        safe += _split_if_needed(e)
    # send in batches of up to 10
    for i in range(0, len(safe), MAX_EMBEDS_PER_POST):
        batch = safe[i:i+MAX_EMBEDS_PER_POST]
        r = requests.post(DISCORD_WEBHOOK, json={"embeds": batch}, timeout=15)
        if r.status_code != 204:
            logger.error(f"Discord error: {r.status_code} {r.text}")
            # try splitting one-by-one if a batch somehow still fails
            for e in batch:
                rr = requests.post(DISCORD_WEBHOOK, json={"embeds":[e]}, timeout=15)
                if rr.status_code != 204:
                    logger.error(f"Discord single-post error: {rr.status_code} {rr.text}")
        time.sleep(0.8)

# ---------- main scan ----------
TRADER: Optional[PaperTrader] = None

def run_complete_scan():
    logger.info(f"\n{'='*64}\n[{ny_now().strftime('%Y-%m-%d %I:%M %p ET')}] Session: {', '.join(get_market_session())}\n{'='*64}")
    if not TWITTER_BEARER and TWITTER_HANDLES:
        logger.warning("TWITTER_BEARER_TOKEN not set; skipping tweets")
    embeds=[]

    # News first
    news = fetch_global_news(max_items=8, max_age_minutes=120)
    embeds += create_news_embed(news, tweets=[])

    # Signals
    stocks_hourly = scan_stocks_hourly()
    stocks_daily  = scan_stocks_daily()
    futs          = scan_futures()
    fx            = scan_forex()

    if stocks_hourly: embeds.append(_options_embed_block(stocks_hourly, "🔴 STOCK OPTIONS - Hourly Plays (Day/Scalp)", RED)); store_trades(stocks_hourly)
    if stocks_daily:  embeds.append(_options_embed_block(stocks_daily,  "🟣 STOCK OPTIONS - Daily Swings (Weekly+ Holds)", PURPLE)); store_trades(stocks_daily)
    if futs:          embeds.append(create_futures_embed(futs)); store_trades(futs)
    if fx:            embeds.append(create_forex_embed(fx));    store_trades(fx)

    # Paper trader update + entries (max 4 open)
    if TRADER is not None:
        candidates = (stocks_hourly or []) + (stocks_daily or [])
        paper_embed = TRADER.update_and_open(candidates)
        if paper_embed: embeds.append(paper_embed)

    embeds.append(create_disclaimer_embed())
    post_embeds(embeds)
    logger.info(f"✅ Posted {len(embeds)} embed group(s). Next scan in {SCAN_INTERVAL} seconds.")

def main():
    global TRADER
    init_db()
    TRADER = PaperTrader(DB_PATH, start_balance=10000.0, max_open=4, risk_pct=0.02)
    logger.info("\n" + "="*60)
    logger.info("PROFESSIONAL MARKET SCANNER v2.6")
    logger.info("="*60)
    logger.info("2-hour scans + VWAP + TradingView links + paper trading + safe Discord posting")
    logger.info("="*60 + "\n")
    while True:
        try:
            run_complete_scan()
            time.sleep(SCAN_INTERVAL)
        except KeyboardInterrupt:
            logger.info("\nStopped by user."); break
        except Exception as ex:
            logger.error(f"Scanner error: {ex}"); time.sleep(60)

if __name__=="__main__":
    main()