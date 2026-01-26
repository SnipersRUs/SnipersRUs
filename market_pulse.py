import os, json, time, requests, pandas as pd, numpy as np
from dotenv import load_dotenv
from datetime import date
from utils import WHITE, BLUE, ORANGE, RED, fmt_price, now_et_iso, bullet, sleep_minutes
from providers import get_1h_vs_1d_vwap, news_blurbs
from scoring import decide
from state import load_state, save_state, day_key, week_key

load_dotenv()
WEBHOOK = os.getenv("WEBHOOK_URL","").strip()
SCAN_HOURS = int(os.getenv("SCAN_HOURS","4"))

MAX_STOCKS_DAY  = int(os.getenv("MAX_STOCKS_DAY","3"))
MAX_STOCKS_WEEK = int(os.getenv("MAX_STOCKS_WEEK","1"))
MAX_FUTURES_DAY = int(os.getenv("MAX_FUTURES_DAY","1"))
MAX_FOREX_DAY   = int(os.getenv("MAX_FOREX_DAY","1"))

def read_list(path):
    try:
        with open(path) as f:
            return [l.strip() for l in f if l.strip() and not l.startswith("#")]
    except:
        return []

UNIV_STOCKS  = read_list("universe/stocks.txt")
UNIV_FUTURES = read_list("universe/futures.txt")
UNIV_FOREX   = read_list("universe/forex.txt")

def pick_best(tickers, cap):
    ideas = []
    for t in tickers:
        v = get_1h_vs_1d_vwap(t)
        d = decide(v)
        if d: ideas.append((t, d))
    ideas.sort(key=lambda x: x[1]["score"], reverse=True)
    return ideas[:cap], ideas  # top, all (for watchlist)

def embed(title, color, lines):
    desc = "\n".join(lines) if lines else "_No setups right now._"
    return {
        "title": title,
        "description": desc,
        "color": color,
        "timestamp": now_et_iso()
    }

def idea_lines(tag, ideas, prior):
    out = []
    for t, d in ideas:
        key = f"{tag}:{t}:{d['direction']}"
        was = prior.get(key)
        still_valid = (was is not None and abs(was.get("entry", d["entry"]) - d["entry"]) / max(d["entry"],1e-9) <= 0.02)
        status = "**STILL VALID** — " if still_valid else ""
        s = d["score"]
        why = d["reason"]
        entry = fmt_price(d["entry"]); stop=fmt_price(d["stop"]); t1=fmt_price(d["t1"]); t2=fmt_price(d["t2"])
        tv = f"https://www.tradingview.com/chart/?symbol={t.replace('=','%3D')}"
        out.append(
            f"**{t}** • **{d['direction']}** • {s}/10\n"
            f"{status}Entry: `{entry}` | Stop: `{stop}` | T1/T2: `{t1}` / `{t2}`\n"
            f"_Why:_ {why}\n"
            f"[Chart]({tv})"
        )
    return out

def watchlist_lines(all_ideas, take_range=(7,8)):
    low, high = take_range
    lines=[]
    for t,d in all_ideas:
        s=d["score"]
        if low<=s<=high:
            dot = bullet(d["direction"]=="LONG")
            tv = f"https://www.tradingview.com/chart/?symbol={t.replace('=','%3D')}"
            lines.append(f"{dot} **{t}** • {s}/10 • [Chart]({tv})")
    return lines[:10] if lines else []

def post_discord(embeds):
    if not WEBHOOK:
        print("[WARN] No WEBHOOK_URL provided.")
        return
    try:
        requests.post(WEBHOOK, json={"embeds": embeds}, timeout=15)
    except Exception as e:
        print("discord error:", e)

def run_once():
    state = load_state()
    dkey = day_key()
    wkey = week_key()

    # STOCKS — intraday top 3
    top_stocks, all_stocks = pick_best(UNIV_STOCKS, MAX_STOCKS_DAY)
    # WEEKLY stock — pick best of stocks using same engine (swing proxy)
    weekly_stock = top_stocks[:MAX_STOCKS_WEEK] if top_stocks else []

    # FUTURES — best 1
    top_futs, all_futs = pick_best(UNIV_FUTURES, MAX_FUTURES_DAY)
    # FOREX — best 1
    top_fx, all_fx = pick_best(UNIV_FOREX, MAX_FOREX_DAY)

    # Save for STILL VALID tracking
    today_bucket = {}
    for t,d in top_stocks: today_bucket[f"STOCK:{t}:{d['direction']}"]=d
    for t,d in weekly_stock: today_bucket[f"WEEK:{t}:{d['direction']}"]=d
    for t,d in top_futs: today_bucket[f"FUT:{t}:{d['direction']}"]=d
    for t,d in top_fx: today_bucket[f"FX:{t}:{d['direction']}"]=d

    state.setdefault(dkey, {})
    state[dkey].update(today_bucket)
    # keep last 14 days
    keys = sorted(state.keys())[-14:]
    state = {k: state[k] for k in keys}
    save_state(state)

    prior = state.get(dkey, {})

    # Build embeds
    embeds=[]

    # Stocks (white)
    embeds.append(embed("Stock Picks (Top 3, Intraday)", WHITE, idea_lines("STOCK", top_stocks, prior)))

    # Weekly stock (white)
    embeds.append(embed("Weekly Stock Swing (Top 1)", WHITE, idea_lines("WEEK", weekly_stock, prior)))

    # Futures (blue)
    embeds.append(embed("Futures Pick (Today)", BLUE, idea_lines("FUT", top_futs, prior)))

    # Forex (orange)
    embeds.append(embed("Forex Pick (Today)", ORANGE, idea_lines("FX", top_fx, prior)))

    # Watchlist (scores 7–8) — combine all markets, keep dots
    wl = watchlist_lines(all_stocks + all_futs + all_fx, (7,8))
    embeds.append(embed("Watchlist (7–8/10)", RED, wl))

    # News (red)
    news = [f"• [{title}]({link})" for title,link in news_blurbs()]
    embeds.append(embed("News & Headlines", RED, news if news else ["No fresh headlines found."]))

    post_discord(embeds)
    print("[INFO] scan complete; posted", sum(1 for e in embeds if e.get("description")),"embeds.")

def main_loop():
    print("[INFO] Market Pulse v2 online.")
    while True:
        try:
            run_once()
        except Exception as e:
            print("[ERROR] scan error:", e)
        print(f"[INFO] sleeping {SCAN_HOURS*60} min…")
        sleep_minutes(SCAN_HOURS*60)

if __name__=="__main__":
    import sys
    if len(sys.argv)>1 and sys.argv[1]=="once":
        run_once()
    else:
        main_loop()
