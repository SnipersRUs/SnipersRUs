#!/usr/bin/env python3
"""
Send BTC New Year's Eve Update to Discord webhook as purple embed
"""

import requests
import time
from datetime import datetime, timezone

WEBHOOK_URL = ""

# Purple color for Discord embed (0x9B59B6)
PURPLE_COLOR = 0x9B59B6

# Split message into 3 parts to fit Discord's 4096 character limit per embed
EMBED_1 = """📅 BTC YEAR-END UPDATE - DECEMBER 2025 📅
Price: $87,740 | APPROACHING YEAR END | Critical $88k Test

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 YEAR-END APPROACHING 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ FINAL DAYS OF 2025
- Testing $87.7k-$88k resistance NOW
- Tax loss harvesting window closing soon
- Year-end book closing approaching
- New year = fresh capital incoming
- Volatility expected to increase

📊 What's Happening:
- Bounced from $86k to $87.7k overnight
- Testing descending channel resistance
- Multiple attempts to break $88k
- Low liquidity = big wicks possible
- Institutions preparing for year-end

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 CRITICAL LEVELS (ALL TIMEFRAMES)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 RESISTANCE (Must Break):
$88,000-$88,500 (descending channel top)
$89,000-$89,300 (major resistance zone)
$90,000-$90,600 (psychological + heavy)
$91,200-$91,600 (purple resistance cluster)

🟢 SUPPORT (Critical):
$87,600-$87,700 (TESTING NOW) ⚠️
$86,800-$87,000 (yesterday's low)
$86,000-$86,400 (major support)
$85,100-$85,900 (last line before cascade)
$84,900 (red zone - if breaks = $80k)

⚠️ THE DECISION: $88,000
Break above = $90k+ into 2026
Reject here = retest $86k-$87k

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 MULTI-TF TECHNICAL ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
15m Chart Analysis:
- White/purple trend projection showing path
- Purple box resistance $88k-$90k
- Green support at $87.6k holding
- Red/pink zones $86k, $85.1k, $84.9k below
- White trendline showing potential moves

1h Chart Analysis:
- Multiple descending trendlines (white)
- Red flags at rejection zones
- Green/blue dotted MAs all below price
- Purple support boxes breaking up
- Orange resistance at $88.9k-$89k
- Pink arrows showing projected moves down

Daily Chart Analysis:
- MASSIVE descending channel from ATH
- Multiple dotted resistance zones stacked
- White ascending trendline from lows
- Currently in compression zone
- Green candle forming = bounce attempt
- Orange boxes showing key decision zones
- Red zones $86k, $84.9k critical support

KEY OBSERVATIONS:
- Ascending channel bottom: $85k-$87k
- Descending channel top: $88k-$90k
- SQUEEZE forming = big move coming
- Direction depends on $88k break/reject
- Volume declining = coiling for explosion
- All TFs showing $88k as THE pivot"""

