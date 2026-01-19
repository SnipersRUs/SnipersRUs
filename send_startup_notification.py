#!/usr/bin/env python3
"""
Send startup notification to Discord
"""
import asyncio
import aiohttp
import ssl
from datetime import datetime

async def send_startup_notification():
    webhook_url = "https://discord.com/api/webhooks/1414775093829046272/B01HW18b-OVgfflsDBUdooSv2EAM8_joEwHQcYeTmduSWXnVmocM3-YLz-L1LpWzXiY7"
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            payload = {
                "embeds": [{
                    "title": "🚀 Enhanced Scanner Started",
                    "description": "**Status**: Online and scanning\n"
                                 "**Symbols**: 12 pairs\n"
                                 "**Min Trade Confidence**: 75%\n"
                                 "**Min Watch Confidence**: 60%\n"
                                 "**Scan Frequency**: Every hour\n"
                                 "**Exchanges**: MEXC, Bybit, Bitget, Binance",
                    "color": 0x00ff00,
                    "timestamp": datetime.now().isoformat(),
                    "footer": {"text": "Enhanced Scanner Bot"}
                }]
            }
            
            async with session.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 204:
                    print("✅ Startup notification sent to Discord!")
                    return True
                else:
                    print(f"❌ Failed to send notification: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error sending notification: {e}")
            return False

if __name__ == "__main__":
    print("📤 Sending startup notification to Discord...")
    asyncio.run(send_startup_notification())
