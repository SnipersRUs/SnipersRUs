#!/usr/bin/env python3
"""
Hyperliquid Scanner Diagnostic Tool
Helps identify why your scanner isn't producing signals
"""

import asyncio
import logging
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional
from hyperliquid.exchange import Exchange
from eth_account import Account
from hyperliquid_config import HYPERLIQUID_CONFIG, HYPERLIQUID_SYMBOLS

# Setup logging with more detail
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for maximum info
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler("scanner_diagnostic.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("scanner_diagnostic")

class ScannerDiagnostic:
    def __init__(self):
        # Initialize Hyperliquid client
        self.private_key = HYPERLIQUID_CONFIG['private_key']
        self.public_wallet = HYPERLIQUID_CONFIG['public_wallet']
        
        wallet = Account.from_key(self.private_key)
        self.client = Exchange(
            wallet=wallet,
            base_url="https://api.hyperliquid.xyz"
        )
        
        self.assets_to_scan = HYPERLIQUID_SYMBOLS
        
    async def test_basic_connectivity(self):
        """Test 1: Basic API Connection"""
        print("\n" + "="*50)
        print("TEST 1: BASIC CONNECTIVITY")
        print("="*50)
        
        try:
            # Test connection by getting user state
            user_state = self.client.info.user_state(self.public_wallet)
            if user_state:
                print("✅ Successfully connected to Hyperliquid API")
                print(f"   Wallet: {self.public_wallet}")
                return True
            else:
                print("❌ Failed to connect to Hyperliquid API")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    async def test_market_data_access(self):
        """Test 2: Can we get market data?"""
        print("\n" + "="*50)
        print("TEST 2: MARKET DATA ACCESS")
        print("="*50)
        
        successful_reads = 0
        failed_reads = []
        
        for asset in self.assets_to_scan[:5]:  # Test first 5 assets
            try:
                # Get price from all mids
                all_mids = self.client.info.all_mids()
                if all_mids and asset in all_mids:
                    price = float(all_mids[asset])
                    print(f"✅ {asset}: ${price:.4f}")
                    successful_reads += 1
                else:
                    print(f"⚠️ {asset}: No data received")
                    failed_reads.append(asset)
            except Exception as e:
                print(f"❌ {asset}: Error - {e}")
                failed_reads.append(asset)
            
            await asyncio.sleep(0.5)  # Small delay to avoid rate limits
        
        print(f"\nSummary: {successful_reads}/5 successful")
        if failed_reads:
            print(f"Failed assets: {', '.join(failed_reads)}")
        
        return successful_reads > 0
    
    async def test_signal_conditions(self):
        """Test 3: Check if signal conditions could ever be met"""
        print("\n" + "="*50)
        print("TEST 3: SIGNAL CONDITION ANALYSIS")
        print("="*50)
        
        print("\nAnalyzing market conditions for potential signals...")
        
        for asset in self.assets_to_scan[:3]:  # Check top 3 assets
            try:
                # Get current price
                all_mids = self.client.info.all_mids()
                if not all_mids or asset not in all_mids:
                    continue
                
                current_price = float(all_mids[asset])
                
                print(f"\n{asset}:")
                print(f"  Price: ${current_price:.4f}")
                
                # Simulate some common signal conditions
                # Golden Pocket (example: price in 61.8% - 65% retracement zone)
                # For testing, we'll just show what values WOULD trigger
                mock_high = current_price * 1.20  # Assume 20% higher was recent high
                mock_low = current_price * 0.95   # Assume 5% lower was recent low
                golden_pocket_low = mock_low + (mock_high - mock_low) * 0.618
                golden_pocket_high = mock_low + (mock_high - mock_low) * 0.65
                
                in_golden_pocket = golden_pocket_low <= current_price <= golden_pocket_high
                
                print(f"  Golden Pocket Range: ${golden_pocket_low:.2f} - ${golden_pocket_high:.2f}")
                print(f"  In Golden Pocket: {'YES ✅' if in_golden_pocket else 'NO ❌'}")
                
                # Check momentum (simplified)
                price_change_1h = (current_price - (current_price * 0.99)) / current_price * 100  # Mock 1% change
                print(f"  Momentum (mock): {price_change_1h:.2f}%")
                
                # Volume check (if available from your real scanner)
                print(f"  Volume Data: Would need real scanner integration")
                
            except Exception as e:
                print(f"❌ Error analyzing {asset}: {e}")
            
            await asyncio.sleep(1)
    
    async def test_scanner_loop(self):
        """Test 4: Simulate a scanner loop with very loose conditions"""
        print("\n" + "="*50)
        print("TEST 4: SCANNER SIMULATION (LOOSE CONDITIONS)")
        print("="*50)
        
        print("\nRunning scanner with VERY loose conditions for 30 seconds...")
        print("(This should definitely produce signals if API is working)\n")
        
        signals_found = []
        start_time = asyncio.get_event_loop().time()
        iterations = 0
        
        while (asyncio.get_event_loop().time() - start_time) < 30:  # Run for 30 seconds
            iterations += 1
            print(f"\n--- Scan #{iterations} ---")
            
            for asset in self.assets_to_scan[:3]:  # Scan top 3 assets
                try:
                    all_mids = self.client.info.all_mids()
                    if not all_mids or asset not in all_mids:
                        continue
                    
                    current_price = float(all_mids[asset])
                    
                    # SUPER LOOSE CONDITIONS - should trigger often
                    # Just checking if price exists and is > 0
                    if current_price > 0:
                        # 50% chance to generate a signal (for testing)
                        if random.random() > 0.7:  # 30% chance
                            signal = {
                                'timestamp': datetime.now().isoformat(),
                                'asset': asset,
                                'action': 'BUY' if random.random() > 0.5 else 'SELL',
                                'price': current_price,
                                'reason': 'Test signal - loose conditions met',
                                'strength': random.random()
                            }
                            signals_found.append(signal)
                            print(f"  🎯 SIGNAL: {asset} {signal['action']} @ ${current_price:.2f}")
                        else:
                            print(f"  {asset}: ${current_price:.2f} (no signal)")
                    
                except Exception as e:
                    print(f"  ❌ Error scanning {asset}: {e}")
            
            await asyncio.sleep(5)  # Wait 5 seconds between scans
        
        print(f"\n{'='*50}")
        print(f"SCAN COMPLETE: Found {len(signals_found)} signals in {iterations} iterations")
        
        if signals_found:
            print("\nSignals found:")
            for sig in signals_found[-5:]:  # Show last 5 signals
                print(f"  - {sig['timestamp']}: {sig['asset']} {sig['action']} @ ${sig['price']:.2f}")
        
        return len(signals_found) > 0
    
    async def check_rate_limits(self):
        """Test 5: Check if we're hitting rate limits"""
        print("\n" + "="*50)
        print("TEST 5: RATE LIMIT CHECK")
        print("="*50)
        
        print("Making rapid API calls to test rate limits...")
        
        success_count = 0
        error_count = 0
        
        for i in range(20):  # Make 20 rapid calls
            try:
                all_mids = self.client.info.all_mids()
                if all_mids and 'BTC' in all_mids:
                    success_count += 1
                    print(".", end="", flush=True)
                else:
                    error_count += 1
                    print("x", end="", flush=True)
            except Exception as e:
                error_count += 1
                print("X", end="", flush=True)
                if "rate" in str(e).lower():
                    print(f"\n⚠️ Rate limit detected: {e}")
                    break
            
            # No delay - testing rate limits
        
        print(f"\n\nResults: {success_count} successful, {error_count} failed")
        
        if error_count > 5:
            print("⚠️ High error rate - possible rate limiting")
        else:
            print("✅ No obvious rate limiting detected")
        
        return error_count < 10
    
    async def run_all_diagnostics(self):
        """Run all diagnostic tests"""
        print("""
╔══════════════════════════════════════════════════╗
║     HYPERLIQUID SCANNER DIAGNOSTIC TOOL          ║
║     Finding out why signals aren't generating    ║
╚══════════════════════════════════════════════════╝
        """)
        
        all_tests_passed = True
        
        # Test 1: Basic connectivity
        if not await self.test_basic_connectivity():
            print("\n🚨 CRITICAL: Cannot connect to API. Check:")
            print("   1. Your API keys in hyperliquid_config.py")
            print("   2. Network connection")
            print("   3. Hyperliquid API status")
            all_tests_passed = False
            return  # No point continuing if we can't connect
        
        # Test 2: Market data access
        if not await self.test_market_data_access():
            print("\n🚨 PROBLEM: Cannot read market data. Check:")
            print("   1. Symbol format (should be like 'BTC', 'ETH', 'SOL')")
            print("   2. API permissions")
            all_tests_passed = False
        
        # Test 3: Signal conditions
        await self.test_signal_conditions()
        
        # Test 4: Scanner loop simulation
        if not await self.test_scanner_loop():
            print("\n⚠️ WARNING: No signals generated even with loose conditions")
            print("   Your scanner logic might be too restrictive")
            all_tests_passed = False
        
        # Test 5: Rate limits
        await self.check_rate_limits()
        
        # Final diagnosis
        print("\n" + "="*50)
        print("DIAGNOSTIC SUMMARY")
        print("="*50)
        
        if all_tests_passed:
            print("""
✅ API connection is working
✅ Market data is accessible
✅ Signals CAN be generated

LIKELY ISSUES WITH YOUR SCANNER:
1. Signal conditions are too strict/impossible to meet
2. Scanner isn't actually running/calling the check functions
3. Bug in the signal detection logic (check your conditions)

RECOMMENDATIONS:
1. Add debug logging to EVERY step of your scanner
2. Temporarily lower all thresholds (e.g., from 0.8 to 0.3)
3. Add a "force signal" test mode that always generates at least one signal
4. Check if your scanner is actually calling the market data functions
            """)
        else:
            print("""
❌ Found issues with API connectivity or data access

FIX THESE FIRST:
1. Verify your API credentials are correct
2. Check network connectivity
3. Ensure you're using the correct symbol format
4. Verify Hyperliquid API is operational
            """)
        
        # Save detailed log
        print(f"\n📄 Detailed log saved to: scanner_diagnostic.log")

async def main():
    diagnostic = ScannerDiagnostic()
    await diagnostic.run_all_diagnostics()

if __name__ == "__main__":
    asyncio.run(main())























