EMBED_2 = """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 TRADING SCENARIOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 SCENARIO A: Break $88k → $90k+ (40%)
Bull breakout toward year end

What Happens:
- Break above $88k with volume
- Short squeeze to $89k-$90k
- Test $91k resistance
- Year-end momentum builds
- Fresh 2026 capital anticipation

🟢 Trade Setup LONG:
📍 Entry: $88,200-$88,800 (on break)
🛑 Stop: $87,200
🎯 Targets: $89.5k / $90.5k / $91.5k
💡 Breakout confirmation needed
✅ Confirm: 1H close > $88.5k + volume

Triggers:
- Clean break above $88k channel
- SPX/NDX rally into year end
- Risk-on sentiment
- January effect anticipation
- Shorts covering positions

📉 SCENARIO B: Reject → $86k Test (35%)
Year-end tax selling pressure

What Happens:
- Fail at $88k resistance (again)
- Drop to $86.8k-$87k
- Possible wick to $86k
- Year-end liquidations
- Books closing for 2025

🔴 Trade Setup SHORT (risky):
📍 Entry: $88,000-$88,500 (on reject)
🛑 Stop: $89,200
🎯 Targets: $87k / $86.5k / $86k
💡 High risk - tight stops
✅ Confirm: Rejection wick + volume

OR BETTER - Wait to LONG:
📍 Entry: $86,000-$86,500 (at support)
🛑 Stop: $85,200
🎯 Targets: $88k / $89k / $91k
💡 Better R/R at support

Triggers:
- Rejection at $88k resistance
- Year-end tax selling
- Book closing activity
- Low liquidity dumps
- SPX/NDX weakness

🤷 SCENARIO C: Chop $87k-$88.5k (25%)
Range grind into year end

What Happens:
- Consolidation continues
- Low conviction
- Waiting for year-end clarity
- Volatile sessions ahead

Strategy:
- Scalp only if experienced
- Better to wait for clear direction
- Preserve capital
- Avoid the noise

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ KEY TIMELINE AHEAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TODAY:
- Market session continues
- Watch $88k test closely
- Volume patterns shifting
- Year-end positioning

THIS WEEK:
- Year-end book closing approaches
- Tax loss harvesting window closing
- Low liquidity periods expected
- Volatility spikes possible

DEC 31 (New Year's Eve):
- FINAL TRADING DAY of 2025
- Books close 4PM EST
- Tax deadline passes
- Last liquidations possible
- Expect WILD moves

JAN 1, 2026:
- FRESH START
- New tax year begins
- Fresh capital potentially enters
- Holiday (markets closed)
- Real direction Jan 2-3"""

EMBED_3 = """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎲 PROBABILITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This Week:
40% → Break $88k, rally to $90k-$91k
35% → Reject at $88k, test $86k-$87k
25% → Chop $87k-$88.5k (wait for year-end)

Year-End → Jan 1:
45% → Rally continues to $90k-$92k
35% → Pullback to $86k-$88k
20% → Range $87k-$89k

Early January (Jan 2-5):
50% → Bullish $90k-$95k (January effect)
30% → Neutral $87k-$92k (range)
20% → Bearish $83k-$87k (if support fails)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📰 MARKET CONTEXT & NEWS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 BEARISH FACTORS:
- Still in descending channel
- December down -9% (brutal)
- Year-end tax selling ongoing
- Books closing for 2025 approaching
- Low liquidity = volatility
- Resistance at $88k-$90k heavy
- Traditional markets mixed
- Year-end profit taking

✅ BULLISH FACTORS:
- Bounced from $86k (held support)
- Tax selling window closing soon
- Fresh 2026 capital incoming
- January historically strongest month
- Ascending support holding $85k-$87k
- Institutions preparing for new year
- Squeeze forming on charts
- DATs accumulated 42k BTC in Dec
- Year-end = new beginnings ahead

📊 KEY DATA POINTS:
- December: -9% (worst since April)
- Current: ~$87.7k vs $126k ATH
- 2025 YTD: Still down ~30%
- Hash rate: -4% (bullish contrarian)
- DAT purchases: +42k BTC (bullish)
- Funding rates: 5% (vs 7.4% avg - neutral)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 TRADING WISDOM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ DO:
- Watch $88k break/reject closely
- Long $88.2k-$88.8k IF clean break
- OR long $86k-$86.5k if we drop
- Use 1-2% position size MAX
- Set tight stops (2-3%)
- Take profits at resistance
- Prepare for year-end volatility
- Position for January trades

❌ DON'T:
- Use large size (year-end chaos)
- Short current levels blindly
- Hold without stops
- FOMO into moves
- Fight the $88k level
- Ignore low liquidity risk
- Revenge trade
- Overtrade during year-end

🎯 BEST STRATEGY:

Option 1 - Aggressive:
1. Current at $87.7k testing $88k
2. IF breaks $88k with volume
3. Long $88.2k-$88.8k
4. Stop $87.2k (tight below)
5. Target $89.5k (30%), $90.5k (40%), $91.5k (30%)
6. Scale out into year-end

Option 2 - Conservative:
1. Wait for $88k rejection OR break
2. If reject → wait for $86k-$86.5k
3. Long $86k-$86.5k (BEST R/R)
4. Stop $85.2k
5. Target $88k / $89k / $91k
6. Hold into January if momentum

Option 3 - Smart Money:
1. Position carefully
2. Preserve capital
3. Wait for clear setups
4. Trade with clarity
5. Better opportunities ahead
6. Avoid year-end noise

⏰ KEY DATES AHEAD:
- Today: Watch $88k test
- This Week: Year-end positioning
- Dec 31: Final trading day 2025
- Jan 1: New Year begins
- Jan 2-3: Real direction emerges

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 KEY RESOURCES & LINKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Live Bitcoin Price:
https://www.coindesk.com/price/bitcoin/

📊 Traditional Markets:
https://finance.yahoo.com/
https://www.bloomberg.com/markets

📊 Crypto News:
https://www.theblock.co/
https://cointelegraph.com/

📊 Economic Calendar:
https://tradingeconomics.com/calendar

📊 Bitcoin Magazine:
https://bitcoinmagazine.com/

📊 On-Chain Metrics:
https://glassnode.com/
https://www.lookintobitcoin.com/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💭 FINAL THOUGHTS 💭

We're approaching the end of 2025. Currently at $87.7k testing $88k channel resistance. Break above = $90k+ rally into year-end and 2026. Reject = possible $86k retest.

Year-end tax selling window closing soon. Books will close for 2025 on Dec 31. January historically the STRONGEST month for Bitcoin.

BEST PLAY: If you're trading, long the $88k breakout OR wait for $86k dip. Position carefully as we approach year-end. Fresh capital coming in 2026.

Manage risk as we head into year-end. Don't hold risky positions without clear stops. 2026 brings new opportunities.

Here's to finishing 2025 strong and an epic 2026! 🚀

May the charts be ever in your favor! 💎🙌

DYOR | NFA | Trade safe! 🎯"""

