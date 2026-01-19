#!/usr/bin/env python3
import time, importlib.util, sys, os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.logger import info, err
from src.discord_notifier import send_embed
from src.mm_detector_v2 import MMDetectorWithMonitoring
from src.data_fetcher import (
    get_spot_data, get_futures_data, get_orderbook,
    get_coinbase_spot, get_recent_liqs
)
from src.volatility_profile import typical_high_vol_hours, next24_windows
from src.flush_detector import start_flush_monitor
from src.metrics import (
    cvd_from_trades, orderbook_imbalance, vwap_and_bands,
    premium_vs_coinbase, oi_delta, liq_clusters_summary
)
from src.scalp_signal import scalp_setup, _score_prob, attach_probability
from src.top_gainer import pick_coin_of_day
from src.trade_logger import append_open, append_close, update_stats, pnl_pct

# Load config & tz
spec=importlib.util.spec_from_file_location("cfg","config/config.py")
cfg=importlib.util.module_from_spec(spec); spec.loader.exec_module(cfg)
ET=ZoneInfo(cfg.TIMEZONE_NAME); UTC=timezone.utc

detector=MMDetectorWithMonitoring()
VOL_HOURS={}
ACTIVE_SCALPS={}   # symbol -> {"side","entry","tp1","tp2","stop","last_status"}
ACTIVE_OPENS={}    # symbol -> open trade data for logging

def _refresh_vol_hours():
    for s in cfg.TRADING_PAIRS:
        try: VOL_HOURS[s]=typical_high_vol_hours(cfg.BINANCE_SPOT_REST, s, days=30, top=3)
        except Exception as e: err("vol hours:", s, e)

def next_snapshot_ts():
    now=datetime.now(ET)
    nxt= now.replace(minute=0,second=0,microsecond=0) + timedelta(hours=1)
    return nxt.astimezone(UTC).timestamp()

def _funding_bias(funding):
    if funding > 0.01:  return "BEAR tilt (crowded longs)"
    if funding > 0.0:   return "slight BEAR tilt"
    if funding < -0.01: return "BULL tilt (crowded shorts)"
    if funding < 0.0:   return "slight BULL tilt"
    return "neutral"

# ---------- TradingView + visuals helpers ----------
def _tv_links(symbol: str):
    # Build MEXC & Binance perp links for TradingView; MEXC first as requested
    base = symbol.replace("USDT","")
    mexc = f"https://www.tradingview.com/chart/?symbol=MEXC:{base}USDT"
    bperp = f"https://www.tradingview.com/chart/?symbol=BINANCE:{base}USDT.P"
    return mexc, bperp

def _bias_dots(m15, h1, h4):
    dot = {"LONG":"🟢","SHORT":"🟣","NEUTRAL":"⚪️"}
    return f"M15 {dot.get(m15,'⚪️')} | H1 {dot.get(h1,'⚪️')} | H4 {dot.get(h4,'⚪️')}"

def _card_color(m15, h1, h4):
    votes_long = sum(x=="LONG" for x in (m15,h1,h4))
    votes_short = sum(x=="SHORT" for x in (m15,h1,h4))
    if votes_long >= 2: return 0x2ECC71  # green
    if votes_short >= 2: return 0x9B59B6  # purple (bearish as requested)
    return 0x95A5A6  # neutral gray

def _top_liquidity(bids, asks, last_px, pct=0.7, n=2):
    # Aggregate within +/- pct% of last price and return top N per side
    if not bids or not asks or not last_px:
        return [], [], "neutral"
    lo = last_px*(1-pct/100.0); hi = last_px*(1+pct/100.0)

    def pick(rows, reverse):
        rows = [r for r in rows if lo <= float(r[0]) <= hi]
        rows.sort(key=lambda x: float(x[1]), reverse=True)
        return [[float(p), float(q)] for p,q in rows[:n]]

    tb = pick(bids, True)
    ta = pick(asks, True)

    sum_b = sum(q for _,q in tb); sum_a = sum(q for _,q in ta)
    magnet = "UP" if sum_a > sum_b*1.2 else "DOWN" if sum_b > sum_a*1.2 else "neutral"
    return tb, ta, magnet

