#!/usr/bin/env python3
"""
Hyperliquid Exchange Adapter
US-friendly decentralized exchange
"""

import requests
import json
import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from hyperliquid import HyperliquidSync
from hyperliquid_config import HYPERLIQUID_CONFIG, HYPERLIQUID_NOTIFICATION_CONFIG

class HyperliquidExchange:
    def __init__(self, paper_trading: bool = False):
        self.paper_trading = paper_trading
        self.private_key = HYPERLIQUID_CONFIG['private_key']
        self.api_wallet = HYPERLIQUID_CONFIG['api_wallet']
        self.public_wallet = HYPERLIQUID_CONFIG['public_wallet']
        self.discord_webhook = HYPERLIQUID_NOTIFICATION_CONFIG['discord_webhook']
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('hyperliquid_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize Hyperliquid client
        if not self.paper_trading:
            self.client = HyperliquidSync(
                private_key=self.private_key,
                wallet_address=self.public_wallet
            )
        else:
            self.client = None
        
        # Paper trading simulation
        self.balance = 1000.0  # Simulated balance
        self.positions = {}
        self.last_prices = {}
        
        self.logger.info(f"Hyperliquid Exchange initialized (Paper Trading: {paper_trading})")
        self.logger.info(f"API Wallet: {self.api_wallet}")
        self.logger.info(f"Public Wallet: {self.public_wallet}")
    
    async def test_connection(self) -> bool:
        """Test connection to Hyperliquid"""
        try:
            if self.paper_trading:
                self.logger.info("Paper trading mode - connection test passed")
                return True
            
            # Test with balance endpoint
            balance = self.client.get_balance()
            if balance is not None:
                self.logger.info("Hyperliquid connection test passed")
                return True
            else:
                self.logger.error("Hyperliquid connection test failed - no balance returned")
                return False
                
        except Exception as e:
            self.logger.error(f"Hyperliquid connection test failed: {e}")
            return False
    
    async def get_account_balance(self) -> Dict[str, float]:
        """Get account balance"""
        if self.paper_trading:
            return {
                'USDC': self.balance,
                'total': self.balance
            }
        else:
            try:
                balance = self.client.get_balance()
                if balance:
                    # Parse balance from Hyperliquid response
                    usdc_balance = 0
                    for asset in balance:
                        if asset.get('coin') == 'USDC':
                            usdc_balance = float(asset.get('free', 0))
                            break
                    
                    return {
                        'USDC': usdc_balance,
                        'total': usdc_balance
                    }
                else:
                    self.logger.error("Failed to fetch balance - no data returned")
                    return {'USDC': 0, 'total': 0}
                    
            except Exception as e:
                self.logger.error(f"Failed to fetch balance: {e}")
                return {'USDC': 0, 'total': 0}
    
    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get current ticker for symbol"""
        try:
            if self.paper_trading:
                # Simulate ticker data
                price = self.last_prices.get(symbol, 50000)
                return {
                    'symbol': symbol,
                    'last': price,
                    'bid': price * 0.9999,
                    'ask': price * 1.0001,
                    'volume': 1000000,
                    'timestamp': time.time()
                }
            else:
                # Get price from Hyperliquid
                price = self.client.get_price(symbol)
                if price:
                    ticker = {
                        'symbol': symbol,
                        'last': float(price),
                        'bid': float(price) * 0.9999,
                        'ask': float(price) * 1.0001,
                        'volume': 1000000,
                        'timestamp': time.time()
                    }
                    self.last_prices[symbol] = ticker['last']
                    return ticker
                else:
                    self.logger.error(f"Failed to fetch ticker for {symbol}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            return None
    
    async def place_order(self, symbol: str, side: str, amount: float, 
                         price: Optional[float] = None, order_type: str = 'market',
                         leverage: int = 1) -> Optional[Dict]:
        """Place an order on Hyperliquid"""
        try:
            if self.paper_trading:
                return await self._simulate_order(symbol, side, amount, price, order_type, leverage)
            else:
                # Place order using Hyperliquid client
                order = self.client.place_order(
                    symbol=f"{symbol}-PERP",
                    side=side,
                    quantity=amount,
                    price=price,
                    order_type=order_type
                )
                
                if order:
                    self.logger.info(f"Order placed: {symbol} {side} {amount} @ {price or 'market'}")
                    return order
                else:
                    self.logger.error("Failed to place order")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Failed to place order: {e}")
            return None
    
    async def _simulate_order(self, symbol: str, side: str, amount: float, 
                             price: Optional[float], order_type: str, leverage: int) -> Dict:
        """Simulate order execution for paper trading"""
        current_price = self.last_prices.get(symbol, 50000)
        entry_price = price if price else current_price
        
        # Simulate order execution
        order = {
            'id': f"sim_{int(time.time())}",
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': entry_price,
            'type': order_type,
            'status': 'filled',
            'filled': amount,
            'timestamp': time.time()
        }
        
        # Update position tracking
        position_key = f"{symbol}_{side}"
        if position_key in self.positions:
            self.positions[position_key]['amount'] += amount
        else:
            self.positions[position_key] = {
                'amount': amount,
                'entry_price': entry_price,
                'leverage': leverage,
                'timestamp': time.time()
            }
        
        self.logger.info(f"Simulated order: {symbol} {side} {amount} @ {entry_price}")
        return order
    
    async def send_discord_alert(self, title: str, description: str, color: int = 0x00ff00, fields: list = None):
        """Send Discord alert"""
        try:
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Hyperliquid Golden Pocket Bot"
                }
            }
            if fields:
                embed["fields"] = fields
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            if response.status_code == 204:
                self.logger.info(f"Discord alert sent: {title}")
            else:
                self.logger.error(f"Discord alert failed: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Error sending Discord alert: {e}")

async def test_hyperliquid_trading():
    """Test Hyperliquid trading functionality"""
    print("🚀 TESTING HYPERLIQUID TRADING...")
    
    # Initialize API
    api = HyperliquidExchange(paper_trading=False)  # Real trading
    
    # Test connection
    print("🔗 Testing connection...")
    connected = await api.test_connection()
    if not connected:
        print("❌ Connection test failed")
        return
    
    print("✅ Connection test passed")
    
    # Get balance
    print("💰 Getting account balance...")
    balance = await api.get_account_balance()
    print(f"💰 Account Balance: ${balance['USDC']:.2f} USDC")
    
    # Get SOL price
    print("📊 Getting SOL price...")
    ticker = await api.get_ticker('SOL')
    if not ticker:
        print("❌ Could not get SOL ticker")
        return
    
    current_price = ticker['last']
    print(f"💰 SOL Current Price: ${current_price:.4f}")
    
    # Test trade
    print("🎯 Testing trade execution...")
    order = await api.place_order(
        symbol='SOL',
        side='buy',
        amount=0.1,  # 0.1 SOL
        order_type='market',
        leverage=15
    )
    
    if order:
        print("✅ TRADE EXECUTED SUCCESSFULLY!")
        print(f"  Order ID: {order.get('id', 'N/A')}")
        print(f"  Status: {order.get('status', 'N/A')}")
        
        # Send Discord notification
        await api.send_discord_alert(
            title="🚀 HYPERLIQUID TRADE EXECUTED",
            description=f"**SOL** LONG @ ${current_price:.4f}",
            color=0x00ff00,
            fields=[
                {"name": "Exchange", "value": "Hyperliquid", "inline": True},
                {"name": "Order ID", "value": str(order.get('id', 'N/A')), "inline": True},
                {"name": "Amount", "value": "0.1 SOL", "inline": True},
                {"name": "Entry Price", "value": f"${current_price:.4f}", "inline": True},
                {"name": "Leverage", "value": "15x", "inline": True},
                {"name": "Status", "value": order.get('status', 'N/A'), "inline": True},
                {"name": "✅ US-Friendly", "value": "Hyperliquid works for US users!", "inline": False}
            ]
        )
        
        print("✅ Trade notification sent to Discord!")
    else:
        print("❌ Failed to execute trade")

if __name__ == "__main__":
    asyncio.run(test_hyperliquid_trading())