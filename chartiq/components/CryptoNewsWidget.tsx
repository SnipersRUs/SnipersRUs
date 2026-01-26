'use client';

import { useState, useEffect } from 'react';

interface CryptoNews {
  id: string;
  title: string;
  source: string;
  url: string;
  timestamp: number;
  category: 'DeFi' | 'NFT' | 'Regulation' | 'Tech' | 'Trading' | 'General';
  sentiment: 'bullish' | 'bearish' | 'neutral';
  tokens: string[];
  impact: 'low' | 'medium' | 'high' | 'critical';
  excerpt?: string;
}

interface WhaleTransaction {
  id: string;
  hash: string;
  from: string;
  to: string;
  amount: string;
  token: string;
  tokenSymbol: string;
  valueUSD: number;
  timestamp: number;
  type: 'transfer' | 'exchange' | 'withdrawal' | 'deposit';
  exchange?: string;
  impact: 'low' | 'medium' | 'high' | 'critical';
}

interface Stats {
  hotNews: number;
  activeAlerts: number;
  influencers: number;
  totalNews: number;
}

type ViewMode = 'news' | 'whales' | 'onchain';

const CATEGORY_COLORS: Record<string, string> = {
  'DeFi': 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  'NFT': 'bg-pink-500/20 text-pink-300 border-pink-500/30',
  'Regulation': 'bg-red-500/20 text-red-300 border-red-500/30',
  'Tech': 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  'Trading': 'bg-green-500/20 text-green-300 border-green-500/30',
  'General': 'bg-gray-500/20 text-gray-300 border-gray-500/30',
};

const IMPACT_COLORS: Record<string, string> = {
  'critical': 'bg-red-500 text-white',
  'high': 'bg-orange-500 text-white',
  'medium': 'bg-yellow-500 text-black',
  'low': 'bg-gray-500 text-white',
};

const SENTIMENT_EMOJIS: Record<string, string> = {
  'bullish': '📈',
  'bearish': '📉',
  'neutral': '➡️',
};

