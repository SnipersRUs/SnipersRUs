#!/usr/bin/env python3
"""
Free Crypto LLM Discord Bot - Slash Commands Version
This version uses slash commands which don't require Message Content Intent
"""
import discord
from discord import app_commands
import os
import asyncio
import logging
import random
import requests
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

# Import our modules
try:
    from free_crypto_llm_bot.llm_client import OllamaClient
    from free_crypto_llm_bot.onchain_data import EtherscanClient, SolanaClient, BitcoinClient
    from free_crypto_llm_bot.market_data import CoinGeckoClient
    from free_crypto_llm_bot.news_sentiment import NewsFetcher, SentimentAnalyzer
    try:
        from free_crypto_llm_bot.web_search import WebSearcher, search_duckduckgo
    except ImportError:
        WebSearcher = None
        search_duckduckgo = None
    try:
        from free_crypto_llm_bot.bot_analyzer import BOT_INFO, check_bot_status, get_bot_trades, get_bot_summary
    except ImportError:
        BOT_INFO = {}
        check_bot_status = None
        get_bot_trades = None
        get_bot_summary = None
    try:
        from free_crypto_llm_bot.bot_scanner_integration import LiquidationScannerIntegration, ShortSniperIntegration
    except ImportError:
        LiquidationScannerIntegration = None
        ShortSniperIntegration = None
except ImportError:
    import sys
    from pathlib import Path
    bot_dir = Path(__file__).parent
    sys.path.insert(0, str(bot_dir.parent))
    from free_crypto_llm_bot.llm_client import OllamaClient
    from free_crypto_llm_bot.onchain_data import EtherscanClient, SolanaClient, BitcoinClient
    from free_crypto_llm_bot.market_data import CoinGeckoClient
    from free_crypto_llm_bot.news_sentiment import NewsFetcher, SentimentAnalyzer
    try:
        from free_crypto_llm_bot.web_search import WebSearcher, search_duckduckgo
    except ImportError:
        WebSearcher = None
        search_duckduckgo = None

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('free_crypto_llm_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')
SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')

# Discord intents (slash commands don't need any privileged intents)
intents = discord.Intents.default()
intents.message_content = False  # Not needed for slash commands
intents.members = False  # Not needed for slash commands

# Initialize clients
llm_client = OllamaClient(base_url=OLLAMA_URL, model=OLLAMA_MODEL)
etherscan = EtherscanClient(ETHERSCAN_API_KEY) if ETHERSCAN_API_KEY else None
solana = SolanaClient(rpc_url=SOLANA_RPC_URL)
bitcoin = BitcoinClient()
coingecko = CoinGeckoClient(api_key=COINGECKO_API_KEY)
news_fetcher = NewsFetcher()
sentiment_analyzer = SentimentAnalyzer()
web_searcher = WebSearcher() if WebSearcher else None
liquidation_scanner = LiquidationScannerIntegration() if LiquidationScannerIntegration else None
short_sniper_scanner = ShortSniperIntegration() if ShortSniperIntegration else None

# Discord client with slash commands
class CryptoBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync slash commands
        await self.tree.sync()
        logger.info("✅ Slash commands synced")

    async def on_ready(self):
        logger.info(f'✅ Bot logged in as {self.user}')
        logger.info(f'🤖 LLM Model: {OLLAMA_MODEL}')

        if llm_client.is_available():
            logger.info('✅ Ollama LLM is available')
        else:
            logger.warning('⚠️ Ollama LLM is not available')

        await self.change_presence(
            activity=discord.Game(name="Sniper Ready")
        )
        logger.info('🚀 Bot is ready!')

client = CryptoBot()

# ========== SLASH COMMANDS ==========

