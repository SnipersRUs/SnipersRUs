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
    ""
)
TZ = ZoneInfo("America/New_York")
MORNING_TIME = (5, 0)   # 5:00 AM ET
EVENING_TIME = (19, 0)  # 7:00 PM ET (adjusted for daylight savings - Asia open timing)

BASE_DIR = os.path.expanduser("~/Desktop/mind")
LOG_FILE = os.path.join(BASE_DIR, "logs", "mind.log")
METRICS_DIR = os.path.join(BASE_DIR, "metrics")
METRICS_FILE = os.path.join(METRICS_DIR, "metrics.json")
STATE_FILE = os.path.join(BASE_DIR, "last_sent.json")
MESSAGE_HISTORY_FILE = os.path.join(BASE_DIR, "message_history.json")

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
    for p in (LOG_FILE, STATE_FILE, METRICS_FILE, MESSAGE_HISTORY_FILE):
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

# ========= MARKET CHARACTER ANALYZER =========
class MarketCharacterAnalyzer:
    """Analyzes the market to determine its character for psychology messaging"""

    @staticmethod
    def analyze_session_character(market_data=None) -> dict:
        """
        Analyzes the market and returns a character profile.
        Returns a dict with: character, volatility, trend_strength, key_events
        """
        if not market_data:
            return {
                "character": "NEUTRAL",
                "volatility": "NORMAL",
                "trend_strength": "WEAK",
                "key_events": []
            }

        btc_change = market_data.get('btc_change', 0)
        range_pct = market_data.get('range_pct', 0)
        price_position = market_data.get('price_position', 50)
        btc_price = market_data.get('btc_price', 0)

        # 1. Calculate Volatility (using range percentage)
        if range_pct > 8:
            volatility = "HIGH"
        elif range_pct > 4:
            volatility = "NORMAL"
        else:
            volatility = "LOW"

        # 2. Determine Trend Strength
        if abs(btc_change) > 5:
            trend_strength = "STRONG"
        elif abs(btc_change) > 2.5:
            trend_strength = "MODERATE"
        elif abs(btc_change) > 1:
            trend_strength = "WEAK"
        else:
            trend_strength = "WEAK"

        # 3. Identify Key Events
        key_events = []

        # Extreme price position (like 3σ deviation)
        if price_position > 90:
            key_events.append("EXTREME_HIGH")
        elif price_position < 10:
            key_events.append("EXTREME_LOW")

        # High volatility with weak trend = chaotic
        if volatility == "HIGH" and trend_strength == "WEAK":
            key_events.append("CHAOTIC_MOVES")

        # Strong trend with high volatility = explosive
        if trend_strength == "STRONG" and volatility == "HIGH":
            key_events.append("EXPLOSIVE_MOVE")

        # 4. Synthesize into a final "Character"
        character = "NEUTRAL"

        # Strong or moderate trend with normal volatility = TRENDING
        if (trend_strength == "STRONG" or trend_strength == "MODERATE") and volatility == "NORMAL":
            character = "TRENDING"
        # Weak trend with low volatility = RANGING
        elif trend_strength == "WEAK" and volatility == "LOW":
            character = "RANGING_CHOPPY"
        # High volatility scenarios
        elif volatility == "HIGH":
            if trend_strength == "WEAK":
                character = "VOLATILE_CHAOTIC"
            else:
                character = "VOLATILE_TRENDING"
        # Extreme positions
        elif "EXTREME_HIGH" in key_events or "EXTREME_LOW" in key_events:
            if abs(btc_change) > 3:
                character = "MEAN_REVERTING"
            else:
                character = "EXTREME_POSITION"
        # Moderate trend with low volatility = still trending but weaker
        elif trend_strength == "MODERATE" and volatility == "LOW":
            character = "TRENDING"
        else:
            character = "NEUTRAL"

        return {
            "character": character,
            "volatility": volatility,
            "trend_strength": trend_strength,
            "key_events": key_events,
            "price_position": price_position,
            "change": btc_change
        }

