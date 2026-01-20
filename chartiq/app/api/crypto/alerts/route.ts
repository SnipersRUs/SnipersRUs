import { NextRequest, NextResponse } from 'next/server';
import { getAlerts, resolveAlert } from '@/lib/cryptoNews';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const activeOnly = searchParams.get('active') === 'true';
    
    let alerts = getAlerts();
    
    if (activeOnly) {
      alerts = alerts.filter(a => !a.resolved);
    }
    
    // Sort by timestamp (newest first)
    alerts.sort((a, b) => b.timestamp - a.timestamp);
    
    return NextResponse.json({
      success: true,
      data: alerts,
      count: alerts.length,
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

export async function PATCH(request: NextRequest) {
  try {
    const body = await request.json();
    const { alertId } = body;
    
    if (!alertId) {
      return NextResponse.json(
        { success: false, error: 'alertId is required' },
        { status: 400 }
      );
    }
    
    resolveAlert(alertId);
    
    return NextResponse.json({
      success: true,
      message: 'Alert resolved',
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}
