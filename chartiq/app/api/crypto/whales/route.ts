import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db-fresh'
import axios from 'axios'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const refresh = searchParams.get('refresh') === 'true'
    const impact = searchParams.get('impact')
    const limit = parseInt(searchParams.get('limit') || '50')

    let whales = await db.whaleTransaction.findMany({
      where: impact ? { impact: impact as any } : {},
      orderBy: { timestamp: 'desc' },
      take: limit
    })

    // If refresh requested, fetch new data
    if (refresh) {
      const newWhales = await fetchWhaleTransactions()
      if (newWhales.length > 0) {
        whales = newWhales
      }
    }

    return NextResponse.json({
      success: true,
      data: whales,
      count: whales.length
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
    const whales = await fetchWhaleTransactions()
    
    return NextResponse.json({
      success: true,
      message: `Fetched ${whales.length} whale transactions`,
      count: whales.length,
      data: whales
    })
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    )
  }
}

async function fetchWhaleTransactions() {
  const whales: any[] = []
  
  try {
    const WHALE_ALERT_API_KEY = process.env.WHALE_ALERT_API_KEY || 'demo'
    
    // Fetch BTC whale transactions (>$1M)
    const btcResponse = await axios.get(
      `https://api.whale-alert.io/v1/transactions/bitcoin?min_value=1000000&api_key=${WHALE_ALERT_API_KEY}`,
      { timeout: 10000 }
    ).catch(() => null)

    if (btcResponse?.data?.transactions) {
      for (const tx of btcResponse.data.transactions.slice(0, 10)) {
        const valueUSD = tx.amount_usd || 0
        let impact: string = 'low'
        if (valueUSD > 100_000_000) impact = 'critical'
        else if (valueUSD > 10_000_000) impact = 'high'
        else if (valueUSD > 1_000_000) impact = 'medium'

        const whale = await db.whaleTransaction.upsert({
          where: { hash: tx.hash },
          update: {},
          create: {
            hash: tx.hash,
            from: tx.from?.address || 'Unknown',
            to: tx.to?.address || 'Unknown',
            amount: tx.amount?.toString() || '0',
            token: 'BTC',
            tokenSymbol: 'BTC',
            valueUSD: valueUSD,
            timestamp: new Date((tx.timestamp || Date.now()) * 1000),
            type: tx.from?.owner_type === 'exchange' ? 'withdrawal' : 
                  tx.to?.owner_type === 'exchange' ? 'deposit' : 'transfer',
            exchange: tx.from?.owner_type === 'exchange' ? tx.from.owner : 
                     tx.to?.owner_type === 'exchange' ? tx.to.owner : undefined,
            impact: impact as any,
          }
        })
        
        whales.push(whale)
      }
    }

    // Fetch ETH whale transactions
    const ethResponse = await axios.get(
      `https://api.whale-alert.io/v1/transactions/ethereum?min_value=1000000&api_key=${WHALE_ALERT_API_KEY}`,
      { timeout: 10000 }
    ).catch(() => null)

    if (ethResponse?.data?.transactions) {
      for (const tx of ethResponse.data.transactions.slice(0, 10)) {
        const valueUSD = tx.amount_usd || 0
        let impact: string = 'low'
        if (valueUSD > 100_000_000) impact = 'critical'
        else if (valueUSD > 10_000_000) impact = 'high'
        else if (valueUSD > 1_000_000) impact = 'medium'

        const whale = await db.whaleTransaction.upsert({
          where: { hash: tx.hash },
          update: {},
          create: {
            hash: tx.hash,
            from: tx.from?.address || 'Unknown',
            to: tx.to?.address || 'Unknown',
            amount: tx.amount?.toString() || '0',
            token: 'ETH',
            tokenSymbol: 'ETH',
            valueUSD: valueUSD,
            timestamp: new Date((tx.timestamp || Date.now()) * 1000),
            type: tx.from?.owner_type === 'exchange' ? 'withdrawal' : 
                  tx.to?.owner_type === 'exchange' ? 'deposit' : 'transfer',
            exchange: tx.from?.owner_type === 'exchange' ? tx.from.owner : 
                     tx.to?.owner_type === 'exchange' ? tx.to.owner : undefined,
            impact: impact as any,
          }
        })
        
        whales.push(whale)
      }
    }

  } catch (error) {
    console.error('Error fetching whale transactions:', error)
  }

  return whales
}
