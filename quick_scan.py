#!/usr/bin/env python3
"""
Quick scan for micro cap opportunities
"""

import asyncio
import requests
from vwap_bottom_scanner import VWAPBottomScanner

async def run_immediate_scan():
    print('🔍 Running immediate micro cap scan...')
    scanner = VWAPBottomScanner()
    
    # Run scan
    signals = await scanner.scan_for_opportunities()
    
    if signals:
        print(f'🎉 Found {len(signals)} micro cap opportunities!')
        for i, signal in enumerate(signals[:6]):  # Top 6
            print(f'{i+1}. {signal.symbol} LONG @ ${signal.entry_price:.6f} ({signal.confidence:.1f}%) - {signal.drawdown_percent:.1f}% down')
            print(f'   Market Cap: ${signal.market_cap:,.0f} | Volume: ${signal.volume_24h:,.0f}')
            print(f'   Reason: {signal.reason}')
            print()
        
        # Send alerts
        await scanner.send_discord_alert(signals)
        print('📤 Discord alerts sent!')
    else:
        print('⏳ No micro cap opportunities found this scan')
        # Send no signals alert
        no_signals_embed = {
            'title': '⏳ NO MICRO CAP OPPORTUNITIES FOUND',
            'description': '**Current scan completed - no micro cap gems at bottoms right now**\n\n🔍 **Next scan:** In 1 hour\n⏰ **Timing alerts:** 20 minutes before optimal entry times',
            'color': 0xffa500,
            'fields': [
                {'name': '🎯 What We Look For', 'value': '• Micro caps under $30M market cap\n• Price under hourly VWAP\n• 40%+ drawdown from recent high\n• Volume building up (momentum)', 'inline': False},
                {'name': '⏰ Next Alert', 'value': 'Bot will alert 20 minutes before optimal entry times', 'inline': False}
            ],
            'footer': {'text': 'Micro Cap Bottom Scanner • No Opportunities Found'}
        }
        
        payload = {'embeds': [no_signals_embed]}
        response = requests.post('https://discord.com/api/webhooks/1417770393737105468/59DvcFXjcBwhlGiaugoz_hOc0hLwLP32BRzeojqCJ6fghJRT1lEmL-92hMy7qYcuBqxL', json=payload, timeout=10)
        print(f'📤 No signals alert sent: {response.status_code}')

if __name__ == "__main__":
    asyncio.run(run_immediate_scan())






















































