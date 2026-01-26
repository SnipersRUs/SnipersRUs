import { PrismaClient } from '@prisma/client'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL || 'file:../../dev.db'
    }
  }
})

// Configuration
const SCRAPE_INTERVAL_MINUTES = 3 // Scrape every 3 minutes
const NUM_RESULTS = 25

const ZAI = (await import('z-ai-web-dev-sdk')).default

// Crypto tokens and keywords
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

function analyzeCryptoNews(text: string): {
  level: string
  sentiment: string
  category: string
  tokens: string
} {
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

async function scrapeCryptoNews() {
  console.log(`[${new Date().toISOString()}] Scraping crypto news...`)

  const zai = await ZAI.create()

  const searchQueries = [
    'cryptocurrency news bitcoin ethereum today',
    'crypto market update defi nft',
    'crypto regulation sec approval',
    'web3 blockchain developments',
    'altcoin news solana cardano'
  ]

  let allResults: any[] = []

  for (const query of searchQueries) {
    try {
      const results = await zai.functions.invoke('web_search', {
        query: query,
        num: Math.floor(NUM_RESULTS / searchQueries.length)
      })

      if (Array.isArray(results)) {
        allResults = [...allResults, ...results]
      }

      await new Promise(resolve => setTimeout(resolve, 500))
    } catch (error: any) {
      console.error(`Error searching "${query}":`, error.message)
    }
  }

  // Process and save
  let savedCount = 0
  for (const item of allResults) {
    try {
      const analysis = analyzeCryptoNews(`${item.name} ${item.snippet}`)

      const existing = await prisma.cryptoNews.findFirst({
        where: { url: item.url }
      })

      if (!existing) {
        const newsItem = await prisma.cryptoNews.create({
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

        savedCount++
        console.log(`✓ Saved: ${newsItem.title.substring(0, 60)}... [${newsItem.impactLevel}]`)

        // Create alerts for high impact
        if (analysis.level === 'high' || analysis.level === 'critical') {
          try {
            const existingAlert = await prisma.cryptoAlert.findFirst({
              where: {
                sourceId: newsItem.id,
                resolved: false
              }
            })

            if (!existingAlert) {
              await prisma.cryptoAlert.create({
                data: {
                  title: `${analysis.level.toUpperCase()}: ${newsItem.title.substring(0, 80)}`,
                  description: newsItem.snippet,
                  severity: analysis.level === 'critical' ? 'critical' : 'warning',
                  sourceType: 'news',
                  sourceId: newsItem.id,
                  tokens: analysis.tokens
                }
              })
              console.log(`🚨 Created alert for high-impact news`)
            }
          } catch (alertError: any) {
            console.error('Error creating alert:', alertError.message)
          }
        }
      }
    } catch (error: any) {
      console.error('Error saving news:', error.message)
    }
  }

  return { total: allResults.length, saved: savedCount }
}

async function main() {
  console.log('🚀 Crypto News Scheduler Started')
  console.log(`📊 Scraping interval: ${SCRAPE_INTERVAL_MINUTES} minutes`)
  console.log(`🎯 Results per scrape: ${NUM_RESULTS}`)

  // Initial scrape
  console.log('\n========== Initial Scrape ==========')
  await scrapeCryptoNews()

  // Schedule periodic scrapes
  setInterval(async () => {
    console.log('\n========== Scheduled Scrape ==========')
    await scrapeCryptoNews()
  }, SCRAPE_INTERVAL_MINUTES * 60 * 1000)

  console.log(`\n✅ Scheduler running. Next scrape in ${SCRAPE_INTERVAL_MINUTES} minutes...`)
}

main().catch(error => {
  console.error('❌ Fatal error:', error)
  process.exit(1)
})
