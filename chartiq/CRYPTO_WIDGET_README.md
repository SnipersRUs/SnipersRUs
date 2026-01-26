# CryptoPulse - Real-Time Crypto News Widget

A beautiful, embeddable crypto news scraper widget perfect for landing pages. Tracks real-time crypto news, detects market-moving events, and monitors influential accounts like Trump, Elon Musk, and Vitalik.

## 🚀 Features

- **Real-Time News Scraping** - Automatically scrapes crypto news from multiple sources
- **Smart Impact Detection** - Identifies high-impact news (crashes, surges, regulations)
- **Token Detection** - Automatically tags BTC, ETH, SOL, and other major tokens
- **Sentiment Analysis** - Labels news as bullish 📈, bearish 📉, or neutral ➡️
- **Category Filtering** - Filter by DeFi, NFT, Regulation, Tech, Trading
- **Influencer Monitoring** - Tracks big accounts that can move markets
- **Auto-Alerts** - Critical alerts for market-moving events
- **Beautiful UI** - Dark gradient theme perfect for modern landing pages

## 📍 Access the Widget

Visit: **http://localhost:3000/crypto**

Or embed the component in any page:

```tsx
import CryptoNewsWidget from '@/components/CryptoNewsWidget';

export default function MyPage() {
  return (
    <div>
      <CryptoNewsWidget />
    </div>
  );
}
```

## 🔧 API Endpoints

- `GET /api/crypto/news` - Get all news (optional `?category=DeFi&limit=50`)
- `POST /api/crypto/news` - Trigger news scraping
- `GET /api/crypto/influencers` - Get monitored influencers
- `GET /api/crypto/alerts` - Get alerts (`?active=true` for unresolved only)
- `GET /api/crypto/stats` - Get dashboard statistics
- `POST /api/crypto/init` - Initialize with default data

## 🎯 How It Works

1. **News Scraping**: Scrapes from CoinTelegraph RSS and CryptoPanic API
2. **Impact Detection**: Analyzes keywords like "crash", "surge", "trump", "regulation"
3. **Token Detection**: Identifies mentions of BTC, ETH, SOL, etc.
4. **Auto-Alerts**: Creates alerts for high/critical impact news
5. **Real-Time Updates**: Auto-refreshes every 2 minutes

## 🎨 Pre-Loaded Influencers

- **Legendary**: Vitalik Buterin, Elon Musk, CZ, Donald Trump
- **High**: Andre Cronje, a16z, Coinbase, Arthur Hayes, and more

## 💡 Usage Tips

1. **First Time**: Visit `/api/crypto/init` or click "Refresh" to scrape initial news
2. **Auto-Refresh**: Widget automatically refreshes every 2 minutes
3. **Filtering**: Click category buttons to filter news
4. **High Impact**: News with "HIGH" or "CRITICAL" badges are market-moving events
5. **Trump Detection**: Any mention of "Trump" is automatically flagged as HIGH IMPACT

## 🔄 Adding to Landing Page

Simply import and use the component:

```tsx
import CryptoNewsWidget from '@/components/CryptoNewsWidget';

// In your landing page
<CryptoNewsWidget />
```

The widget is fully self-contained and will handle all data fetching and updates automatically.

## 📊 Data Storage

News, alerts, and influencer data are stored in JSON files in the `data/` directory:
- `data/crypto-news.json` - All scraped news
- `data/crypto-influencers.json` - Monitored accounts
- `data/crypto-alerts.json` - Active alerts

## 🎯 Market Impact Keywords

The system automatically detects high-impact news using keywords:
- **Critical**: crash, surge, plunge, rally, collapse, exploit, hack, ban, regulation, sanction, emergency, trump, president, fed, sec lawsuit, bankruptcy, liquidation, flash crash, rug pull, scam

## 🚨 Alert System

Alerts are automatically created for:
- News with "critical" or "high" impact levels
- Mentions of influential figures (especially Trump)
- Major market events (crashes, regulations, hacks)

---

**Made with ❤️ for crypto traders who need real-time market intelligence**
