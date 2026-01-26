#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send BTC Analysis to Discord Webhook
"""

import requests
import json
from datetime import datetime

def send_btc_analysis():
    """Send comprehensive BTC analysis to Discord"""

    webhook_url = ""

    embed = {
        "title": "📊 TUESDAY NY SESSION UPDATE — OCT 21, 2025",
        "description": "**BTC (all TFs condensed) • Bias • Entries • Probabilities • News to watch**",
        "color": 3447003,
        "fields": [
            {
                "name": "🔍 STATE (what price did last session)",
                "value": "• Post-flush bounce stalled beneath 111.5–112.5k (prior breakdown origin). We printed lower highs on 30m/1h, and the 8h still sits under a descending guide. LTFs basing above 107.2–108.0k, but VWAP reclaims keep failing on retests. Net: compression between 108.0k support and 111.5k resistance; momentum neutral→slightly bearish until VWAP stack turns up.",
                "inline": False
            },
            {
                "name": "📈 STRUCTURE READ (one pass across your 8h/1h/30m/10m)",
                "value": "• **8h:** Lower-high sequence from the 125k spike; mean reversion carried to the mid-channel. Reclaim of 112.6k is required to argue a fresh leg up; otherwise this is distribution under resistance.\n• **1h:** VWAP rolling flat/down; rallies sold at the underside of the prior value area (111–112k). Buyers defended 107.3–108.0k multiple times—key shelf.\n• **30m/10m:** Tight range building 108.3–109.4k with quick rejections at 110.2–110.8k; liquidity is collecting above 111.5k and below 107.2k for the next impulse.",
                "inline": False
            },
            {
                "name": "🎯 BIAS INTO NY",
                "value": "• Continuation chop with downside skew until VWAPs flip: **45%**\n• Stop-run squeeze toward 112.5–114k, then fade: **35%**\n• Trend extension lower to 105–106k: **20%**",
                "inline": False
            },
            {
                "name": "📊 LEVELS THAT MATTER (rounded)",
                "value": "• **Resistance:** 110.8k → 111.5k → 112.6k → 114.0k\n• **Support:** 108.3k → 107.3k (pivot) → 106.2k → 105.3k (strong demand)",
                "inline": False
            },
            {
                "name": "⚡ TRADE SETUPS (execute only on trigger; risk 0.5–1.0%)",
                "value": "**1) VWAP Reclaim LONG** (only if NY turns tape)\n• Trigger: 15m close & hold above 110.8k with rising delta; quick retest holds.\n• Entry: 110.9–111.1k | Invalidation: 110.2k\n• Targets: 111.9k → 112.6k → 113.8k (trail >112.6k)\n\n**2) Sweep-and-Lift LONG** (best R:R if we dip first)\n• Trigger: Fast sweep into 107.2–107.6k, immediate reclaim of 108.0k.\n• Entry: 107.7–107.9k | Invalidation: 107.1k\n• Targets: 109.2k → 110.4k → 111.5k\n\n**3) Lower-High FADE** (base case while VWAPs are bearish/flat)\n• Trigger: Rejection at 110.8–111.5k with VWAP roll + weakening delta.\n• Entry: ~111.2k | Invalidation: 112.0k\n• Targets: 109.9k → 108.8k → 107.6k (scale quickly)\n\n**4) Breakdown CONTINUATION** (only on acceptance)\n• Trigger: Hourly close <107.2k and fail to reclaim on retest.\n• Entry: 107.0–107.2k | Invalidation: 107.8k\n• Targets: 106.2k → 105.3k → stretch 103.8k",
                "inline": False
            },
            {
                "name": "⚠️ EXECUTION NOTES (stern)",
                "value": "• Trade edges (reclaims/sweeps), not the middle of 108–111k.\n• First partial ≥ +0.8R; trail behind reclaimed VWAP/swing lows.\n• If NY opens with wide spread and no tape confirmation, stand down—let first 30–45m set the VWAP bias.",
                "inline": False
            },
            {
                "name": "🔄 CYCLE / VWAP CONTEXT (your 4–9 day view, simplified)",
                "value": "• 4-day VWAP rolls into \"day 5 transition\" → typically traps & fake moves.\n• True size for longs often comes after the reset aligns with the 9-day (Thu/Fri).\n• Until stack turns up together, treat bounces as \"sell the underside\" zones.",
                "inline": False
            },
            {
                "name": "📰 MACRO / NEWS THAT CAN MOVE TAPE (today → week)",
                "value": "• **FOMC next week (Oct 28–29)**; positioning flows can cap trends ahead of it.\n• **CPI (Sep) Friday Oct 24, 8:30a ET**; options & basis traders already hedging around it.\n• **Ukraine power-grid strikes** keep energy risk elevated (risk-off impulse if escalates).\n• **Gaza truce fragile; U.S. pushing next-phase talks**—headline risk intraday.\n• **Digital-asset flows:** Recent **outflows from BTC ETPs** while **ETH/SOL saw inflows**; near-term supply overhang for BTC until flows stabilize.\n• Some trackers flag **soft ETF demand day in the U.S.** (adds to chop risk).",
                "inline": False
            },
            {
                "name": "🎯 BOTTOM LINE",
                "value": "We're boxed between 108s support and 111–112k resistance. I stay short-biased into NY **until** a clean VWAP reclaim above ~110.8–111.1k sticks. If 107.2k breaks and accepts, expect 106.2k→105.3k. If NY squeezes through 112.6k with volume, flip long and aim 113.8–114.0k, then reassess.",
                "inline": False
            }
        ],
        "footer": {
            "text": "Sniper Guru • NY Session Analysis • Oct 21, 2025"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

    payload = {"embeds": [embed]}

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 204:
            print("✅ BTC Analysis sent successfully to Discord!")
        else:
            print(f"❌ Failed to send: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error sending to Discord: {e}")

if __name__ == "__main__":
    send_btc_analysis()