export default function CryptoNewsWidget() {
  const [news, setNews] = useState<CryptoNews[]>([]);
  const [whales, setWhales] = useState<WhaleTransaction[]>([]);
  const [stats, setStats] = useState<Stats>({ hotNews: 0, activeAlerts: 0, influencers: 0, totalNews: 0 });
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('news');
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);

  const categories = ['all', 'DeFi', 'NFT', 'Regulation', 'Tech', 'Trading'];

  const fetchNews = async () => {
    try {
      const categoryParam = selectedCategory === 'all' ? '' : `?category=${selectedCategory}`;
      const res = await fetch(`/api/crypto/news${categoryParam}`);
      const data = await res.json();
      if (data.success) {
        setNews(data.data || []);
      }
    } catch (error) {
      console.error('Error fetching news:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/crypto/stats');
      const data = await res.json();
      if (data.success) {
        setStats(data.data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchWhales = async () => {
    try {
      const res = await fetch('/api/crypto/whales?refresh=true');
      const data = await res.json();
      if (data.success) {
        setWhales(data.data || []);
      }
    } catch (error) {
      console.error('Error fetching whales:', error);
    }
  };

  const handleScrape = async () => {
    setScraping(true);
    try {
      const res = await fetch('/api/crypto/news', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        await fetchNews();
        await fetchStats();
      }
    } catch (error) {
      console.error('Error scraping:', error);
    } finally {
      setScraping(false);
    }
  };

  useEffect(() => {
    fetchNews();
    fetchStats();
    if (viewMode === 'whales') {
      fetchWhales();
    }
    
    const interval = setInterval(() => {
      fetchNews();
      fetchStats();
      if (viewMode === 'whales') {
        fetchWhales();
      }
    }, 120000); // Refresh every 2 minutes

    return () => clearInterval(interval);
  }, [selectedCategory, viewMode]);

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-4">
      {/* Header with Stats */}
      <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-orange-400 bg-clip-text text-transparent">
                        CryptoPulse
                    </h1>
                    <p className="text-gray-400 text-sm mt-1">Real-time crypto news & market intelligence</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => setViewMode('news')}
                        className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                            viewMode === 'news' 
                                ? 'bg-gradient-to-r from-purple-600 to-orange-600 text-white' 
                                : 'bg-gray-800/50 text-gray-400 hover:bg-gray-700/50'
                        }`}
                    >
                        📰 News
                    </button>
                    <button
                        onClick={() => setViewMode('whales')}
                        className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                            viewMode === 'whales' 
                                ? 'bg-gradient-to-r from-purple-600 to-orange-600 text-white' 
                                : 'bg-gray-800/50 text-gray-400 hover:bg-gray-700/50'
                        }`}
                    >
                        🐋 Whales
                    </button>
                    <button
                        onClick={handleScrape}
                        disabled={scraping}
                        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-orange-600 rounded-lg font-semibold text-white hover:opacity-90 transition-all disabled:opacity-50"
                    >
                        {scraping ? 'Scraping...' : '🔄 Refresh'}
                    </button>
                </div>
            </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 backdrop-blur-sm border border-purple-500/30 rounded-xl p-4">
            <div className="text-2xl font-bold text-purple-300">{stats.hotNews}</div>
            <div className="text-sm text-gray-400">Hot News</div>
          </div>
          <div className="bg-gradient-to-br from-red-900/50 to-red-800/30 backdrop-blur-sm border border-red-500/30 rounded-xl p-4">
            <div className="text-2xl font-bold text-red-300">{stats.activeAlerts}</div>
            <div className="text-sm text-gray-400">Active Alerts</div>
          </div>
          <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 backdrop-blur-sm border border-blue-500/30 rounded-xl p-4">
            <div className="text-2xl font-bold text-blue-300">{stats.influencers}</div>
            <div className="text-sm text-gray-400">Influencers</div>
          </div>
          <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 backdrop-blur-sm border border-green-500/30 rounded-xl p-4">
            <div className="text-2xl font-bold text-green-300">{stats.totalNews}</div>
            <div className="text-sm text-gray-400">Total News</div>
          </div>
        </div>

        {/* Category Filters - Only show for news view */}
        {viewMode === 'news' && (
          <div className="flex flex-wrap gap-2 mb-4">
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                  selectedCategory === cat
                    ? 'bg-gradient-to-r from-purple-600 to-orange-600 text-white'
                    : 'bg-gray-800/50 text-gray-400 hover:bg-gray-700/50'
                }`}
              >
                {cat === 'all' ? 'All' : cat}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Content based on view mode */}
      {viewMode === 'news' && (
        <div className="space-y-4">
          {loading && news.length === 0 ? (
            <div className="text-center py-12 text-gray-400">Loading news...</div>
          ) : news.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">📰</div>
              <div className="text-gray-400 mb-4">No news found. Click refresh to scrape!</div>
              <button
                onClick={handleScrape}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-orange-600 rounded-lg font-semibold text-white hover:opacity-90"
              >
                Scrape News Now
              </button>
            </div>
          ) : (
            news.map(item => (
              <a
                key={item.id}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block bg-gradient-to-br from-gray-900/80 to-gray-800/60 backdrop-blur-sm border border-gray-700/50 rounded-xl p-5 hover:border-purple-500/50 transition-all hover:shadow-lg hover:shadow-purple-500/20"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <span className={`px-2 py-1 rounded text-xs font-medium border ${CATEGORY_COLORS[item.category] || CATEGORY_COLORS['General']}`}>
                        {item.category}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs font-bold ${IMPACT_COLORS[item.impact]}`}>
                        {item.impact.toUpperCase()}
                      </span>
                      <span className="text-lg">{SENTIMENT_EMOJIS[item.sentiment]}</span>
                      {item.tokens.length > 0 && (
                        <div className="flex gap-1 flex-wrap">
                          {item.tokens.slice(0, 3).map(token => (
                            <span key={token} className="px-2 py-1 bg-yellow-500/20 text-yellow-300 rounded text-xs font-medium">
                              {token}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2 hover:text-purple-300 transition-colors">
                      {item.title}
                    </h3>
                    {item.excerpt && (
                      <p className="text-gray-400 text-sm mb-2 line-clamp-2">{item.excerpt}</p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>{item.source}</span>
                      <span>•</span>
                      <span>{formatTime(item.timestamp)}</span>
                    </div>
                  </div>
                </div>
              </a>
            ))
          )}
        </div>
      )}

      {viewMode === 'whales' && (
        <div className="space-y-4">
          {whales.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">🐋</div>
              <div className="text-gray-400 mb-4">No whale transactions found. Click refresh to fetch!</div>
              <button
                onClick={async () => {
                  await fetch('/api/crypto/whales', { method: 'POST' });
                  await fetchWhales();
                }}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-orange-600 rounded-lg font-semibold text-white hover:opacity-90"
              >
                Fetch Whale Data
              </button>
            </div>
          ) : (
            whales.map(whale => {
              const explorerUrl = whale.token === 'BTC' 
                ? `https://www.blockchain.com/btc/tx/${whale.hash}`
                : `https://etherscan.io/tx/${whale.hash}`;
              
              return (
                <a
                  key={whale.id}
                  href={explorerUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block bg-gradient-to-br from-gray-900/80 to-gray-800/60 backdrop-blur-sm border border-gray-700/50 rounded-xl p-5 hover:border-blue-500/50 transition-all hover:shadow-lg hover:shadow-blue-500/20"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${IMPACT_COLORS[whale.impact]}`}>
                          {whale.impact.toUpperCase()}
                        </span>
                        <span className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded text-xs font-medium border border-blue-500/30">
                          {whale.type.toUpperCase()}
                        </span>
                        {whale.exchange && (
                          <span className="px-2 py-1 bg-green-500/20 text-green-300 rounded text-xs font-medium border border-green-500/30">
                            {whale.exchange}
                          </span>
                        )}
                        <span className="px-2 py-1 bg-yellow-500/20 text-yellow-300 rounded text-xs font-medium">
                          {whale.tokenSymbol}
                        </span>
                      </div>
                      <h3 className="text-lg font-semibold text-white mb-2">
                        ${(whale.valueUSD / 1_000_000).toFixed(2)}M {whale.tokenSymbol} Transfer
                      </h3>
                      <div className="space-y-1 text-sm text-gray-400 mb-2">
                        <div>
                          <span className="text-gray-500">From: </span>
                          <span className="font-mono text-xs">{whale.from.substring(0, 10)}...{whale.from.substring(whale.from.length - 8)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">To: </span>
                          <span className="font-mono text-xs">{whale.to.substring(0, 10)}...{whale.to.substring(whale.to.length - 8)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Amount: </span>
                          <span className="text-white font-semibold">
                            {parseFloat(whale.amount).toLocaleString()} {whale.tokenSymbol}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>View on Explorer</span>
                        <span>•</span>
                        <span>{formatTime(whale.timestamp)}</span>
                      </div>
                    </div>
                  </div>
                </a>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
