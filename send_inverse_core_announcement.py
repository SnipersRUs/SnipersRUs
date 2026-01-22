#!/usr/bin/env python3
"""
Send Inverse Core announcement to Discord webhook
"""

import requests
import json

def send_discord_webhook():
    webhook_url = ""

    message = """🎯 **WELCOME TO INVERSE CORE** — our "Independent-Move" Crypto Scanner

This bot hunts USDT-perp futures and surfaces coins out of sync with BTC (laggards). Clean asymmetric moves show up in rotations when BTC runs, and mean-reversions when it doesn't.

**What it looks for:**
• **BTC Divergence plays:**
• Laggards — BTC runs, coin hasn't → catch-up LONG
• Opposite movers — BTC dumps, coin pumps → exhaustion SHORT/LONG
• Solo pumps/dumps while BTC flat → snap-back setups
• **Fresh listings:**
• Dump → bounce setups (reversal LONGs)
• Overhyped pumps showing weakness (top-in shorts)

**Each alert shows:**
• Pair + exchange (e.g., ARB/USDT • MEXC)
• Bias — 🟢 LONG or 🔴 SHORT
• Quick reason + stats + chart links

**Simple playbook:**
1. Read bias & reason
2. Open chart, confirm on your timeframe
3. Execute with risk management
4. Context matters: BTC pumping = laggard LONGs, BTC dumping = opposite SHORTs

**Why it works:**
• Rotations: BTC moves → capital chases laggards
• Asymmetry: Opposite movers create cleaner risk/reward
• Volume confirms crowd participation

⚠️ **Not financial advice.** Use stops, size responsibly, always check charts first."""

    payload = {
        "content": message
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        response.raise_for_status()
        print("✅ Discord message sent successfully!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending Discord message: {e}")
        return False

if __name__ == "__main__":
    send_discord_webhook()
