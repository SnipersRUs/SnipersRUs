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


def send_friday_game_plan():
    """Send FRI NY SESSION GAME PLAN to the specified Discord webhook, splitting if needed."""

    webhook_url = "https://discord.com/api/webhooks/1417680286921134251/qP3_kjOWd3UvXSyv27UXjO7HTzqLx9AhfVlLalkyE3DQrmmKtR99UwE-NGvEu9KIHClO"

    base_message = (
        "FRI NY SESSION GAME PLAN — OCT 24, 2025\n"
        "BTC (all TFs you sent, condensed) • Levels • Entries • Probabilities • Market-moving news\n\n"
        "WHAT PRICE JUST DID (prev session → now)\n"
        "• 5m/15m: Steady grind from ~108k into 111k with a rising intraday trendline; rallies repeatedly capped by the **magenta/white VWAP/AVWAP stack** and prior supply at **111.5k–112.0k**. Buyers defended **110.2k–110.4k** several times (pullback bids held the ascending base).\n"
        "• 1h: Structure = **range-under-resistance**. We're building value under the purple AVWAP from the dump; each tag of **~111.8k** fades unless VWAP turns up and holds.\n"
        "• 1D: Yesterday printed a **higher low** off the channel mid (green bounce), but we're still below the last breakdown cluster **113.6k–114.4k**. Trend not repaired yet—needs acceptance back above that shelf.\n\n"
        "MY BIAS INTO NY\n"
        "• Base case = \"**watching the reset**\": chop with a slight **up-bias** while 110.2k holds, but **no size long** unless 111.8k+ is accepted. Shorts only on clear rejections.\n"
        "• Probabilities (into U.S. close):\n"
        "  – Stop-run squeeze into 112.5k–113.6k then fade: **45%**\n"
        "  – Range 110.2k–111.8k (grind & trap): **35%**\n"
        "  – Breakdown to 109.2k / 108.0k retest: **20%**\n\n"
        "LEVELS THAT MATTER (rounded)\n"
        "• Resistance / upside targets: **111.8k → 112.5k → 113.6k → 114.4k**\n"
        "• Support / buy zones: **110.4k → 110.2k (pivot)** → **109.2k → 108.0k**\n"
        "• Trend risk line (invalidate up-bias): sustained **<107.3k**\n\n"
        "TRADE SETUPS (execute only on trigger; risk 0.5–1.0%)\n"
        "1) **VWAP Reclaim LONG** (confirmation > momentum)\n"
        "   • Trigger: 15m close & hold **>111.8k** with rising delta; quick retest holds above **111.5k**.\n"
        "   • Entry: 111.6–111.9k on the retest\n"
        "   • Invalidation: 111.1k\n"
        "   • TPs: **112.5k → 113.6k → 114.4k** (trail after 113.6k)\n\n"
        "2) **Sweep-and-Lift LONG** (best R:R if we dip first)\n"
        "   • Trigger: Liquidity sweep into **110.2k** (or wicks to **109.8k**) followed by immediate reclaim of **110.4k**.\n"
        "   • Entry: 110.3–110.5k\n"
        "   • Invalidation: 109.7k\n"
        "   • TPs: **111.2k → 111.8k → 112.5k**\n\n"
        "3) **Lower-High FADE** (if VWAP rolls at supply)\n"
        "   • Trigger: Rejection inside **111.8k–112.5k** with momentum divergence / failed retest.\n"
        "   • Entry: ~112.1k\n"
        "   • Invalidation: 112.7k\n"
        "   • TPs: **111.0k → 110.4k → 109.2k** (scale quick)\n\n"
        "EXECUTION NOTES (stern)\n"
        "• Trade the **edges** (reclaims/sweeps), not mid-range.\n"
        "• First partial ≥ **+0.8R**; trail behind last reclaimed VWAP or higher low.\n"
        "• If NY headlines hit during the push, flatten to core and re-evaluate at levels.\n\n"
        "VWAP CYCLE CONTEXT (your 4→9-day view)\n"
        "• We're in the **pre-reset window**: 4-day → day-5 transition often = traps & fake moves.\n"
        "• Real size long usually comes **after** 4-day aligns with the 9-day (late Thu → Fri).\n"
        "• Until the stack turns **bullish together**, treat bounces into **111.8k–112.5k** as fade candidates; treat **110.2k** as the line-in-the-sand for the up-bias.\n\n"
        "WHAT CAN MOVE MARKETS TODAY / THIS WEEK (with sources)\n"
        "• **CPI (Sep) released today 8:30a ET**; October CPI due **Nov 13**. Expect vol around the print and revisions.  [oai_citation:0‡Bureau of Labor Statistics](https://www.bls.gov/schedule/news_release/cpi.htm?utm_source=chatgpt.com)\n"
        "• **FOMC meeting next week (Oct 28–29) with Powell press conference**—positioning flows can cap trends ahead of it.  [oai_citation:1‡Federal Reserve](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm?utm_source=chatgpt.com)\n"
        "• **Digital-asset ETP flows:** Latest CoinShares shows **US$513M outflows** week of Oct 20 (BTC led outflows; ETH/SOL saw inflows). Prior weeks showed **record inflows**—net backdrop still supportive but choppy.  [oai_citation:2‡CoinShares](https://coinshares.com/insights/research-data/fund-flows-20-10-25/?utm_source=chatgpt.com)\n"
        "• **Geopolitics:** Ongoing **Ukraine strikes** and **Gaza ceasefire fragility** = headline risk → quick risk-off spikes possible.  [oai_citation:3‡Reuters](https://www.reuters.com/world/russian-missile-strikes-spark-fires-send-debris-across-ukraines-kyiv-mayor-says-2025-10-22/?utm_source=chatgpt.com)\n"
        "• **General U.S. calendar** (claims, PMIs, home sales) to color macro tone into close.  [oai_citation:4‡Trading Economics](https://tradingeconomics.com/united-states/calendar?utm_source=chatgpt.com)\n\n"
        "BOTTOM LINE\n"
        "We're coiling under **111.8k–112.5k** with buyers defending **110.2k**. I'll **join strength** on a clean 111.8k reclaim toward **113.6k/114.4k**; otherwise I'll **fade the lower-high** back toward **110.4k/109.2k**. Size up **after** the VWAP stack flips in sync—until then, patience and precision."
    )

    def build_prefix(i: int) -> str:
        header = "**FRI NY SESSION GAME PLAN — OCT 24, 2025**\n" if i == 1 else "**FRI NY SESSION GAME PLAN (cont.)**\n"
        mention = "@everyone\n" if i == 1 else ""
        return mention + header

    messages = split_message_with_prefix(base_message, build_prefix, 2000)

    print("📣 Sending Friday NY Session Game Plan to Discord...")
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
    send_friday_game_plan()














