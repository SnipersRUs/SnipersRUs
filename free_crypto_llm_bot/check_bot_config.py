#!/usr/bin/env python3
"""
Check bot's actual configuration via Discord API
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

if not token:
    print("❌ DISCORD_TOKEN not found!")
    exit(1)

print("🔍 Checking Bot Configuration via Discord API")
print("=" * 60)
print()

headers = {"Authorization": f"Bot {token}"}

# Get bot info
print("📱 Bot Information:")
try:
    response = requests.get("https://discord.com/api/v10/users/@me", headers=headers, timeout=10)
    if response.status_code == 200:
        bot_data = response.json()
        print(f"   Username: {bot_data.get('username')}#{bot_data.get('discriminator')}")
        print(f"   Bot ID: {bot_data.get('id')}")
        print(f"   Verified: {bot_data.get('verified', False)}")
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Get application info (this shows intents)
print("⚙️  Application Configuration:")
try:
    response = requests.get("https://discord.com/api/v10/applications/@me", headers=headers, timeout=10)
    if response.status_code == 200:
        app_data = response.json()
        print(f"   Name: {app_data.get('name')}")
        print(f"   Application ID: {app_data.get('id')}")

        # Check flags (intents are part of flags)
        flags = app_data.get('flags', 0)
        print(f"   Flags: {flags}")

        # Intent flags (these are set when intents are enabled)
        # We can't directly read intents from this endpoint, but we can check if bot is verified
        print()
        print("   Note: Discord API doesn't expose intent status directly.")
        print("   Intents are configured in the Developer Portal only.")

    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("=" * 60)
print()
print("💡 Important Notes:")
print()
print("1. Discord's API doesn't expose intent configuration directly")
print("2. Intents must be enabled in Developer Portal: https://discord.com/developers/applications/1454983045089333382/bot")
print("3. After enabling, you MUST click 'Save Changes' at the bottom")
print("4. Changes can take 1-5 minutes to propagate")
print()
print("🔍 To verify intents are enabled:")
print("   → Go to Developer Portal")
print("   → Bot tab → Scroll to 'Privileged Gateway Intents'")
print("   → 'MESSAGE CONTENT INTENT' should be ON (blue toggle)")
print("   → If it's ON but bot still fails, wait 2-5 minutes and try again")
print()



