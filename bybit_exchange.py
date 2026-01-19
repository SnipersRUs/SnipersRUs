#!/usr/bin/env python3
"""
Bybit Exchange Adapter
High-performance trading bot integration with Bybit API
"""

import requests
import json
import time
import logging
import asyncio
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlencode

class BybitExchange:
    def __init__(self, paper_trading: bool = False):
        self.paper_trading = paper_trading
        self.base_url = "https://api.bybit.com"
        self.testnet_url = "https://api-testnet.bybit.com"
        
        # API credentials (will be set via environment variables)
        self.api_key = None
        self.api_secret = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bybit_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Paper trading simulation
        self.balance = 1000.0  # Simulated balance
        self.positions = {}
        self.last_prices = {}
        
        self.logger.info(f"Bybit Exchange initialized (Paper Trading: {paper_trading})")
    
    def set_credentials(self, api_key: str, api_secret: str):
        """Set API credentials"""
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger.info("Bybit API credentials set")
    
    def _generate_signature(self, params: str, timestamp: str) -> str:
        """Generate HMAC signature for Bybit API"""
        if not self.api_secret:
            raise ValueError("API secret not set")
        
        message = timestamp + self.api_key + "5000" + params
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """Make HTTP request to Bybit API"""
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        if self.paper_trading:
            url = f"{self.testnet_url}{endpoint}"
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'TradingBot/1.0'
        }
        
        if signed and self.api_key and self.api_secret:
            timestamp = str(int(time.time() * 1000))
            params_str = urlencode(params) if params else ""
            signature = self._generate_signature(params_str, timestamp)
            
            headers.update({
                'X-BAPI-API-KEY': self.api_key,
                'X-BAPI-SIGN': signature,
                'X-BAPI-SIGN-TYPE': '2',
                'X-BAPI-TIMESTAMP': timestamp,
                'X-BAPI-RECV-WINDOW': '5000'
            })
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test connection to Bybit"""
        try:
            if self.paper_trading:
                # Test with paper trading
                self.logger.info("Testing paper trading connection...")
                return True
            
            # Test with real API
            response = self._make_request('GET', '/v5/market/time')
            if response.get('retCode') == 0:
                self.logger.info("✅ Bybit connection successful")
                return True
            else:
                self.logger.error(f"❌ Bybit connection failed: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Connection test failed: {e}")
            return False
    
    async def get_account_balance(self) -> Dict:
        """Get account balance"""
        if self.paper_trading:
            return {
                'totalEquity': str(self.balance),
                'accountIMRate': '0.01',
                'totalMarginBalance': str(self.balance),
                'totalAvailableBalance': str(self.balance * 0.8),
                'totalPerpUPL': '0',
                'totalInitialMargin': '0',
                'totalPositionIM': '0',
                'totalMaintenanceMargin': '0'
            }
        
        try:
            response = self._make_request('GET', '/v5/account/wallet-balance', signed=True)
            if response.get('retCode') == 0:
                return response['result']
            else:
                self.logger.error(f"Failed to get balance: {response}")
                return {}
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return {}
    
    async def get_positions(self) -> List[Dict]:
        """Get current positions"""
        if self.paper_trading:
            return list(self.positions.values())
        
        try:
            response = self._make_request('GET', '/v5/position/list', signed=True)
            if response.get('retCode') == 0:
                return response['result']['list']
            else:
                self.logger.error(f"Failed to get positions: {response}")
                return []
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
    
    async def get_ticker(self, symbol: str) -> Dict:
        """Get ticker data for symbol"""
        try:
            params = {'symbol': symbol}
            response = self._make_request('GET', '/v5/market/tickers', params)
            
            if response.get('retCode') == 0:
                tickers = response['result']['list']
                for ticker in tickers:
                    if ticker['symbol'] == symbol:
                        return ticker
            return {}
        except Exception as e:
            self.logger.error(f"Error getting ticker for {symbol}: {e}")
            return {}
    
    async def place_order(self, symbol: str, side: str, order_type: str, qty: str, 
                         price: str = None, stop_loss: str = None, take_profit: str = None) -> Dict:
        """Place order on Bybit"""
        if self.paper_trading:
            # Simulate order placement
            order_id = f"paper_{int(time.time())}"
            self.logger.info(f"📝 Paper order placed: {side} {qty} {symbol} @ {price}")
            return {
                'orderId': order_id,
                'orderLinkId': order_id,
                'symbol': symbol,
                'side': side,
                'orderType': order_type,
                'qty': qty,
                'price': price,
                'status': 'New'
            }
        
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'side': side,
                'orderType': order_type,
                'qty': qty,
                'timeInForce': 'GTC'
            }
            
            if price:
                params['price'] = price
            
            if stop_loss:
                params['stopLoss'] = stop_loss
            
            if take_profit:
                params['takeProfit'] = take_profit
            
            response = self._make_request('POST', '/v5/order/create', params, signed=True)
            
            if response.get('retCode') == 0:
                self.logger.info(f"✅ Order placed successfully: {response['result']}")
                return response['result']
            else:
                self.logger.error(f"❌ Order placement failed: {response}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return {}
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel order"""
        if self.paper_trading:
            self.logger.info(f"📝 Paper order cancelled: {order_id}")
            return True
        
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'orderId': order_id
            }
            
            response = self._make_request('POST', '/v5/order/cancel', params, signed=True)
            
            if response.get('retCode') == 0:
                self.logger.info(f"✅ Order cancelled successfully: {order_id}")
                return True
            else:
                self.logger.error(f"❌ Order cancellation failed: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return False
    
    async def get_klines(self, symbol: str, interval: str = '1', limit: int = 200) -> List[List]:
        """Get kline/candlestick data"""
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = self._make_request('GET', '/v5/market/kline', params)
            
            if response.get('retCode') == 0:
                return response['result']['list']
            else:
                self.logger.error(f"Failed to get klines: {response}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting klines: {e}")
            return []
    
    async def get_funding_rate(self, symbol: str) -> Dict:
        """Get funding rate for symbol"""
        try:
            params = {'symbol': symbol}
            response = self._make_request('GET', '/v5/market/funding/history', params)
            
            if response.get('retCode') == 0:
                funding_data = response['result']['list']
                if funding_data:
                    return funding_data[0]  # Latest funding rate
            return {}
        except Exception as e:
            self.logger.error(f"Error getting funding rate: {e}")
            return {}
    
    async def get_liquidation_orders(self, symbol: str = None) -> List[Dict]:
        """Get liquidation orders"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            
            response = self._make_request('GET', '/v5/market/recent-trade', params)
            
            if response.get('retCode') == 0:
                return response['result']['list']
            else:
                self.logger.error(f"Failed to get liquidation orders: {response}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting liquidation orders: {e}")
            return []
