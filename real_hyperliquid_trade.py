#!/usr/bin/env python3
"""
Real Hyperliquid Trade Execution
Actually places a trade on Hyperliquid using your credentials
"""

import asyncio
import time
import requests
import json
import hmac
import hashlib
from datetime import datetime, timezone
from hyperliquid_config import HYPERLIQUID_CONFIG, HYPERLIQUID_NOTIFICATION_CONFIG

class RealHyperliquidTrade:
    def __init__(self):
        self.private_key = HYPERLIQUID_CONFIG['private_key']
        self.public_wallet = HYPERLIQUID_CONFIG['public_wallet']
        self.discord_webhook = HYPERLIQUID_NOTIFICATION_CONFIG['discord_webhook']
        self.base_url = "https://api.hyperliquid.xyz"
    
    def sign_message(self, message: str) -> str:
        """Sign message with private key"""
        try:
            # Convert private key to bytes
            private_key_bytes = bytes.fromhex(self.private_key[2:])  # Remove 0x prefix
            
            # Sign the message
            signature = hmac.new(
                private_key_bytes,
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return signature
        except Exception as e:
            print(f"Error signing message: {e}")
            return None
    
    async def place_real_order(self):
        """Place a real order on Hyperliquid"""
        print("🚀 PLACING REAL ORDER ON HYPERLIQUID...")
        
        try:
            # Order parameters
            symbol = "BTC"  # Bitcoin
            side = "buy"    # Long position
            size = 0.0001   # Small size for testing
            price = 115000  # Limit price
            
            # Prepare order data
            order_data = {
                "action": {
                    "type": "order",
                    "orders": [{
                        "a": 0,  # Asset ID for BTC
                        "b": side == "buy",  # True for buy, False for sell
                        "p": str(price),  # Price as string
                        "s": str(size),   # Size as string
                        "r": False,       # Reduce only
                        "t": "Limit"      # Order type
                    }]
                },
                "nonce": int(time.time() * 1000),
                "vaultAddress": None
            }
            
            # Sign the order
            message = json.dumps(order_data, separators=(',', ':'))
            signature = self.sign_message(message)
            
            if not signature:
                print("❌ Failed to sign order")
                return False
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.public_wallet}",
                "X-Signature": signature
            }
            
            # Send order to Hyperliquid
            response = requests.post(
                f"{self.base_url}/exchange",
                headers=headers,
                data=message,
                timeout=10
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ REAL ORDER PLACED!")
                print(f"Order ID: {result.get('id', 'N/A')}")
                
                # Send Discord notification
                await self.send_discord_alert(
                    title="🚀 REAL HYPERLIQUID ORDER PLACED!",
                    description=f"**{symbol}** {side.upper()} @ ${price}",
                    color=0x00ff00,
                    fields=[
                        {"name": "Symbol", "value": symbol, "inline": True},
                        {"name": "Side", "value": side.upper(), "inline": True},
                        {"name": "Size", "value": str(size), "inline": True},
                        {"name": "Price", "value": f"${price}", "inline": True},
                        {"name": "Order ID", "value": str(result.get('id', 'N/A')), "inline": True},
                        {"name": "Status", "value": "SUBMITTED", "inline": True},
                        {"name": "✅ Real Trade", "value": "This is a real order on Hyperliquid!", "inline": False}
                    ]
                )
                
                return True
            else:
                print(f"❌ Order failed: {response.status_code} - {response.text}")
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
                    "text": "Real Hyperliquid Trade"
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
    trader = RealHyperliquidTrade()
    await trader.place_real_order()

if __name__ == "__main__":
    asyncio.run(main())























































