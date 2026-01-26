import { NextResponse } from 'next/server'
import { db } from '@/lib/db-fresh'

export async function GET() {
  try {
    const [hotNews, activeAlerts, influencers, totalNews] = await Promise.all([
      db.cryptoNews.count({ where: { impactLevel: { in: ['high', 'critical'] } } }),
      db.cryptoAlert.count({ where: { resolved: false } }),
      db.cryptoInfluencer.count({ where: { active: true } }),
      db.cryptoNews.count()
    ])
    
    return NextResponse.json({
      success: true,
      data: {
        hotNews,
        activeAlerts,
        influencers,
        totalNews
      }
    })
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    )
  }
}
