#!/usr/bin/env python3
"""
Test script to verify bot connection and intents
"""
import discord
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

if not token:
    print("❌ DISCORD_TOKEN not found!")
    sys.exit(1)

print("🔍 Testing Bot Connection...")
print("=" * 50)

# Configure intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

print(f"✅ Message Content Intent: {intents.message_content}")
print(f"✅ Members Intent: {intents.members}")
print()

# Create client
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("=" * 50)
    print(f"✅ SUCCESS! Bot connected as: {client.user}")
    print(f"✅ Bot ID: {client.user.id}")
    print(f"✅ Guilds: {len(client.guilds)}")
    print("=" * 50)
    print()
    print("🎉 Bot is working! You can now use it in Discord.")
    await client.close()

try:
    print("Connecting to Discord...")
    client.run(token)
except discord.errors.PrivilegedIntentsRequired as e:
    print("=" * 50)
    print("❌ ERROR: Privileged Intents Not Enabled!")
    print("=" * 50)
    print()
    print("Even though the toggle is ON, Discord might not have saved it yet.")
    print()
    print("Try this:")
    print("1. Go back to Discord Developer Portal")
    print("2. Toggle 'MESSAGE CONTENT INTENT' OFF")
    print("3. Click 'Save Changes'")
    print("4. Wait 5 seconds")
    print("5. Toggle 'MESSAGE CONTENT INTENT' ON again")
    print("6. Click 'Save Changes'")
    print("7. Wait 10 seconds for Discord to process")
    print("8. Run this test again: python3 free_crypto_llm_bot/test_connection.py")
    print()
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



