import { NextResponse } from 'next/server'
import { db } from '@/lib/db-fresh'

export async function POST() {
  try {
    // Check if influencers already exist
    const existingCount = await db.cryptoInfluencer.count()

    if (existingCount > 0) {
      return NextResponse.json({
        success: true,
        message: 'Already initialized',
        count: existingCount
      })
    }

    // Seed default crypto influencers
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
      },
      {
        name: 'Messari',
        handle: '@messaricrypto',
        platform: 'Twitter/X',
        influenceLevel: 'medium',
        focus: 'general',
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
      message: 'Initialized crypto influencers',
      count: results.length,
      influencers: results
    })
  } catch (error) {
    console.error('Error initializing crypto app:', error)
    return NextResponse.json(
      { error: 'Failed to initialize' },
      { status: 500 }
    )
  }
}
