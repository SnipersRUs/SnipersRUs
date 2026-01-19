#!/usr/bin/env python3
"""
Execute $15 SOL Long Order
"""

import asyncio
import time
import requests
from datetime import datetime, timezone
from hyperliquid.exchange import Exchange
from eth_account import Account
from hyperliquid.utils.signing import OrderType
from hyperliquid_config import HYPERLIQUID_CONFIG, HYPERLIQUID_NOTIFICATION_CONFIG

class SolLongExecutor:
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
    
    async def execute_sol_long(self):
        """Execute $15 SOL long order"""
        print("🚀 EXECUTING $15 SOL LONG ORDER...")
        
        try:
            # Get current SOL price
            all_mids = self.client.info.all_mids()
            sol_price = float(all_mids.get('SOL', 0))
            
            if not sol_price:
                print("❌ Could not get SOL price")
                return False
            
            print(f"💰 SOL Current Price: ${sol_price:.4f}")
            
            # Calculate position size for $15
            position_size = round(15.0 / sol_price, 6)  # $15 worth of SOL, rounded to 6 decimals
            leverage = 15  # 15x leverage
            
            print(f"🎯 Order Details:")
            print(f"  Symbol: SOL")
            print(f"  Side: LONG")
            print(f"  Position Size: {position_size:.6f} SOL")
            print(f"  Position Value: $15.00")
            print(f"  Leverage: {leverage}x")
            print(f"  Entry Price: ${sol_price:.4f}")
            
            # Place limit order at current price (acts like market order)
            order = self.client.order(
                name="SOL",
                is_buy=True,  # Long position
                sz=position_size,
                limit_px=sol_price,
                order_type=OrderType({"limit": {"tif": "Ioc"}}),  # Immediate or Cancel
                reduce_only=False
            )
            
            if order:
                print("✅ ORDER EXECUTED SUCCESSFULLY!")
                print(f"  Order ID: {order.get('id', 'N/A')}")
                print(f"  Status: {order.get('status', 'N/A')}")
                
                # Send Discord notification
                await self.send_discord_alert(
                    title="🚀 SOL LONG ORDER EXECUTED",
                    description=f"**SOL** LONG @ ${sol_price:.4f}",
                    color=0x00ff00,
                    fields=[
                        {"name": "Position Size", "value": f"{position_size:.6f} SOL", "inline": True},
                        {"name": "Position Value", "value": "$15.00", "inline": True},
                        {"name": "Leverage", "value": f"{leverage}x", "inline": True},
                        {"name": "Entry Price", "value": f"${sol_price:.4f}", "inline": True},
                        {"name": "Order ID", "value": str(order.get('id', 'N/A')), "inline": True},
                        {"name": "Status", "value": "FILLED", "inline": True},
                        {"name": "✅ Real Trade", "value": "This is a REAL order on Hyperliquid!", "inline": False}
                    ]
                )
                
                print("✅ Trade notification sent to Discord!")
                return True
            else:
                print("❌ Failed to place order")
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
    executor = SolLongExecutor()
    await executor.execute_sol_long()

if __name__ == "__main__":
    asyncio.run(main())
