#!/usr/bin/env python3
"""Close partial positions and ping PnL"""

import os
import sys
import json
from datetime import datetime
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bounty_seeker_kcex import BountySeekerV5, PAPER_PATH

def close_partial_positions():
    """Close half of AR short and ARIA long positions"""
    webhook = os.getenv("DISCORD_WEBHOOK", "").strip()
    if not webhook and os.path.exists(".webhook"):
        try:
            webhook = open(".webhook").read().strip()
        except:
            pass

    if not webhook:
        print("No webhook found!")
        return

    # Load paper state
    try:
        with open(PAPER_PATH, 'r') as f:
            state = json.load(f)
        paper = state.get('paper', {})
        trades = paper.get('trades', [])
    except Exception as e:
        print(f"Error loading paper state: {e}")
        return

    # Find positions
    ar_short = None
    aria_long = None

    for trade in trades:
        if trade.get('status') != 'OPEN':
            continue
        symbol = trade.get('symbol', '').upper()
        direction = trade.get('direction', '').upper()

        if 'AR/USDT' in symbol or 'AR:' in symbol:
            if direction == 'SHORT':
                ar_short = trade
        elif 'ARIA/USDT' in symbol or 'ARIA:' in symbol:
            if direction == 'LONG':
                aria_long = trade

    if not ar_short and not aria_long:
        print("No matching positions found!")
        return

    # Initialize bot for price fetching
    bot = BountySeekerV5(webhook_url=webhook)
    closed_pnl = []
    updated_trades = []

    # Close half of AR short
    if ar_short:
        symbol = ar_short['symbol']
        try:
            ticker = bot.ex.fetch_ticker(symbol)
            current_price = float(ticker.get('last', 0) or 0)
        except:
            current_price = float(ar_short.get('entry', 0))

        entry = float(ar_short['entry'])
        qty = float(ar_short['qty'])
        close_qty = qty * 0.5  # Close half

        # Calculate PnL (SHORT: profit when price goes down)
        pnl = (entry - current_price) * close_qty
        pnl_pct = ((entry - current_price) / entry) * 100

        # Update position
        ar_short['qty'] = qty - close_qty
        if ar_short['qty'] < 0.0001:  # If almost nothing left, mark as closed
            ar_short['status'] = 'CLOSED'

        # Update balance
        paper['balance'] = float(paper.get('balance', 10000.0)) + pnl
        stats = paper.get('stats', {})
        stats['realized_pnl'] = stats.get('realized_pnl', 0.0) + pnl
        stats['total_pnl'] = stats.get('total_pnl', 0.0) + pnl
        paper['stats'] = stats

        closed_pnl.append({
            'symbol': symbol.split('/')[0] if '/' in symbol else symbol,
            'direction': 'SHORT',
            'qty_closed': close_qty,
            'entry': entry,
            'exit': current_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
        updated_trades.append(ar_short)
        print(f"Closed {close_qty:.4f} AR SHORT @ ${current_price:.6f}, PnL: ${pnl:+.2f}")

    # Close half of ARIA long
    if aria_long:
        symbol = aria_long['symbol']
        try:
            ticker = bot.ex.fetch_ticker(symbol)
            current_price = float(ticker.get('last', 0) or 0)
        except:
            current_price = float(aria_long.get('entry', 0))

        entry = float(aria_long['entry'])
        qty = float(aria_long['qty'])
        close_qty = qty * 0.5  # Close half

        # Calculate PnL (LONG: profit when price goes up)
        pnl = (current_price - entry) * close_qty
        pnl_pct = ((current_price - entry) / entry) * 100

        # Update position
        aria_long['qty'] = qty - close_qty
        if aria_long['qty'] < 0.0001:  # If almost nothing left, mark as closed
            aria_long['status'] = 'CLOSED'

        # Update balance
        paper['balance'] = float(paper.get('balance', 10000.0)) + pnl
        stats = paper.get('stats', {})
        stats['realized_pnl'] = stats.get('realized_pnl', 0.0) + pnl
        stats['total_pnl'] = stats.get('total_pnl', 0.0) + pnl
        paper['stats'] = stats

        closed_pnl.append({
            'symbol': symbol.split('/')[0] if '/' in symbol else symbol,
            'direction': 'LONG',
            'qty_closed': close_qty,
            'entry': entry,
            'exit': current_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
        updated_trades.append(aria_long)
        print(f"Closed {close_qty:.4f} ARIA LONG @ ${current_price:.6f}, PnL: ${pnl:+.2f}")

    # Remove fully closed trades
    paper['trades'] = [t for t in trades if t.get('status') == 'OPEN']

    # Save state
    state['paper'] = paper
    with open(PAPER_PATH, 'w') as f:
        json.dump(state, f, indent=2)

    # Send Discord ping
    total_closed_pnl = sum(c['pnl'] for c in closed_pnl)
    balance = paper['balance']

    lines = []
    for close in closed_pnl:
        dir_emoji = "🟢" if close['direction'] == 'LONG' else "🟣"
        pnl_emoji = "✅" if close['pnl'] > 0 else "❌"
        lines.append(
            f"{dir_emoji} **{close['symbol']} {close['direction']}** (50% closed)\n"
            f"{pnl_emoji} Entry: ${close['entry']:.6f} → Exit: ${close['exit']:.6f}\n"
            f"PnL: ${close['pnl']:+.2f} ({close['pnl_pct']:+.2f}%)"
        )

    embed = {
        "title": "💰 Partial Position Closes",
        "description": "\n\n".join(lines),
        "color": 0x00ff00 if total_closed_pnl > 0 else 0xff0000,
        "timestamp": datetime.utcnow().isoformat(),
        "fields": [
            {"name": "Total Closed PnL", "value": f"${total_closed_pnl:+.2f}", "inline": True},
            {"name": "New Balance", "value": f"${balance:.2f}", "inline": True},
            {"name": "Remaining Positions", "value": f"{len(paper['trades'])} open", "inline": True}
        ],
        "footer": {"text": "Bounty Seeker • Partial Close"}
    }

    payload = {"embeds": [embed]}
    requests.post(webhook, json=payload, timeout=15)
    print(f"✅ Ping sent! Total closed PnL: ${total_closed_pnl:+.2f}, New balance: ${balance:.2f}")

if __name__ == "__main__":
    close_partial_positions()







