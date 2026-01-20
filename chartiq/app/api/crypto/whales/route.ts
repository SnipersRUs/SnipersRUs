import { NextRequest, NextResponse } from 'next/server';
import { getWhaleTransactions, fetchWhaleTransactions } from '@/lib/onchainData';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const refresh = searchParams.get('refresh') === 'true';
    
    let whales = getWhaleTransactions();
    
    // If refresh requested, fetch new data
    if (refresh) {
      const newWhales = await fetchWhaleTransactions();
      whales = newWhales.length > 0 ? newWhales : whales;
    }
    
    // Sort by timestamp (newest first)
    whales.sort((a, b) => b.timestamp - a.timestamp);
    
    // Filter by impact if provided
    const impact = searchParams.get('impact');
    if (impact) {
      whales = whales.filter(w => w.impact === impact);
    }
    
    // Limit results
    const limit = parseInt(searchParams.get('limit') || '50');
    const limited = whales.slice(0, limit);
    
    return NextResponse.json({
      success: true,
      data: limited,
      count: limited.length,
      total: whales.length,
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

export async function POST() {
  try {
    // Trigger whale fetch
    const whales = await fetchWhaleTransactions();
    
    return NextResponse.json({
      success: true,
      message: `Fetched ${whales.length} whale transactions`,
      count: whales.length,
      data: whales,
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}
