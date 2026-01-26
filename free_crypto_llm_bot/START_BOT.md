# 🚀 Starting the Bot from Cursor

## Option 1: Use the Helper Script (Easiest)

This will automatically open the Discord Developer Portal for you:

```bash
cd /Users/bishop/Documents/GitHub/SnipersRUs
python3 free_crypto_llm_bot/enable_intent_helper.py
```

**What it does:**
1. Opens your browser to the Discord Developer Portal
2. Shows you exactly what to click
3. Waits for you to enable the intent
4. Starts the bot automatically

## Option 2: Quick Start Script

```bash
cd /Users/bishop/Documents/GitHub/SnipersRUs
./quick_start_bot.sh
```

## Option 3: Manual Start (After Enabling Intent)

If you've already enabled the intent:

```bash
cd /Users/bishop/Documents/GitHub/SnipersRUs
python3 run_free_crypto_llm_bot.py
```

## Option 4: Direct from Cursor Terminal

1. Open terminal in Cursor (`` Ctrl+` `` or View → Terminal)
2. Run:
   ```bash
   cd /Users/bishop/Documents/GitHub/SnipersRUs
   python3 free_crypto_llm_bot/enable_intent_helper.py
   ```

---

## ⚠️ Important Note

**Discord requires you to manually enable intents** - this is a security feature. The helper script opens the page for you, but you still need to click the toggle button yourself.

**Why?** Discord doesn't allow bots to enable privileged intents programmatically for security reasons.

---

## 🔗 Direct Link to Enable Intent

If you prefer to do it manually:
https://discord.com/developers/applications/1454983045089333382/bot

Scroll to "Privileged Gateway Intents" → Enable "MESSAGE CONTENT INTENT" → Save



