#!/usr/bin/env python3
"""
Send one-time announcement about PivotX Scanner Bot
"""

import requests
from datetime import datetime, timezone

WEBHOOK_URL = "https://discord.com/api/webhooks/1450009873734434867/2-sSMgoMU0mwWoZfe-RVX6Vamp7NNjPK74lSOwYi2nOqP9N_6YLFJe6bGOttz1Eydjie"
PIVOTX_INDICATOR_LINK = "https://www.tradingview.com/script/BQXcICYn-PivotX/"

def send_bot_announcement():
    """Send Discord announcement about PivotX Scanner Bot"""

    embed = {
        "title": "🤖 PivotX Scanner Bot - Now Live!",
        "description": (
            "**Automated Pivot Detection & Setup Scanner**\n\n"
            "## 🎯 What It Does\n\n"
            "The PivotX Scanner Bot automatically scans the crypto markets to find the best pivot-based trading setups using the **PivotX Pro** indicator logic.\n\n"
            "**Key Features:**\n"
            "• Scans **5m, 15m, and 1H** timeframes\n"
            "• Focuses on **BTC, SOL, SUI** + top 100 cryptos\n"
            "• Detects **pivot highs and lows** using ATR-based dynamic detection\n"
            "• Identifies **pullback setups** (price retracing to pivot zones)\n"
            "• Maintains **watchlist of 3-4 best setups**\n"
            "• Sends **Discord alerts** for high-quality opportunities\n\n"
            "## 📊 How It Uses PivotX Indicator\n\n"
            "The bot implements the same pivot detection logic from **PivotX Pro**:\n\n"
            "**1. Dynamic Pivot Detection**\n"
            "• Uses ATR (Average True Range) to calculate pivot strength\n"
            "• Adapts to market volatility automatically\n"
            "• Timeframe-adaptive: stricter on lower TFs, looser on higher TFs\n\n"
            "**2. Pivot Quality Rating**\n"
            "• **A+ Quality**: 1H pivots (best for swing trades)\n"
            "• **A Quality**: 15m pivots (good for day trading)\n"
            "• **B Quality**: 5m pivots (quick scalps)\n\n"
            "**3. Setup Detection**\n"
            "• **Pullback Setups**: Price retracing to pivot zone (±30% ATR)\n"
            "• **Confirmed Pivots**: Price closed beyond ATR threshold\n"
            "• **Stop Placement**: Below pivot low (LONG) or above pivot high (SHORT)\n\n"
            "**4. Scoring System**\n"
            "• Quality bonus (A+ = 100, A = 50, B = 25)\n"
            "• Confirmed pivot bonus (+30)\n"
            "• Pullback bonus (+40, minus distance)\n"
            "• Priority coin bonus (+20)\n\n"
            "## 🚀 What You Get\n\n"
            "**Discord Cards Include:**\n"
            "✅ Pivot type (HIGH/LOW) and exact price\n"
            "✅ Timeframe and quality rating\n"
            "✅ Current price and distance to pivot\n"
            "✅ Stop loss placement recommendation\n"
            "✅ Entry zone and targets (TP1, TP2)\n"
            "✅ Direct TradingView chart link\n\n"
            "**Watchlist Summary:**\n"
            "• Updated every 5 minutes\n"
            "• Shows top 3-4 setups with highest scores\n"
            "• Includes all key information at a glance\n\n"
            "## ⚙️ How It Works\n\n"
            "1. **Scans** 50+ symbols every 5 minutes\n"
            "2. **Detects** pivots using PivotX Pro logic\n"
            "3. **Evaluates** each pivot for pullback potential\n"
            "4. **Scores** setups based on quality and confirmation\n"
            "5. **Sends** Discord alerts for setups scoring >80\n"
            "6. **Maintains** watchlist of best opportunities\n\n"
            "## 💡 Trading Strategy\n\n"
            "**Entry:** When price pulls back to pivot zone\n"
            "**Stop Loss:** Below pivot low (LONG) or above pivot high (SHORT)\n"
            "**Targets:** TP1 at 2%, TP2 at 5% from pivot\n"
            "**Best Setups:** 1H pivots (A+ quality) for swing trades\n\n"
            f"**[📊 View PivotX Pro Indicator]({PIVOTX_INDICATOR_LINK})**\n\n"
            "---\n"
            "**Bot Status:** ✅ Running | **Scan Interval:** 5 minutes | **Exchange:** Coinbase"
        ),
        "color": 0x9B59B6,  # Purple
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "PivotX Scanner Bot • Powered by PivotX Pro Indicator"
        },
        "url": PIVOTX_INDICATOR_LINK
    }

    try:
        payload = {"embeds": [embed]}
        response = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        response.raise_for_status()
        print("✅ PivotX Scanner Bot announcement sent successfully!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending announcement: {e}")
        return False

if __name__ == "__main__":
    send_bot_announcement()


