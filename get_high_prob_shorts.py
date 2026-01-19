#!/usr/bin/env python3
"""
Get High Probability Short Opportunities
Filters 5m scan results for best short setups
"""

import asyncio
import sys
sys.path.append('.')
from quick_5m_short_scan import Quick5mShortScanner

async def main():
    """Get and filter high probability shorts"""
    scanner = Quick5mShortScanner()
    results = await scanner.run_scan()

    # Filter for high probability: close distance (< 0.2%) AND high importance (70%+)
    high_prob = [
        r for r in results
        if r['distance_pct'] < 0.2 and r['importance'] >= 70
    ]

    # Also get very close ones (< 0.1%) even if importance is lower
    very_close = [
        r for r in results
        if r['distance_pct'] < 0.1 and r['importance'] >= 60
    ]

    # Combine and deduplicate
    all_best = {}
    for r in high_prob + very_close:
        symbol = r['symbol']
        if symbol not in all_best or r['distance_pct'] < all_best[symbol]['distance_pct']:
            all_best[symbol] = r

    best_list = sorted(all_best.values(), key=lambda x: (x['distance_pct'], -x['importance']))

    print("\n" + "="*70)
    print("🔥 HIGH PROBABILITY SHORT OPPORTUNITIES 🔥")
    print("="*70)
    print(f"\nFound {len(best_list)} high-probability short setups:\n")

    if not best_list:
        print("❌ No high-probability shorts found. Running full scan...\n")
        # Show top 10 overall
        for i, result in enumerate(results[:10], 1):
            print(f"{i}. {result['symbol']}")
            print(f"   📍 Distance: {result['distance_pct']:.2f}% | 🔥 Importance: {result['importance']:.0f}%")
            print(f"   💰 Level: ${result['level']:.6f} | Current: ${result['current_price']:.6f}")
            print(f"   🔗 {result['tradingview_link']}\n")
    else:
        for i, result in enumerate(best_list, 1):
            # Calculate risk/reward estimate
            distance_to_level = abs(result['level'] - result['current_price'])
            entry = result['current_price']
            stop = result['level'] * 1.001  # 0.1% above liquidation
            target = entry * 0.98  # 2% target
            risk = abs(entry - stop) / entry * 100
            reward = abs(entry - target) / entry * 100
            rr = reward / risk if risk > 0 else 0

            print(f"{i}. 🎯 {result['symbol']}")
            print(f"   📍 Distance to Liquidation: {result['distance_pct']:.2f}%")
            print(f"   🔥 Importance Score: {result['importance']:.0f}%")
            print(f"   💰 Liquidation Level: ${result['level']:.6f}")
            print(f"   💵 Current Price: ${result['current_price']:.6f}")
            print(f"   📊 Suggested Entry: ${entry:.6f}")
            print(f"   🛑 Stop Loss: ${stop:.6f} ({risk:.2f}% risk)")
            print(f"   🎯 Take Profit: ${target:.6f} ({reward:.2f}% reward)")
            print(f"   ⚖️  Risk:Reward = 1:{rr:.2f}")
            print(f"   🔗 Chart: {result['tradingview_link']}\n")

    print("="*70)
    print("💡 SETUP: These coins are approaching TOP liquidation levels where")
    print("   longs were liquidated. Watch for rejection/cascade for SHORT entries.")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())


