#!/usr/bin/env python3
"""
Market Data Fetcher
Fetches cryptocurrency market data from CoinGecko (free tier)
"""
import requests
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class CoinGeckoClient:
    """Client for CoinGecko API (free tier)"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CoinGecko client

        Args:
            api_key: Optional CoinGecko API key (free tier available)
                     If None, uses public API (rate limited)
        """
        self.api_key = api_key
        if api_key:
            self.base_url = "https://api.coingecko.com/api/v3"
            self.headers = {"x-cg-demo-api-key": api_key}
        else:
            self.base_url = "https://api.coingecko.com/api/v3"
            self.headers = {}

    def get_price(self, coin_id: str, vs_currency: str = "usd") -> Optional[Dict]:
        """
        Get current price for a cryptocurrency

        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum', 'solana')
            vs_currency: Currency to compare against (default: 'usd')

        Returns:
            Dict with price, market_cap, 24h_change, etc.
        """
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": vs_currency,
                "include_market_cap": "true",
                "include_24hr_change": "true",
                "include_24hr_vol": "true",
                "include_last_updated_at": "true"
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if coin_id in data:
                coin_data = data[coin_id]
                return {
                    "price": coin_data.get(f"{vs_currency}", 0),
                    "market_cap": coin_data.get(f"{vs_currency}_market_cap", 0),
                    "volume_24h": coin_data.get(f"{vs_currency}_24h_vol", 0),
                    "change_24h": coin_data.get(f"{vs_currency}_24h_change", 0),
                    "last_updated": coin_data.get("last_updated_at", 0)
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching price for {coin_id}: {e}")
            return None

    def get_multiple_prices(self, coin_ids: List[str], vs_currency: str = "usd") -> Dict[str, Dict]:
        """
        Get prices for multiple cryptocurrencies

        Args:
            coin_ids: List of CoinGecko coin IDs
            vs_currency: Currency to compare against

        Returns:
            Dict mapping coin_id to price data
        """
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                "ids": ",".join(coin_ids),
                "vs_currencies": vs_currency,
                "include_market_cap": "true",
                "include_24hr_change": "true",
                "include_24hr_vol": "true"
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching multiple prices: {e}")
            return {}

    def get_trending(self) -> Optional[List[Dict]]:
        """Get trending cryptocurrencies"""
        try:
            url = f"{self.base_url}/search/trending"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('coins', [])
        except Exception as e:
            logger.error(f"Error fetching trending coins: {e}")
            return None

    def get_coin_info(self, coin_id: str) -> Optional[Dict]:
        """
        Get detailed information about a cryptocurrency

        Args:
            coin_id: CoinGecko coin ID

        Returns:
            Dict with coin information
        """
        try:
            url = f"{self.base_url}/coins/{coin_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false"
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching coin info: {e}")
            return None

    def format_price_message(self, coin_id: str, coin_name: str, price_data: Dict) -> str:
        """Format price data into a Discord-friendly message"""
        if not price_data:
            return f"❌ Could not fetch price data for {coin_name}"

        price = price_data.get('price', 0)
        market_cap = price_data.get('market_cap', 0)
        volume_24h = price_data.get('volume_24h', 0)
        change_24h = price_data.get('change_24h', 0)

        # Format numbers
        price_str = f"${price:,.2f}" if price >= 0.01 else f"${price:.6f}"
        market_cap_str = f"${market_cap:,.0f}" if market_cap > 0 else "N/A"
        volume_str = f"${volume_24h:,.0f}" if volume_24h > 0 else "N/A"

        # Change emoji
        change_emoji = "📈" if change_24h >= 0 else "📉"
        change_color = "🟢" if change_24h >= 0 else "🔴"

        message = f"""💰 **{coin_name.upper()}** ({coin_id})
{change_emoji} **Price:** {price_str}
📊 **Market Cap:** {market_cap_str}
💵 **24h Volume:** {volume_str}
{change_color} **24h Change:** {change_24h:.2f}%"""

        return message



