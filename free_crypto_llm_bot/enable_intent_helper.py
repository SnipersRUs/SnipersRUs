#!/usr/bin/env python3
"""
Helper script to guide you through enabling Message Content Intent
Opens the Discord Developer Portal page automatically
"""
import webbrowser
import sys
import time

def main():
    print("=" * 60)
    print("🔧 Discord Bot Intent Enabler Helper")
    print("=" * 60)
    print()
    print("This script will open the Discord Developer Portal for you.")
    print("You'll need to manually enable 'Message Content Intent' there.")
    print()
    print("⚠️  Why this is needed:")
    print("   Discord requires you to manually enable privileged intents")
    print("   for security reasons. This cannot be done programmatically.")
    print()

    # The exact URL to the bot settings
    bot_url = "https://discord.com/developers/applications/1454983045089333382/bot"

    print("📋 Steps to follow:")
    print("   1. The browser will open to your bot's settings page")
    print("   2. Scroll down to 'Privileged Gateway Intents'")
    print("   3. Find 'MESSAGE CONTENT INTENT'")
    print("   4. Toggle it ON (enable it)")
    print("   5. Click 'Save Changes'")
    print("   6. Come back here and restart the bot")
    print()

    input("Press Enter to open the Discord Developer Portal...")

    print()
    print("🌐 Opening browser...")
    webbrowser.open(bot_url)

    print("✅ Browser opened!")
    print()
    print("=" * 60)
    print("📝 What to do next:")
    print("=" * 60)
    print()
    print("1. In the browser that just opened:")
    print("   → Scroll down to 'Privileged Gateway Intents'")
    print("   → Enable 'MESSAGE CONTENT INTENT'")
    print("   → Click 'Save Changes'")
    print()
    print("2. Come back here and press Enter when done...")
    print()

    input("Press Enter after you've enabled the intent and saved changes...")

    print()
    print("✅ Great! Now let's start the bot...")
    print()
    print("Starting bot in 3 seconds...")
    time.sleep(3)

    # Import and run the bot
    import os
    import subprocess

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bot_script = os.path.join(project_root, "run_free_crypto_llm_bot.py")

    print("🚀 Starting bot...")
    print()
    subprocess.run([sys.executable, bot_script])

if __name__ == "__main__":
    main()



