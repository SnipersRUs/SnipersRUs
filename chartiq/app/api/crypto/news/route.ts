import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db-fresh'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const category = searchParams.get('category')
    const tokens = searchParams.get('tokens')
    const limit = parseInt(searchParams.get('limit') || '50')

    const where: any = {}

    if (category && category !== 'all') {
      where.category = category
    }

    if (tokens) {
      where.tokens = {
        contains: tokens
      }
    }

    const cryptoNews = await db.cryptoNews.findMany({
      where,
      orderBy: {
        publishedAt: 'desc'
      },
      take: limit
    })

    return NextResponse.json(cryptoNews)
  } catch (error) {
    console.error('Error fetching crypto news:', error)
    return NextResponse.json(
      { error: 'Failed to fetch crypto news' },
      { status: 500 }
    )
  }
}
