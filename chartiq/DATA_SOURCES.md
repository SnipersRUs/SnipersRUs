# CryptoPulse - Data Sources & APIs

## 📰 News Sources (Real URLs)

All news items include clickable links to original articles:

1. **CoinTelegraph RSS** - `https://cointelegraph.com/rss`
   - Real article URLs
   - Latest crypto news
   - High-quality content

2. **CryptoPanic API** - `https://cryptopanic.com/api/v1/posts/`
   - Free tier available
   - Aggregated crypto news
   - Real article URLs

3. **CoinDesk RSS** - `https://www.coindesk.com/arc/outboundfeeds/rss/`
   - Professional crypto journalism
   - Real article URLs

4. **Decrypt RSS** - `https://decrypt.co/feed`
   - Crypto news and analysis
   - Real article URLs

## 🐋 Whale Tracking

### Whale Alert API
- **Endpoint**: `https://api.whale-alert.io/v1/transactions/`
- **Free Tier**: 10 requests/hour
- **Get API Key**: https://whale-alert.io/
- **Features**:
  - BTC transactions >$1M
  - ETH transactions >$1M
  - Exchange deposits/withdrawals
  - Large wallet movements

### Transaction Explorers
- **Bitcoin**: https://www.blockchain.com/btc/tx/{hash}
- **Ethereum**: https://etherscan.io/tx/{hash}
- All whale transactions link to blockchain explorers

## ⛓️ On-Chain Data Sources

### Etherscan API (Free Tier)
- **Endpoint**: `https://api.etherscan.io/api`
- **Get API Key**: https://etherscan.io/apis
- **Features**:
  - ETH price
  - Total supply
  - Block height
  - Transaction data

### CoinGecko API (No Key Required)
- **Endpoint**: `https://api.coingecko.com/api/v3/`
- **Free**: No API key needed
- **Rate Limit**: 10-50 calls/minute
- **Features**:
  - Real-time prices
  - 24h price changes
  - Market data

## 🔑 API Keys Setup

Create a `.env.local` file in the `chartiq` directory:

```env
# Whale Alert API (optional - free tier available)
WHALE_ALERT_API_KEY=your_api_key_here

# Etherscan API (optional - free tier available)
ETHERSCAN_API_KEY=your_api_key_here
```

## 📊 Data Refresh Rates

- **News**: Every 2 minutes (auto) or manual refresh
- **Whale Transactions**: On-demand or every 5 minutes
- **On-Chain Metrics**: Every 5 minutes

## 🚀 Alternative Data Sources

### For Production Use:

1. **The Graph** - Decentralized indexing
   - https://thegraph.com/
   - Subgraph queries for on-chain data

2. **Dune Analytics** - SQL queries on blockchain data
   - https://dune.com/
   - Free tier available

3. **Glassnode** - On-chain analytics
   - https://glassnode.com/
   - Professional tier for advanced metrics

4. **Nansen** - Wallet labeling and analytics
   - https://www.nansen.ai/
   - Smart money tracking

5. **Arkham Intelligence** - Entity tracking
   - https://www.arkhamintelligence.com/
   - Whale wallet identification

## 💡 Tips

- Start with free APIs (CoinGecko, RSS feeds)
- Add Whale Alert API key for whale tracking
- Use Etherscan API for detailed on-chain data
- Consider paid APIs for production (higher rate limits)
