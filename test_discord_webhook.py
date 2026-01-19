#!/usr/bin/env python3
"""
Test Discord webhook connectivity
"""
import asyncio
import aiohttp
import ssl
from datetime import datetime

async def test_discord_webhook():
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
                    "title": "🧪 Discord Webhook Test",
                    "description": "**Status**: Enhanced Scanner Bot is working!\n**Time**: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "color": 0x00ff00,
                    "timestamp": datetime.now().isoformat(),
                    "footer": {"text": "Enhanced Scanner Bot - Test"}
                }]
            }
            
            async with session.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 204:
                    print("✅ Discord webhook test successful!")
                    print(f"   Response status: {response.status}")
                    return True
                else:
                    print(f"❌ Discord webhook test failed!")
                    print(f"   Response status: {response.status}")
                    print(f"   Response text: {await response.text()}")
                    return False
                    
        except Exception as e:
            print(f"❌ Discord webhook test error: {e}")
            return False

if __name__ == "__main__":
    print("🧪 Testing Discord webhook...")
    asyncio.run(test_discord_webhook())

















































