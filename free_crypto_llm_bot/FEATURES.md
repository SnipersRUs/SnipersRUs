# Features Overview 🎯

## Core Features

### 1. 🤖 Local LLM Integration
- **Powered by Ollama**: Run LLMs locally (Mistral, Llama 3, etc.)
- **Completely Free**: No API costs, no usage limits
- **Private**: All processing happens on your machine
- **Commands**:
  - `!ask <question>` - General questions
  - `!askcrypto <question>` - Crypto-specific questions with expert context

### 2. 💰 Market Data (CoinGecko)
- Real-time cryptocurrency prices
- Market cap, volume, 24h change
- Trending cryptocurrencies
- **Commands**:
  - `!price [coin]` - Get price (e.g., `!price ethereum`)
  - `!trending` - Top trending coins

### 3. 🔗 On-Chain Data

#### Ethereum (Etherscan)
- Latest block information
- Block details (gas, transactions, timestamp)
- Address balance lookup
- **Commands**:
  - `!ethblock` - Latest block
  - `!ethbalance <address>` - Address balance

#### Solana (Public RPC)
- Current slot and block height
- Address balance lookup
- **Commands**:
  - `!solblock` - Latest block info
  - `!solbalance <address>` - Address balance

#### Bitcoin (Blockstream)
- Latest block height
- Block details (transactions, size)
- **Commands**:
  - `!btcblock` - Latest block info

### 4. 📰 News & Sentiment Analysis

#### News Sources
- Cointelegraph
- CoinDesk
- The Block
- Decrypt

#### Sentiment Analysis
- VADER Sentiment Analyzer (default)
- TextBlob (fallback)
- Analyzes news headlines and summaries
- Overall market sentiment score

**Commands**:
- `!news [source]` - Latest crypto news
- `!sentiment` - Market sentiment analysis

### 5. 🛠️ Utility Commands
- `!help` - Show all commands
- `!status` - Check bot and API status

## Technical Stack

### Free APIs Used
- **Etherscan**: Ethereum blockchain data (free tier: 5 calls/sec, 100k/day)
- **CoinGecko**: Market data (free tier: 10-50 calls/min, 50/min with API key)
- **Solana RPC**: Public mainnet endpoint
- **Blockstream**: Bitcoin blockchain data (no official limit)

### Open Source Tools
- **Ollama**: Local LLM hosting
- **VADER Sentiment**: Sentiment analysis
- **TextBlob**: Alternative sentiment analysis
- **feedparser**: RSS feed parsing
- **discord.py**: Discord bot framework

## Rate Limits

| Service | Free Tier Limit |
|---------|----------------|
| Etherscan | 5 calls/sec, 100k/day |
| CoinGecko (Public) | 10-50 calls/min |
| CoinGecko (API Key) | 50 calls/min |
| Solana RPC | Varies by endpoint |
| Blockstream | No official limit |

The bot includes basic error handling and will inform you if rate limits are hit.

## Model Options

You can use different Ollama models by changing `OLLAMA_MODEL` in `.env`:

- **mistral** (Recommended) - Fast, 7B parameters, ~4GB
- **llama3** - Meta's Llama 3, 8B parameters, ~4.7GB
- **llama3:70b** - Larger model, better responses, ~40GB
- **codellama** - Code-focused model
- **phi** - Microsoft's small, fast model

Pull a model:
```bash
ollama pull <model_name>
```

## Privacy & Security

- ✅ **Local LLM Processing**: All AI responses generated locally
- ✅ **No Data Collection**: Bot doesn't store or transmit your questions
- ✅ **Free APIs**: No paid services, no data sharing agreements
- ✅ **Open Source**: Full code transparency

## Limitations

- Local LLMs are slower than cloud APIs (GPT-4, Claude)
- Free API tiers have rate limits
- Basic sentiment analysis (not as sophisticated as large models)
- On-chain data limited to what free APIs provide
- Requires local machine to run Ollama (or remote server)

## Future Enhancements (Possible)

- More blockchain networks (Polygon, Avalanche, etc.)
- Additional news sources
- Price alerts and notifications
- Portfolio tracking
- Technical analysis integration
- More advanced sentiment models
- Slash commands support
- Web dashboard

---

**All features are 100% free to use!** 🎉



