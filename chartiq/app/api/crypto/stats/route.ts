import { NextResponse } from 'next/server';
import { getNews, getAlerts, getInfluencers } from '@/lib/cryptoNews';

export async function GET() {
  try {
    const news = getNews();
    const alerts = getAlerts().filter(a => !a.resolved);
    const influencers = getInfluencers();
    
    const hotNews = news.filter(n => n.impact === 'high' || n.impact === 'critical').length;
    
    return NextResponse.json({
      success: true,
      data: {
        hotNews,
        activeAlerts: alerts.length,
        influencers: influencers.length,
        totalNews: news.length,
      },
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}
