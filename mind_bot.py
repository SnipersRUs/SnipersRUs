#!/usr/bin/env python3
# Third Eye Sentiment Bot — Snipers-R-Us
# Runs locally, no external deps. Posts to Discord at 5:00 AM & 7:00 PM ET daily.
# Stores metrics in ~/Desktop/mind/metrics/metrics.json

import json, time, random, sys, os, datetime
import requests
from zoneinfo import ZoneInfo  # Python 3.9+
import hashlib

# ========= CONFIG =========
WEBHOOK_URL = os.environ.get(
    "WEBHOOK_URL",
    "https://discord.com/api/webhooks/1427057480470626375/LsSUOBgc_HKdV7l7WheinXXuSwWyzapoHLXZIkztuZkfWFcL_5kK6FWT4NyF6DvpNc50"
)
TZ = ZoneInfo("America/New_York")
MORNING_TIME = (5, 0)   # 5:00 AM ET
EVENING_TIME = (19, 0)  # 7:00 PM ET (adjusted for daylight savings - Asia open timing)

BASE_DIR = os.path.expanduser("~/Desktop/mind")
LOG_FILE = os.path.join(BASE_DIR, "logs", "mind.log")
METRICS_DIR = os.path.join(BASE_DIR, "metrics")
METRICS_FILE = os.path.join(METRICS_DIR, "metrics.json")
STATE_FILE = os.path.join(BASE_DIR, "last_sent.json")

# ========= UTIL =========
def log(msg: str):
    ts = datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"Log write error: {e}")

def ensure_dirs():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(METRICS_DIR, exist_ok=True)
    # Touch files
    for p in (LOG_FILE, STATE_FILE, METRICS_FILE):
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write("{}" if p.endswith(".json") else "")

def post_discord(message: str) -> bool:
    payload = {
        "content": message,
        "username": "Third Eye"
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        if response.status_code == 204:
            return True
        log(f"Discord response code: {response.status_code}")
        return False
    except Exception as e:
        log(f"Post error: {e}")
        return False

def update_metrics(success: bool, kind: str):
    metrics = {
        "morning_success": 0,
        "morning_fail": 0,
        "evening_success": 0,
        "evening_fail": 0,
        "last_updated": datetime.datetime.now(TZ).isoformat()
    }
    try:
        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                metrics.update(json.load(f))
        key = f"{kind}_success" if success else f"{kind}_fail"
        metrics[key] = metrics.get(key, 0) + 1
        metrics["last_updated"] = datetime.datetime.now(TZ).isoformat()
        with open(METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"Metrics update error: {e}")

def next_run_after(now: datetime.datetime, target_hm: tuple[int,int]) -> datetime.datetime:
    hour, minute = target_hm
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        candidate = candidate + datetime.timedelta(days=1)
    return candidate

def get_market_data():
    """Fetch detailed market data for unique daily messages"""
    try:
        # Get Bitcoin price data with 24h high/low and change
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_24hr_high=true&include_24hr_low=true",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            btc_data = data['bitcoin']
            btc_price = btc_data['usd']
            btc_change = btc_data.get('usd_24h_change', 0)

            # Calculate price range and volatility
            high_24h = btc_data.get('usd_24h_high', btc_price)
            low_24h = btc_data.get('usd_24h_low', btc_price)
            range_24h = high_24h - low_24h
            range_pct = (range_24h / btc_price) * 100 if btc_price > 0 else 0

            # Determine where price is in the range
            if high_24h > low_24h:
                price_position = ((btc_price - low_24h) / (high_24h - low_24h)) * 100
            else:
                price_position = 50

            return {
                'btc_price': btc_price,
                'btc_change': btc_change,
                'high_24h': high_24h,
                'low_24h': low_24h,
                'range_24h': range_24h,
                'range_pct': range_pct,
                'price_position': price_position,  # 0-100, where price is in the range
                'timestamp': datetime.datetime.now(TZ).isoformat()
            }
    except Exception as e:
        log(f"Market data fetch error: {e}")

    return None

def get_daily_seed():
    """Generate a unique seed based on date and market data"""
    today = datetime.datetime.now(TZ).strftime("%Y-%m-%d")
    market_data = get_market_data()

    # Create unique seed from date + market data
    seed_string = today
    if market_data:
        # Use BTC price and change to influence the seed
        btc_price = int(market_data['btc_price'])
        btc_change = int(market_data['btc_change'] * 100)  # Convert to integer
        seed_string += f"-{btc_price}-{btc_change}"

    # Create hash for consistent daily randomization
    return int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)

