import requests
import json
import time


def split_message_with_prefix(content: str, prefix_builder, max_len: int = 2000):
    """Split content into parts ensuring each final message (prefix + body) <= max_len."""
    parts = []
    idx = 1
    start = 0
    n = len(content)
    while start < n:
        prefix = prefix_builder(idx)
        room = max_len - len(prefix)
        if room <= 0:
            raise ValueError("Prefix too long for Discord limit")
        end = min(n, start + room)
        # prefer splitting on a newline within room
        cut = content.rfind("\n", start, end)
        if cut == -1 or cut <= start + int(room*0.5):
            cut = end
        part = content[start:cut].rstrip("\n")
        parts.append(prefix + part)
        start = cut
        # skip leading newlines
        while start < n and content[start] == "\n":
            start += 1
        idx += 1
    return parts


def send_monday_outlook():
    """Send MONDAY NY SESSION OUTLOOK to the specified Discord webhook, splitting if needed."""

    webhook_url = ""

    base_message = (
        "MONDAY NY SESSION OUTLOOK — OCT 20, 2025\n"
        "BTC WEEK PLAN • LEVELS • ENTRIES • PROBABILITIES • NEWS\n\n"
        "MARKET CONTEXT\n"
        "BTC flushed hard last week, tagged deep liquidity (~105k) then ripped a sharp reversal back above 110k. We’re now sitting under major confluence around 111k–112k (prior range support turned resistance + VWAP stack overhead). Daily and 4H structure still bullish as long as we stay above 108k–109k. Market is transitioning from “panic sell” to “retest the breakdown zone.”\n\n"
        "This week is LOADED with catalysts — so expect volatility, trap moves, and fake breakouts.\n\n"
        "──────────────────────────────\n"
        "🗓️ KEY EVENTS THIS WEEK\n"
        "• Mon: No major US data – positioning day\n"
        "• Tue: Existing Home Sales (minor), Fed speakers\n"
        "• Wed: **FOMC Rate Decision + Powell Press Conference** (HIGH VOL)\n"
        "• Thu: GDP (Q3 Advanced) + Jobless Claims\n"
        "• Fri: Core PCE (Fed’s #1 inflation metric)\n\n"
        "Earnings: Tesla, Meta, IBM, Intel – Tech earnings can drive risk assets.\n"
        "Geopolitics: \n"
        "– Middle East ceasefire talks still unstable.\n"
        "– Ukraine energy infrastructure strikes ongoing.\n"
        "– Oil slightly elevated → inflation risk.\n\n"
        "Global risk: Neutral-to-cautious. No meltdown, but nobody is relaxed.\n\n"
        "──────────────────────────────\n"
        "₿ BTC STRUCTURE (ALL TFs IN ONE READ)\n"
        "• Daily: Still in uptrend channel. Pullback tested midline & bounced.\n"
        "• 4H: Higher low formed at 105k. Now retesting the underside of broken structure (111–112k).\n"
        "• 1H: VWAP turning up, but price is fighting resistance. Needs breakout + acceptance above 111.5k to open bullish continuation.\n"
        "• 10m/15m: Choppy neutral. Approaching decision point.\n\n"
        "This is a classic “compression under resistance” — market deciding if this bounce is real or just a dead cat.\n\n"
        "──────────────────────────────\n"
        "🔥 PROBABILITIES (MON-WED PRE-FOMC)\n"
        "• Squeeze higher into resistance / stop shorts: 45%\n"
        "• Range chop 108k–112k: 35%\n"
        "• Deeper pullback into 105k–107k: 20%\n\n"
        "*After FOMC, probabilities may flip hard depending on Powell.*\n\n"
        "──────────────────────────────\n"
        "🎯 LEVELS THAT MATTER\n"
        "MAJOR RESISTANCE / TARGETS\n"
        "• 111,200 – first rejection zone (current ceiling)\n"
        "• 112,500 – key breakdown origin\n"
        "• 114,000–115,000 – major liquidity\n"
        "• 117,000+ – high momentum breakout zones\n\n"
        "SUPPORT / BUY ZONES\n"
        "• 109,000 – intraday VWAP support (must HOLD)\n"
        "• 107,500 – previous pivot / mid-range\n"
        "• 105,500 – liquidation shelf / demand\n"
        "• 103,000 – last strong buyer zone\n"
        "• 99,800 – ultimate swing long level (guarded by whales)\n\n"
        "──────────────────────────────\n"
        "✅ GAME PLAN & ENTRIES\n\n"
        "1) BULLISH CONTINUATION LONG (most likely if VWAP holds)\n"
        "   Trigger: Reclaim + hold above 111.5k with volume\n"
        "   Entry: 111.6–112.0k on retest\n"
        "   Stop: 110.7k\n"
        "   Targets: 113.5k → 115k → trail to 117k\n\n"
        "2) RANGE FADE LONG (best R:R)\n"
        "   Trigger: Reject top, flush down to 108–109k zone, strong bounce\n"
        "   Entry: 108.5–109k\n"
        "   Stop: 107.9k\n"
        "   Targets: 111k → 113k\n\n"
        "3) LOWER-HIGH SHORT (if we fail again at 112k)\n"
        "   Trigger: 112k rejection + VWAP roll\n"
        "   Entry: 111.8k\n"
        "   Stop: 112.6k\n"
        "   Targets: 110k → 108.5k → 107k\n\n"
        "4) DEEP DUMP SWING LONG (only if panic)\n"
        "   Trigger: fast move into 105–106k with wick + bounce\n"
        "   Entry: 105.5k\n"
        "   Stop: 104.8k\n"
        "   Targets: 109k → 112k → 115k\n"
        "   (This is the buy-the-fear setup)\n\n"
        "──────────────────────────────\n"
        "📈 ETH & SOL QUICK READ\n"
        "• ETH: Sitting under 3.2k resistance | Needs reclaim 3.25k → 3.4k | Lose 3.05k = deeper pullback\n"
        "• SOL: Strong relative strength | Above 180 = bullish | Reclaim 190 → 200+ quickly | Lose 175 = caution\n\n"
        "──────────────────────────────\n"
        "⚠️ REMINDER: FOMC WEEK = FAKE MOVES\n"
        "• Early week = positioning / traps\n"
        "• Wednesday = fireworks\n"
        "• Best trades = after Powell clarity\n"
        "• DO NOT swing blindly into Wednesday\n\n"
        "──────────────────────────────\n"
        "🧠 MINDSET FOR THE WEEK\n"
        "• Be patient. This is a waiting game.\n"
        "• Let price show acceptance, then act.\n"
        "• This week separates disciplined traders from gamblers.\n"
        "• Trade VWAPs, structure, and liquidity — not feelings.\n\n"
        "──────────────────────────────\n"
        "Indicators: https://snipersrus.github.io/SnipersRUs/\n\n"
        "──────────────────────────────\n"
        "✅ BOTTOM LINE\n"
        "We are at the decision point.\n"
        "Hold 109k and reclaim 112k → next leg to 115k/117k.\n"
        "Lose 109k and accept under 107.5k → 105k test coming.\n\n"
        "Let NY session show intent… then strike with precision.\n\n"
        "Patience = Profit.\n"
        "Snipers only.  @everyone"
    )

    def build_prefix(i: int) -> str:
        header = "**MONDAY NY SESSION OUTLOOK — OCT 20, 2025**\n" if i == 1 else "**MONDAY NY SESSION OUTLOOK (cont.)**\n"
        mention = "@everyone\n" if i == 1 else ""
        return mention + header

    messages = split_message_with_prefix(base_message, build_prefix, 2000)

    print("📣 Sending Monday NY Session Outlook to Discord...")
    for idx, content in enumerate(messages, start=1):
        payload = {"content": content, "username": "Sniper Guru"}
        try:
            resp = requests.post(webhook_url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=15)
            resp.raise_for_status()
            print(f"✅ Sent part {idx}/{len(messages)} | {len(content)} chars")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed sending part {idx}: {e} | {resp.text if 'resp' in locals() else ''}")
            break
        time.sleep(1.2)


if __name__ == "__main__":
    send_monday_outlook()
