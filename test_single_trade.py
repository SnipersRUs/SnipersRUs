#!/usr/bin/env python3
"""
Test Single Trade - Just try to place ONE trade
"""

import asyncio
import time
import logging
import requests
from datetime import datetime, timezone
from hyperliquid.exchange import Exchange
from eth_account import Account
from hyperliquid_config import (
    HYPERLIQUID_CONFIG, 
    HYPERLIQUID_NOTIFICATION_CONFIG
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_single_trade():
    """Test placing a single trade"""
    
    # Initialize client
    private_key = HYPERLIQUID_CONFIG['private_key']
    public_wallet = HYPERLIQUID_CONFIG['public_wallet']
    discord_webhook = HYPERLIQUID_NOTIFICATION_CONFIG['discord_webhook']
    
    wallet = Account.from_key(private_key)
    client = Exchange(wallet=wallet, base_url="https://api.hyperliquid.xyz")
    
    logger.info("🔍 Testing single trade...")
    
    try:
        # Get balance
        user_state = client.info.user_state(public_wallet)
        balance = float(user_state['marginSummary']['accountValue'])
        logger.info(f"💰 Balance: ${balance:.2f}")
        
        # Get SOL price
        all_mids = client.info.all_mids()
        sol_price = float(all_mids['SOL'])
        logger.info(f"📈 SOL Price: ${sol_price:.2f}")
        
        # Calculate position size
        position_size = 0.1  # Very small size
        rounded_price = round(sol_price, 2)
        
        logger.info(f"🎯 Attempting SOL LONG: size={position_size}, price={rounded_price}")
        
        # Place order
        order = client.order(
            name="SOL",
            is_buy=True,
            sz=position_size,
            limit_px=rounded_price,
            order_type={"limit": {"tif": "Gtc"}},
            reduce_only=False
        )
        
        logger.info(f"📋 Order response: {order}")
        
        # Check if successful
        if order and 'response' in order:
            response = order['response']
            if 'data' in response and 'statuses' in response['data']:
                statuses = response['data']['statuses']
                if statuses and len(statuses) > 0:
                    status = statuses[0]
                    if 'error' not in status or status['error'] is None:
                        logger.info("✅ TRADE SUCCESSFUL!")
                        
                        # Send Discord alert
                        embed = {
                            "title": "🎯 TEST TRADE EXECUTED!",
                            "description": f"**SOL** LONG @ ${rounded_price:.2f}",
                            "color": 0x00ff00,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "fields": [
                                {"name": "Position Size", "value": f"{position_size}", "inline": True},
                                {"name": "Price", "value": f"${rounded_price:.2f}", "inline": True},
                                {"name": "✅ REAL TRADE", "value": "This is a REAL order on Hyperliquid!", "inline": False}
                            ]
                        }
                        
                        payload = {"embeds": [embed]}
                        response = requests.post(discord_webhook, json=payload, timeout=10)
                        
                        if response.status_code == 204:
                            logger.info("✅ Discord alert sent!")
                        else:
                            logger.error(f"❌ Discord failed: {response.status_code}")
                            
                        return True
                    else:
                        error_msg = status.get('error', 'Unknown error')
                        logger.error(f"❌ Order failed: {error_msg}")
                        return False
                else:
                    logger.error("❌ No status in response")
                    return False
            else:
                logger.error("❌ Invalid response structure")
                return False
        else:
            logger.error("❌ No response from order")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

async def main():
    logger.info("🚀 Starting single trade test...")
    success = await test_single_trade()
    
    if success:
        logger.info("🎉 SUCCESS! Trade was placed successfully!")
    else:
        logger.error("💥 FAILED! Trade could not be placed.")
    
    logger.info("Test completed.")

if __name__ == "__main__":
    asyncio.run(main())























































