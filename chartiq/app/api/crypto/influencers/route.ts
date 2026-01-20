import { NextResponse } from 'next/server';
import { getInfluencers } from '@/lib/cryptoNews';

export async function GET() {
  try {
    const influencers = getInfluencers();
    
    return NextResponse.json({
      success: true,
      data: influencers,
      count: influencers.length,
    });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}
