#!/usr/bin/env python3
"""
Send referral card to Discord webhook
"""

import requests
import json

WEBHOOK_URL = "https://discord.com/api/webhooks/1438335989507686553/omLFMLZdWsglW2ruQ02cQUEkKeDpJkBlopmqL3gzW2r53Kl2RJd9By78Apaf9E_QzC8S"

def create_referral_embed():
    """Create a beautiful Discord embed with referral links"""

    embed = {
        "title": "🎯 SNIPERS-R-US REFERRAL CARD",
        "description": "**Your Referral Links & Socials**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "color": 0x8b5cf6,  # Purple color
        "fields": [
            {
                "name": "💰 **EXCHANGE REFERRALS**",
                "value": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "inline": False
            },
            {
                "name": "📈 **Zoomex**",
                "value": "[Click here to sign up](https://www.zoomex.com/en-US/feediscount?params=ref=0VL4Z8G|ID=1c2e380a-836b-415c-ade1-cdbfb7b2c674|actUserId=524534287|actUserName=rickytspanish%E2%80%8B@gmail.com)",
                "inline": True
            },
            {
                "name": "🚀 **Bitunix**",
                "value": "[Click here to sign up](https://www.bitunix.com/register?inviteCode=3vm3p7)",
                "inline": True
            },
            {
                "name": "📊 **TradingView** ($15 Credit)",
                "value": "[Get $15 towards subscription](https://www.tradingview.com/pricing/?share_your_love=Bishopbizzle)",
                "inline": True
            },
            {
                "name": "🌐 **SOCIAL MEDIA & LINKS**",
                "value": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "inline": False
            },
            {
                "name": "🐦 **Twitter**",
                "value": "[@Brypto_sniper](https://twitter.com/Brypto_sniper)",
                "inline": True
            },
            {
                "name": "▶️ **YouTube**",
                "value": "[@rickytspanish](https://www.youtube.com/@rickytspanish)",
                "inline": True
            },
            {
                "name": "🎵 **TikTok**",
                "value": "[@rickytspanish](https://www.tiktok.com/@rickytspanish?_r=1&_t=ZT-91tq1sdWMmc)",
                "inline": True
            },
            {
                "name": "🎯 **Official Site**",
                "value": "[SnipersRUs](https://snipersrus.github.io/SnipersRUs/)",
                "inline": True
            },
            {
                "name": "📈 **TradingView**",
                "value": "[TradingView Platform](https://www.tradingview.com)",
                "inline": True
            }
        ],
        "footer": {
            "text": "🔗 Share these links and support the SnipersRUs community!"
        },
        "timestamp": None
    }

    return embed

def send_to_discord():
    """Send the referral card to Discord"""

    embed = create_referral_embed()

    payload = {
        "embeds": [embed],
        "username": "Sniper Guru"
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("✅ Referral card sent successfully to Discord!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending to Discord: {e}")
        return False

if __name__ == "__main__":
    send_to_discord()
















