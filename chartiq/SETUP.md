# CryptoPulse Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Set Up Database
```bash
# Generate Prisma Client
npx prisma generate

# Push schema to database
npx prisma db push
```

### 3. Initialize Default Data
```bash
# Initialize influencers
curl -X POST http://localhost:3000/api/crypto/init
```

### 4. Start Development Server
```bash
npm run dev
```

Visit: http://localhost:3000

### 5. Start Background Scheduler (Optional)
```bash
cd mini-services/crypto-scheduler
bun install
bun run dev
```

## 📊 Features

✅ **Real-time News Scraping** - Uses ZAI SDK for web search
✅ **Whale Tracking** - Monitor large transactions (>$1M)
✅ **On-Chain Metrics** - Real-time price data from CoinGecko
✅ **Influencer Monitoring** - Track crypto influencers
✅ **Auto-Alerts** - High-impact news triggers alerts
✅ **Clickable News** - All articles link to original sources

## 🔑 Optional API Keys

Add to `.env.local`:

```env
# Whale Alert API (free tier: 10 req/hour)
WHALE_ALERT_API_KEY=your_key_here

# Etherscan API (optional)
ETHERSCAN_API_KEY=your_key_here

# Database (already set)
DATABASE_URL="file:./dev.db"
```

## 🎯 API Endpoints

- `GET /api/crypto/news` - Get news
- `POST /api/crypto/scrape` - Trigger scraping
- `GET /api/crypto/influencers` - Get influencers
- `GET /api/crypto/alerts` - Get alerts
- `GET /api/crypto/whales` - Get whale transactions
- `GET /api/crypto/onchain` - Get on-chain metrics
- `POST /api/crypto/init` - Initialize default data

## 🐋 Whale Tracking

Whale transactions are automatically fetched and stored. Click "🐋 Whales" in the UI to view large transactions.

## 📰 News Sources

News is scraped from multiple sources using ZAI web search:
- Cryptocurrency news
- DeFi updates
- NFT marketplace news
- Regulation updates
- Exchange news

## 🔄 Auto-Refresh

- News auto-refreshes every 2 minutes
- Scheduler runs every 3 minutes (if enabled)
- Whale data fetched on-demand

## 🎨 UI Features

- Dark gradient theme
- Real-time stats dashboard
- Category filtering
- Impact level badges
- Sentiment indicators
- Token tags
- Critical alerts panel
- Influencer list
- Hot takes sidebar

## 🛠️ Troubleshooting

**Database errors?**
```bash
npx prisma db push
npx prisma generate
```

**No news showing?**
- Click "Refresh" button
- Check scheduler is running
- Verify ZAI SDK is working

**Whale data not loading?**
- Check Whale Alert API key (optional)
- Falls back to demo mode if no key

## 📝 Next Steps

1. Visit http://localhost:3000
2. Click "Refresh" to scrape news
3. View whale transactions
4. Monitor alerts
5. Track influencers

Enjoy your crypto intelligence dashboard! 🚀
