#!/usr/bin/env python3
"""
Close SOL Long Position
"""

import asyncio
import time
import requests
from datetime import datetime, timezone
from hyperliquid.exchange import Exchange
from eth_account import Account
from hyperliquid_config import HYPERLIQUID_CONFIG, HYPERLIQUID_NOTIFICATION_CONFIG

class SolPositionCloser:
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
    
    async def close_sol_position(self):
        """Close SOL long position"""
        print("🔴 CLOSING SOL LONG POSITION...")
        
        try:
            # First, check current positions
            user_state = self.client.info.user_state(self.public_wallet)
            positions = user_state.get('assetPositions', [])
            
            print("📊 Current Positions:")
            sol_position = None
            for pos in positions:
                coin = pos['position']['coin']
                size = float(pos['position']['szi'])
                entry_px = float(pos['position']['entryPx'])
                
                print(f"  {coin}: {size} @ ${entry_px}")
                
                if coin == 'SOL' and size > 0:
                    sol_position = pos
                    print(f"  ✅ Found SOL long position: {size} SOL @ ${entry_px}")
            
            if not sol_position:
                print("❌ No SOL long position found to close")
                return False
            
            # Get current SOL price
            all_mids = self.client.info.all_mids()
            sol_price = float(all_mids.get('SOL', 0))
            rounded_price = self.round_to_tick_size(sol_price, 0.01)
            
            position_size = float(sol_position['position']['szi'])
            entry_price = float(sol_position['position']['entryPx'])
            
            print(f"💰 Current SOL Price: ${sol_price:.4f}")
            print(f"💰 Rounded Price: ${rounded_price:.2f}")
            print(f"📊 Position Size: {position_size} SOL")
            print(f"📊 Entry Price: ${entry_price:.2f}")
            
            # Calculate P&L
            pnl = (sol_price - entry_price) * position_size
            pnl_pct = ((sol_price - entry_price) / entry_price) * 100
            
            print(f"💰 P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
            
            # Close position with market order
            print(f"🔴 Closing {position_size} SOL @ ${rounded_price:.2f}")
            
            # Place close order (sell to close long)
            order = self.client.order(
                name="SOL",
                is_buy=False,  # Sell to close long
                sz=position_size,
                limit_px=rounded_price,
                order_type={"limit": {"tif": "Ioc"}},  # Immediate or Cancel
                reduce_only=True  # This is important for closing
            )
            
            if order and order.get('response', {}).get('data', {}).get('statuses', [{}])[0].get('error') is None:
                print("✅ POSITION CLOSED SUCCESSFULLY!")
                print(f"  Order Response: {order}")
                
                # Send Discord notification
                await self.send_discord_alert(
                    title="🔴 SOL POSITION CLOSED",
                    description=f"Closed {position_size} SOL @ ${rounded_price:.2f}",
                    color=0xff0000,
                    fields=[
                        {"name": "Position Size", "value": f"{position_size} SOL", "inline": True},
                        {"name": "Close Price", "value": f"${rounded_price:.2f}", "inline": True},
                        {"name": "Entry Price", "value": f"${entry_price:.2f}", "inline": True},
                        {"name": "P&L", "value": f"${pnl:.2f}", "inline": True},
                        {"name": "P&L %", "value": f"{pnl_pct:+.2f}%", "inline": True},
                        {"name": "Order Response", "value": str(order), "inline": False},
                        {"name": "✅ Position Closed", "value": "SOL long position successfully closed!", "inline": False}
                    ]
                )
                
                print("✅ Position close notification sent to Discord!")
                return True
            else:
                error = order.get('response', {}).get('data', {}).get('statuses', [{}])[0].get('error', 'Unknown error')
                print(f"❌ Failed to close position: {error}")
                
                # Try with GTC order if IOC failed
                print("🔄 Trying GTC order...")
                order = self.client.order(
                    name="SOL",
                    is_buy=False,  # Sell to close long
                    sz=position_size,
                    limit_px=rounded_price,
                    order_type={"limit": {"tif": "Gtc"}},  # Good Till Cancel
                    reduce_only=True
                )
                
                if order and order.get('response', {}).get('data', {}).get('statuses', [{}])[0].get('error') is None:
                    print("✅ POSITION CLOSE ORDER PLACED!")
                    print(f"  Order Response: {order}")
                    return True
                else:
                    error = order.get('response', {}).get('data', {}).get('statuses', [{}])[0].get('error', 'Unknown error')
                    print(f"❌ GTC order also failed: {error}")
                    return False
                
        except Exception as e:
            print(f"❌ Error closing position: {e}")
            return False
    
    async def send_discord_alert(self, title: str, description: str, color: int = 0xff0000, fields: list = None):
        """Send Discord alert"""
        try:
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Hyperliquid Position Close"
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
    closer = SolPositionCloser()
    await closer.close_sol_position()

if __name__ == "__main__":
    asyncio.run(main())























