def analyze_market_action(market_data=None):
    """Analyze actual market price action for natural descriptions"""
    if not market_data:
        return {
            'feel': "quiet pressure building",
            'action': "market is finding its footing",
            'volatility': "normal",
            'trend': "neutral",
            'position': "mid-range",
            'position_risk': "neutral territory",
            'range_pct': 0,
            'change': 0
        }

    btc_change = market_data.get('btc_change', 0)
    range_pct = market_data.get('range_pct', 0)
    price_position = market_data.get('price_position', 50)

    # Determine volatility
    if range_pct > 8:
        volatility = "high"
        vol_desc = "wide swings"
    elif range_pct > 4:
        volatility = "moderate"
        vol_desc = "decent moves"
    else:
        volatility = "low"
        vol_desc = "tight range"

    # Determine trend strength
    if btc_change > 5:
        trend = "strong_bull"
        trend_desc = "strong bullish momentum"
    elif btc_change > 2:
        trend = "bull"
        trend_desc = "bullish energy"
    elif btc_change < -5:
        trend = "strong_bear"
        trend_desc = "strong bearish pressure"
    elif btc_change < -2:
        trend = "bear"
        trend_desc = "bearish pressure"
    else:
        trend = "neutral"
        trend_desc = "sideways energy"

    # Determine price position in range
    if price_position > 80:
        position_desc = "near the highs"
        position_risk = "potential rejection zone"
    elif price_position < 20:
        position_desc = "near the lows"
        position_risk = "potential support zone"
    else:
        position_desc = "mid-range"
        position_risk = "neutral territory"

    # Generate natural feel based on combination
    feels = []
    if trend == "strong_bull" and volatility == "high":
        feels = ["explosive bullish momentum", "breakout energy building", "strong upward pressure"]
    elif trend == "strong_bull":
        feels = ["steady bullish momentum", "uptrend acceleration", "bullish conviction"]
    elif trend == "strong_bear" and volatility == "high":
        feels = ["sharp bearish pressure", "correction energy", "downward momentum building"]
    elif trend == "strong_bear":
        feels = ["steady bearish pressure", "downtrend acceleration", "bearish conviction"]
    elif trend == "bull" and volatility == "high":
        feels = ["choppy bullish moves", "volatile uptrend", "bullish but unstable"]
    elif trend == "bear" and volatility == "high":
        feels = ["choppy bearish moves", "volatile downtrend", "bearish but unstable"]
    elif volatility == "high" and trend == "neutral":
        feels = ["high volatility chop", "two-sided battle", "indecisive wide swings"]
    elif volatility == "low" and trend == "neutral":
        feels = ["tight consolidation", "range-bound patience", "equilibrium testing"]
    else:
        feels = ["measured momentum", "balanced energy", "neutral pressure"]

    # Use daily seed for consistent randomization
    seed = get_daily_seed()
    random.seed(seed)
    feel = random.choice(feels)
    random.seed()  # Reset random seed

    return {
        'feel': feel,
        'action': f"{trend_desc} with {vol_desc}",
        'volatility': volatility,
        'trend': trend,
        'position': position_desc,
        'position_risk': position_risk,
        'range_pct': range_pct,
        'change': btc_change
    }