# ========= PSYCHOLOGY MESSAGE ENGINE =========
class PsychologyMessageEngine:
    """Generates dynamic trading psychology messages based on market character"""

    def __init__(self):
        self.message_templates = {
            "TRENDING": {
                "psychology": [
                    "The FOMO Engine is firing. You see the trend and your brain screams 'get in or miss out'. This is where most traders get wrecked—chasing price.",
                    "Momentum is building. Your lizard brain wants to jump in NOW. But the smart money already positioned. Don't be the exit liquidity.",
                    "The trend is clear. Everyone sees it. The question is: are you chasing or waiting for your setup? Chasers lose. Snipers win."
                ],
                "before_session": [
                    "Today's market is showing a strong trend. **Your Mission:** Don't chase. Be a sniper, not a chaser. Wait for a pullback to a value area before entering. Patience is your edge.",
                    "Strong directional move detected. **Your Mission:** If you're not already in, don't FOMO in. Wait for the pullback. The trend will give you another chance—if you're patient.",
                    "Trending market ahead. **Your Mission:** Resist the urge to chase. The best entries come on pullbacks, not breakouts. Your discipline is your edge today."
                ],
                "during_session": [
                    "Are you feeling the urge to jump in? Stop. The market doesn't care about your FOMO. Stick to your plan. If you missed the move, so what? There's another trade tomorrow. Protect your capital.",
                    "The trend is moving. Are you chasing? If yes, you're about to learn an expensive lesson. If you're waiting for your setup, you're doing it right. Patience pays.",
                    "FOMO is real right now. But remember: the best trades are the ones you don't take. If you're not in, don't force it. The market will give you another chance."
                ],
                "end_session": [
                    "The trend held its ground. Did you? If you were patient and waited for your entry, you likely had a calm day. If you chased, you're probably stressed. Review your discipline. That's the real PnL.",
                    "Trend day complete. If you waited for your setup, you're a professional. If you chased, you're a gambler. Which one were you today?",
                    "The trend played out. Did you respect it or fight it? Your answer determines whether you're building a career or a gambling addiction."
                ]
            },
            "RANGING_CHOPPY": {
                "psychology": [
                    "This market is designed to frustrate you. It gives you hope with a small move, then rips it away. Your brain will try to force a trade out of boredom. Don't fall for it.",
                    "Choppy markets are psychological warfare. They make you think you're missing opportunities. You're not. You're protecting capital.",
                    "Range-bound markets test your patience. They whisper 'just one trade' in your ear. That whisper is the devil. Ignore it."
                ],
                "before_session": [
                    "We're in a choppy, range-bound market. **Your Mission:** Be a butcher, not a surgeon. This is not for fancy trend trades. This is for buying the low end of the range and selling the high end. Or better yet... don't trade at all.",
                    "Choppy market detected. **Your Mission:** Today is about preservation, not profit. If you MUST trade, fade the extremes with tiny size. Your goal is to not lose money.",
                    "Range-bound conditions ahead. **Your Mission:** This is a 'no-trade' zone for most. Your best trade today might be staying flat. Protect your capital."
                ],
                "during_session": [
                    "Feeling antsy? Good. That's the market trying to bait you. This is a 'no-trade' zone for most. If you MUST trade, fade the extremes of the range with tiny size. Your goal today is to not lose money.",
                    "The chop is frustrating. That's the point. The market wants you to force a trade. Don't. Boredom is not a trading signal. Patience is.",
                    "Range-bound markets make you feel like you're missing out. You're not. You're being smart. The best traders know when NOT to trade."
                ],
                "end_session": [
                    "If you're frustrated, you win. If you lost money fighting this chop, you learned an expensive lesson. Choppy markets weed out the impatient. Count this as a victory if you stayed flat.",
                    "Choppy day complete. If you stayed flat, you're a professional. If you forced trades, you're a gambler. The market doesn't reward impatience.",
                    "Range-bound day done. Did you respect the chop or fight it? Your answer shows your discipline level."
                ]
            },
            "VOLATILE_CHAOTIC": {
                "psychology": [
                    "Panic and Euphoria are on a seesaw. One minute you're terrified, the next you're a genius. This is pure emotional warfare. Your risk management is the only thing that can save you.",
                    "High volatility means high emotion. Your brain is being tested. Can you stay calm when everything is moving? That's the real trade.",
                    "Chaos is here. The market is trying to shake you out. Your discipline is your only weapon. Use it."
                ],
                "before_session": [
                    "Warning: High volatility and chaos expected. **Your Mission:** Survive. Cut your position size in half. Widen your stops. Your only goal is to not get margin called. The big money is made by surviving these days.",
                    "Volatile conditions ahead. **Your Mission:** Risk management is everything today. Reduce size. Widen stops. Your goal is survival, not heroics.",
                    "Chaos incoming. **Your Mission:** This is not the day to prove you're right. This is the day to prove you can manage risk. Protect your account."
                ],
                "during_session": [
                    "Breathe. If you're in a trade, manage it. If you're not, don't be a hero. This is not the time to prove you're right. It's the time to prove you can manage risk. Check your stop loss, not your PnL.",
                    "Volatility is high. Your emotions are being tested. Stay calm. Manage your risk. The market doesn't care about your feelings.",
                    "Chaos is happening. Are you panicking or staying disciplined? Your answer determines your survival. Check your stops. Manage your risk."
                ],
                "end_session": [
                    "You made it through the storm. Whether you're up or down, if you followed your risk plan, you're a professional trader. If you blew up your account, you were a gambler. Which one were you today?",
                    "Volatile day survived. If you managed your risk, you're building a career. If you let emotions rule, you're building a problem.",
                    "Chaos day complete. Did you survive with discipline or get destroyed by emotion? Your answer is your report card."
                ]
            },
            "MEAN_REVERTING": {
                "psychology": [
                    "The market has stretched too far, too fast. Your brain thinks 'this time is different' and the trend will never end. It's lying. The smart money is preparing to fade this move.",
                    "Extreme moves create extreme emotions. The crowd is euphoric or panicked. That's your edge. The extremes are where reversals happen.",
                    "Price is at an extreme. Everyone thinks it will continue. History says otherwise. The rubber band is stretched. It will snap back."
                ],
                "before_session": [
                    "Price is at an extreme deviation. **Your Mission:** Fade the move. This is a high-probability reversal zone. Look for signs of exhaustion and take a contrarian trade against the madness.",
                    "Extreme position detected. **Your Mission:** The crowd is wrong at extremes. Look for reversal signals. This is where contrarian trades pay.",
                    "Mean reversion setup. **Your Mission:** The market has overextended. Smart money fades extremes. Look for exhaustion and reversal signals."
                ],
                "during_session": [
                    "Are you scared to go against the trend? Good. That's the edge. The crowd is wrong at the extremes. Scale in slowly. Your conviction should be in your analysis, not the price action.",
                    "Extreme moves create fear or greed. That's your signal. When everyone is euphoric, be cautious. When everyone is panicked, be ready.",
                    "The market is stretched. Are you following the crowd or thinking independently? Contrarian thinking at extremes is where edges are found."
                ],
                "end_session": [
                    "The rubber band snapped. Did you have the guts to hold the contrarian view? Reversals are hard on the mind but pay the bills. Review the exhaustion signal—your ability to spot it is your next level up.",
                    "Mean reversion played out. If you faded the extreme, you're thinking like a pro. If you followed the crowd, you learned a lesson.",
                    "Extreme day complete. Did you trade the reversal or follow the crowd? Your answer shows your trading maturity."
                ]
            },
            "VOLATILE_TRENDING": {
                "psychology": [
                    "Explosive moves are happening. Your brain wants to chase. But volatility means whipsaws. One wrong move and you're stopped out. Patience is your weapon.",
                    "Strong trend with high volatility. This is where traders get shaken out. The trend is real, but the ride is rough. Can you hold through the noise?",
                    "Explosive momentum is building. Everyone sees it. But high volatility means false breakouts. Don't chase. Wait for your setup."
                ],
                "before_session": [
                    "Explosive trending conditions. **Your Mission:** The trend is strong but volatile. Don't chase. Wait for pullbacks. Reduce size. The moves are big, but so are the whipsaws.",
                    "Volatile trend detected. **Your Mission:** This is not for the faint of heart. Reduce size. Widen stops. Wait for pullbacks. The trend will give you chances—don't force it.",
                    "Explosive market ahead. **Your Mission:** Strong trend, high volatility. This means big moves but also big whipsaws. Be patient. Wait for your entry."
                ],
                "during_session": [
                    "The trend is explosive but volatile. Are you chasing or waiting? Chasing in volatile markets is suicide. Wait for pullbacks. Your patience is your edge.",
                    "Big moves are happening. But volatility means false signals. Don't get shaken out. Don't chase. Stick to your plan. The market will give you your entry.",
                    "Explosive moves create FOMO. But volatility creates whipsaws. Don't chase. Wait for pullbacks. Your discipline separates you from the crowd."
                ],
                "end_session": [
                    "Explosive day complete. If you waited for pullbacks, you're a sniper. If you chased, you're a casualty. Volatile trends reward patience, not FOMO.",
                    "Volatile trend day done. Did you respect the volatility or fight it? Your answer determines your survival in these conditions.",
                    "Explosive moves played out. Did you trade with discipline or emotion? Your answer is your report card."
                ]
            },
            "NEUTRAL": {
                "psychology": [
                    "The market is giving you no clear direction. This is boredom's playground, and boredom is the mother of all stupid trades.",
                    "No clear edge is present. Your brain will try to create one. Don't let it. Sometimes the best trade is no trade.",
                    "Neutral markets test your patience. They make you think you should be trading. You shouldn't. Wait for clarity."
                ],
                "before_session": [
                    "No clear edge is present. **Your Mission:** Do nothing. The best trade you can make is the one you don't take. Protect your capital. Wait for clarity.",
                    "Neutral conditions ahead. **Your Mission:** Today is about preservation. Don't force trades. Wait for the market to show its hand. Patience is your edge.",
                    "Unclear market conditions. **Your Mission:** When in doubt, stay out. The market will give you clarity eventually. Don't create trades out of boredom."
                ],
                "during_session": [
                    "Feeling like you should be trading? That's boredom talking. The market hasn't given you an edge. Don't create one. Wait for clarity.",
                    "No clear direction. Are you forcing trades or waiting? Forcing trades in neutral markets is how accounts get destroyed. Wait for your setup.",
                    "The market is unclear. Your brain wants action. Don't give it. The best traders know when NOT to trade. This is one of those times."
                ],
                "end_session": [
                    "Neutral day complete. If you stayed flat, you're a professional. If you forced trades, you're a gambler. The market doesn't reward impatience.",
                    "No clear edge day done. Did you respect the uncertainty or fight it? Your answer shows your discipline.",
                    "Neutral day survived. Did you wait for clarity or create trades? Your answer determines your longevity."
                ]
            }
        }

    def get_psychology_message(self, character: str, session_type: str, market_data: dict = None) -> str:
        """Get a psychology message based on market character and session type"""
        if character not in self.message_templates:
            character = "NEUTRAL"

        templates = self.message_templates[character]

        # Get the right template list based on session type
        if session_type == "morning":
            template_list = templates.get("before_session", [])
        elif session_type == "evening":
            template_list = templates.get("end_session", [])
        else:
            template_list = templates.get("during_session", [])

        if not template_list:
            template_list = templates.get("psychology", ["Stay disciplined. Follow your plan."])

        # Use daily seed for consistent randomization
        seed = get_daily_seed()
        random.seed(seed)
        message = random.choice(template_list)
        random.seed()

        return message

    def get_psychology_intro(self, character: str) -> str:
        """Get the psychology intro based on market character"""
        if character not in self.message_templates:
            character = "NEUTRAL"

        templates = self.message_templates[character]
        psychology_list = templates.get("psychology", ["Stay disciplined."])

        seed = get_daily_seed()
        random.seed(seed)
        intro = random.choice(psychology_list)
        random.seed()

        return intro

