#!/usr/bin/env python3
"""
Free Crypto LLM Discord Bot
A completely free-tier crypto analysis bot using local LLMs and free APIs
"""
import discord
import os
import sys
import asyncio
import logging
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

# Import our modules
# Handle both module import and direct execution
try:
    from free_crypto_llm_bot.llm_client import OllamaClient
    from free_crypto_llm_bot.onchain_data import EtherscanClient, SolanaClient, BitcoinClient
    from free_crypto_llm_bot.market_data import CoinGeckoClient
    from free_crypto_llm_bot.news_sentiment import NewsFetcher, SentimentAnalyzer
except ImportError:
    # If running as a script directly, use relative imports
    import sys
    from pathlib import Path
    bot_dir = Path(__file__).parent
    sys.path.insert(0, str(bot_dir.parent))
    from free_crypto_llm_bot.llm_client import OllamaClient
    from free_crypto_llm_bot.onchain_data import EtherscanClient, SolanaClient, BitcoinClient
    from free_crypto_llm_bot.market_data import CoinGeckoClient
    from free_crypto_llm_bot.news_sentiment import NewsFetcher, SentimentAnalyzer

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
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')  # Optional
SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')

# Discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Initialize clients
llm_client = OllamaClient(base_url=OLLAMA_URL, model=OLLAMA_MODEL)
etherscan = EtherscanClient(ETHERSCAN_API_KEY) if ETHERSCAN_API_KEY else None
solana = SolanaClient(rpc_url=SOLANA_RPC_URL)
bitcoin = BitcoinClient()
coingecko = CoinGeckoClient(api_key=COINGECKO_API_KEY)
news_fetcher = NewsFetcher()
sentiment_analyzer = SentimentAnalyzer()

# Discord client
client = discord.Client(intents=intents)

# Command prefix
PREFIX = '!'


@client.event
async def on_ready():
    """Called when the bot is ready"""
    logger.info(f'✅ Bot logged in as {client.user}')
    logger.info(f'🤖 LLM Model: {OLLAMA_MODEL}')
    logger.info(f'🔗 LLM URL: {OLLAMA_URL}')

    # Check if Ollama is available
    if llm_client.is_available():
        logger.info('✅ Ollama LLM is available')
    else:
        logger.warning('⚠️ Ollama LLM is not available. LLM commands will not work.')

    # Set bot status
    await client.change_presence(
        activity=discord.Game(name=f"{PREFIX}help | Free Crypto LLM Bot")
    )

    logger.info('🚀 Bot is ready!')


@client.event
async def on_message(message):
    """Handle incoming messages"""
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Only respond to commands
    if not message.content.startswith(PREFIX):
        return

    # Parse command
    parts = message.content[len(PREFIX):].strip().split(' ', 1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    try:
        # LLM Commands
        if command == 'ask' or command == 'askllm':
            await handle_ask_command(message, args)

        elif command == 'askcrypto':
            await handle_ask_crypto_command(message, args)

        # Market Data Commands
        elif command == 'price':
            await handle_price_command(message, args)

        elif command == 'trending':
            await handle_trending_command(message)

        # On-Chain Commands
        elif command == 'ethblock' or command == 'ethereum':
            await handle_eth_block_command(message)

        elif command == 'solblock' or command == 'solana':
            await handle_sol_block_command(message)

        elif command == 'btcblock' or command == 'bitcoin':
            await handle_btc_block_command(message)

        elif command == 'ethbalance':
            await handle_eth_balance_command(message, args)

        elif command == 'solbalance':
            await handle_sol_balance_command(message, args)

        # News & Sentiment Commands
        elif command == 'news':
            await handle_news_command(message, args)

        elif command == 'sentiment':
            await handle_sentiment_command(message)

        # Utility Commands
        elif command == 'help':
            await handle_help_command(message)

        elif command == 'status':
            await handle_status_command(message)

    except Exception as e:
        logger.error(f"Error handling command {command}: {e}", exc_info=True)
        await message.channel.send(f"❌ An error occurred: {str(e)}")


# ========== COMMAND HANDLERS ==========

async def handle_ask_command(message, question: str):
    """Handle !ask command - general LLM question"""
    if not question:
        await message.channel.send("❌ Please ask a question. Usage: `!ask <your question>`")
        return

    # Check if LLM is available
    if not llm_client.is_available():
        await message.channel.send(
            "❌ LLM is not available. Please ensure Ollama is running:\n"
            "```bash\nollama serve\n```"
        )
        return

    # Show typing indicator
    async with message.channel.typing():
        response = llm_client.query(question)
        await message.channel.send(f"**🤖 LLM Response:**\n>>> {response}")


async def handle_ask_crypto_command(message, question: str):
    """Handle !askcrypto command - crypto-specific LLM question"""
    if not question:
        await message.channel.send("❌ Please ask a crypto question. Usage: `!askcrypto <your question>`")
        return

    if not llm_client.is_available():
        await message.channel.send("❌ LLM is not available. Please ensure Ollama is running.")
        return

    async with message.channel.typing():
        system_prompt = llm_client.get_crypto_context_prompt()
        response = llm_client.query(question, system_prompt=system_prompt)
        await message.channel.send(f"**🤖 Crypto Expert:**\n>>> {response}")


async def handle_price_command(message, coin: str):
    """Handle !price command - get cryptocurrency price"""
    if not coin:
        coin = "bitcoin"  # Default to Bitcoin

    # Common coin mappings
    coin_map = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "sol": "solana",
        "bnb": "binancecoin",
        "ada": "cardano",
        "dot": "polkadot",
        "matic": "matic-network",
        "avax": "avalanche-2",
        "link": "chainlink",
        "xrp": "ripple"
    }

    coin_id = coin_map.get(coin.lower(), coin.lower())

    async with message.channel.typing():
        price_data = coingecko.get_price(coin_id)

        if price_data:
            message_text = coingecko.format_price_message(coin_id, coin_id, price_data)
            await message.channel.send(message_text)
        else:
            await message.channel.send(
                f"❌ Could not find price for `{coin}`.\n"
                f"💡 Try using the CoinGecko coin ID (e.g., 'bitcoin', 'ethereum', 'solana')"
            )