def send_to_discord():
    """Send BTC New Year's Eve update as purple embeds to Discord (split into 2 messages)"""
    timestamp = datetime.now(timezone.utc).isoformat()

    # First message: Header + Levels + Technical Analysis + Scenarios
    embeds_1 = [
        {
            "title": "📅 BTC YEAR-END UPDATE - DECEMBER 2025 📅",
            "description": EMBED_1,
            "color": PURPLE_COLOR,
            "timestamp": timestamp
        },
        {
            "description": EMBED_2,
            "color": PURPLE_COLOR,
            "timestamp": timestamp
        }
    ]

    # Second message: Probabilities + Context + Wisdom + Final Thoughts
    embeds_2 = [
        {
            "description": EMBED_3,
            "color": PURPLE_COLOR,
            "timestamp": timestamp,
            "footer": {
                "text": "Sniper Guru • Year-End 2025"
            }
        }
    ]

    payload_1 = {
        "embeds": embeds_1,
        "username": "Sniper Guru"
    }

    payload_2 = {
        "embeds": embeds_2,
        "username": "Sniper Guru"
    }

    try:
        # Send first message
        response_1 = requests.post(WEBHOOK_URL, json=payload_1, timeout=15)
        response_1.raise_for_status()
        print("✅ Part 1 sent successfully!")

        # Small delay between messages
        time.sleep(0.5)

        # Send second message
        response_2 = requests.post(WEBHOOK_URL, json=payload_2, timeout=15)
        response_2.raise_for_status()
        print("✅ Part 2 sent successfully!")
        print("✅ BTC New Year's Eve Update sent successfully to Discord!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending to Discord: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

if __name__ == "__main__":
    send_to_discord()
