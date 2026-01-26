#!/usr/bin/env python3
"""
Move all open stops to 1% in profit (trailing stop)
"""
import json
import os
from datetime import datetime
import requests

PAPER_PATH = "paper_kcex.json"
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "").strip()
PROFIT_PCT = 0.01  # 1% profit

def load_paper():
    if not os.path.exists(PAPER_PATH):
        return {"balance": 10000.0, "trades": [], "history": [], "stats": {}}
    try:
        with open(PAPER_PATH, 'r') as f:
            return json.load(f)
    except:
        return {"balance": 10000.0, "trades": [], "history": [], "stats": {}}

def save_paper(paper):
    with open(PAPER_PATH, 'w') as f:
        json.dump(paper, f, indent=2)

def post_discord(embeds):
    if not DISCORD_WEBHOOK or not DISCORD_WEBHOOK.startswith("http"):
        print("Webhook not set; skipping Discord post.")
        return
    try:
        payload = {"embeds": embeds}
        r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"Discord post error: {e}")

if __name__ == "__main__":
    paper = load_paper()
    open_trades = [t for t in paper.get('trades', []) if t.get('status') == 'OPEN']

    if not open_trades:
        print("No open trades to update.")
        # Still send notification that there are no open positions
        if DISCORD_WEBHOOK and DISCORD_WEBHOOK.startswith("http"):
            embed = {
                "title": "🔒 Stop Update",
                "description": "No open positions to update.",
                "color": 0x808080,  # Gray
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {"text": "No open trades"}
            }
            try:
                payload = {"content": "@here", "embeds": [embed]}
                r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
                r.raise_for_status()
                print("📤 Discord notification sent")
            except Exception as e:
                print(f"Discord post error: {e}")
        exit(0)

    updated_trades = []
    trade_lines = []

    for trade in open_trades:
        symbol = trade.get('symbol', 'N/A')
        direction = trade.get('direction', 'N/A')
        entry = float(trade.get('entry', 0))
        old_stop = float(trade.get('stop', 0))

        # Move stop to 1% in profit
        if direction == 'LONG':
            # LONG: stop at entry + 1% profit
            new_stop = entry * (1 + PROFIT_PCT)
        else:  # SHORT
            # SHORT: stop at entry - 1% profit
            new_stop = entry * (1 - PROFIT_PCT)

        trade['stop'] = new_stop
        updated_trades.append(trade)

        base_sym = symbol.split('/')[0] if '/' in symbol else symbol
        profit_pct_display = PROFIT_PCT * 100
        trade_lines.append(f"**{base_sym} {direction}**\nEntry: ${entry:.6f} → Stop: ${new_stop:.6f} (+{profit_pct_display:.1f}% profit)")
        print(f"✅ {symbol} {direction}: Stop moved to ${new_stop:.6f} (was ${old_stop:.6f}, {profit_pct_display:.1f}% profit)")

    # Update trades in paper state
    for trade in paper.get('trades', []):
        if trade.get('status') == 'OPEN':
            # Find matching updated trade
            for updated in updated_trades:
                if updated.get('id') == trade.get('id'):
                    trade['stop'] = updated['stop']
                    break

    save_paper(paper)
    profit_pct_display = PROFIT_PCT * 100
    print(f"\n✅ Updated {len(updated_trades)} positions to {profit_pct_display:.1f}% profit")

    # Send Discord notification with @here
    if DISCORD_WEBHOOK and DISCORD_WEBHOOK.startswith("http"):
        embed = {
            "title": f"🔒 Stops Moved to {profit_pct_display:.1f}% Profit",
            "description": "\n\n".join(trade_lines),
            "color": 0x00ff00,  # Green (profit)
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": f"{len(updated_trades)} positions updated • Trailing stop"}
        }
        try:
            payload = {"content": "@here", "embeds": [embed]}
            r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
            r.raise_for_status()
            print("📤 Discord notification sent with @here")
        except Exception as e:
            print(f"Discord post error: {e}")
    else:
        print("Webhook not set; skipping Discord post.")
