"""
Quick test to verify Discord webhook is working
"""
import requests
import json

WEBHOOK_URL = ""

def test_discord_webhook():
    """Test Discord webhook connection"""
    embed = {
        "title": "✅ Pocket Option Scanner - Discord Test",
        "description": "Discord webhook is configured correctly! The scanner is ready to send signals.",
        "color": 0x00ff00,
        "fields": [
            {"name": "Status", "value": "Connected", "inline": True},
            {"name": "Channel", "value": "POS", "inline": True},
        ],
        "footer": {"text": "Pocket Option Scanner Bot"}
    }

    try:
        payload = {"embeds": [embed]}
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)

        if r.status_code in (200, 201, 204):
            print("✅ Discord webhook test successful! Check your Discord channel.")
            print(f"   Status: {r.status_code}")
            return True
        else:
            print(f"❌ Discord error: {r.status_code}")
            print(f"   Response: {r.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to send test message: {e}")
        return False

if __name__ == "__main__":
    print("Testing Discord webhook...")
    test_discord_webhook()








