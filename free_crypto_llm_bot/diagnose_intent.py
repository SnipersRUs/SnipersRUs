#!/usr/bin/env python3
"""
Diagnostic script to check bot intent status
"""
import discord
import os
import sys
from dotenv import load_dotenv
import requests

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

if not token:
    print("❌ DISCORD_TOKEN not found!")
    sys.exit(1)

print("🔍 Bot Intent Diagnostic Tool")
print("=" * 60)
print()

# Check token format
print(f"📝 Token Info:")
print(f"   Length: {len(token)} characters")
print(f"   Format: {'Valid' if len(token) > 50 else 'Invalid'}")
print()

# Try to get bot info via Discord API
print("🌐 Checking bot via Discord API...")
try:
    headers = {"Authorization": f"Bot {token}"}
    response = requests.get("https://discord.com/api/v10/users/@me", headers=headers, timeout=10)

    if response.status_code == 200:
        bot_data = response.json()
        print(f"✅ Bot found: {bot_data.get('username')}#{bot_data.get('discriminator')}")
        print(f"   Bot ID: {bot_data.get('id')}")
        print()

        # Get application info
        app_response = requests.get("https://discord.com/api/v10/applications/@me", headers=headers, timeout=10)
        if app_response.status_code == 200:
            app_data = app_response.json()
            print(f"📱 Application: {app_data.get('name')}")
            print(f"   Application ID: {app_data.get('id')}")
            print()
    else:
        print(f"⚠️  API Response: {response.status_code}")
        print(f"   {response.text}")
        print()
except Exception as e:
    print(f"⚠️  Could not check via API: {e}")
    print()

# Test connection with intents
print("🔌 Testing Connection with Intents...")
print()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

print(f"   Message Content Intent: {intents.message_content}")
print(f"   Members Intent: {intents.members}")
print()

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("=" * 60)
    print("✅ SUCCESS! Bot Connected!")
    print("=" * 60)
    print(f"   Bot: {client.user}")
    print(f"   ID: {client.user.id}")
    print(f"   Guilds: {len(client.guilds)}")
    if client.guilds:
        print(f"   Server: {client.guilds[0].name}")
    print("=" * 60)
    print()
    print("🎉 The bot is working! You can now use commands in Discord.")
    await client.close()

try:
    print("Connecting...")
    client.run(token)
except discord.errors.PrivilegedIntentsRequired as e:
    print("=" * 60)
    print("❌ PRIVILEGED INTENTS ERROR")
    print("=" * 60)
    print()
    print("The bot is still getting a PrivilegedIntentsRequired error.")
    print()
    print("🔧 Troubleshooting Steps:")
    print()
    print("1. VERIFY INTENT IS SAVED:")
    print("   → Go to: https://discord.com/developers/applications/1454983045089333382/bot")
    print("   → Scroll to 'Privileged Gateway Intents'")
    print("   → Make sure 'MESSAGE CONTENT INTENT' toggle is ON (blue)")
    print("   → Look for a 'Save Changes' button at the BOTTOM of the page")
    print("   → Click 'Save Changes' and wait for confirmation")
    print()
    print("2. WAIT FOR PROPAGATION:")
    print("   → After saving, wait 30-60 seconds")
    print("   → Discord's API can take time to update")
    print()
    print("3. RE-INVITE THE BOT:")
    print("   → Sometimes bots need to be re-invited after enabling intents")
    print("   → Use: https://discord.com/oauth2/authorize?client_id=1454983045089333382&permissions=67584&integration_type=0&scope=bot")
    print()
    print("4. CHECK BOT PERMISSIONS:")
    print("   → Make sure bot has 'Send Messages' permission in your server")
    print("   → Right-click server → Server Settings → Integrations → Bot")
    print()
    print("5. TRY TOGGLE OFF/ON:")
    print("   → Toggle intent OFF → Save → Wait 5 sec → Toggle ON → Save")
    print()
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