def load_message_history():
    """Load message history to avoid repeats"""
    try:
        if os.path.exists(MESSAGE_HISTORY_FILE):
            with open(MESSAGE_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        log(f"Error loading message history: {e}")
    return {"morning": [], "evening": []}

def save_message_history(history: dict):
    """Save message history"""
    try:
        # Keep only last 30 days of history
        for key in history:
            if len(history[key]) > 30:
                history[key] = history[key][-30:]

        with open(MESSAGE_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"Error saving message history: {e}")

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
    """Build unique morning message based on market character and psychology"""
    market_data = get_market_data()

    # Use new Market Character Analyzer
    character_analysis = MarketCharacterAnalyzer.analyze_session_character(market_data)
    character = character_analysis['character']

    # Use Psychology Message Engine
    psychology_engine = PsychologyMessageEngine()
    psychology_intro = psychology_engine.get_psychology_intro(character)
    psychology_message = psychology_engine.get_psychology_message(character, "morning", market_data)

    # Keep existing analysis for market context
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

    # Market context
    market_context = ""
    if market_data:
        btc_price = market_data['btc_price']
        btc_change = market_data['btc_change']
        price_emoji = "🟢" if btc_change > 0 else "🔴" if btc_change < 0 else "⚪"
        market_context = f"\n{price_emoji} BTC: ${btc_price:,.0f} ({btc_change:+.1f}%)"

    # Time-based opening
    seed = get_daily_seed()
    random.seed(seed)
    now = datetime.datetime.now(TZ)
    hour = now.hour
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

    lines = [
        "@everyone",
        opening,
        "",
        f"**🧠 The Psychology:**",
        psychology_intro,
        "",
        f"**🌅 The Vibe:**",
        f"Today carries {analysis['feel']}.{market_context}",
        f"Market Character: {character.replace('_', ' ').title()}",
        "",
        f"**✨ Your Mission Today:**",
        psychology_message,
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
    ]

    return "\n".join(lines)

def build_evening_message() -> str:
    """Build unique evening message based on market character and psychology"""
    market_data = get_market_data()

    # Use new Market Character Analyzer
    character_analysis = MarketCharacterAnalyzer.analyze_session_character(market_data)
    character = character_analysis['character']

    # Use Psychology Message Engine
    psychology_engine = PsychologyMessageEngine()
    psychology_intro = psychology_engine.get_psychology_intro(character)
    psychology_message = psychology_engine.get_psychology_message(character, "evening", market_data)

    # Keep existing analysis for market context
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

    # Market context
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

    lines = [
        "@everyone",
        opening,
        "",
        f"**🧠 The Psychology:**",
        psychology_intro,
        "",
        f"**☁️ The Vibe:**",
        f"Today carried {analysis['feel']}.{market_context}",
        f"Market Character: {character.replace('_', ' ').title()}",
        "",
        f"**✨ Reflection on Today:**",
        psychology_message,
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
    ]

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
