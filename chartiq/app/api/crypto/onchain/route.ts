import { NextRequest, NextResponse } from 'next/server';
import { getOnChainMetrics, fetchPublicOnChainData } from '@/lib/onchainData';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const refresh = searchParams.get('refresh') === 'true';
    
    let metrics = getOnChainMetrics();
    
    // If refresh requested, fetch new data
    if (refresh) {
      const newMetrics = await fetchPublicOnChainData();
      metrics = newMetrics.length > 0 ? newMetrics : metrics;
    }
    
    return NextResponse.json({
      success: true,
      data: metrics,
      count: metrics.length,
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
    // Trigger on-chain data fetch
    const metrics = await fetchPublicOnChainData();
    
    return NextResponse.json({
      success: true,
      message: `Fetched ${metrics.length} on-chain metrics`,
      count: metrics.length,
      data: metrics,
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}
