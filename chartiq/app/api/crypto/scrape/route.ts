import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db-fresh'
import ZAI from 'z-ai-web-dev-sdk'

// Crypto-focused keywords and analysis
const CRYPTO_TOKENS = [
  'btc', 'bitcoin', 'eth', 'ethereum', 'sol', 'solana',
  'bnb', 'binance', 'ada', 'cardano', 'xrp', 'ripple',
  'doge', 'dogecoin', 'dot', 'polkadot', 'matic', 'polygon',
  'avax', 'avalanche', 'link', 'chainlink', 'uni', 'uniswap',
  'aave', 'comp', 'maker', 'defi', 'nft', 'web3'
]

const HIGH_IMPACT_KEYWORDS = [
  'crash', 'surge', 'plunge', 'rally', 'breakthrough', 'pump',
  'dump', 'record high', 'record low', 'major', 'significant',
  'soar', 'skyrocket', 'collapse', 'emergency', 'ban', 'regulation',
  'approval', 'rejection', 'sec', 'lawsuit', 'hack', 'exploit',
  'airdrop', 'mainnet', 'launch', 'upgrade', 'merge', 'fork'
]

const BULLISH_KEYWORDS = [
  'surge', 'rally', 'breakthrough', 'soar', 'skyrocket', 'pump',
  'bull', 'positive', 'gain', 'profit', 'up', 'rise', 'recover',
  'upgrade', 'adoption', 'partnership', 'launch', 'mainnet'
]

const BEARISH_KEYWORDS = [
  'crash', 'plunge', 'dump', 'collapse', 'fall', 'drop', 'bear',
  'negative', 'loss', 'down', 'decline', 'hack', 'exploit',
  'regulation', 'ban', 'sec', 'lawsuit', 'fud'
]

const CATEGORIES = {
  defi: ['defi', 'dex', 'yield', 'lending', 'borrowing', 'liquidity'],
  nft: ['nft', 'digital art', 'collectible', 'opensea', 'mint'],
  regulation: ['sec', 'regulation', 'ban', 'law', 'legal', 'compliance', 'approval'],
  tech: ['layer 2', 'scaling', 'zk', 'rollup', 'bridge', 'cross-chain', 'upgrade'],
  trading: ['price', 'volume', 'market cap', 'trading', 'exchange', 'list', 'delist']
}

function extractTokens(text: string): string {
  const found: string[] = []
  const lowerText = text.toLowerCase()

  CRYPTO_TOKENS.forEach(token => {
    if (lowerText.includes(token)) {
      found.push(token)
    }
  })

  return [...new Set(found)].join(',')
}

function analyzeImpact(text: string): { level: string; sentiment: string; category: string; tokens: string } {
  const lowerText = text.toLowerCase()

  // Extract tokens
  const tokens = extractTokens(lowerText)

  // Determine impact level
  let impactLevel = 'low'
  const highImpactCount = HIGH_IMPACT_KEYWORDS.filter(keyword =>
    lowerText.includes(keyword)
  ).length

  if (highImpactCount >= 2 || lowerText.includes('hack') || lowerText.includes('exploit')) {
    impactLevel = 'critical'
  } else if (highImpactCount >= 1 || lowerText.includes('sec') || lowerText.includes('regulation')) {
    impactLevel = 'high'
  } else if (tokens.length >= 2) {
    impactLevel = 'medium'
  }

  // Determine sentiment
  const bullishCount = BULLISH_KEYWORDS.filter(keyword =>
    lowerText.includes(keyword)
  ).length

  const bearishCount = BEARISH_KEYWORDS.filter(keyword =>
    lowerText.includes(keyword)
  ).length

  let sentiment = 'neutral'
  if (bullishCount > bearishCount) {
    sentiment = 'bullish'
  } else if (bearishCount > bullishCount) {
    sentiment = 'bearish'
  }

  // Determine category
  let category = 'general'
  for (const [key, keywords] of Object.entries(CATEGORIES)) {
    if (keywords.some(keyword => lowerText.includes(keyword))) {
      category = key
      break
    }
  }

  return { level: impactLevel, sentiment, category, tokens }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}))
    const { numResults = 30 } = body

    const zai = await ZAI.create()

    // Crypto-focused search queries
    const searchQueries = [
      'cryptocurrency news bitcoin ethereum',
      'crypto market update today',
      'defi news uniswap aave',
      'nft marketplace news',
      'crypto regulation sec approval',
      'web3 blockchain developments',
      'altcoin news solana cardano',
      'crypto exchange news binance coinbase'
    ]

    let allResults: any[] = []

    // Search for each query
    for (const query of searchQueries) {
      try {
        const results = await zai.functions.invoke('web_search', {
          query: query,
          num: Math.floor(numResults / searchQueries.length)
        })

        if (Array.isArray(results)) {
          allResults = [...allResults, ...results]
        }

        // Small delay between searches
        await new Promise(resolve => setTimeout(resolve, 500))
      } catch (error) {
        console.error(`Error searching for "${query}":`, error)
      }
    }

    // Process and save news items
    const savedNews = []
    for (const item of allResults) {
      try {
        const analysis = analyzeImpact(`${item.name} ${item.snippet}`)

        // Check if news already exists
        const existing = await db.cryptoNews.findFirst({
          where: { url: item.url }
        })

        if (!existing) {
          const newsItem = await db.cryptoNews.create({
            data: {
              title: item.name,
              snippet: item.snippet,
              url: item.url,
              source: item.host_name || 'unknown',
              category: analysis.category,
              tokens: analysis.tokens || null,
              impactLevel: analysis.level,
              sentiment: analysis.sentiment,
              publishedAt: item.date ? new Date(item.date) : new Date()
            }
          })

          savedNews.push(newsItem)
        }
      } catch (error) {
        console.error('Error saving crypto news:', error)
      }
    }

    // Create alerts for high impact news
    const highImpactNews = savedNews.filter((news: any) =>
      news.impactLevel === 'high' || news.impactLevel === 'critical'
    )

    for (const news of highImpactNews) {
      try {
        const existingAlert = await db.cryptoAlert.findFirst({
          where: {
            sourceId: news.id,
            resolved: false
          }
        })

        if (!existingAlert) {
          await db.cryptoAlert.create({
            data: {
              title: `${news.impactLevel.toUpperCase()}: ${news.title.substring(0, 80)}`,
              description: news.snippet,
              severity: news.impactLevel === 'critical' ? 'critical' : 'warning',
              sourceType: 'news',
              sourceId: news.id,
              tokens: news.tokens
            }
          })
        }
      } catch (error) {
        console.error('Error creating alert:', error)
      }
    }

    return NextResponse.json({
      success: true,
      count: savedNews.length,
      totalScraped: allResults.length,
      alertsCreated: highImpactNews.length,
      highImpact: highImpactNews.length
    })
  } catch (error) {
    console.error('Error in crypto scrape endpoint:', error)
    return NextResponse.json(
      { error: 'Failed to scrape crypto news' },
      { status: 500 }
    )
  }
}
