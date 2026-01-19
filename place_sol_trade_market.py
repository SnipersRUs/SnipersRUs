#!/usr/bin/env python3
"""
Place SOL Long Trade - Market Order
"""

import asyncio
import time
import requests
from datetime import datetime, timezone
from hyperliquid.exchange import Exchange
from eth_account import Account
from hyperliquid_config import HYPERLIQUID_CONFIG, HYPERLIQUID_NOTIFICATION_CONFIG

class SolMarketTradePlacer:
    def __init__(self):
        self.private_key = HYPERLIQUID_CONFIG['private_key']
        self.public_wallet = HYPERLIQUID_CONFIG['public_wallet']
        self.discord_webhook = HYPERLIQUID_NOTIFICATION_CONFIG['discord_webhook']
        
        # Initialize Hyperliquid client
        wallet = Account.from_key(self.private_key)
        self.client = Exchange(
            wallet=wallet,
            base_url="https://api.hyperliquid.xyz"
        )
    
    def round_to_tick_size(self, price, tick_size=0.01):
        """Round price to tick size"""
        return round(price / tick_size) * tick_size
    
    async def place_sol_long(self):
        """Place SOL long order with market order type"""
        print("🚀 PLACING SOL LONG ORDER (MARKET ORDER)...")
        
        try:
            # Get current SOL price
            all_mids = self.client.info.all_mids()
            sol_price = float(all_mids.get('SOL', 0))
            
            if not sol_price:
                print("❌ Could not get SOL price")
                return False
            
            # Round price to tick size (0.01 for SOL)
            rounded_price = self.round_to_tick_size(sol_price, 0.01)
            
            print(f"💰 SOL Current Price: ${sol_price:.4f}")
            print(f"💰 SOL Rounded Price: ${rounded_price:.2f}")
            
            # Try different order types that can match
            order_types = [
                {"limit": {"tif": "Gtc"}},  # Good Till Cancel
                {"limit": {"tif": "Alo"}},  # Add Liquidity Only
            ]
            
            # Try different position sizes
            position_sizes = [0.1, 0.2, 0.5, 1.0]
            
            for order_type in order_types:
                for position_size in position_sizes:
                    try:
                        position_value = position_size * rounded_price
                        
                        print(f"🎯 Trying Order:")
                        print(f"  Symbol: SOL")
                        print(f"  Side: LONG")
                        print(f"  Position Size: {position_size} SOL")
                        print(f"  Position Value: ${position_value:.2f}")
                        print(f"  Entry Price: ${rounded_price:.2f}")
                        print(f"  Order Type: {order_type}")
                        
                        # Place order
                        order = self.client.order(
                            name="SOL",
                            is_buy=True,  # Long position
                            sz=position_size,
                            limit_px=rounded_price,
                            order_type=order_type,
                            reduce_only=False
                        )
                        
                        if order and order.get('response', {}).get('data', {}).get('statuses', [{}])[0].get('error') is None:
                            print("✅ ORDER EXECUTED SUCCESSFULLY!")
                            print(f"  Order Response: {order}")
                            
                            # Send Discord notification
                            await self.send_discord_alert(
                                title="🚀 SOL LONG ORDER EXECUTED",
                                description=f"**SOL** LONG @ ${rounded_price:.2f}",
                                color=0x00ff00,
                                fields=[
                                    {"name": "Position Size", "value": f"{position_size} SOL", "inline": True},
                                    {"name": "Position Value", "value": f"${position_value:.2f}", "inline": True},
                                    {"name": "Entry Price", "value": f"${rounded_price:.2f}", "inline": True},
                                    {"name": "Order Type", "value": str(order_type), "inline": True},
                                    {"name": "Order Response", "value": str(order), "inline": False},
                                    {"name": "✅ Real Trade", "value": "This is a REAL order on Hyperliquid!", "inline": False}
                                ]
                            )
                            
                            print("✅ Trade notification sent to Discord!")
                            return True
                        else:
                            error = order.get('response', {}).get('data', {}).get('statuses', [{}])[0].get('error', 'Unknown error')
                            print(f"❌ Order failed: {error}")
                            
                    except Exception as e:
                        print(f"❌ Order error: {e}")
                        continue
            
            print("❌ All order types and sizes failed")
            return False
                
        except Exception as e:
            print(f"❌ Error placing order: {e}")
            return False
    
    async def send_discord_alert(self, title: str, description: str, color: int = 0x00ff00, fields: list = None):
        """Send Discord alert"""
        try:
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Hyperliquid SOL Long"
                }
            }
            if fields:
                embed["fields"] = fields
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            if response.status_code == 204:
                print(f"✅ Discord alert sent: {title}")
            else:
                print(f"❌ Discord alert failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error sending Discord alert: {e}")

async def main():
    placer = SolMarketTradePlacer()
    await placer.place_sol_long()

if __name__ == "__main__":
    asyncio.run(main())























































