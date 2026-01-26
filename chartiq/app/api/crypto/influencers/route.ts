import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db-fresh'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const active = searchParams.get('active')
    const influenceLevel = searchParams.get('influenceLevel')
    const focus = searchParams.get('focus')

    const where: any = {}

    if (active !== null) {
      where.active = active === 'true'
    }

    if (influenceLevel) {
      where.influenceLevel = influenceLevel
    }

    if (focus) {
      where.focus = focus
    }

    const influencers = await db.cryptoInfluencer.findMany({
      where,
      include: {
        posts: {
          orderBy: {
            postedAt: 'desc'
          },
          take: 5
        }
      },
      orderBy: {
        influenceLevel: 'desc'
      }
    })

    return NextResponse.json(influencers)
  } catch (error) {
    console.error('Error fetching influencers:', error)
    return NextResponse.json(
      { error: 'Failed to fetch influencers' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action } = body

    if (action === 'seed') {
      const defaultInfluencers = [
        {
          name: 'Vitalik Buterin',
          handle: '@VitalikButerin',
          platform: 'Twitter/X',
          influenceLevel: 'legendary',
          focus: 'tech',
          active: true
        },
        {
          name: 'Elon Musk',
          handle: '@elonmusk',
          platform: 'Twitter/X',
          influenceLevel: 'legendary',
          focus: 'trading',
          active: true
        },
        {
          name: 'CZ',
          handle: '@cz_binance',
          platform: 'Twitter/X',
          influenceLevel: 'legendary',
          focus: 'trading',
          active: true
        },
        {
          name: 'Donald Trump',
          handle: '@realDonaldTrump',
          platform: 'Twitter/X',
          influenceLevel: 'legendary',
          focus: 'trading',
          active: true
        },
        {
          name: 'Andre Cronje',
          handle: '@AndreCronjeTech',
          platform: 'Twitter/X',
          influenceLevel: 'high',
          focus: 'defi',
          active: true
        },
        {
          name: 'Andresen Horowitz',
          handle: '@a16z',
          platform: 'Twitter/X',
          influenceLevel: 'high',
          focus: 'defi',
          active: true
        },
        {
          name: 'Coinbase',
          handle: '@coinbase',
          platform: 'Twitter/X',
          influenceLevel: 'high',
          focus: 'trading',
          active: true
        },
        {
          name: 'Arthur Hayes',
          handle: '@CryptoHayes',
          platform: 'Twitter/X',
          influenceLevel: 'high',
          focus: 'trading',
          active: true
        },
        {
          name: 'Stani Kulechov',
          handle: '@StaniKulechov',
          platform: 'Twitter/X',
          influenceLevel: 'high',
          focus: 'defi',
          active: true
        },
        {
          name: 'Hayden Adams',
          handle: '@haydenzadams',
          platform: 'Twitter/X',
          influenceLevel: 'high',
          focus: 'defi',
          active: true
        },
        {
          name: 'Brian Armstrong',
          handle: '@brian_armstrong',
          platform: 'Twitter/X',
          influenceLevel: 'high',
          focus: 'trading',
          active: true
        },
        {
          name: 'Michael Saylor',
          handle: '@saylor',
          platform: 'Twitter/X',
          influenceLevel: 'high',
          focus: 'trading',
          active: true
        }
      ]

      const results = []
      for (const influencer of defaultInfluencers) {
        const existing = await db.cryptoInfluencer.findFirst({
          where: { handle: influencer.handle }
        })

        if (!existing) {
          const created = await db.cryptoInfluencer.create({
            data: influencer
          })
          results.push(created)
        }
      }

      return NextResponse.json({
        success: true,
        count: results.length,
        influencers: results
      })
    }

    return NextResponse.json(
      { error: 'Invalid action' },
      { status: 400 }
    )
  } catch (error) {
    console.error('Error creating influencers:', error)
    return NextResponse.json(
      { error: 'Failed to create influencers' },
      { status: 500 }
    )
  }
}