def _format_signal_card(sym, st, fut, spot, bids, asks, windows, coinbase_px, liqs):
    fr  = float(fut.get("funding_rate",0.0))*100.0
    nft_ms = int(fut.get("next_funding_time",0))
    nft_txt = datetime.fromtimestamp(nft_ms/1000, UTC).astimezone(ET).strftime("%Y-%m-%d %H:%M ET") if nft_ms>0 else "—"
    funding_line = f"{fr:+.4f}% (next @ {nft_txt}) — {_funding_bias(fr/100)}"

    signal = st.h1_bias
    if fr > 1.0 and signal=="LONG":   signal="NEUTRAL"
    if fr < -1.0 and signal=="SHORT": signal="NEUTRAL"
    if st.m15_bias==st.h1_bias==st.h4_bias and st.h1_bias!="NEUTRAL":
        signal = st.h1_bias

    cvd  = cvd_from_trades(spot["trades"])
    imb, bid_w, ask_w = orderbook_imbalance(bids, asks, pct_window=0.5)
    vwap, v_up, v_dn  = vwap_and_bands(spot["prices"], spot["volumes"])
    last_px = spot["prices"][-1]
    v_loc = "below VWAP (value)" if last_px<=vwap else "above VWAP (momentum)"
    prem = premium_vs_coinbase(last_px, coinbase_px)
    oi_d = oi_delta(sym, fut["open_interest"][-1] if fut.get("open_interest") else 0)
    liq  = liq_clusters_summary(liqs, last_px)

    # liquidity walls (Binance)
    top_b, top_a, magnet = _top_liquidity(bids, asks, last_px, pct=0.7, n=2)
    liq_line = "none"
    if top_b or top_a:
        Lb = "  |  ".join([f"↓ {p:.0f}@{q:.0f}" for p,q in top_b]) if top_b else ""
        La = "  |  ".join([f"↑ {p:.0f}@{q:.0f}" for p,q in top_a]) if top_a else ""
        liq_line = ("  ".join([Lb,La]).strip("  |")) + f"  → magnet: {magnet.lower()}"

    # scalp idea (still present if actionable)
    idea = scalp_setup(signal, last_px, st.support, st.resistance, vwap, v_up, v_dn)
    prob = _score_prob(st.m15_bias==st.h1_bias==st.h4_bias and st.h1_bias!='NEUTRAL',
                       cvd, imb, _funding_bias(fr/100), oi_d, v_loc)
    idea  = attach_probability(idea, prob)
    if idea.get("available"):
        ACTIVE_SCALPS[sym] = {k:idea[k] for k in ("side","entry","tp1","tp2","stop","prob","rr")}
        ACTIVE_SCALPS[sym]["last_status"]="posted"

    # visuals
    badges = _bias_dots(st.m15_bias, st.h1_bias, st.h4_bias)
    bias_line = f"{badges}"
    mexc, bperp = _tv_links(sym)

    scalp_line = ("**⚡ Scalp watch**: "
                  f"{idea['side']}  |  Entry **{idea['entry']:.2f}**  |  TP1 **{idea['tp1']:.2f}**  |  TP2 **{idea['tp2']:.2f}**  |  "
                  f"Stop **{idea['stop']:.2f}**  |  Prob **{idea['prob']}%**  (R:R {idea['rr']})"
                 ) if idea.get("available") else "**⚡ Scalp watch**: none (need better alignment)"

    desc=(f"**Bias**: {bias_line}\n"
          f"**Funding**: {funding_line}\n"
          f"**Flow**: CVD {cvd:+.0f}  |  OB Imb {imb:+.2f} (bid {bid_w:.0f} / ask {ask_w:.0f})  |  OI Δ {oi_d:+.2f}  |  Premium {prem:+.2f}%\n"
          f"**VWAP**: {vwap:.2f} (↑ {v_up:.2f} / ↓ {v_dn:.2f})  |  **Liquidity (±0.7%)**: {liq_line}\n"
          f"**Levels**: S {st.support:.0f}  •  P {st.pivot:.0f}  •  R {st.resistance:.0f}\n"
          f"**Chart**: [MEXC]({mexc}) • [Binance]({bperp})\n\n"
          f"{scalp_line}")

    color=_card_color(st.m15_bias, st.h1_bias, st.h4_bias)
    return {"title":f"{sym} — Hourly MM Snapshot (Explained + Scalp)",
            "description":desc, "color":color,
            "footer":{"text":f"{datetime.now(ET):%Y-%m-%d %H:%M} ET / {datetime.now(UTC):%H:%M} UTC"}}

