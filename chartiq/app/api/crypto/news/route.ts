import { NextRequest, NextResponse } from 'next/server';
import { getNews, addNews } from '@/lib/cryptoNews';
import { scrapeCryptoNews } from '@/lib/newsScraper';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const category = searchParams.get('category');
    const limit = parseInt(searchParams.get('limit') || '50');
    
    let news = getNews();
    
    // Filter by category if provided
    if (category && category !== 'all') {
      news = news.filter(n => n.category.toLowerCase() === category.toLowerCase());
    }
    
    // Sort by timestamp (newest first)
    news.sort((a, b) => b.timestamp - a.timestamp);
    
    // Limit results
    const limited = news.slice(0, limit);
    
    return NextResponse.json({
      success: true,
      data: limited,
      count: limited.length,
      total: news.length,
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    // Trigger scraping
    const scrapedNews = await scrapeCryptoNews();
    
    return NextResponse.json({
      success: true,
      message: `Scraped ${scrapedNews.length} news items`,
      count: scrapedNews.length,
      data: scrapedNews,
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}
