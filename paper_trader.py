#!/usr/bin/env python3
"""
Paper trading engine for Bounty Seeker v4
- 15x leverage
- $250 margin per position (notional = margin * leverage)
- Max 3 open positions
- Take profit aggressively when UPNL >= $50 (after fees)
- Update balance/PnL every scan
"""

from datetime import datetime, timezone
import time

LEVERAGE = 15
MARGIN_PER_TRADE = 250.0          # $250 margin
MAX_OPEN = 3
TP_USD = 50.0                      # take profit threshold
FEE_ROUNDTRIP = 0.0012             # est. round-trip fee (0.12%) on notional

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def _et():
    return datetime.now(timezone.utc).strftime("%-I:%M %p ET")

def _tv_link(symbol: str, exchange: str) -> str:
    base = symbol.replace("/USDT", "").replace(":USDT","").replace("/","")
    exch = {"bybit":"BYBIT","bitget":"BITGET","mexc":"MEXC","binance":"BINANCE"}.get(exchange.lower(),"BINANCE")
    return f"https://www.tradingview.com/chart/?symbol={exch}:{base}USDT.P"

class PaperTrader:
    def __init__(self, state: dict):
        # state is st["paper"] from the bot; ensure defaults
        self.state = state if isinstance(state, dict) else {}
        self.state.setdefault("balance", 10_000.0)
        self.state.setdefault("trades", [])
        self.state.setdefault("history", [])
        self.state.setdefault("stats", {})
        stats = self.state["stats"]
        stats.setdefault("wins", 0)
        stats.setdefault("losses", 0)
        stats.setdefault("realized_pnl", 0.0)
        stats.setdefault("unrealized_pnl", 0.0)
        stats.setdefault("total_pnl", 0.0)
        stats.setdefault("daily_pnl", 0.0)
        stats.setdefault("last_reset", _now_iso())
        self.ex_map = {}

    # Provided by runner
    def bind_exchanges(self, ex_map: dict):
        self.ex_map = ex_map or {}

    # ---------- helpers ----------
    def _get_px(self, ex_id: str, symbol: str):
        try:
            ex = self.ex_map[ex_id]
            t = ex.fetch_ticker(symbol)
            return float(t.get("last") or t.get("close") or 0)
        except Exception:
            return None

    def can_open_more(self) -> bool:
        return len(self.state["trades"]) < MAX_OPEN

    def _fees_estimate(self, entry: float, qty: float) -> float:
        notional = abs(entry * qty)
        return notional * FEE_ROUNDTRIP

    # ---------- opening ----------
    def open_from_signals(self, signals):
        """Open up to available slots from ranked signals (already top-sorted)."""
        for s in signals:
            if not self.can_open_more():
                return
            entry = float(s.get("entry", 0.0))
            if entry <= 0:
                continue
            # margin-based position; notional = margin * leverage
            notional = MARGIN_PER_TRADE * LEVERAGE
            qty = notional / entry
            self.state["trades"].append({
                "exchange": s["exchange"],
                "symbol": s["symbol"],
                "base": s.get("base") or s["symbol"].split("/")[0],
                "dir": s["direction"],         # LONG / SHORT
                "entry": entry,
                "qty": qty,
                "opened": _now_iso(),
                "style": s.get("style",""),
                "leverage": LEVERAGE,
                "margin": MARGIN_PER_TRADE,
                "tp_hit": False,
            })

    # ---------- updating & closing ----------
    def update_positions(self):
        """Update UPNL; close positions when UPNL >= TP_USD (after fees)."""
        stats = self.state["stats"]
        # daily reset
        try:
            last = datetime.fromisoformat(stats.get("last_reset", _now_iso()))
            if (datetime.now(timezone.utc) - last).days >= 1:
                stats["daily_pnl"] = 0.0
                stats["last_reset"] = _now_iso()
        except Exception:
            stats["daily_pnl"] = stats.get("daily_pnl", 0.0)
            stats["last_reset"] = _now_iso()

        new_trades = []
        unreal_total = 0.0
        bal = float(self.state.get("balance", 10_000.0))

        for t in self.state["trades"]:
            px = self._get_px(t["exchange"], t["symbol"])
            if not px:
                new_trades.append(t)
                continue
            side = 1 if t["dir"] == "LONG" else -1
            upnl = (px - t["entry"]) * side * t["qty"]
            unreal_total += upnl

            # close aggressively when profit covers threshold + fees
            fees = self._fees_estimate(t["entry"], t["qty"])
            if upnl >= (TP_USD + fees):
                bal += upnl
                stats["realized_pnl"] = stats.get("realized_pnl", 0.0) + upnl
                stats["daily_pnl"] = stats.get("daily_pnl", 0.0) + upnl
                stats["wins"] += 1 if upnl >= 0 else 0
                stats["losses"] += 1 if upnl < 0 else 0
                stats["total_pnl"] = stats.get("total_pnl", 0.0) + upnl
                self.state["history"].append({
                    **t,
                    "exit": px,
                    "exit_ts": _now_iso(),
                    "pnl": upnl,
                    "reason": "TP(>$50)"
                })
            else:
                new_trades.append(t)

        self.state["trades"] = new_trades
        self.state["balance"] = bal
        stats["unrealized_pnl"] = unreal_total
        stats["total_pnl"] = stats.get("realized_pnl", 0.0) + unreal_total

    # ---------- discord cards ----------
    def account_card(self):
        s = self.state["stats"]
        bal = float(self.state.get("balance", 10_000.0))
        realized = s.get("realized_pnl", 0.0)
        unreal = s.get("unrealized_pnl", 0.0)
        daily = s.get("daily_pnl", 0.0)
        open_n = len(self.state.get("trades", []))

        return {
            "title": "💼 Paper Account",
            "description": "\n".join([
                f"**Balance:** ${bal:,.2f}",
                f"**Realized PnL:** ${realized:+.2f}",
                f"**Unrealized PnL:** ${unreal:+.2f}",
                f"**Daily PnL:** ${daily:+.2f}",
                f"**Open:** {open_n}/{MAX_OPEN} • **Lev:** {LEVERAGE}x • **Margin/pos:** ${MARGIN_PER_TRADE:.0f}",
                f"Updated: {_et()}"
            ]),
            "color": 0x2F3136
        }

    def positions_card(self, get_px=None):
        if not self.state["trades"]:
            return None
        lines = []
        tot_upnl = 0.0
        for t in self.state["trades"]:
            px = None
            if callable(get_px):
                px = get_px(t["exchange"], t["symbol"])
            if px is None:
                px = self._get_px(t["exchange"], t["symbol"]) or t["entry"]
            side = 1 if t["dir"] == "LONG" else -1
            upnl = (px - t["entry"]) * side * t["qty"]
            tot_upnl += upnl
            emoji = "🟢" if t["dir"] == "LONG" else "🔴"
            tv = _tv_link(t["symbol"], t["exchange"])
            lines.append(f"{emoji} **{t['base']}** ${t['entry']:.6f} → ${px:.6f} • PnL: ${upnl:+.2f}  [TV]({tv})")

        return {
            "title": "📊 Current Positions",
            "description": "\n".join(lines + [f"\n**Total Open PnL:** ${tot_upnl:+.2f}"]),
            "color": 0xFFFFFF
        }





