#!/usr/bin/env python3
"""
Discord Webhook Script for BTC Tuesday Update
Sends BTC Tuesday update as a purple embed card to Discord
"""

import requests
import json
import sys

def send_btc_update():
    """Send the BTC Tuesday update to Discord as a purple embed card"""

    # Discord webhook URL
    webhook_url = ""

    # Purple color for embed
    PURPLE_COLOR = 0x8E44AD

    # Create the embed
    embed = {
        "title": "🚨 BTC TUESDAY UPDATE - NOV 26 NY OPEN 🚨",
        "description": "**Current Price:** $87,430 | Bounced from $81k | +7.9%",
        "color": PURPLE_COLOR,
        "fields": [
            {
                "name": "⚡ MAJOR DEVELOPMENTS",
                "value": (
                    "✅ EPIC V-BOTTOM from $81k to $89k (+10%)\n"
                    "✅ Fed rate cut odds SURGED to 75.5%\n"
                    "✅ NY Fed Williams signals December cut coming\n"
                    "✅ Channel support HELD at $81k (8H chart)\n"
                    "✅ Higher lows forming: $81k → $84k → $86k\n\n"
                    "**Current Status:**\n"
                    "• Consolidating $86k-$88k after bounce\n"
                    "• Testing resistance at $87.5k-$88k\n"
                    "• NY open will decide next $2k-$3k move\n"
                    "• Post-Thanksgiving low volume"
                ),
                "inline": False
            },
            {
                "name": "📊 CRITICAL LEVELS",
                "value": (
                    "**🔴 RESISTANCE:**\n"
                    "$87,500 (immediate)\n"
                    "$88,000-$88,500 (MAJOR - break = moon)\n"
                    "$89,000-$90,000 (psychological)\n"
                    "$94,000-$96,000 (next target)\n\n"
                    "**🟢 SUPPORT:**\n"
                    "$86,500 (immediate)\n"
                    "$86,000 (STRONG - must hold)\n"
                    "$84,000 (secondary)\n"
                    "$81,000 (channel support - tested & held)\n\n"
                    "**⚠️ THE LINE: $88,000**\n"
                    "Break above = test $90k-$94k\n"
                    "Reject here = retest $86k or lower"
                ),
                "inline": False
            },
            {
                "name": "🎯 BEST TRADES FOR NY OPEN",
                "value": (
                    "**🟢 LONG #1: Breakout (60% win)**\n"
                    "Entry: $88,200-$88,500 (on break)\n"
                    "Stop: $86,800 | Targets: $89.5k / $90.5k / $92k\n\n"
                    "**🟢 LONG #2: Support (65% win)**\n"
                    "Entry: $86,000-$86,500 (on dip)\n"
                    "Stop: $85,200 | Targets: $87.5k / $88.5k / $90k\n\n"
                    "**🔴 SHORT: Failed Breakout (55% win)**\n"
                    "Entry: $88,500-$89,000\n"
                    "Stop: $89,800 | Targets: $87k / $86k / $84.5k"
                ),
                "inline": False
            },
            {
                "name": "🎲 NY SESSION PROBABILITIES",
                "value": (
                    "**Next 8 Hours (9AM-5PM EST):**\n"
                    "50% → Break above $88k to $89k-$90k\n"
                    "30% → Reject at $88k, retest $86k\n"
                    "20% → Chop $86.5k-$87.5k\n\n"
                    "**This Week:**\n"
                    "45% → Rally to $90k-$94k\n"
                    "35% → Chop $84k-$88k\n"
                    "20% → Retest $81k-$84k"
                ),
                "inline": False
            },
            {
                "name": "📰 MARKET NEWS & SENTIMENT",
                "value": (
                    "**✅ MASSIVELY BULLISH:**\n"
                    "• Fed Williams: \"Room for further adjustment\"\n"
                    "• December rate cut odds: 75.5% (was 45%)\n"
                    "• Channel support HELD at $81k perfectly\n"
                    "• $81k = local bottom confirmed\n"
                    "• Higher lows forming (bullish structure)\n\n"
                    "**⚠️ STILL BEARISH:**\n"
                    "• Fear & Greed: EXTREME FEAR (19/100)\n"
                    "• $3B ETF outflows in November\n"
                    "• Down 30% from $126k ATH still\n"
                    "• Must reclaim $90k for trend reversal"
                ),
                "inline": False
            },
            {
                "name": "💡 TRADING WISDOM FOR TODAY",
                "value": (
                    "**✅ DO:**\n"
                    "• Watch for $88k breakout (key level)\n"
                    "• Use moderate size (2-3% risk)\n"
                    "• Long dips to $86k-$86.5k\n"
                    "• Set alerts for $88k and $90k\n\n"
                    "**❌ DON'T:**\n"
                    "• Chase above $88k without confirmation\n"
                    "• Short the absolute lows at $86k\n"
                    "• Use large size (post-holiday thin volume)\n"
                    "• Ignore $86k breakdown (=danger)"
                ),
                "inline": False
            },
            {
                "name": "⚡ BOTTOM LINE",
                "value": (
                    "We just bounced 10% from $81k to $89k - that's MASSIVE. The $81k level held perfectly on the 8H channel support. Now we're consolidating $86k-$88k.\n\n"
                    "Fed Williams basically confirmed December rate cut is coming (75% odds). This is BULLISH for BTC. The question now: do we break $88k and run to $90k-$94k, or do we reject and retest $86k?\n\n"
                    "**BEST PLAY:** Long the $86k-$86.5k dip OR wait for $88k breakout. Don't chase above $88k without confirmation. If we break $88k with volume, we're going to $90k+. If we reject, we retest $86k.\n\n"
                    "The $81k bottom is likely IN. Channel held. Bulls are back in control SHORT-TERM. But we MUST reclaim $90k to confirm the bigger trend reversal."
                ),
                "inline": False
            }
        ],
        "footer": {
            "text": "DYOR | NFA | Stack sats fam! 💎🙌"
        }
    }

    # Discord webhook payload
    payload = {
        "content": "@everyone",
        "embeds": [embed],
        "username": "Sniper Guru"
    }

    try:
        # Send the webhook request
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 204:
            print("✅ Discord BTC Tuesday update sent successfully!")
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
    print("🚀 Sending BTC Tuesday Update to Discord...")
    print("=" * 60)

    success = send_btc_update()

    if success:
        print("=" * 60)
        print("✅ BTC update delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)
