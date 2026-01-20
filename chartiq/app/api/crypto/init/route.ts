import { NextResponse } from 'next/server';
import { scrapeCryptoNews } from '@/lib/newsScraper';

export async function POST() {
  try {
    // Initialize by scraping news
    const news = await scrapeCryptoNews();
    
    return NextResponse.json({
      success: true,
      message: `Initialized with ${news.length} news items`,
      count: news.length,
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}