def pick_breath_pattern(market_data=None):
    """Generate unique daily breath pattern based on market conditions"""
    patterns = [
        ("Inhale 4 • Hold 4 • Exhale 6", "I move with calm precision."),
        ("Inhale 4 • Hold 4 • Exhale 8", "I don't chase— I execute."),
        ("Inhale 5 • Hold 5 • Exhale 5", "My plan sets my pace."),
        ("Inhale 4 • Hold 2 • Exhale 6", "I trade facts, not feelings."),
        ("Inhale 6 • Hold 4 • Exhale 8", "Patience is profit."),
        ("Inhale 3 • Hold 3 • Exhale 6", "I flow with market rhythm."),
        ("Inhale 5 • Hold 3 • Exhale 7", "I trust my process."),
        ("Inhale 4 • Hold 6 • Exhale 8", "I remain centered in chaos."),
        ("Inhale 6 • Hold 2 • Exhale 4", "I adapt without losing focus."),
        ("Inhale 3 • Hold 4 • Exhale 5", "I stay grounded in volatility."),
    ]

    # Use daily seed for consistent randomization
    seed = get_daily_seed()
    random.seed(seed)
    pattern = random.choice(patterns)
    random.seed()  # Reset random seed

    return pattern

# ========= MESSAGE BUILDERS =========
def build_morning_message() -> str:
    """Build unique morning message based on actual market price action"""
    market_data = get_market_data()
    analysis = analyze_market_action(market_data)
    breath, mantra = pick_breath_pattern(market_data)

    # Get current time for context
    now = datetime.datetime.now(TZ)
    hour = now.hour

    # Market context based on actual data
    market_context = ""
    if market_data:
        btc_price = market_data['btc_price']
        btc_change = market_data['btc_change']
        price_emoji = "🟢" if btc_change > 0 else "🔴" if btc_change < 0 else "⚪"
        market_context = f"\n{price_emoji} BTC: ${btc_price:,.0f} ({btc_change:+.1f}%)"

    # Time-based opening - varied
    seed = get_daily_seed()
    random.seed(seed)
    if hour < 6:
        openings = [
            "The night shift is ending. Early risers are setting the tone.",
            "Asia's closing, Europe's opening. The global dance continues.",
            "Pre-market energy is building. The calm before the storm."
        ]
    elif hour < 9:
        openings = [
            "London's done its dance. New York is next. The real moves are coming.",
            "European session wrapped. US session starting. This is where it gets interesting.",
            "London closed, New York opening. The main event begins now."
        ]
    else:
        openings = [
            "Markets are waking up. The day's energy is building.",
            "Morning session underway. Positions are being set.",
            "The trading day is here. Energy is building."
        ]
    opening = random.choice(openings)
    random.seed()

    # Generate natural, varied guidance based on actual market analysis
    guidance = []
    trend = analysis['trend']
    volatility = analysis['volatility']
    position = analysis['position']

    if trend == "strong_bull":
        if volatility == "high":
            guidance_options = [
                "Strong bullish momentum with high volatility—wait for pullbacks, not breakouts.",
                "Explosive moves are happening—don't chase, let price come to you.",
                "Uptrend is strong but choppy—patience on entries is key."
            ]
        else:
            guidance_options = [
                "Steady bullish momentum—trend is your friend, but wait for your zone.",
                "Clean uptrend building—pullbacks are opportunities, not threats.",
                "Bullish energy is strong—don't fight it, but don't chase it either."
            ]
    elif trend == "strong_bear":
        if volatility == "high":
            guidance_options = [
                "Sharp bearish pressure with high volatility—support levels are being tested.",
                "Downward momentum is strong—don't catch falling knives, wait for bounces.",
                "Bearish energy is intense—patience is your best weapon here."
            ]
        else:
            guidance_options = [
                "Steady bearish pressure—support zones are critical today.",
                "Downtrend is clear—wait for your setup, don't force trades.",
                "Bearish momentum building—fear creates opportunity, but timing is everything."
            ]
    elif trend == "bull":
        guidance_options = [
            "Mild bullish energy—trend is up but not explosive. Wait for confirmation.",
            "Bullish but choppy—patience required, don't get shaken out.",
            "Slight upward bias—range trading might be safer than trend following."
        ]
    elif trend == "bear":
        guidance_options = [
            "Mild bearish pressure—downtrend is weak, support might hold.",
            "Bearish but unstable—could reverse, wait for clear signals.",
            "Slight downward bias—range trading might be safer than trend following."
        ]
    elif volatility == "high":
        guidance_options = [
            "High volatility chop—two-sided battle, wait for clear direction.",
            "Wide swings happening—don't get caught in the middle, wait for edges.",
            "Indecisive high volatility—patience is key, let the market show its hand."
        ]
    else:
        guidance_options = [
            "Tight consolidation—range traders are in their element today.",
            "Low volatility, sideways action—patience is the game, no rush.",
            "Equilibrium testing—wait for the breakout or trade the range edges."
        ]

    # Add position-specific guidance
    if position == "near the highs":
        guidance_options.append(f"Price is {position}—watch for rejection or continuation.")
    elif position == "near the lows":
        guidance_options.append(f"Price is {position}—support zone, watch for bounce or breakdown.")

    random.seed(seed)
    guidance = [random.choice(guidance_options)]

    # Add 2 more varied guidance points
    general_guidance = [
        "Wait for price to step into your zones. Clean confirmation or no entry.",
        "Protect your capital. One good shot beats five guesses.",
        "Match the market's pace, don't force your own rhythm.",
        "Clarity over confusion. If unsure, don't trade.",
        "Plan your exits before your entries. Risk management is everything."
    ]
    random.shuffle(general_guidance)
    guidance.extend(general_guidance[:2])
    random.seed()

    # Varied vibe descriptions
    vibe_descriptions = [
        "The market's energy is building. Some are already positioned, others are waiting.",
        "Positions are being set. The calm few are studying their zones, not chasing the noise.",
        "Early moves are happening. Smart money is positioning, retail is watching.",
        "The session is starting. Some are ready, others are scrambling.",
        "Energy is building. The prepared are waiting, the unprepared are rushing."
    ]
    random.seed(seed)
    vibe_desc = random.choice(vibe_descriptions)
    random.seed()

    lines = [
        "@everyone",
        opening,
        "",
        f"**🌅 The Vibe:**",
        f"Today carries {analysis['feel']}.{market_context}",
        vibe_desc,
        "",
        f"**✨ Guidance for Today:**"
    ]

    # Add guidance bullets
    for item in guidance:
        lines.append(f"• {item}")

    lines.extend([
        "",
        f"**🧘 Third Eye Morning Drill:**",
        breath,
        f"Say: \"{mantra}\"",
        "",
        f"**⚖️ Rules for Today:**",
        "1. If you're unsure, don't trade. Clarity beats confusion.",
        "2. If you're confident, size appropriately. Greed kills discipline.",
        "3. Plan your exits before your entries. Risk management is everything.",
        "",
        f"**🧠 The mindset:**",
        "You showed up ready. Stay sharp, stay patient, stay profitable.",
        "Third Eye—starting the day with focus, discipline, and precision."
    ])

    return "\n".join(lines)

