import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db-fresh'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const unresolved = searchParams.get('unresolved')
    const severity = searchParams.get('severity')
    const limit = parseInt(searchParams.get('limit') || '20')

    const where: any = {}

    if (unresolved === 'true') {
      where.resolved = false
    }

    if (severity) {
      where.severity = severity
    }

    const alerts = await db.cryptoAlert.findMany({
      where,
      orderBy: {
        createdAt: 'desc'
      },
      take: limit
    })

    return NextResponse.json(alerts)
  } catch (error) {
    console.error('Error fetching alerts:', error)
    return NextResponse.json(
      { error: 'Failed to fetch alerts' },
      { status: 500 }
    )
  }
}

export async function PATCH(request: NextRequest) {
  try {
    const body = await request.json()
    const { id, resolved } = body

    const alert = await db.cryptoAlert.update({
      where: { id },
      data: {
        resolved,
        resolvedAt: resolved ? new Date() : null
      }
    })

    return NextResponse.json(alert)
  } catch (error) {
    console.error('Error updating alert:', error)
    return NextResponse.json(
      { error: 'Failed to update alert' },
      { status: 500 }
    )
  }
}