def _coin_of_day_card(spot_base):
    pick = pick_coin_of_day(spot_base)
    if not pick: return None
    sym, last_px = pick["symbol"], pick["last"]
    # quick pullback plan around last 60m VWAP bands
    spot = get_spot_data(spot_base, sym, 120)
    vwap, v_up, v_dn = vwap_and_bands(spot["prices"], spot["volumes"], window=60)
    entry = max(v_dn, min(spot["prices"][-60:])) * 1.003
    stop  = entry * 0.992
    tp1   = vwap
    tp2   = max(v_up, max(spot["prices"][-60:])) * 0.998
    desc=(f"**Coin of the Day**: {sym}\n"
          f"**Why**: strong 1h momentum and high $ volume (not fully cooked yet)\n"
          f"**Pullback scalp** → Entry **{entry:.4f}**, Stop **{stop:.4f}**, TP1 **{tp1:.4f}**, TP2 **{tp2:.4f}**\n"
          f"**Tip**: add on VWAP holds; reduce into prior high.\n")
    return {"title":f"{sym} — Coin of the Day", "description":desc, "color":0xE67E22}

def _send_pnl_card(webhook, csv_path, last_n=5):
    import csv, os
    rows=[]
    if not os.path.exists(csv_path):
        return
    with open(csv_path,"r") as f:
        r=csv.DictReader(f)
        for row in r:
            if row.get("outcome"):
                rows.append(row)
    rows=rows[-last_n:]
    if not rows:
        return
    wins = sum(1 for r in rows if r["outcome"].startswith("WIN"))
    total = len(rows)
    wl = f"{wins}/{total}  ({(wins/total*100):.0f}%)"
    lines=[]
    for r in rows[::-1]:
        side=r["side"]; sym=r["symbol"]; oc=r["outcome"]; pnl=r.get("pnl_pct","")
        ep=r.get("entry",""); xp=r.get("exit_price","")
        lines.append(f"• **{sym}** {side} {oc}  PnL {pnl}%  (in/out {ep}→{xp})")
    desc="\n".join(lines)
    send_embed(webhook, {
        "title":"📊 Last trades (recent 5)",
        "description": f"{desc}\n\nW/L: **{wl}**",
        "color": 0x1ABC9C
    }, cfg.MAX_ALERTS_PER_HOUR)

