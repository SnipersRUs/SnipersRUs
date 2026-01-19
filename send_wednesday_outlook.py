#!/usr/bin/env python3
"""
Discord Webhook Script for Wednesday Market Outlook
Sends comprehensive market analysis with @everyone ping to Discord channel
"""

import requests
import json
import sys

def send_wednesday_outlook():
    """Send the Wednesday market outlook to Discord with @everyone ping"""
    
    # Discord webhook URL
    webhook_url = "https://discord.com/api/webhooks/1417680286921134251/qP3_kjOWd3UvXSyv27UXjO7HTzqLx9AhfVlLalkyE3DQrmmKtR99UwE-NGvEu9KIHClO"
    
    # The Wednesday outlook message content with @everyone ping (condensed for Discord 2000 char limit)
    message_content = """@everyone
**WEDNESDAY OUTLOOK - OCT 8, 2025**  
**BITCOIN | ETH | SOL**  

Good morning traders — heading into NY session, cooling across BTC after Asia/Europe chop. Structure favors upside continuation *if* VWAP reclaim levels hold.

🌍 **MACRO**
• Futures: Mildly red. S&P/NASDAQ down ~0.2%
• Dollar firm near 106; 10-yr yields up — caution ahead of next week's CPI
• BTC dominance ~55%, alts mixed with SOL/AVAX strong
• ETF inflows net positive
• No major data today. Eyes on PPI (Oct 10) and CPI (Oct 15)

₿ **BTC TECHNICAL**
**Current:** ~$122.5K | **Bias:** Neutral-bullish ST | Bullish MT
**VWAP:** Just under H1; H4 intact (bullish slope)
**Momentum:** Cooling from ATH, but structure intact

**Timeframes:**
- 1m-15m: VWAPs flipped bearish (normal post-ATH digestion)
- H1-H4: Healthy retracement; bulls defended 121.5K cleanly
- 12H-1D: Upward channel intact; targeting 127.5-128K
- Weekly: Trend intact, higher lows since September

🎯 **NY SESSION GAME PLAN**
**Range:** 121.5K-123.8K
Watch for VWAP reclaim + volume before chasing

**Scenario 1 - VWAP reclaim long (60%)**
Trigger: reclaim 122.9K-123.2K on NY volume
Entry: 123.0K | Stop: 122.3K | Targets: 124.4K → 125.2K → 126.0K

**Scenario 2 - Range long (35%)**
Trigger: dip to 121.4K-121.8K with absorption
Entry: 121.6K | Stop: 120.9K | Targets: 122.9K → 124.0K

**Scenario 3 - Breakdown short (15%)**
Trigger: close below 121.4K with volume
Entry: 121.2K | Stop: 122.0K | Targets: 120.1K → 118.8K

Ξ **ETH | SOL**
**ETH:** ~3.42K — watch 3.45K reclaim for 3.6K. Support 3.36K
**SOL:** Strong. Above 195 bullish; upside 205 → 212

📅 **STRATEGY**
• Let NY open define direction (first 30-45min)
• Don't force early entries
• Best opportunities: VWAP reclaim around 121.6K-122.8K
• Take partials aggressively
• 1-2 quality setups only

**Inflection zones:**
Bull above 123.2K | Neutral under 122.2K | Bear below 121.4K

Trade with focus - this week's patience will pay."""

    # Discord webhook payload
    payload = {
        "content": message_content,
        "username": "Sniper Guru",
        "avatar_url": "https://cdn.discordapp.com/attachments/1234567890/1234567890/sniper_guru_avatar.png"  # Optional: add avatar URL
    }
    
    try:
        # Send the webhook request
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 204:
            print("✅ Discord Wednesday outlook sent successfully!")
            print(f"📊 Message length: {len(message_content)} characters")
            return True
        else:
            print(f"❌ Failed to send Discord message. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending Discord message: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("📈 Sending Wednesday Market Outlook to Discord...")
    print("=" * 60)
    
    success = send_wednesday_outlook()
    
    if success:
        print("=" * 60)
        print("✅ Wednesday outlook delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)
