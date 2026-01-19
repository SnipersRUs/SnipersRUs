import requests
import json

webhook_url = "https://discord.com/api/webhooks/1363315528831340787/KfoIJA6G1eEYjegzgrkgZ2qtDaaHL1hrs-ocU00wajpAdNsejWOm5HTvsmCYyrF9jOgr"

embed = {
    "title": "🎯 Sniper Mini VWAP - Major Update: ORB Strategy Added!",
    "description": "The Sniper Mini VWAP indicator just got a major upgrade with multi-session ORB (Opening Range Breakout) strategy!",
    "color": 0x00FF00,  # Green color
    "fields": [
        {
            "name": "📊 What is ORB? (For Beginners)",
            "value": "**Opening Range Breakout (ORB)** is a trading strategy that identifies the high and low of a specific time period (usually the first 30-60 minutes of a trading session).\n\n"
                    "• The **ORB High** and **ORB Low** form a trading range\n"
                    "• When price **breaks above** the high → potential bullish move\n"
                    "• When price **breaks below** the low → potential bearish move\n"
                    "• The range acts as **support/resistance** for the rest of the day",
            "inline": False
        },
        {
            "name": "🚀 What's New",
            "value": "**Multi-Session ORB System:**\n"
                    "✅ Automatically calculates ORB for all 4 major forex sessions\n"
                    "✅ 24-hour ORB boxes for full-day visibility\n"
                    "✅ Shows up to 4 days of ORB history\n"
                    "✅ Session colors: Cyan (Sydney), Blue (Tokyo), Yellow (London), Orange (NY)\n\n"
                    "**Enhanced VWAP Display:**\n"
                    "✅ Thin cross-style lines (cleaner chart)\n"
                    "✅ Updated colors: Neon Green (1H), Neon Yellow (4H), Magenta (8H), Red (Daily)\n\n"
                    "**Simplified Signals:**\n"
                    "✅ Green circle = Buy (price breaks above ORB high)\n"
                    "✅ Purple circle = Sell (price breaks below ORB low)\n"
                    "✅ Only major breakouts - no clutter!",
            "inline": False
        },
        {
            "name": "💡 How to Use VWAP + ORB Together",
            "value": "**Step 1: Use Mini VWAPs for Direction & Trend**\n"
                    "• Price above Daily VWAP = **Bullish bias**\n"
                    "• Price below Daily VWAP = **Bearish bias**\n"
                    "• Stacked VWAPs (1H > 4H > Daily) = **Strong bullish trend**\n"
                    "• Stacked down (1H < 4H < Daily) = **Strong bearish trend**\n\n"
                    "**Step 2: Use ORB for Entry Timing**\n"
                    "• **Bullish setup:** If VWAPs show bullish bias → wait for price to break **above** an ORB high (green signal)\n"
                    "• **Bearish setup:** If VWAPs show bearish bias → wait for price to break **below** an ORB low (purple signal)\n"
                    "• **Key:** ORB boxes extend for 24 hours, so you can see when price comes back into the range for potential trades\n\n"
                    "**The Strategy:**\n"
                    "1️⃣ Determine direction using VWAP alignment\n"
                    "2️⃣ Wait for ORB breakout signal in that direction\n"
                    "3️⃣ Enter on the breakout\n"
                    "4️⃣ Watch for price returning to ORB range for additional opportunities",
            "inline": False
        },
        {
            "name": "📚 Get the Indicator",
            "value": "[**Download Sniper Mini VWAP on TradingView**](https://www.tradingview.com/script/krDAvdXq-Sniper-Mini-VWAP/)\n\n"
                    "🔗 [Open in TradingView](https://www.tradingview.com/script/krDAvdXq-Sniper-Mini-VWAP/)",
            "inline": False
        },
        {
            "name": "🎥 More Info Coming Soon",
            "value": "**Ricky Spanish** will be releasing a detailed video tutorial soon explaining:\n"
                    "• Advanced ORB trading strategies\n"
                    "• How to combine VWAP trend analysis with ORB entries\n"
                    "• Real trade examples\n"
                    "• Best practices for crypto trading\n\n"
                    "Stay tuned for the full walkthrough! 👀",
            "inline": False
        }
    ],
    "footer": {
        "text": "Sniper Mini VWAP - Enhanced with Multi-Session ORB Strategy"
    },
    "timestamp": None
}

payload = {
    "embeds": [embed]
}

response = requests.post(webhook_url, json=payload)

if response.status_code == 204:
    print("✅ Discord announcement sent successfully!")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)







