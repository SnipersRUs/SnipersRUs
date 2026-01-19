#!/usr/bin/env python3
"""
Quick script to list all MEXC perpetual futures pairs
"""

import ccxt

print("🔍 Loading MEXC perpetual futures pairs...\n")

try:
    exchange = ccxt.mexc({
        "enableRateLimit": True,
        "options": {"defaultType": "swap"}
    })

    exchange.load_markets()

    perpetual_pairs = []

    for symbol, market in exchange.markets.items():
        # MEXC perpetual futures
        if (market.get("type") == "swap" and
            market.get("quote", "").upper() == "USDT" and
            market.get("active", True)):
            perpetual_pairs.append(symbol)

    perpetual_pairs.sort()

    print(f"✅ Found {len(perpetual_pairs)} MEXC perpetual futures pairs:\n")
    print("=" * 60)

    # Group by base asset (first part of symbol)
    grouped = {}
    for pair in perpetual_pairs:
        base = pair.split('/')[0] if '/' in pair else pair.split(':')[0]
        if base not in grouped:
            grouped[base] = []
        grouped[base].append(pair)

    # Print grouped
    for base in sorted(grouped.keys()):
        pairs = grouped[base]
        print(f"\n{base} ({len(pairs)} pairs):")
        for pair in pairs[:10]:  # Show first 10 per group
            print(f"  • {pair}")
        if len(pairs) > 10:
            print(f"  ... and {len(pairs) - 10} more")

    print("\n" + "=" * 60)
    print(f"\n📊 Total: {len(perpetual_pairs)} perpetual futures pairs")
    print(f"✅ These are the pairs that Bounty Seeker v5 will scan")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
