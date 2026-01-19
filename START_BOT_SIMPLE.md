# 🚀 Simple Bot Start Guide

## Current Status
The bot detected that **Message Content Intent is NOT enabled** yet.

## Quick Fix (2 steps):

### Step 1: Enable the Intent
Run this command to open the Discord Developer Portal:
```bash
./open_discord_portal.sh
```

Or manually open:
**https://discord.com/developers/applications/1454983045089333382/bot**

Then:
1. Scroll down to **"Privileged Gateway Intents"**
2. Find **"MESSAGE CONTENT INTENT"**
3. **Toggle it ON** ✅
4. Click **"Save Changes"**

### Step 2: Start the Bot
After enabling the intent, run:
```bash
python3 run_free_crypto_llm_bot.py
```

---

## One-Line Commands

**Open Discord Portal:**
```bash
./open_discord_portal.sh
```

**Start Bot (after enabling intent):**
```bash
python3 run_free_crypto_llm_bot.py
```

---

## What You'll See When It Works

```
✅ Bot logged in as YourBotName#1234
✅ Ollama LLM is available
🚀 Bot is ready!
```

Then in Discord, type `!help` and the bot will respond! 🎉



