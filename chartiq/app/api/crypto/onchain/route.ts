import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db-fresh'
import axios from 'axios'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const refresh = searchParams.get('refresh') === 'true'
    
    let metrics = await db.onChainMetric.findMany({
      orderBy: { timestamp: 'desc' },
      take: 20
    })
    
    // If refresh requested, fetch new data
    if (refresh) {
      const newMetrics = await fetchPublicOnChainData()
      if (newMetrics.length > 0) {
        metrics = newMetrics
      }
    }
    
    return NextResponse.json({
      success: true,
      data: metrics,
      count: metrics.length
    })
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    )
  }
}

export async function POST() {
  try {
    const metrics = await fetchPublicOnChainData()
    
    return NextResponse.json({
      success: true,
      message: `Fetched ${metrics.length} on-chain metrics`,
      count: metrics.length,
      data: metrics
    })
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    )
  }
}

async function fetchPublicOnChainData() {
  const metrics: any[] = []
  
  try {
    // Use CoinGecko API for market data (free, no key needed)
    const geckoResponse = await axios.get(
      'https://api.coingecko.com/api/v3/simple/price?ids=ethereum,bitcoin&vs_currencies=usd&include_24hr_change=true',
      { timeout: 10000 }
    ).catch(() => null)

    if (geckoResponse?.data) {
      if (geckoResponse.data.ethereum) {
        const metric = await db.onChainMetric.upsert({
          where: { id: 'eth-price' },
          update: {
            value: geckoResponse.data.ethereum.usd,
            change24h: geckoResponse.data.ethereum.usd_24h_change || 0,
            timestamp: new Date()
          },
          create: {
            id: 'eth-price',
            metric: 'ETH Price',
            value: geckoResponse.data.ethereum.usd,
            change24h: geckoResponse.data.ethereum.usd_24h_change || 0,
            timestamp: new Date()
          }
        })
        metrics.push(metric)
      }
      
      if (geckoResponse.data.bitcoin) {
        const metric = await db.onChainMetric.upsert({
          where: { id: 'btc-price' },
          update: {
            value: geckoResponse.data.bitcoin.usd,
            change24h: geckoResponse.data.bitcoin.usd_24h_change || 0,
            timestamp: new Date()
          },
          create: {
            id: 'btc-price',
            metric: 'BTC Price',
            value: geckoResponse.data.bitcoin.usd,
            change24h: geckoResponse.data.bitcoin.usd_24h_change || 0,
            timestamp: new Date()
          }
        })
        metrics.push(metric)
      }
    }
  } catch (error) {
    console.error('Error fetching public on-chain data:', error)
  }

  return metrics
}
