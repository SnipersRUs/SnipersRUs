# ⚠️ CRITICAL: Enable Message Content Intent

## Why the bot isn't responding

If you typed `!help` and nothing happened, the bot needs **"Message Content Intent"** enabled in Discord.

## 🔧 How to Fix (2 minutes)

### Step 1: Go to Discord Developer Portal
**Click this link:**
https://discord.com/developers/applications/1454983045089333382/bot

### Step 2: Enable Message Content Intent
1. You should see your bot's settings page
2. Scroll down to find **"Privileged Gateway Intents"** section
3. Find **"MESSAGE CONTENT INTENT"**
4. **Toggle it ON** (enable it)
5. Click **"Save Changes"** at the bottom

### Step 3: Restart the Bot
After enabling, restart the bot:
```bash
cd /Users/bishop/Documents/GitHub/SnipersRUs
python3 run_free_crypto_llm_bot.py
```

## ✅ What You Should See

After enabling and restarting:
- Bot shows as "Online" in your Discord server
- Typing `!help` gets a response
- All commands work

## 🖼️ Visual Guide

The setting looks like this:
```
┌─────────────────────────────────────┐
│ Privileged Gateway Intents          │
├─────────────────────────────────────┤
│ ☑ PRESENCE INTENT                   │
│ ☑ SERVER MEMBERS INTENT             │
│ ☑ MESSAGE CONTENT INTENT  ← ENABLE! │
└─────────────────────────────────────┘
```

Make sure the checkbox is **checked** ✅

---

**Once enabled, the bot will work!** 🚀