async def handle_trending_command(message):
    """Handle !trending command - get trending cryptocurrencies"""
    async with message.channel.typing():
        trending = coingecko.get_trending()

        if not trending:
            await message.channel.send("❌ Could not fetch trending coins.")
            return

        message_text = "🔥 **Trending Cryptocurrencies**\n\n"

        for i, item in enumerate(trending[:10], 1):
            coin = item.get('item', {})
            name = coin.get('name', 'Unknown')
            symbol = coin.get('symbol', '').upper()
            rank = coin.get('market_cap_rank', 'N/A')

            message_text += f"{i}. **{name}** ({symbol}) - Rank #{rank}\n"

        await message.channel.send(message_text)


async def handle_eth_block_command(message):
    """Handle !ethblock command - get latest Ethereum block"""
    if not etherscan:
        await message.channel.send("❌ Etherscan API key not configured.")
        return

    async with message.channel.typing():
        block_number = etherscan.get_latest_block()

        if block_number:
            block_info = etherscan.get_block_info(block_number)
            if block_info:
                tx_count = len(block_info.get('transactions', []))
                gas_used = int(block_info.get('gasUsed', '0x0'), 16)
                gas_limit = int(block_info.get('gasLimit', '0x0'), 16)

                message_text = f"""🔗 **Latest Ethereum Block**
📦 **Block Number:** {block_number:,}
⛽ **Gas Used:** {gas_used:,} / {gas_limit:,}
📝 **Transactions:** {tx_count}
🕐 **Timestamp:** {datetime.fromtimestamp(int(block_info.get('timestamp', '0x0'), 16)).strftime('%Y-%m-%d %H:%M:%S')}"""
            else:
                message_text = f"🔗 **Latest Ethereum Block:** {block_number:,}"

            await message.channel.send(message_text)
        else:
            await message.channel.send("❌ Could not fetch Ethereum block data.")


async def handle_sol_block_command(message):
    """Handle !solblock command - get latest Solana block"""
    async with message.channel.typing():
        slot = solana.get_slot()
        block_height = solana.get_block_height()

        if slot or block_height:
            message_text = "🔗 **Latest Solana Block**\n"
            if slot:
                message_text += f"🎰 **Slot:** {slot:,}\n"
            if block_height:
                message_text += f"📦 **Block Height:** {block_height:,}"
            await message.channel.send(message_text)
        else:
            await message.channel.send("❌ Could not fetch Solana block data.")


async def handle_btc_block_command(message):
    """Handle !btcblock command - get latest Bitcoin block"""
    async with message.channel.typing():
        block_height = bitcoin.get_latest_block_height()

        if block_height:
            block_info = bitcoin.get_block_info(block_height)
            if block_info:
                tx_count = block_info.get('tx_count', 0)
                size = block_info.get('size', 0)

                message_text = f"""🔗 **Latest Bitcoin Block**
📦 **Block Height:** {block_height:,}
📝 **Transactions:** {tx_count}
💾 **Size:** {size:,} bytes"""
            else:
                message_text = f"🔗 **Latest Bitcoin Block:** {block_height:,}"

            await message.channel.send(message_text)
        else:
            await message.channel.send("❌ Could not fetch Bitcoin block data.")


async def handle_eth_balance_command(message, address: str):
    """Handle !ethbalance command - get Ethereum address balance"""
    if not address:
        await message.channel.send("❌ Please provide an Ethereum address. Usage: `!ethbalance <address>`")
        return

    if not etherscan:
        await message.channel.send("❌ Etherscan API key not configured.")
        return

    async with message.channel.typing():
        balance = etherscan.get_balance(address)

        if balance is not None:
            await message.channel.send(f"💰 **Ethereum Balance**\n**Address:** `{address[:10]}...{address[-8:]}`\n**Balance:** {balance:.6f} ETH")
        else:
            await message.channel.send("❌ Could not fetch balance. Please check the address.")