@client.tree.command(name="ask", description="Ask Sniper Guru a question (with web search for current info)")
@app_commands.describe(question="Your question")
async def ask_command(interaction: discord.Interaction, question: str):
    """Ask the LLM a general question with web search"""
    if not llm_client.is_available():
        await interaction.response.send_message(
            "❌ LLM is not available. Please ensure Ollama is running.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    # Search the web for current information
    search_results = []
    search_context = ""
    if search_duckduckgo:
        try:
            search_results = search_duckduckgo(question, max_results=3)
            if search_results and web_searcher:
                search_context = web_searcher.format_search_results(search_results, question)
        except Exception as e:
            logger.warning(f"Web search error: {e}")

    # Enhanced system prompt for Google-like responses
    system_prompt = f"""You are Sniper Guru, an expert assistant that provides comprehensive, Google-like information.

Your goal is to be HELPFUL and INFORMATIVE, not generic. Think like Google search results:
- Give direct, specific answers
- Provide details, numbers, and facts
- Explain concepts clearly
- Be comprehensive but concise

{search_context}

Answer the user's question in a helpful, informative way. Use the search results above for current information."""

    response = llm_client.query(question, system_prompt=system_prompt)
    await interaction.followup.send(f"**Sniper Guru:**\n>>> {response}")

@client.tree.command(name="askcrypto", description="Ask Sniper Guru a crypto question (with web search & current prices)")
@app_commands.describe(question="Your crypto question")
async def ask_crypto_command(interaction: discord.Interaction, question: str):
    """Ask the LLM a crypto-specific question with web search and current prices"""
    if not llm_client.is_available():
        await interaction.response.send_message("❌ LLM is not available.", ephemeral=True)
        return

    await interaction.response.defer()

    # Get current price context if question is about a specific coin
    price_context = ""
    question_lower = question.lower()
    coin_mentions = ["bitcoin", "btc", "ethereum", "eth", "solana", "sol", "cardano", "ada",
                     "polkadot", "dot", "chainlink", "link", "avalanche", "avax", "polygon", "matic"]
    for coin in coin_mentions:
        if coin in question_lower:
            coin_id_map = {
                "bitcoin": "bitcoin", "btc": "bitcoin",
                "ethereum": "ethereum", "eth": "ethereum",
                "solana": "solana", "sol": "solana",
                "cardano": "cardano", "ada": "cardano",
                "polkadot": "polkadot", "dot": "polkadot",
                "chainlink": "chainlink", "link": "chainlink",
                "avalanche": "avalanche-2", "avax": "avalanche-2",
                "polygon": "matic-network", "matic": "matic-network"
            }
            coin_id = coin_id_map.get(coin, coin)
            price_data = coingecko.get_price(coin_id)
            if price_data:
                price = price_data.get('price', 0)
                change_24h = price_data.get('change_24h', 0)
                market_cap = price_data.get('market_cap', 0)
                price_context = f"\n\n**CURRENT MARKET DATA:**\n{coin_id.upper()} Price: ${price:,.2f}\n24h Change: {change_24h:+.2f}%\nMarket Cap: ${market_cap:,.0f}\n\nUse this current data when discussing prices or market conditions."
            break

    # Search the web for current crypto information
    search_results = []
    search_context = ""
    if search_duckduckgo:
        try:
            crypto_query = f"cryptocurrency {question}"
            search_results = search_duckduckgo(crypto_query, max_results=3)
            if search_results and web_searcher:
                search_context = web_searcher.format_search_results(search_results, crypto_query)
        except Exception as e:
            logger.warning(f"Web search error: {e}")

    # Enhanced crypto system prompt
    system_prompt = llm_client.get_crypto_context_prompt()
    if price_context:
        system_prompt += price_context
    if search_context:
        system_prompt += f"\n\n{search_context}"

    system_prompt += "\n\n**Remember:** Be specific, informative, and helpful. Provide comprehensive answers like Google would. Include numbers, facts, and actionable insights."

    response = llm_client.query(question, system_prompt=system_prompt)
    await interaction.followup.send(f"**Sniper Guru:**\n>>> {response}")

@client.tree.command(name="price", description="Get cryptocurrency price")
@app_commands.describe(coin="Cryptocurrency name (e.g., bitcoin, ethereum)")
async def price_command(interaction: discord.Interaction, coin: str = "bitcoin"):
    """Get cryptocurrency price"""
    coin_map = {
        "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
        "bnb": "binancecoin", "ada": "cardano", "dot": "polkadot"
    }
    coin_id = coin_map.get(coin.lower(), coin.lower())

    await interaction.response.defer()
    price_data = coingecko.get_price(coin_id)

    if price_data:
        message_text = coingecko.format_price_message(coin_id, coin_id, price_data)
        await interaction.followup.send(message_text)
    else:
        await interaction.followup.send(
            f"❌ Could not find price for `{coin}`.\n"
            f"💡 Try using the CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')"
        )

@client.tree.command(name="trending", description="Get trending cryptocurrencies")
async def trending_command(interaction: discord.Interaction):
    """Get trending cryptocurrencies"""
    await interaction.response.defer()
    trending = coingecko.get_trending()

    if not trending:
        await interaction.followup.send("❌ Could not fetch trending coins.")
        return

    message_text = "🔥 **Trending Cryptocurrencies**\n\n"
    for i, item in enumerate(trending[:10], 1):
        coin = item.get('item', {})
        name = coin.get('name', 'Unknown')
        symbol = coin.get('symbol', '').upper()
        rank = coin.get('market_cap_rank', 'N/A')
        message_text += f"{i}. **{name}** ({symbol}) - Rank #{rank}\n"

    await interaction.followup.send(message_text)

@client.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Show help"""
    help_text = """🤖 **Sniper Guru Bot Commands**

**LLM Commands:**
`/ask <question>` - Ask the LLM a general question
`/askcrypto <question>` - Ask the LLM a crypto-specific question

**Market Data:**
`/price [coin]` - Get cryptocurrency price (default: Bitcoin)
`/trending` - Get trending cryptocurrencies
`/market` - Quick market overview

**Analysis & News:**
`/analyze <coin>` - Deep LLM analysis with current data
`/news <coin>` - Coin-specific news aggregation

**Utility:**
`/help` - Show this help message
`/status` - Check bot and LLM status

**Fun Commands:**
`/gm` - Say good morning! 🌅
`/gn` - Say good night! 🌙

**Bot Management:**
`/bots` - List all available trading bots
`/scanbot <bot_name>` - Scan and analyze a specific bot

**Live Bot Scans:**
`/scanliquidation [timeframe] [max_distance]` - Scan for coins near liquidation stacks
`/scansniper [deviation] [direction]` - Scan for coins at deviation VWAP zones

**Note:** This bot uses slash commands. Type `/` to see all commands!
"""
    await interaction.response.send_message(help_text, ephemeral=True)

@client.tree.command(name="status", description="Check bot status")
async def status_command(interaction: discord.Interaction):
    """Check bot status"""
    llm_status = "✅ Available" if llm_client.is_available() else "❌ Not Available"
    etherscan_status = "✅ Configured" if etherscan else "❌ Not Configured"
    coingecko_status = "✅ Configured" if COINGECKO_API_KEY else "⚠️ Using Public API"

    status_text = f"""🤖 **Bot Status**

**LLM (Ollama):**
- Status: {llm_status}
- Model: {OLLAMA_MODEL}
- URL: {OLLAMA_URL}

**APIs:**
- Etherscan: {etherscan_status}
- CoinGecko: {coingecko_status}
- Solana RPC: ✅ Public Endpoint
- Bitcoin API: ✅ Blockstream

**Bot Info:**
- Uptime: Online
- Commands: Use `/help` for full list
"""
    await interaction.response.send_message(status_text, ephemeral=True)

@client.tree.command(name="market", description="Get quick market overview")
async def market_command(interaction: discord.Interaction):
    """Get overall market overview"""
    await interaction.response.defer()

    # Get top cryptocurrencies
    top_coins = ["bitcoin", "ethereum", "solana", "binancecoin", "cardano"]
    prices = coingecko.get_multiple_prices(top_coins)

    # Calculate total market data
    total_market_cap = 0
    total_volume = 0
    btc_price = 0
    btc_change = 0

    market_data = {}
    for coin_id in top_coins:
        if coin_id in prices:
            data = prices[coin_id]
            market_cap = data.get('usd_market_cap', 0)
            volume = data.get('usd_24h_vol', 0)
            total_market_cap += market_cap
            total_volume += volume

            if coin_id == "bitcoin":
                btc_price = data.get('usd', 0)
                btc_change = data.get('usd_24h_change', 0)

            market_data[coin_id] = {
                'price': data.get('usd', 0),
                'change': data.get('usd_24h_change', 0),
                'market_cap': market_cap
            }

    # Format market overview
    message = "📊 **Market Overview**\n\n"
    message += f"💰 **Total Market Cap:** ${total_market_cap:,.0f}\n"
    message += f"💵 **24h Volume:** ${total_volume:,.0f}\n\n"

    message += "**Top Cryptocurrencies:**\n"
    coin_names = {
        "bitcoin": "BTC",
        "ethereum": "ETH",
        "solana": "SOL",
        "binancecoin": "BNB",
        "cardano": "ADA"
    }

    for coin_id in top_coins:
        if coin_id in market_data:
            data = market_data[coin_id]
            name = coin_names.get(coin_id, coin_id.upper())
            price = data['price']
            change = data['change']
            emoji = "🟢" if change >= 0 else "🔴"

            price_str = f"${price:,.2f}" if price >= 0.01 else f"${price:.6f}"
            message += f"{emoji} **{name}:** {price_str} ({change:+.2f}%)\n"

    message += f"\n📈 **BTC Dominance:** {((market_data.get('bitcoin', {}).get('market_cap', 0) / total_market_cap) * 100):.2f}%"

    await interaction.followup.send(message)

@client.tree.command(name="analyze", description="Deep LLM analysis of a cryptocurrency with current data")
@app_commands.describe(coin="Cryptocurrency to analyze (e.g., bitcoin, ethereum)")
async def analyze_command(interaction: discord.Interaction, coin: str):
    """Deep analysis of a cryptocurrency using LLM + current data"""
    if not llm_client.is_available():
        await interaction.response.send_message("❌ LLM is not available.", ephemeral=True)
        return

    await interaction.response.defer()

    # Get current market data
    coin_map = {
        "btc": "bitcoin", "bitcoin": "bitcoin",
        "eth": "ethereum", "ethereum": "ethereum",
        "sol": "solana", "solana": "solana",
        "bnb": "binancecoin", "binancecoin": "binancecoin",
        "ada": "cardano", "cardano": "cardano",
        "dot": "polkadot", "polkadot": "polkadot",
        "link": "chainlink", "chainlink": "chainlink",
        "avax": "avalanche-2", "avalanche": "avalanche-2",
        "matic": "matic-network", "polygon": "matic-network"
    }

    coin_id = coin_map.get(coin.lower(), coin.lower())
    price_data = coingecko.get_price(coin_id)
    coin_info = coingecko.get_coin_info(coin_id) if price_data else None

    # Build comprehensive context
    analysis_context = f"""**COMPREHENSIVE ANALYSIS REQUEST FOR {coin_id.upper()}**

CURRENT MARKET DATA:"""

    if price_data:
        price = price_data.get('price', 0)
        market_cap = price_data.get('market_cap', 0)
        volume_24h = price_data.get('volume_24h', 0)
        change_24h = price_data.get('change_24h', 0)

        analysis_context += f"""
- Current Price: ${price:,.2f}
- Market Cap: ${market_cap:,.0f}
- 24h Volume: ${volume_24h:,.0f}
- 24h Change: {change_24h:+.2f}%
"""

    if coin_info:
        analysis_context += f"""
- Rank: #{coin_info.get('market_cap_rank', 'N/A')}
- Circulating Supply: {coin_info.get('market_data', {}).get('circulating_supply', 0):,.0f}
- Total Supply: {coin_info.get('market_data', {}).get('total_supply', 0):,.0f}
"""

    # Search for recent news/analysis
    search_results = []
    if search_duckduckgo:
        try:
            search_query = f"{coin_id} cryptocurrency analysis 2024"
            search_results = search_duckduckgo(search_query, max_results=3)
        except Exception as e:
            logger.warning(f"Search error: {e}")

    if search_results and web_searcher:
        analysis_context += f"\n{web_searcher.format_search_results(search_results, search_query)}"

    # Enhanced analysis prompt
    analysis_prompt = f"""You are Sniper Guru, a cryptocurrency analysis expert. Provide a comprehensive, in-depth analysis of {coin_id.upper()}.

{analysis_context}

**Provide a detailed analysis covering:**
1. **Current Market Position**: Price analysis, market cap ranking, recent performance
2. **Technical Analysis**: Support/resistance levels, trend analysis, key indicators
3. **Fundamental Analysis**: Project strengths, use cases, technology, team
4. **Market Sentiment**: Recent news impact, community sentiment, adoption trends
5. **Risk Assessment**: Potential risks, volatility, market conditions
6. **Outlook**: Short-term and medium-term outlook based on current data

Be specific, use numbers and data points, and provide actionable insights. This is not financial advice."""

    response = llm_client.query(
        f"Provide a comprehensive analysis of {coin_id.upper()} cryptocurrency.",
        system_prompt=analysis_prompt
    )

    await interaction.followup.send(f"**Sniper Guru Analysis - {coin_id.upper()}:**\n>>> {response}")

@client.tree.command(name="news", description="Get coin-specific news aggregation")
@app_commands.describe(coin="Cryptocurrency to get news for (e.g., bitcoin, ethereum)")
async def news_command(interaction: discord.Interaction, coin: str):
    """Get news for a specific cryptocurrency"""
    await interaction.response.defer()

    # Map coin names
    coin_map = {
        "btc": "Bitcoin", "bitcoin": "Bitcoin",
        "eth": "Ethereum", "ethereum": "Ethereum",
        "sol": "Solana", "solana": "Solana",
        "bnb": "Binance Coin", "binancecoin": "Binance Coin",
        "ada": "Cardano", "cardano": "Cardano"
    }

    coin_name = coin_map.get(coin.lower(), coin.capitalize())

    # Fetch general crypto news
    articles = news_fetcher.fetch_news(limit=10)

    # Filter for coin-specific news
    coin_articles = []
    search_terms = [coin.lower(), coin_name.lower()]

    for article in articles:
        title_lower = article.get('title', '').lower()
        summary_lower = article.get('summary', '').lower()

        # Check if article mentions the coin
        if any(term in title_lower or term in summary_lower for term in search_terms):
            coin_articles.append(article)

    # If no specific news, get general crypto news
    if not coin_articles:
        coin_articles = articles[:5]
        message = f"📰 **Latest Crypto News** (No specific {coin_name} news found, showing general crypto news)\n\n"
    else:
        message = f"📰 **{coin_name} News**\n\n"

    # Format news
    for i, article in enumerate(coin_articles[:5], 1):
        title = article['title'][:100]
        link = article['link']
        source = article['source'].title()
        published = article['published'].strftime('%Y-%m-%d %H:%M') if article['published'] else "Unknown"

        message += f"{i}. **{title}**\n"
        message += f"   📅 {published} | 📰 {source}\n"
        message += f"   🔗 {link}\n\n"

    # Add sentiment analysis if available
    if coin_articles and sentiment_analyzer.method:
        sentiment_data = sentiment_analyzer.analyze_news(coin_articles[:5])
        overall = sentiment_data.get('overall_sentiment', 'neutral')
        score = sentiment_data.get('overall_score', 0.0)

        emoji_map = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}
        emoji = emoji_map.get(overall, "🟡")

        message += f"\n{emoji} **Sentiment:** {overall.upper()} (Score: {score:.3f})"

    await interaction.followup.send(message)

# ========== GM/GN COMMANDS ==========

# GM (Good Morning) phrases
GM_PHRASES = [
    "🌅 Good morning! Rise and grind, sniper!",
    "☀️ Morning! Time to catch those green candles!",
    "🌄 Good morning! Let's make today profitable!",
    "☕ Morning vibes! Ready to snipe some trades?",
    "🌞 Good morning! May your charts be green today!",
    "🚀 Morning! Time to stack some sats!",
    "💎 Good morning! Diamond hands only!",
    "📈 Morning! Let's find those perfect entries!",
    "⚡ Good morning! Time to charge up and trade!",
    "🎯 Morning! Lock and load, sniper!",
    "🔥 Good morning! Let's set the market on fire!",
    "💪 Morning! Time to flex those trading skills!",
    "🌟 Good morning! Shine bright like Bitcoin!",
    "🎲 Morning! Let's roll the dice on some trades!",
    "⚔️ Good morning! Ready for battle, warrior?"
]

# GN (Good Night) phrases
GN_PHRASES = [
    "🌙 Good night! Rest up for tomorrow's trades!",
    "🌃 Night! May your dreams be filled with green candles!",
    "🌌 Good night! Sleep well, sniper!",
    "🌉 Night! See you on the charts tomorrow!",
    "🌠 Good night! Dream of those perfect setups!",
    "💤 Night! Rest those diamond hands!",
    "🌛 Good night! Tomorrow's another trading day!",
    "🌜 Night! May your portfolio grow while you sleep!",
    "⭐ Good night! Stars align for tomorrow's trades!",
    "🌆 Night! Close those positions and rest!",
    "🌇 Good night! Sunset on another trading day!",
    "🌃 Night! Time to recharge those sniper skills!",
    "🌉 Good night! Bridge to tomorrow's opportunities!",
    "🌌 Night! Sleep tight, crypto warrior!",
    "🌠 Good night! Shooting stars for tomorrow's gains!"
]

@client.tree.command(name="gm", description="Say good morning!")
async def gm_command(interaction: discord.Interaction):
    """Good morning command with random phrase"""
    phrase = random.choice(GM_PHRASES)
    await interaction.response.send_message(phrase)

@client.tree.command(name="gn", description="Say good night!")
async def gn_command(interaction: discord.Interaction):
    """Good night command with random phrase"""
    phrase = random.choice(GN_PHRASES)
    await interaction.response.send_message(phrase)

@client.tree.command(name="scanbot", description="Scan and analyze one of your trading bots")
@app_commands.describe(bot_name="Bot to scan (short_sniper, pivotx, mcro, cloudflare, liquidation, traditional, forex)")
async def scanbot_command(interaction: discord.Interaction, bot_name: str):
    """Scan and analyze an existing trading bot"""
    if not BOT_INFO or not check_bot_status:
        await interaction.response.send_message(
            "❌ Bot analyzer not available. Bot analyzer module may have issues.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    bot_key = bot_name.lower()
    if bot_key not in BOT_INFO:
        available = ", ".join(BOT_INFO.keys())
        await interaction.followup.send(
            f"❌ Bot '{bot_name}' not found.\n\n**Available bots:**\n{available}\n\nUse: `/scanbot <bot_name>`"
        )
        return

    # Get bot summary
    summary = get_bot_summary(bot_key)

    # Get recent trades if available
    trades = []
    if get_bot_trades:
        try:
            trades = get_bot_trades(bot_key, limit=3)
        except Exception as e:
            logger.warning(f"Could not get trades: {e}")

    message = summary

    if trades:
        message += "\n**Recent Activity:**\n"
        for i, trade in enumerate(trades[:3], 1):
            # Format trade info (structure varies by bot)
            trade_str = f"{i}. "
            if 'symbol' in trade:
                trade_str += f"{trade['symbol']} "
            if 'side' in trade:
                trade_str += f"{trade['side'].upper()} "
            if 'entry_price' in trade:
                trade_str += f"@ ${trade['entry_price']:.2f} "
            if 'pnl' in trade:
                pnl = trade['pnl']
                emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                trade_str += f"{emoji} P&L: ${pnl:.2f}"
            message += trade_str + "\n"

    await interaction.followup.send(message)

@client.tree.command(name="bots", description="List all available trading bots")
async def bots_command(interaction: discord.Interaction):
    """List all available trading bots"""
    if not BOT_INFO:
        await interaction.response.send_message(
            "❌ Bot information not available.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    message = "🤖 **Available Trading Bots**\n\n"

    for bot_key, bot_info in BOT_INFO.items():
        status = check_bot_status(bot_key) if check_bot_status else {"running": False}
        status_emoji = "🟢" if status.get("running") else "🔴"

        message += f"{status_emoji} **{bot_info['name']}** (`{bot_key}`)\n"
        message += f"   {bot_info['description']}\n"
        message += f"   Focus: {bot_info['focus']}\n\n"

    message += "**Usage:** `/scanbot <bot_name>` to get detailed info about a specific bot"

    await interaction.followup.send(message)

@client.tree.command(name="scanliquidation", description="Scan for coins close to liquidation stacks")
@app_commands.describe(
    timeframe="Timeframe to check (15m, 1h, 1d)",
    max_distance="Maximum distance from liquidation level (%)"
)
async def scanliquidation_command(interaction: discord.Interaction, timeframe: str = "15m", max_distance: float = 5.0):
    """Scan for coins close to liquidation stacks"""
    if not liquidation_scanner:
        await interaction.response.send_message(
            "❌ Liquidation scanner not available.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    # Validate timeframe
    if timeframe not in ["15m", "1h", "1d"]:
        await interaction.followup.send(
            "❌ Invalid timeframe. Use: 15m, 1h, or 1d"
        )
        return

    # Scan for liquidation stacks
    results = liquidation_scanner.scan_for_liquidation_stacks(
        timeframe=timeframe,
        max_distance_pct=max_distance
    )

    if not results:
        await interaction.followup.send(
            f"❌ No coins found within {max_distance}% of {timeframe} liquidation levels."
        )
        return

    # Format results
    message = f"🔍 **Liquidation Scanner Results ({timeframe})**\n\n"
    message += f"Found **{len(results)}** coins within **{max_distance}%** of liquidation levels:\n\n"

    for i, result in enumerate(results[:10], 1):  # Top 10
        symbol = result['symbol'].replace('/USDT', '')
        distance = result['distance_pct']
        importance = result['importance']
        liq_type = result['type']
        current_price = result['current_price']
        liq_level = result['liquidation_level']

        emoji = "🔴" if distance < 1.0 else "🟡" if distance < 3.0 else "🟢"
        type_emoji = "⬆️" if liq_type == "top" else "⬇️"

        message += f"{i}. {emoji} **{symbol}** {type_emoji}\n"
        message += f"   Price: ${current_price:,.2f} | Liq Level: ${liq_level:,.2f}\n"
        message += f"   Distance: {distance:.2f}% | Importance: {importance:.0f}/100\n\n"

    if len(results) > 10:
        message += f"... and {len(results) - 10} more"

    await interaction.followup.send(message)

@client.tree.command(name="scansniper", description="Scan for coins at deviation VWAP zones")
@app_commands.describe(
    deviation="Deviation level (2 for 2a+, 3 for 3a+)",
    direction="Direction: above (shorts) or below (longs)"
)
async def scansniper_command(interaction: discord.Interaction, deviation: int = 2, direction: str = "above"):
    """Scan for coins at deviation VWAP zones"""
    if not short_sniper_scanner:
        await interaction.response.send_message(
            "❌ Short sniper scanner not available.",
            ephemeral=True
        )
        return

    if deviation not in [2, 3]:
        await interaction.response.send_message(
            "❌ Deviation must be 2 (2a+) or 3 (3a+)",
            ephemeral=True
        )
        return

    if direction not in ["above", "below"]:
        await interaction.response.send_message(
            "❌ Direction must be 'above' (shorts) or 'below' (longs)",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    # Scan for deviation VWAP zones
    results = short_sniper_scanner.scan_for_deviation_vwap(
        deviation_level=deviation,
        direction=direction
    )

    if not results:
        zone_name = f"{deviation}a+"
        await interaction.followup.send(
            f"❌ No coins found at {zone_name} zone ({direction} VWAP)."
        )
        return

    # Format results
    zone_name = f"{deviation}a+"
    direction_text = "SHORT" if direction == "above" else "LONG"
    message = f"🎯 **Deviation VWAP Scanner - {zone_name} Zone**\n\n"
    message += f"Found **{len(results)}** coins at **{zone_name}** zone ({direction_text} opportunities):\n\n"

    for i, result in enumerate(results[:10], 1):  # Top 10
        symbol = result['symbol'].replace('/USDT', '')
        price = result['current_price']
        vwap = result['vwap']
        dev_sigma = result['deviation_sigma']
        distance = result['distance_from_band']

        if direction == "above":
            band_price = result.get('upper2' if deviation == 2 else 'upper3', 0)
            message += f"{i}. **{symbol}** ⬆️ SHORT\n"
        else:
            band_price = result.get('lower2' if deviation == 2 else 'lower3', 0)
            message += f"{i}. **{symbol}** ⬇️ LONG\n"

        message += f"   Price: ${price:,.2f} | VWAP: ${vwap:,.2f}\n"
        message += f"   Deviation: {dev_sigma:.2f}σ | Band: ${band_price:,.2f}\n"
        message += f"   Distance from band: ${abs(distance):,.2f}\n\n"

    if len(results) > 10:
        message += f"... and {len(results) - 10} more"

    await interaction.followup.send(message)

# ========== MAIN ==========

def main():
    """Main entry point"""
    if not DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN not found in environment variables!")
        return

    logger.info("🚀 Starting Free Crypto LLM Discord Bot (Slash Commands)...")
    client.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
