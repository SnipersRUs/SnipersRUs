#!/usr/bin/env python3
"""
Diagnostic scanner to check what symbols are available
"""

import ccxt
import pandas as pd

def check_exchange_symbols(exchange_name):
    """Check what symbols are available on an exchange"""
    print(f"\n🔍 Checking {exchange_name.upper()}...")
    
    try:
        if exchange_name == "binance":
            exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {'defaultType': 'future'},
                'timeout': 10000
            })
        elif exchange_name == "bybit":
            exchange = ccxt.bybit({
                'enableRateLimit': True,
                'options': {'defaultType': 'linear'},
                'timeout': 10000
            })
        elif exchange_name == "mexc":
            exchange = ccxt.mexc({
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'},
                'timeout': 10000
            })
        else:
            print(f"❌ Unknown exchange: {exchange_name}")
            return
        
        # Load markets
        exchange.load_markets()
        print(f"✅ Loaded {len(exchange.markets)} total markets")
        
        # Check different market types
        futures_count = 0
        usdt_count = 0
        active_count = 0
        
        for symbol, market in exchange.markets.items():
            # Check if it's USDT
            if market.get('quote') == 'USDT':
                usdt_count += 1
                
                # Check if active
                if market.get('active'):
                    active_count += 1
                    
                    # Check if futures
                    is_futures = False
                    if exchange_name == "binance":
                        is_futures = (market.get('future') == True and 
                                    market.get('linear') == True)
                    elif exchange_name == "bybit":
                        is_futures = (market.get('linear') == True and 
                                    market.get('swap') == True)
                    elif exchange_name == "mexc":
                        is_futures = (market.get('swap') == True and 
                                    market.get('linear') == True)
                    
                    if is_futures:
                        futures_count += 1
                        if futures_count <= 10:  # Show first 10
                            print(f"  📈 {symbol} - {market.get('type', 'unknown')}")
        
        print(f"📊 Summary for {exchange_name.upper()}:")
        print(f"  Total markets: {len(exchange.markets)}")
        print(f"  USDT markets: {usdt_count}")
        print(f"  Active USDT: {active_count}")
        print(f"  Futures USDT: {futures_count}")
        
        # Test a few tickers
        print(f"\n🧪 Testing tickers...")
        test_symbols = []
        for symbol, market in exchange.markets.items():
            if (market.get('quote') == 'USDT' and 
                market.get('active') and 
                len(test_symbols) < 5):
                
                is_futures = False
                if exchange_name == "binance":
                    is_futures = (market.get('future') == True and 
                                market.get('linear') == True)
                elif exchange_name == "bybit":
                    is_futures = (market.get('linear') == True and 
                                market.get('swap') == True)
                elif exchange_name == "mexc":
                    is_futures = (market.get('swap') == True and 
                                market.get('linear') == True)
                
                if is_futures:
                    test_symbols.append(symbol)
        
        for symbol in test_symbols[:3]:
            try:
                ticker = exchange.fetch_ticker(symbol)
                volume = ticker.get('quoteVolume', 0)
                print(f"  {symbol}: Volume ${volume:,.0f}")
            except Exception as e:
                print(f"  {symbol}: Error - {e}")
        
    except Exception as e:
        print(f"❌ Error with {exchange_name}: {e}")

def main():
    print("🔍 DIAGNOSTIC SCANNER - Checking Exchange Availability")
    print("=" * 60)
    
    exchanges = ["binance", "bybit", "mexc"]
    
    for exchange in exchanges:
        check_exchange_symbols(exchange)
    
    print(f"\n✅ Diagnostic complete!")

if __name__ == "__main__":
    main()