def build_evening_message() -> str:
    """Build unique evening message based on actual market price action"""
    market_data = get_market_data()
    analysis = analyze_market_action(market_data)
    breath, mantra = pick_breath_pattern(market_data)

    # Market context for evening
    market_context = ""
    if market_data:
        btc_price = market_data['btc_price']
        btc_change = market_data['btc_change']
        price_emoji = "🟢" if btc_change > 0 else "🔴" if btc_change < 0 else "⚪"
        market_context = f"\n{price_emoji} BTC: ${btc_price:,.0f} ({btc_change:+.1f}%)"

    # Varied opening lines
    seed = get_daily_seed()
    random.seed(seed)
    openings = [
        "The candles are slowing down. Liquidity's fading. It's that space between exhaustion and reset—where real traders breathe while everyone else forces one more trade.",
        "The session is winding down. Volume is drying up. Smart money is done, weak hands are still fighting.",
        "Day's end is here. The noise is fading. This is where discipline separates winners from losers.",
        "Markets are closing. Energy is draining. The prepared are already done, the desperate are still trading.",
        "Liquidity is thinning. The day's story is written. Real traders are protecting their energy, amateurs are chasing one more trade."
    ]
    opening = random.choice(openings)
    random.seed()

    # Generate natural, varied reflection based on actual market performance
    reflection = []
    trend = analysis['trend']
    volatility = analysis['volatility']
    change = analysis['change']

    # Calculate day's range context
    if market_data:
        range_pct = analysis['range_pct']
        if range_pct > 8:
            range_context = "It was a volatile day with wide swings."
        elif range_pct > 4:
            range_context = "The day saw decent moves and decent range."
        else:
            range_context = "It was a tight, range-bound day."
    else:
        range_context = ""

    if trend == "strong_bull":
        if volatility == "high":
            reflection_options = [
                "Strong bullish day with high volatility—momentum traders had their moment.",
                "Explosive green day—the bulls ran hard, did you catch the wave or get shaken out?",
                "Powerful uptrend today—note what worked in the strong moves."
            ]
        else:
            reflection_options = [
                "Steady bullish day—clean uptrend, did you ride it or fight it?",
                "Strong green day—the trend was clear, did you respect it?",
                "Bullish momentum was strong—note your entries and exits."
            ]
    elif trend == "strong_bear":
        if volatility == "high":
            reflection_options = [
                "Sharp bearish day with high volatility—support levels were tested hard.",
                "Explosive red day—the bears had control, did you respect the zones?",
                "Powerful downtrend today—note how you handled the pressure."
            ]
        else:
            reflection_options = [
                "Steady bearish day—clean downtrend, did you wait or fight it?",
                "Strong red day—support was tested, did you respect the levels?",
                "Bearish momentum was clear—note your decision-making process."
            ]
    elif change > 2:
        reflection_options = [
            "Green day energy—uptrend was present, did you catch it?",
            "Bullish day overall—note what worked in the moves.",
            "Positive day—momentum was there, did you trade it well?"
        ]
    elif change < -2:
        reflection_options = [
            "Red day pressure—downtrend was present, did you handle it?",
            "Bearish day overall—note how you managed the downside.",
            "Negative day—pressure was there, did you stay disciplined?"
        ]
    elif volatility == "high":
        reflection_options = [
            "High volatility chop today—two-sided battle, did you get caught in the middle?",
            "Wide swings happened—did you wait for the edges or trade the chaos?",
            "Indecisive but volatile—note your patience level today."
        ]
    else:
        reflection_options = [
            "Sideways day energy—range trading was the game, did you wait for edges?",
            "Consolidation day—patience was required, did you have it?",
            "Tight range today—sometimes the best trade is no trade."
        ]

    random.seed(seed)
    reflection = [random.choice(reflection_options)]

    # Add specific reflection points based on market action
    if market_data:
        if analysis['position'] == "near the highs":
            reflection.append("Price ended near the highs—watch for rejection or continuation tomorrow.")
        elif analysis['position'] == "near the lows":
            reflection.append("Price ended near the lows—support zone, watch for bounce or breakdown tomorrow.")

    # Add varied general reflection
    general_reflection = [
        "Whatever you did today—win, lose, or flat—accept it and log it.",
        "Note the moment you felt FOMO, hesitation, or tilt. That's your edge to sharpen.",
        "Review your trades. What worked? What didn't? Learn and move forward.",
        "The day is done. Tomorrow is a new game. Protect your energy.",
        "Reflect on your discipline. Did you follow your rules or break them?"
    ]
    random.shuffle(general_reflection)
    reflection.extend(general_reflection[:2])
    random.seed()

    # Varied vibe descriptions
    vibe_descriptions = [
        "Some are clutching profits, scared to give them back. Some are fighting red, hoping for a miracle. The calm few are already done, protecting their energy for tomorrow's real setups.",
        "Positions are being closed. Some are happy, some are frustrated. The disciplined are already planning tomorrow.",
        "The day's story is written. Winners are protecting gains, losers are planning revenge. Smart traders are already resetting.",
        "Energy is draining. Some are still trading, others are done. The prepared are already looking ahead.",
        "The session is over. Some are celebrating, some are licking wounds. Real traders are already moving on."
    ]
    random.seed(seed)
    vibe_desc = random.choice(vibe_descriptions)
    random.seed()

    lines = [
        "@everyone",
        opening,
        "",
        f"**☁️ The Vibe:**",
        f"Today carried {analysis['feel']}.{market_context}",
        range_context if range_context else "",
        vibe_desc,
        "",
        f"**✨ Guidance for the Daily Close:**"
    ]

    # Add reflection bullets
    for item in reflection:
        lines.append(f"• {item}")

    lines.extend([
        "",
        f"**🧘 Third Eye Reset Drill:**",
        breath,
        f"Say: \"{mantra}\"",
        "",
        f"**⚖️ Rules for the Close:**",
        "1. If you're green, stop trading. Protect it.",
        "2. If you're red, accept it. Revenge never heals it.",
        "3. Plan your zones and your bias for tomorrow—don't guess.",
        "",
        f"**🧠 The mindset:**",
        "The vibe tonight: quiet, grounded, proud of your discipline.",
        "You showed up, stayed sharp, and lived to trade another day.",
        "Third Eye—ending the day with focus, peace, and precision."
    ])

    return "\n".join(lines)