def _check_triggers_and_log(spot_base):
    from datetime import datetime, timezone
    for sym, plan in list(ACTIVE_SCALPS.items()):
        try:
            spot = get_spot_data(spot_base, sym, 3)
            if not spot.get('prices'):
                continue
            px = float(spot['prices'][-1])
            status = plan.get('last_status','posted')

            # ENTER
            if status=='posted' and ((plan['side']=='LONG' and px<=plan['entry']) or (plan['side']=='SHORT' and px>=plan['entry'])):
                plan['last_status']='entered'
                ts_open = int(time.time())
                open_row = {
                    'ts_open': ts_open,'symbol': sym,'side': plan['side'],
                    'entry': float(plan['entry']),'tp1': float(plan['tp1']),
                    'tp2': float(plan['tp2']),'stop': float(plan['stop']),
                    'prob': int(plan.get('prob',0)),'rr': float(plan.get('rr',0)),'note': ''
                }
                ACTIVE_OPENS[sym] = open_row
                if getattr(cfg,'TRADES_CSV_PATH',None):
                    append_open(cfg.TRADES_CSV_PATH, open_row)
                if getattr(cfg,'ENTRY_ALERTS_ENABLED',True):
                    send_embed(cfg.DISCORD_WEBHOOK_URL, {
                        "title": f"{sym} ⚡ Entry",
                        "description": f"{plan['side']}  |  entry {plan['entry']:.2f}  |  stop {plan['stop']:.2f}  |  tp1 {plan['tp1']:.2f}  |  tp2 {plan['tp2']:.2f}  |  prob {plan.get('prob',0)}%",
                        "color": 0x3498DB
                    }, cfg.MAX_ALERTS_PER_HOUR)

            # STOP (LOSS)
            elif status in ('posted','entered','tp1') and (
                (plan['side']=='LONG' and px<=plan['stop']) or (plan['side']=='SHORT' and px>=plan['stop'])
            ):
                base = ACTIVE_OPENS.get(sym)
                if base:
                    close = {
                        'ts_close': int(time.time()),'exit_price': float(px),
                        'outcome': 'LOSS','pnl_pct': round(pnl_pct(plan['side'], base['entry'], float(px)), 3),
                        'hold_secs': int(time.time()-base['ts_open'])
                    }
                    append_close(cfg.TRADES_CSV_PATH, base, close)
                    update_stats(cfg.TRADES_STATS_PATH, base, close)
                    if getattr(cfg,'OUTCOME_ALERTS_ENABLED',True):
                        send_embed(cfg.DISCORD_WEBHOOK_URL, {
                            "title": f"{sym} ⛔️ Closed: LOSS",
                            "description": f"{plan['side']}  exit {px:.2f}  |  PnL {close['pnl_pct']}%",
                            "color": 0xE74C3C
                        }, cfg.MAX_ALERTS_PER_HOUR)
                        _send_pnl_card(cfg.DISCORD_WEBHOOK_URL, cfg.TRADES_CSV_PATH, last_n=5)
                    del ACTIVE_OPENS[sym]
                del ACTIVE_SCALPS[sym]

            # TP1 marker
            elif status in ('posted','entered') and (
                (plan['side']=='LONG' and px>=plan['tp1']) or (plan['side']=='SHORT' and px<=plan['tp1'])
            ):
                plan['last_status']='tp1'

            # TP2 (WIN)
            elif status in ('tp1','entered') and (
                (plan['side']=='LONG' and px>=plan['tp2']) or (plan['side']=='SHORT' and px<=plan['tp2'])
            ):
                base = ACTIVE_OPENS.get(sym)
                if base:
                    close = {
                        'ts_close': int(time.time()),'exit_price': float(px),
                        'outcome': 'WIN_TP2','pnl_pct': round(pnl_pct(plan['side'], base['entry'], float(px)), 3),
                        'hold_secs': int(time.time()-base['ts_open'])
                    }
                    append_close(cfg.TRADES_CSV_PATH, base, close)
                    update_stats(cfg.TRADES_STATS_PATH, base, close)
                    if getattr(cfg,'OUTCOME_ALERTS_ENABLED',True):
                        send_embed(cfg.DISCORD_WEBHOOK_URL, {
                            "title": f"{sym} ✅ Closed: WIN",
                            "description": f"{plan['side']}  exit {px:.2f}  |  PnL {close['pnl_pct']}%",
                            "color": 0x2ECC71
                        }, cfg.MAX_ALERTS_PER_HOUR)
                        _send_pnl_card(cfg.DISCORD_WEBHOOK_URL, cfg.TRADES_CSV_PATH, last_n=5)
                    del ACTIVE_OPENS[sym]
                del ACTIVE_SCALPS[sym]

        except Exception as e:
            err('trigger-log:', sym, e)
    return

