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


def send_weekly_session_plan():
    """Send WEEKLY & NY SESSION PLAN to the specified Discord webhook, splitting if needed."""

    webhook_url = ""

    base_message = (
        "WEEKLY & NY SESSION PLAN — BTC (as of Oct 27, 2025)\n\n"
        "STRUCTURE SNAPSHOT (all TFs you sent, condensed)\n"
        "• Intraday (10–30m): Pullback from 116.3k peak found bids into the stacked VWAP/MA cluster at 113.7k → 113.4k; first bounce holding 114.2k–114.4k. Momentum neutral, VWAP slightly down but flattening.\n"
        "• 1–4h: Trend = recovery channel from the mid-Oct flush; price is back inside the prior range. Overhead supply sits 115.8k–116.3k (recent high + anchored flows). Support ladder 113.7k → 113.4k → 112.15k (dotted shelf).\n"
        "• 1D: Still within the broad rising regression rails. Bulls need acceptance >115.8k/116.3k to repair structure; loses <112.15k opens 110.2k/109.6k.\n\n"
        "BIASES INTO TOMORROW'S NY\n"
        "• Base case: range-then-resolve around 113.7k–115.8k while macro events line up mid-week.\n"
        "• Directional edge: modest up-bias ONLY if 114.4k holds as intraday base; otherwise expect mean-revert into 113.7k/112.15k before any new push.\n\n"
        "KEY LEVELS (rounded)\n"
        "• Resistance/targets: 115.8k → 116.3k → 118.0k\n"
        "• Supports: 114.4k (intraday pivot) → 113.7k (VWAP/MA stack) → 112.15k (range shelf) → 110.2k\n"
        "• Invalidation for bullish continuation: sustained <112.15k\n\n"
        "TRADE SETUPS (tight risk, size only on confirmation)\n"
        "1) Reclaim-and-Go LONG\n"
        "   • Trigger: 15–30m close >115.0k, retest holds ≥114.8k with rising delta.\n"
        "   • Entry: 114.9k–115.1k   • Invalidation: 114.4k\n"
        "   • TPs: 115.8k → 116.3k (trail) → 118.0k\n\n"
        "2) Sweep-to-Lift LONG\n"
        "   • Trigger: stop run into 113.7k (or quick stab 113.4k) and immediate reclaim of 114.0k.\n"
        "   • Entry: 113.9k–114.1k   • Invalidation: 113.3k\n"
        "   • TPs: 114.9k → 115.8k → 116.3k\n\n"
        "3) Lower-High FADE\n"
        "   • Trigger: rejection/failed retest inside 115.8k–116.3k with VWAP rolling down.\n"
        "   • Entry: ~115.9k   • Invalidation: 116.5k\n"
        "   • TPs: 115.0k → 114.4k → 113.7k (leave runner toward 112.15k if macro turns risk-off)\n\n"
        "PROBABILITIES (into tomorrow's NY)\n"
        "• Range 113.7k–115.8k, two-sided traps: 40%\n"
        "• Stop-run squeeze to 116.3k/118.0k (then fade): 40%\n"
        "• Breakdown to 112.15k → 110.2k: 20%\n\n"
        "VWAP CYCLE NOTE\n"
        "• Your 4-day VWAP window **does reset on Tue, Oct 28 (00:00 UTC)**. Expect fake moves around the roll; higher-quality signals arrive once the new 4-day aligns with the 9-day. Until that alignment turns clearly bullish, treat spikes into 115.8k–116.3k as tactical fades; treat 113.7k as the bull line-in-the-sand.\n\n"
        "WHAT CAN MOVE PRICE THIS WEEK (times ET; links)\n"
        "• **FOMC** two-day meeting **Oct 28–29**; decision/press conf Oct 29. Markets lean to a 25 bp cut to 3.75–4.00%. Fed tone on QT matters.  ⇒ Fed calendar / FOMC schedule.  [Federal Reserve]  [oai_citation:0‡Federal Reserve](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm?utm_source=chatgpt.com)\n"
        "• **Q3 GDP (Advance)** **Thu Oct 30, 8:30a** — headline growth & PCE deflator inside the report.  [BEA schedule / GDP page]  [oai_citation:1‡Bureau of Economic Analysis](https://www.bea.gov/news/schedule?utm_source=chatgpt.com)\n"
        "• **PCE (Sep)** **Fri Oct 31, 8:30a** — the Fed's preferred inflation gauge.  [BEA / PCE page]  [oai_citation:2‡Bureau of Economic Analysis](https://www.bea.gov/data/personal-consumption-expenditures-price-index?utm_source=chatgpt.com)\n"
        "• **Big Tech earnings all week** (MSFT, AAPL, AMZN, GOOGL, META, etc.). Equity reactions can swing crypto beta.  [Kiplinger / MarketScreener / MarketWatch]  [oai_citation:3‡Kiplinger](https://www.kiplinger.com/investing/stocks/17494/next-week-earnings-calendar-stocks?utm_source=chatgpt.com)\n"
        "• **Flows**: Latest CoinShares shows large BTC ETP **inflows (≈US$931M) this week** after prior outflows; rotation out of ETH noted. Watch if that persists post-FOMC.  [CoinShares]  [oai_citation:4‡CoinShares](https://coinshares.com/insights/research-data/fund-flows-27-10-25/?utm_source=chatgpt.com)\n"
        "• **Macro tone**: GDPNow tracking Q3 real GDP ~**3.9%** as of Oct 27 (subject to revision).  [Atlanta Fed]  [oai_citation:5‡Federal Reserve Bank of Atlanta](https://www.atlantafed.org/cqer/research/gdpnow?utm_source=chatgpt.com)\n\n"
        "EXECUTION CHECKLIST (stern & simple)\n"
        "• Trade **edges** only (reclaims/sweeps). First partial ≥ +0.8R; trail behind last reclaimed VWAP.\n"
        "• If headlines hit during a push (FOMC/earnings), cut to core and re-enter at the levels above.\n"
        "• No size until the **new 4-day VWAP** confirms with 9-day; otherwise keep it tactical.\n\n"
        "BOTTOM LINE\n"
        "We're coiling between **113.7k support** and **115.8k–116.3k supply** ahead of heavy macro. Best plays: (a) **reclaim-and-go** through 115.0k toward 116.3k/118.0k, or (b) **fade** a tired pop at 115.8k–116.3k back to 114.4k/113.7k. Break **<112.15k** flips the week back to defensive."
    )

    def build_prefix(i: int) -> str:
        header = "**WEEKLY & NY SESSION PLAN — BTC (as of Oct 27, 2025)**\n" if i == 1 else "**WEEKLY & NY SESSION PLAN (cont.)**\n"
        mention = "@everyone\n" if i == 1 else ""
        return mention + header

    messages = split_message_with_prefix(base_message, build_prefix, 2000)

    print("📣 Sending Weekly & NY Session Plan to Discord...")
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
    send_weekly_session_plan()