async def handle_sol_balance_command(message, address: str):
    """Handle !solbalance command - get Solana address balance"""
    if not address:
        await message.channel.send("❌ Please provide a Solana address. Usage: `!solbalance <address>`")
        return

    async with message.channel.typing():
        balance = solana.get_balance(address)

        if balance is not None:
            await message.channel.send(f"💰 **Solana Balance**\n**Address:** `{address[:10]}...{address[-8:]}`\n**Balance:** {balance:.6f} SOL")
        else:
            await message.channel.send("❌ Could not fetch balance. Please check the address.")


async def handle_news_command(message, source: str):
    """Handle !news command - get latest crypto news"""
    async with message.channel.typing():
        articles = news_fetcher.fetch_news(source=source if source else None, limit=5)
        message_text = news_fetcher.format_news_message(articles, limit=5)
        await message.channel.send(message_text)


async def handle_sentiment_command(message):
    """Handle !sentiment command - analyze market sentiment"""
    async with message.channel.typing():
        # Fetch recent news
        articles = news_fetcher.fetch_news(limit=10)

        if not articles:
            await message.channel.send("❌ Could not fetch news for sentiment analysis.")
            return

        # Analyze sentiment
        sentiment_data = sentiment_analyzer.analyze_news(articles)
        message_text = sentiment_analyzer.format_sentiment_message(sentiment_data)
        await message.channel.send(message_text)


async def handle_help_command(message):
    """Handle !help command - show available commands"""
    help_text = f"""🤖 **Free Crypto LLM Bot Commands**

**LLM Commands:**
`{PREFIX}ask <question>` - Ask the LLM a general question
`{PREFIX}askcrypto <question>` - Ask the LLM a crypto-specific question

**Market Data:**
`{PREFIX}price [coin]` - Get cryptocurrency price (default: Bitcoin)
`{PREFIX}trending` - Get trending cryptocurrencies

**On-Chain Data:**
`{PREFIX}ethblock` - Get latest Ethereum block info
`{PREFIX}solblock` - Get latest Solana block info
`{PREFIX}btcblock` - Get latest Bitcoin block info
`{PREFIX}ethbalance <address>` - Get Ethereum address balance
`{PREFIX}solbalance <address>` - Get Solana address balance

**News & Sentiment:**
`{PREFIX}news [source]` - Get latest crypto news
`{PREFIX}sentiment` - Analyze market sentiment from news

**Utility:**
`{PREFIX}help` - Show this help message
`{PREFIX}status` - Check bot and LLM status

**Examples:**
`{PREFIX}ask What is DeFi?`
`{PREFIX}askcrypto Explain the difference between PoW and PoS`
`{PREFIX}price ethereum`
`{PREFIX}ethblock`
`{PREFIX}news cointelegraph`
"""

    await message.channel.send(help_text)


async def handle_status_command(message):
    """Handle !status command - check bot status"""
    # Check LLM availability
    llm_status = "✅ Available" if llm_client.is_available() else "❌ Not Available"

    # Check API availability
    etherscan_status = "✅ Configured" if etherscan else "❌ Not Configured"
    coingecko_status = "✅ Configured" if COINGECKO_API_KEY else "⚠️ Using Public API"
    sentiment_status = "✅ Available" if sentiment_analyzer.method else "❌ Not Available"

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
- Sentiment Analysis: {sentiment_status}

**Bot Info:**
- Uptime: Online
- Commands: {PREFIX}help for full list
"""

    await message.channel.send(status_text)


# ========== MAIN ==========

def main():
    """Main entry point"""
    if not DISCORD_TOKEN:
        logger.error("❌ DISCORD_TOKEN not found in environment variables!")
        logger.error("Please set DISCORD_TOKEN in your .env file")
        return

    logger.info("🚀 Starting Free Crypto LLM Discord Bot...")

    try:
        client.run(DISCORD_TOKEN)
    except discord.errors.PrivilegedIntentsRequired as e:
        logger.error("=" * 60)
        logger.error("❌ PRIVILEGED INTENTS NOT ENABLED!")
        logger.error("=" * 60)
        logger.error("")
        logger.error("The bot needs 'Message Content Intent' enabled in Discord.")
        logger.error("")
        logger.error("🔗 Go to this URL to enable it:")
        logger.error("   https://discord.com/developers/applications/1454983045089333382/bot")
        logger.error("")
        logger.error("Steps:")
        logger.error("   1. Scroll to 'Privileged Gateway Intents'")
        logger.error("   2. Enable 'MESSAGE CONTENT INTENT'")
        logger.error("   3. Click 'Save Changes'")
        logger.error("   4. Restart this bot")
        logger.error("")
        logger.error("Or run: python3 free_crypto_llm_bot/enable_intent_helper.py")
        logger.error("")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
