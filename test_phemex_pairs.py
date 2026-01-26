#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Phemex futures pairs loading
"""

import ccxt

def test_phemex_pairs():
    """Test loading Phemex futures pairs"""
    print("🔍 Testing Phemex Futures Pairs")
    print("=" * 50)

    try:
        # Initialize Phemex exchange
        exchange = ccxt.phemex({
            'apiKey': "2c213e33-e1bd-44ac-bf9a-44a4cd2e065a",
            'secret': "4Q2dti8eGbr-QeADqpGA1n6hSs9K4Fb7PPNOeYUkQHhlNTg1NzdiMy0yNjkyLTRiNjEtYWU2ZS05OTA5YjljYzQ2MTc",
            'sandbox': False,
            'options': {
                'defaultType': 'swap'
            },
            'enableRateLimit': True,
        })

        print("✅ Phemex exchange initialized")

        # Load markets
        exchange.load_markets()
        markets = exchange.markets

        print(f"📊 Total markets: {len(markets)}")

        # Filter for USDT futures pairs
        futures_pairs = []
        for symbol, market in markets.items():
            if (market['type'] == 'swap' and
                market['quote'] == 'USDT' and
                market['active'] and
                'USDT' in symbol):
                futures_pairs.append(symbol)

        print(f"📈 USDT Futures pairs: {len(futures_pairs)}")

        if futures_pairs:
            print("🔍 First 20 futures pairs:")
            for i, pair in enumerate(futures_pairs[:20]):
                print(f"  {i+1:2d}. {pair}")

            if len(futures_pairs) > 20:
                print(f"  ... and {len(futures_pairs) - 20} more pairs")
        else:
            print("❌ No futures pairs found!")

            # Try alternative approach
            print("\n🔍 Trying alternative approach...")
            alt_pairs = []
            for symbol, market in markets.items():
                if (market['type'] == 'swap' and
                    market['active'] and
                    'USDT' in symbol):
                    alt_pairs.append(symbol)

            print(f"📈 Alternative pairs: {len(alt_pairs)}")
            if alt_pairs:
                print("🔍 First 10 alternative pairs:")
                for i, pair in enumerate(alt_pairs[:10]):
                    print(f"  {i+1:2d}. {pair}")

        return futures_pairs

    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    test_phemex_pairs()















