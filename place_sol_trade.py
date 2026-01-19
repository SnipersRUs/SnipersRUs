#!/usr/bin/env python3
"""
Place SOL Long Trade - Using Working Bot Method
"""

import asyncio
import time
import requests
from datetime import datetime, timezone
from hyperliquid.exchange import Exchange
from eth_account import Account
from hyperliquid_config import HYPERLIQUID_CONFIG, HYPERLIQUID_NOTIFICATION_CONFIG

class SolTradePlacer:
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
    
    async def place_sol_long(self):
        """Place $15 SOL long order"""
        print("🚀 PLACING $15 SOL LONG ORDER...")
        
        try:
            # Get current SOL price
            all_mids = self.client.info.all_mids()
            sol_price = float(all_mids.get('SOL', 0))
            
            if not sol_price:
                print("❌ Could not get SOL price")
                return False
            
            print(f"💰 SOL Current Price: ${sol_price:.4f}")
            
            # Calculate position size for $15
            position_size = round(15.0 / sol_price, 6)
            
            print(f"🎯 Order Details:")
            print(f"  Symbol: SOL")
            print(f"  Side: LONG")
            print(f"  Position Size: {position_size:.6f} SOL")
            print(f"  Position Value: $15.00")
            print(f"  Entry Price: ${sol_price:.4f}")
            
            # Try different order types
            order_types = [
                {"limit": {"tif": "Ioc"}},  # Immediate or Cancel
                {"limit": {"tif": "Alo"}},  # Add Liquidity Only
                {"limit": {"tif": "Gtc"}},  # Good Till Cancel
            ]
            
            for i, order_type in enumerate(order_types):
                try:
                    print(f"🔄 Trying order type {i+1}: {order_type}")
                    
                    # Place order
                    order = self.client.order(
                        name="SOL",
                        is_buy=True,  # Long position
                        sz=position_size,
                        limit_px=sol_price,
                        order_type=order_type,
                        reduce_only=False
                    )
                    
                    if order:
                        print("✅ ORDER EXECUTED SUCCESSFULLY!")
                        print(f"  Order Response: {order}")
                        
                        # Send Discord notification
                        await self.send_discord_alert(
                            title="🚀 SOL LONG ORDER EXECUTED",
                            description=f"**SOL** LONG @ ${sol_price:.4f}",
                            color=0x00ff00,
                            fields=[
                                {"name": "Position Size", "value": f"{position_size:.6f} SOL", "inline": True},
                                {"name": "Position Value", "value": "$15.00", "inline": True},
                                {"name": "Entry Price", "value": f"${sol_price:.4f}", "inline": True},
                                {"name": "Order Type", "value": str(order_type), "inline": True},
                                {"name": "Order Response", "value": str(order), "inline": False},
                                {"name": "✅ Real Trade", "value": "This is a REAL order on Hyperliquid!", "inline": False}
                            ]
                        )
                        
                        print("✅ Trade notification sent to Discord!")
                        return True
                    else:
                        print(f"❌ Order type {i+1} failed")
                        
                except Exception as e:
                    print(f"❌ Order type {i+1} error: {e}")
                    continue
            
            print("❌ All order types failed")
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
    placer = SolTradePlacer()
    await placer.place_sol_long()

if __name__ == "__main__":
    asyncio.run(main())























































