#!/usr/bin/env python3
"""
Send BTC Rejection Update to Discord webhook (split into multiple messages)
"""

import requests
import time

WEBHOOK_URL = "https://discord.com/api/webhooks/1417680286921134251/qP3_kjOWd3UvXSyv27UXjO7HTzqLx9AhfVlLalkyE3DQrmmKtR99UwE-NGvEu9KIHClO"

MESSAGES = [
    """@everyone. 🚨 BTC REJECTION UPDATE - DEC 5, 2025 🚨

Price: $92,167 → Rejected from $94k | Down from $126k ATH

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ REJECTION IN PROGRESS ⚠️

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Failed to hold $93k-$94k resistance
- Lower highs forming: $94.6k → $93.1k → $92.6k
- Currently testing $90k-$92k support
- Descending channel still intact
- Vanguard pump FADED completely
- December weakness playing out

📊 Current Status:

- Rejection at monthly golden pocket top
- Testing critical support $90k-$92k
- Next support: $88k-$89k
- Major support: $85k-$86k (channel)
- Break $90k = cascade to $85k likely""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 CRITICAL LEVELS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 RESISTANCE (Heavy):

$92,500-$93,000 (immediate rejection zone)
$94,000-$95,000 (major resistance)
$96,000-$98,000 (need to reclaim for bull)
$100,000 (psychological - forget it for now)

🟢 SUPPORT (Critical):

$90,000-$91,000 (testing NOW) ⚠️
$88,000-$89,000 (major support)
$85,000-$86,000 (channel support - CRITICAL)
$81,000-$83,000 (if channel breaks = RIP)

⚠️ THE LINE: $90,000

Hold above = possible bounce to $94k
Break below = cascade to $85k-$88k""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 BEST TRADES RIGHT NOW

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 SHORT #1: Rejection (55% - ACTIVE)

📍 Entry: $91,500-$92,500 (NOW)
🛑 Stop: $93,800
🎯 Targets: $89.5k / $87k / $85k
💡 Lower highs = bearish momentum
✅ Confirm: 4H close < $91k

🟢 LONG #1: Support Bounce (60%)

📍 Entry: $88,500-$89,500 (on drop)
🛑 Stop: $87,200
🎯 Targets: $91k / $93k / $95k
💡 Major support zone
✅ Confirm: Volume spike + 1H > $89.5k

🟢 LONG #2: Channel Support (70% IF hit)

📍 Entry: $85,000-$86,500 (capitulation)
🛑 Stop: $83,500
🎯 Targets: $89k / $92k / $95k+
💡 Absolute bottom - max R/R
✅ Confirm: Massive volume + daily > $86k""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎲 PROBABILITIES

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next 48 Hours:

45% → Breakdown to $86k-$88k
     (Lower highs + Dec weakness)

35% → Bounce to $94k-$96k
     (Oversold + BlackRock buying)

20% → Chop $89k-$93k
     (Waiting for Fed clarity)

After Fed (Dec 10):

IF CUT (22-80% odds - DIVIDED):
→ 60% pump to $95k-$100k+
→ Risk-on rally

IF NO CUT (20-78% odds):
→ 40% dump to $85k-$88k
→ Liquidation cascade

Directional Bias:

- Short-term: Bearish (60/40)
- Into Fed: Neutral (50/50)
- After Fed: Depends on decision""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 CRITICAL EVENTS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 TODAY-TOMORROW (Thu-Fri):
- Testing $90k-$92k support
- Low volume expected
- Weekend uncertainty ahead

📌 THIS WEEKEND:
- Thin liquidity = big wicks possible
- $90k must hold
- Asia session critical

📌 NEXT WEEK - THE CATALYST:

🚨 FED FOMC MEETING DEC 9-10 🚨

- Fed Blackout: Nov 29 - Dec 11
- Decision: Dec 10, 2PM EST
- Powell Press: Dec 10, 2:30PM EST
- SEP + DOT PLOT update (projection meeting)

RATE CUT ODDS:

- FactSet economists: 22% (down from 97%)
- CME FedWatch: 41% odds
- Some indicators: 80% odds
- REALITY: Fed is DIVIDED

IF CUT:
→ BTC to $95k-$100k
→ Risk-on across markets
→ Weaker dollar

IF NO CUT:
→ BTC to $85k-$88k
→ Risk-off panic
→ Liquidation cascade""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📰 MARKET SENTIMENT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 BEARISH SIGNALS:

- Down 30% from $126k ATH
- Lower highs on all timeframes
- Below all major MAs (50/100/200-day)
- December historically weak (-3.2% median)
- November: -$3.48B ETF outflows
- Fed divided (22-41% cut odds)
- $787B leveraged positions at risk
- Crypto broad pullback today
- Vanguard pump completely faded
- PayFi -4%, XRP -4.37%, ETH < $3.2k
- Momentum turning bearish

✅ BULLISH SIGNALS:

- BlackRock still accumulating
- Sovereign funds buying dip (Larry Fink)
- Extremely oversold on lower TFs
- Channel support at $85k-$86k held at $81k
- Historical mid-cycle correction (normal)
- Some indicators show 80% Fed cut odds
- Bottom may be forming (Nasdaq correlation)
- Analysts target $112k-$116k IF ETF flows resume
- Long-term bulls unfazed

🎯 KEY STATS:

- Current: $92,167
- 24H change: -1.06%
- From $126k ATH: -27%
- From $81k low: +13.8%
- Fed cut odds: 22-80% (DIVIDED)
- ETF Nov outflows: -$3.48B
- Leverage outstanding: $787B""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 KEY LINKS & RESOURCES

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Live Updates:
https://cryptonews.com/news/live-crypto-news-today-latest-updates-for-dec-05-2025-bitcoin-breaks-under-93k-as-payfi-and-defi-lead-market-declines/

📊 Fed Meeting Details:
https://us.plus500.com/en/newsandmarketinsights/fed-december-2025-meeting

📊 Fed Calendar:
https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm

📊 FOMC Minutes:
https://www.federalreserve.gov/monetarypolicy/fomcminutes20251029.htm

📊 Fed Cut Odds:
https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html

📊 Market Analysis:
https://beincrypto.com/bitcoin-price-outlook-december-2025/

📊 Historical Data:
https://www.cnbc.com/2025/12/04/bitcoin-down-nearly-30percent-from-record-high-history-shows-thats-normal.html

📊 Bloomberg Coverage:
https://www.bloomberg.com/news/articles/2025-12-01/bitcoin-btc-slides-to-below-88-000-in-risk-off-start-to-december

📊 Live Prices:
https://www.coindesk.com/""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 TRADING WISDOM

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DO:

- Short the rejection at $91.5k-$92.5k
- Set tight stops above $93.8k
- Take profits at $89k (resistance becomes support)
- Wait for $88.5k-$89.5k to long
- OR wait for $85k-$86k (best R/R)
- Use 2-3% position sizes MAX
- Close risky positions before Fed Dec 10
- Prepare for volatility

❌ DON'T:

- Long current levels without confirmation
- Chase breakdown without stops
- Use large size before Fed decision
- Fight the lower high pattern
- Ignore the $90k breakdown risk
- FOMO into positions
- Revenge trade
- Forget Fed is Dec 10 (5 days away)""",

    """🎯 BEST STRATEGY:

1. If short from $91.5k-$92.5k (like now)
2. Target $89k first (take 30%)
3. Hold for $87k (take 40%)
4. Let rest run to $85k
5. If we break $90k, momentum down
6. Flip long at $88.5k-$89.5k OR $85k-$86k
7. Close EVERYTHING before Fed Dec 10
8. Trade Fed reaction (not anticipation)

⏰ KEY TIMES:

- This weekend: Low liquidity, big wicks
- Monday Dec 9: Last day before Fed
- Tuesday Dec 10, 2PM EST: Fed decision
- Tuesday Dec 10, 2:30PM EST: Powell
- Watch for immediate reaction 2-4PM

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ BOTTOM LINE ⚡

The Vanguard pump is OVER. We got rejected at the monthly golden pocket top ($92k-$94k) just like Discord analysts called. We're now forming LOWER HIGHS which is bearish AF.

The $90k level is THE line in the sand. Hold above = possible bounce to $94k. Break below = cascade to $85k-$88k.

Fed decision Dec 10 is EVERYTHING. Cut odds range from 22% to 80% depending on who you ask - the Fed is DIVIDED. This means VOLATILITY.

BEST PLAY: Short this rejection at $91.5k-$92.5k with $93.8k stop, target $87k-$89k. Then flip long at $88.5k OR wait for $85k-$86k channel support.

This is NOT the time to be a hero. Reduce size, take profits, and prepare for the Fed. The next 5 days will decide if we rally to $100k or dump to $80k.

DYOR | NFA | Trade safe fam! ⚠️🎯"""
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
    """Send all BTC rejection update messages to Discord"""
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
















