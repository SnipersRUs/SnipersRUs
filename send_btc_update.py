#!/usr/bin/env python3
"""
Send BTC Mega Update to Discord webhook (split into multiple messages)
"""

import requests
import time

WEBHOOK_URL = ""

MESSAGES = [
    """@everyone. 🚨 BTC MEGA UPDATE - DEC 3, 2025 🚨

Price: $92,900 | 24H: +6.8% | From $81k Low: +14.5%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ VANGUARD GAME CHANGER ⚡

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 VANGUARD REVERSED CRYPTO BAN

- $11 TRILLION AUM now accessible
- 50M+ investors can buy BTC ETFs
- BlackRock IBIT: $1.8B volume in 2 hours
- BTC pumped 6% instantly on news
- Even 0.5% allocation = $55B inflows

📊 THE CATALYST:

New CEO Salim Ramji (ex-BlackRock IBIT)
Allows trading of BTC, ETH, XRP, SOL ETFs
From BlackRock, Fidelity, Grayscale, VanEck

💎 THIS IS INSTITUTIONAL FOMO""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 CRITICAL LEVELS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 RESISTANCE (Major):

$93,000-$94,000 (monthly golden pocket top)
$94,500-$95,000 (breakout level)
$96,000-$99,000 (heavy resistance)
$100,000 (MEGA psychological)
$104,000+ (next targets)

🟢 SUPPORT (Critical):

$92,000 (immediate)
$90,000-$91,000 (reclaimed support)
$88,000-$89,000 (secondary)
$86,000 (if rejection happens)
$81,000 (channel support - HELD ✅)

⚠️ THE DECISION ZONE: $92k-$94k

Break above = $96k-$100k possible
Reject here = $88k-$90k retest""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 BEST TRADES RIGHT NOW

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 LONG #1: Vanguard Continuation (55%)

📍 Entry: $92,000-$92,800 (NOW)
🛑 Stop: $90,500
🎯 Targets: $94.5k / $96.5k / $99.5k
💡 Institutional FOMO play
✅ Confirm: 4H close > $93k

🟢 LONG #2: Breakout (65%)

📍 Entry: $94,200-$94,800 (on break)
🛑 Stop: $92,000
🎯 Targets: $96.5k / $99k / $102k+
💡 Short squeeze above $93k likely
✅ Confirm: 1H close > $94.5k + volume

🔴 SHORT: Monthly Top (45%)

📍 Entry: $93,800-$94,500
🛑 Stop: $95,800
🎯 Targets: $91k / $88.5k / $86k
💡 Golden pocket rejection play
✅ Confirm: Wick at $94-95k + 4H < $92k""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎲 PROBABILITIES

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next 48-72 Hours:

50% → Breakout to $96k-$100k
     (Vanguard FOMO + Fed cut expectations)

30% → Rejection to $88k-$90k
     (Monthly top + December weakness)

20% → Chop $90k-$94k
     (Consolidation before Fed)

This Week:

45% → Rally holds, test $96k-$99k
35% → Pullback to $88k-$91k
20% → Range $90k-$94k

After Fed (Dec 10):

60% → Rate cut = pump to $100k-$105k
25% → No cut = dump to $85k-$88k
15% → Mixed reaction = chop $90k-$96k""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 CRITICAL EVENTS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 TODAY (Tue Dec 3):
- Vanguard news digesting
- Testing $92k-$94k resistance
- Institutional flows continuing

📌 THIS WEEK (Dec 4-8):
- Dec 4 = key pivot day
- Watch for $94k breakout
- Markets positioning for Fed

📌 NEXT WEEK - THE BIG ONE:

🚨 FED FOMC MEETING DEC 9-10 🚨

- 80% probability of 25bp rate cut
- Goldman: "Jobs report sealed Dec cut"
- NY Fed Williams basically confirmed it
- Announcement: Dec 10, 2PM EST

IF CUT (80%):
→ BTC pumps to $96k-$102k
→ Risk-on across markets
→ Weaker dollar = bullish crypto

IF NO CUT (20%):
→ BTC dumps to $86k-$88k
→ Risk-off panic
→ Volatility spikes""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📰 MARKET SENTIMENT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 MASSIVELY BULLISH:

- Vanguard $11T unlock = GAME CHANGER
- $1.8B IBIT volume in 2 hours
- BTC reclaimed $90k-$92k ✅
- Channel support held at $81k ✅
- Fed rate cut 80% likely
- Broad crypto rally (+3-12% sectors)
- ETH back above $3k
- Short squeeze setup above $93k
- Institutional FOMO starting
- Q1 2026 could mirror 2019 rally

⚠️ STILL BEARISH:

- Fear & Greed: 28 (Fear)
- Down 25% from $126k ATH
- December historically weak (-3.2% median)
- When Nov red, Dec ALWAYS red (since 2013)
- $1B liquidations Monday
- 37% green days last 30 days
- Fed divided (many want no cut)
- Powell: "Dec cut not foregone conclusion"
- Trump crypto assets down 90%+

🎯 KEY STATS:

- From $81k low: +14.5% in 48h
- Vanguard allocation: 0.5% = $55B
- Fed cut odds: 80% (was 35% last week)
- December pivot: Dec 4th
- FOMC decision: Dec 10, 2PM EST""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 KEY LINKS & RESOURCES

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Vanguard News:
https://coinpedia.org/news/why-crypto-is-up-today-live-updates-on-dec-3-2025/

📊 Market Updates:
https://cryptonews.com/news/live-crypto-news-today-latest-updates-for-dec-03-2025/

📊 Fed Decision:
https://fortune.com/2025/11/24/stocks-fed-interest-rate-cut-december/
https://us.plus500.com/en/newsandmarketinsights/fed-december-2025-meeting

📊 December Analysis:
https://www.newsbtc.com/bitcoin-news/december-bitcoin-roadmap-signals-you-cant-ignore/

📊 Historical Data:
https://www.fool.com/investing/2025/11/30/heres-what-history-says-to-expect-for-bitcoin-in-d/

📊 Live Prices:
https://www.coindesk.com/
https://www.theblock.co/

📊 Fed Calendar:
https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm""",

    """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 TRADING WISDOM

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ DO:

- Long dips to $92k-$92.5k (best R/R)
- Set alerts for $94k breakout
- Take profits at resistance ($94k-$96k)
- Use 2-3% position sizes
- Scale into positions (don't FOMO)
- Watch for Fed commentary
- Close risky positions before Dec 10
- Prepare for volatility

❌ DON'T:

- Chase above $94k without confirmation
- Short the reclaimed $90k-$92k support
- Use large size before Fed decision
- Ignore the monthly golden pocket
- FOMO into random wicks
- Fight the Vanguard momentum
- Forget December history
- Overleverage""",

    """🎯 BEST STRATEGY:

1. Current levels $92k-$92.8k = LONG zone
2. Stop below $90.5k (tight)
3. First target $94.5k (take 30%)
4. If break $94.5k, hold for $96k-$99k
5. If reject at $94k, close and wait
6. Reduce exposure before Fed Dec 10
7. Trade the Fed reaction (not anticipation)

⏰ KEY TIMES TO WATCH:

- Dec 4: Next pivot day
- Dec 9-10: Fed blackout period
- Dec 10, 2PM EST: Fed announcement
- Dec 10, 2:30PM EST: Powell presser

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ BOTTOM LINE ⚡

This Vanguard news is a GAME CHANGER. $11T in assets can now access crypto. We saw $1.8B in IBIT volume in 2 HOURS. BTC pumped 6% instantly. This is the institutional FOMO we've been waiting for.

We're at $92.9k testing the monthly golden pocket top. Break above $94k with volume = $96k-$100k incoming. Reject here = $88k-$90k retest.

The Fed decision next week (80% cut odds) will be THE catalyst. Rate cut = moon. No cut = pain.

BEST PLAY: Long $92k-$92.8k with $90.5k stop, targets $94.5k/$96.5k/$99.5k. Take profits along the way. Reduce risk before Fed Dec 10.

The bottom is IN at $81k. Channel held. Now we're bouncing. This is the opportunity.

DYOR | NFA | Stack sats fam! 💎🙌🚀"""
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
    """Send all BTC update messages to Discord"""
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
