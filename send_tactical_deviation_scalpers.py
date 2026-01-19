#!/usr/bin/env python3
"""
Send Tactical Deviation Indicator announcement for scalpers to Discord
"""

import requests
import time

WEBHOOK_URL = "https://discord.com/api/webhooks/1363315528831340787/KfoIJA6G1eEYjegzgrkgZ2qtDaaHL1hrs-ocU00wajpAdNsejWOm5HTvsmCYyrF9jOgr"

MESSAGES = [
    """@everyone 🎯 **TACTICAL DEVIATION - THE SCALPER'S EDGE** 🎯

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 **WHY THIS IS PERFECT FOR SCALPERS**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Volume-Backed VWAP Deviation Analysis**

This isn't your average VWAP indicator. It's built for quick, high-probability scalps.

**What makes it scalper-friendly:**

✅ **Instant Signals at Deviation Extremes**
• Green triangles = Long signals (oversold)
• Red triangles = Short signals (overbought)
• Signals appear at ±2σ deviation zones
• No guessing - clear entry points

✅ **Volume Confirmation Built-In**
• Signals only appear with volume spikes (1.5x average)
• Filters out weak moves that kill scalps
• Bright colors = volume spike (best quality)
• Lighter colors = volume momentum
• No volume = no signal (saves you from bad trades)

✅ **Mean Reversion Goldmine**
• Price reaches extreme deviation (±2σ)
• Volume confirms the move
• Target: Return to VWAP or opposite band
• Perfect for quick in-and-out scalps

✅ **Multi-Timeframe Context**
• Daily VWAP shows fair value
• Weekly/Monthly VWAPs (optional) for higher timeframe bias
• Know if you're scalping with or against the trend

✅ **Clean Visual Setup**
• Cyan line = Daily VWAP (fair value)
• Deviation bands show extreme zones
• Triangles show exact entry points
• No chart clutter - focus on what matters""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ **HOW TO SCALP WITH IT**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**SCALPING SETUP:**

1. **Watch for Signals at ±2σ**
   • Price hits extreme deviation zone
   • Volume spike confirms (bright triangle)
   • Enter on signal

2. **Quick Targets:**
   • Target 1: Return to VWAP (quick scalp)
   • Target 2: Opposite band (if momentum strong)
   • Stop: Beyond extreme deviation

3. **Signal Quality Matters:**
   • Bright triangle + volume spike = BEST
   • Lighter triangle = Still good, but watch volume
   • Tiny triangle = Skip it (no volume confirmation)

4. **Timeframes:**
   • Use on 1m, 5m, or 15m charts
   • Daily VWAP gives you the anchor
   • Scalp the deviations back to fair value

**EXAMPLE SCALP:**
• Price drops to -2σ (oversold)
• Green triangle appears with volume spike
• Enter long, target VWAP
• Quick 10-30 pip scalp
• Out before price reverses

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **PRO SCALPER TIPS**

• Enable "Require Pivot Reversal" for stronger signals (fewer but higher quality)
• Use 2σ minimum deviation (default) - catches meaningful moves
• Volume spike threshold: 1.5x (default) or 2.0x for major moves
• Check top-right info table for current deviation levels
• Combine with price action for confirmation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 **GET THE INDICATOR:**

[Tactical Deviation on TradingView](https://www.tradingview.com/script/81hGcUOY-Tactical-Deviation/)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Why this beats basic VWAP for scalping:**
• Volume confirmation = fewer false signals
• Deviation bands = clear extreme zones
• Visual signals = no math needed
• Multi-timeframe = context without clutter

Start with defaults, then customize as you learn. This is a game-changer for scalpers looking for quick, high-probability setups.

Happy Scalping! 📈⚡"""
]

def send_message(content, delay=0.5):
    """Send a single message to Discord"""
    payload = {
        "content": content,
        "username": "Sniper Guru"
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending message: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False
    finally:
        if delay > 0:
            time.sleep(delay)

def send_to_discord():
    """Send Tactical Deviation scalper announcement to Discord"""
    print(f"Sending {len(MESSAGES)} messages to Discord...")

    success_count = 0
    for i, message in enumerate(MESSAGES, 1):
        print(f"Sending part {i}/{len(MESSAGES)}...")
        if send_message(message, delay=0.5):
            success_count += 1
        else:
            print(f"Failed to send part {i}")

    if success_count == len(MESSAGES):
        print(f"✅ All {len(MESSAGES)} parts sent successfully to Discord!")
    else:
        print(f"⚠️ Sent {success_count}/{len(MESSAGES)} parts")

if __name__ == "__main__":
    send_to_discord()
