def save_state(kind: str):
    try:
        state = {}
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f) or {}
        now = datetime.datetime.now(TZ).isoformat()
        state[kind] = now
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"save_state error: {e}")

def send_with_retry(content: str, retries: int = 3, backoff: float = 2.0) -> bool:
    kind = "morning" if "Morning crew" in content else "evening"
    for attempt in range(1, retries+1):
        if post_discord(content):
            update_metrics(True, kind)
            return True
        sleep_s = backoff ** attempt
        log(f"Retry {attempt}/{retries} in {sleep_s:.1f}s")
        time.sleep(sleep_s)
    update_metrics(False, kind)
    log(f"Failed to send {kind} message after retries.")
    return False

# ========= RUN MODES =========
def run_once(kind: str):
    ensure_dirs()
    msg = build_morning_message() if kind == "morning" else build_evening_message()
    ok = send_with_retry(msg)
    if ok:
        save_state(kind)
        log(f"Sent {kind} message.")
    else:
        log(f"Failed to send {kind} message after retries.")

def daemon():
    ensure_dirs()
    log("Starting Third Eye Sentiment Bot (5:00 AM & 7:00 PM ET). Ctrl+C to stop.")
    while True:
        now = datetime.datetime.now(TZ)
        next_morn = next_run_after(now, MORNING_TIME)
        next_even = next_run_after(now, EVENING_TIME)
        if next_morn <= next_even:
            target_dt, kind = next_morn, "morning"
        else:
            target_dt, kind = next_even, "evening"

        seconds = (target_dt - now).total_seconds()
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        log(f"Next run: {kind} at {target_dt.strftime('%Y-%m-%d %H:%M:%S %Z')} (in {h:02d}h:{m:02d}m:{s:02d}s)")
        try:
            time.sleep(max(1, int(seconds)))
        except KeyboardInterrupt:
            log("Shutting down.")
            sys.exit(0)

        msg = build_morning_message() if kind == "morning" else build_evening_message()
        ok = send_with_retry(msg)
        if ok:
            save_state(kind)
            log(f"Sent {kind} message.")
        else:
            log(f"Failed to send {kind} message after retries.")
        time.sleep(2)

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--once" in args:
        idx = args.index("--once")
        try:
            kind = args[idx+1].strip().lower()
        except Exception:
            kind = "morning"
        if kind not in ("morning", "evening"):
            print("Usage: python3 mind_bot.py --once [morning|evening]")
            sys.exit(1)
        run_once(kind)
    else:
        daemon()
