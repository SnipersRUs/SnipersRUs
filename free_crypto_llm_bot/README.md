# Free Crypto LLM Discord Bot 🤖💰

A completely **free-tier** cryptocurrency Discord bot powered by local LLMs and free APIs. Get real-time crypto data, on-chain information, news, sentiment analysis, and AI-powered insights—all without spending a dime!

## ✨ Features

- **🤖 Local LLM Integration**: Powered by Ollama (Mistral, Llama 3, etc.) - completely free and private
- **💰 Market Data**: Real-time prices, market cap, volume via CoinGecko (free tier)
- **🔗 On-Chain Data**: Ethereum (Etherscan), Solana (public RPC), Bitcoin (Blockstream)
- **📰 News & Sentiment**: Crypto news from RSS feeds + sentiment analysis (VADER/TextBlob)
- **💬 Discord Commands**: Easy-to-use commands for all features
- **🆓 100% Free**: Uses only free-tier APIs and open-source tools

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Ollama** installed and running ([Download here](https://ollama.com))
3. **Discord Bot** created ([Discord Developer Portal](https://discord.com/developers/applications))

### Step 1: Install Ollama and Pull a Model

```bash
# Install Ollama (follow instructions for your OS at ollama.com)
# Then pull a model:
ollama pull mistral
# OR
ollama pull llama3
```

Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

### Step 2: Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** → Give it a name
3. Go to **"Bot"** tab → Click **"Add Bot"**
4. Under **"Token"**, click **"Reset Token"** → Copy your token (keep it secret!)
5. Enable **"Message Content Intent"** (required for reading messages)
6. Go to **"OAuth2" → "URL Generator"**:
   - Select `bot` scope
   - Select permissions: `Send Messages`, `Read Message History`, `Use Slash Commands`
   - Copy the generated URL and invite bot to your server

### Step 3: Get Free API Keys (Optional but Recommended)

#### Etherscan (For Ethereum on-chain data)
1. Go to [Etherscan API](https://etherscan.io/apis)
2. Register a free account
3. Get your API key
4. Free tier: 5 calls/second, 100,000 calls/day

#### CoinGecko (For better rate limits)
1. Go to [CoinGecko API](https://www.coingecko.com/en/api)
2. Register a free account
3. Get your API key
4. Free tier: 50 calls/minute (vs 10-50 without key)

### Step 4: Install Dependencies

```bash
# Navigate to project directory
cd free_crypto_llm_bot

# Install Python packages
pip install -r ../requirements.txt
```

Or install individually:
```bash
pip install discord.py python-dotenv requests feedparser vaderSentiment textblob
```

### Step 5: Configure Environment Variables

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env and add your tokens/keys
nano .env  # or use your favorite editor
```

Required:
- `DISCORD_TOKEN` - Your Discord bot token

Optional (but recommended):
- `ETHERSCAN_API_KEY` - For Ethereum on-chain data
- `COINGECKO_API_KEY` - For better rate limits
- `OLLAMA_URL` - If Ollama is not on localhost:11434
- `OLLAMA_MODEL` - Model name (default: mistral)

### Step 6: Run the Bot

```bash
# From the project root
python -m free_crypto_llm_bot.bot
```

Or:
```bash
cd free_crypto_llm_bot
python bot.py
```

You should see:
```
✅ Bot logged in as YourBotName#1234
✅ Ollama LLM is available
🚀 Bot is ready!
```

## 📖 Commands

### LLM Commands
- `!ask <question>` - Ask the LLM a general question
- `!askcrypto <question>` - Ask the LLM a crypto-specific question

### Market Data
- `!price [coin]` - Get cryptocurrency price (default: Bitcoin)
  - Examples: `!price`, `!price ethereum`, `!price solana`
- `!trending` - Get top trending cryptocurrencies

### On-Chain Data
- `!ethblock` - Get latest Ethereum block info
- `!solblock` - Get latest Solana block info
- `!btcblock` - Get latest Bitcoin block info
- `!ethbalance <address>` - Get Ethereum address balance
- `!solbalance <address>` - Get Solana address balance

### News & Sentiment
- `!news [source]` - Get latest crypto news
  - Sources: `cointelegraph`, `coindesk`, `theblock`, `decrypt`
  - Example: `!news cointelegraph`
- `!sentiment` - Analyze market sentiment from recent news

### Utility
- `!help` - Show all available commands
- `!status` - Check bot and LLM status

## 🎯 Example Usage

```
User: !ask What is DeFi?
Bot: 🤖 LLM Response:
>>> DeFi (Decentralized Finance) refers to financial services...

User: !askcrypto Explain the difference between PoW and PoS
Bot: 🤖 Crypto Expert:
>>> Proof of Work (PoW) and Proof of Stake (PoS) are...

User: !price ethereum
Bot: 💰 ETHEREUM (ethereum)
📈 Price: $3,245.67
📊 Market Cap: $390,123,456,789
💵 24h Volume: $12,345,678,901
🟢 24h Change: +2.34%

User: !ethblock
Bot: 🔗 Latest Ethereum Block
📦 Block Number: 18,523,456
⛽ Gas Used: 15,234,567 / 30,000,000
📝 Transactions: 234
🕐 Timestamp: 2024-01-15 14:23:45

User: !news
Bot: 📰 Latest Crypto News
1. Bitcoin Reaches New All-Time High...
2. Ethereum Upgrade Scheduled...
...

User: !sentiment
Bot: 🟢 Market Sentiment: POSITIVE
📊 Score: 0.234 (Positive)
...
```

## 🏗️ Architecture

```
free_crypto_llm_bot/
├── bot.py              # Main Discord bot
├── llm_client.py       # Ollama LLM integration
├── onchain_data.py     # Blockchain data (Etherscan, Solana, Bitcoin)
├── market_data.py      # CoinGecko market data
├── news_sentiment.py   # News fetching & sentiment analysis
├── .env.example        # Environment variables template
└── README.md          # This file
```

## 🔧 Configuration

### Ollama Models

You can use different models by changing `OLLAMA_MODEL` in `.env`:

- `mistral` - Fast, good for general use (recommended)
- `llama3` - Meta's Llama 3 (8B or 70B)
- `codellama` - Code-focused model
- `phi` - Microsoft's small, fast model

Pull a model:
```bash
ollama pull <model_name>
```

### Rate Limits

**Free Tier Limits:**
- **Etherscan**: 5 calls/second, 100,000 calls/day
- **CoinGecko (Public)**: 10-50 calls/minute
- **CoinGecko (With API Key)**: 50 calls/minute
- **Solana RPC**: Rate limited (varies by endpoint)
- **Blockstream**: No official limit, but be respectful

The bot includes basic rate limiting, but be mindful of usage.

## 🐛 Troubleshooting

### Bot doesn't respond to commands
- Check that `Message Content Intent` is enabled in Discord Developer Portal
- Verify the bot has permission to read messages in the channel
- Check bot logs for errors

### LLM not available
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start Ollama
ollama serve

# Verify model is pulled
ollama list
```

### API errors
- **Etherscan**: Verify API key is correct and not rate-limited
- **CoinGecko**: Check if you're hitting rate limits (try with API key)
- **Solana/Bitcoin**: These use public endpoints, may be temporarily unavailable

### Import errors
```bash
# Make sure all dependencies are installed
pip install -r requirements.txt

# For sentiment analysis, install:
pip install vaderSentiment textblob
```

## 📝 Notes

- **Privacy**: All LLM processing happens locally (via Ollama). Your questions never leave your machine!
- **Free Tier**: This bot is designed to work entirely on free tiers, but some features may be rate-limited
- **Performance**: Local LLMs are slower than cloud APIs but completely free and private
- **Model Size**: Larger models (70B) require more RAM but provide better responses

## 🚧 Limitations

- Local LLMs are slower than cloud APIs (GPT-4, Claude, etc.)
- Free API tiers have rate limits
- Sentiment analysis is basic (VADER/TextBlob) compared to advanced models
- On-chain data is limited to what free APIs provide

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests!

## 📄 License

This project is open source. Use it freely!

## 🙏 Credits

- **Ollama** - Local LLM hosting
- **Etherscan** - Ethereum blockchain data
- **CoinGecko** - Market data
- **Blockstream** - Bitcoin blockchain data
- **Solana** - Public RPC endpoints
- **VADER/TextBlob** - Sentiment analysis

---

**Enjoy your free crypto LLM bot! 🚀💰**