def run():
    info("MMS signal mode (scalp + coin-of-day) starting.")

    # Start flush monitor
    try:
        start_flush_monitor(cfg.BINANCE_SPOT_REST, cfg.TRADING_PAIRS, cfg.DISCORD_WEBHOOK_URL, cfg.MAX_ALERTS_PER_HOUR)
    except Exception as e:
        err("Flush monitor error:", e)

    # Refresh vol hours
    try:
        _refresh_vol_hours()
    except Exception as e:
        err("Vol hours error:", e)

    # Set next snapshot time
    if cfg.POST_SNAPSHOT_ON_START:
        next_ts = time.time()  # Trigger immediately
        info("Posting snapshot on start - triggering immediately")
    else:
        next_ts = next_snapshot_ts()
        info("Next snapshot @", datetime.fromtimestamp(next_ts,timezone.utc).astimezone(ET).strftime("%Y-%m-%d %H:%M ET"))

    last_coin_card_day = None

    while True:
        try:
            # frequent trigger checks
            _check_triggers_and_log(cfg.BINANCE_SPOT_REST)

            if time.time() >= next_ts:
                info("Triggering hourly snapshots...")
                # hourly snapshots + scalp idea
                for sym in cfg.TRADING_PAIRS:
                    try:
                        info(f"Processing {sym}...")
                        spot = get_spot_data(cfg.BINANCE_SPOT_REST, sym, 300)
                        fut  = get_futures_data(cfg.BINANCE_FUTURES_REST, sym, 300)
                        bids, asks = get_orderbook(cfg.BINANCE_SPOT_REST, sym, 200)
                        cb_px = get_coinbase_spot(sym)
                        liqs  = get_recent_liqs(cfg.BINANCE_FUTURES_REST, sym, minutes=90, limit=1000)

                        if not spot.get("prices") or not fut.get("volumes"):
                            err("Missing data for", sym); continue
                        st = detector.analyze_mm_activity(sym, spot, fut)

                        if sym not in VOL_HOURS or len(VOL_HOURS[sym])==0:
                            VOL_HOURS[sym]=typical_high_vol_hours(cfg.BINANCE_SPOT_REST, sym, 30, 3)
                        windows = next24_windows(VOL_HOURS[sym], tz_name=cfg.TIMEZONE_NAME)

                        embed=_format_signal_card(sym, st, fut, spot, bids, asks, windows, cb_px, liqs)
                        send_embed(cfg.DISCORD_WEBHOOK_URL, embed, cfg.MAX_ALERTS_PER_HOUR)
                        info(f"✅ Sent snapshot for {sym}")
                    except Exception as e:
                        err(f"Error processing {sym}:", e)

                # once per day, drop "coin of the day" (orange card)
                today = datetime.now(ET).date()
                if last_coin_card_day != today:
                    try:
                        card = _coin_of_day_card(cfg.BINANCE_SPOT_REST)
                        if card:
                            send_embed(cfg.DISCORD_WEBHOOK_URL, card, cfg.MAX_ALERTS_PER_HOUR)
                            last_coin_card_day = today
                    except Exception as e:
                        err("Coin of day error:", e)

                next_ts = next_snapshot_ts()
                info("Next snapshot @", datetime.fromtimestamp(next_ts,timezone.utc).astimezone(ET).strftime("%Y-%m-%d %H:%M ET"))

            time.sleep(10)  # faster loop to catch triggers
        except KeyboardInterrupt:
            info("Stopping MMS."); break
        except Exception as e:
            err("Loop:", repr(e)[:240]); time.sleep(5)

if __name__=="__main__": run()
