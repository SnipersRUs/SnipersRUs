import os
import sys
import requests
from datetime import datetime, timezone


def post_discord(webhook: str, embed: dict) -> bool:
    try:
        r = requests.post(webhook, json={"embeds": [embed]}, timeout=10)
        return r.status_code in (200, 201, 204)
    except Exception:
        return False


def main():
    webhook = None
    if len(sys.argv) > 1:
        webhook = sys.argv[1]
    if not webhook:
        webhook = os.getenv("DISCORD_WEBHOOK", "").strip()
    if not webhook:
        print("Missing webhook. Pass as arg or set DISCORD_WEBHOOK.")
        sys.exit(1)

    # Concrete risk and sizing examples for a $10,000 account at 1.5% risk
    account_size = 10000.0
    risk_pct = 0.015
    risk_amount = account_size * risk_pct  # $150

    # Example stop sizes in $ per SOL (entry to stop distance)
    examples = [0.20, 0.50, 1.00, 1.50]
    rows = []
    for stop in examples:
        size = risk_amount / stop  # SOL quantity
        rows.append(f"Stop ${stop:.2f} → Size ≈ {size:.2f} SOL")

    description = (
        "Breakout Prop Bot scans SOL/USDT 5m with strict risk controls.\n\n"
        "Rules to PASS the evaluation:\n"
        "- 4% daily loss limit (soft stop).\n"
        "- 6% max drawdown (hard stop).\n"
        "- Target steady growth; avoid large swings.\n\n"
        f"Concrete risk: 1.5% of $ {account_size:,.0f} = $ {risk_amount:,.0f} per trade.\n"
        "Position sizing: size(SOL) = $risk / ($stop distance).\n"
        + "\n".join([f"- {r}" for r in rows]) + "\n\n"
        "Operating plan:\n"
        "- Bot scans every 60s, pings on startup, and sends 30m heartbeats.\n"
        "- Alerts fire only when 2/3: GPS, Head Hunter, Oath Keeper align (Grade B-A+).\n"
        "- Manual execution allowed; use tight stops and defined targets.\n\n"
        "Risk & discipline (do NOT blow the account):\n"
        f"- Risk exactly $ {risk_amount:,.0f} per trade (1.5%).\n"
        "- Hard cap: stop trading for the day at -3% or after -2R.\n"
        "- Max 2 trades per session unless unrealized drift is 0 and A/A+ setup appears.\n"
        "- No revenge trades. Wait for the next clean confluence.\n"
        "- Avoid entries within 5 minutes of major news; widen stops only if volatility drops after entry.\n"
        "- Place stops beyond recent swing or ~1.5 ATR (whichever is tighter but safe).\n"
        "- Take profits at ≥2.5R; partial at key VWAP/GP levels. Move stop to breakeven after +1R.\n"
        "- If equity hits daily soft stop, shut down scanning/alerts and resume next session.\n"
        "- Log every trade with rationale and screenshot for review.\n"
    )

    fields = [
        {"name": "Instrument", "value": "SOL/USDT Perp (5m)", "inline": True},
        {"name": "Risk per trade", "value": f"$ {risk_amount:,.0f} (1.5% of $ {account_size:,.0f})", "inline": True},
        {"name": "Signal threshold", "value": "≥ 2/3 confirmations", "inline": True},
        {"name": "Targets", "value": ">= 2.5R, partials at VWAP/GP", "inline": True},
        {"name": "Daily limits", "value": "-4% soft, -6% hard", "inline": True},
        {"name": "Heartbeat", "value": "Every 30 minutes", "inline": True},
    ]

    embed = {
        "title": "Breakout Prop: Rules and Passing Plan",
        "description": description,
        "color": 0x3498DB,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": fields,
        "footer": {"text": "Stay disciplined. Protect the curve."},
    }

    ok = post_discord(webhook, embed)
    if not ok:
        print("Failed to post to Discord.")
        sys.exit(2)


if __name__ == "__main__":
    main()
