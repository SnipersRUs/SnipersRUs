#!/bin/bash
# Simple script to start the bot

echo "🚀 Starting Free Crypto LLM Discord Bot"
echo "========================================="
echo ""

# Check if Message Content Intent is enabled
echo "⚠️  BEFORE STARTING:"
echo ""
echo "Make sure 'Message Content Intent' is enabled:"
echo "🔗 https://discord.com/developers/applications/1454983045089333382/bot"
echo ""
echo "Scroll to 'Privileged Gateway Intents' → Enable 'MESSAGE CONTENT INTENT' → Save"
echo ""
read -p "Press Enter to start the bot (or Ctrl+C to enable the intent first)..."

cd /Users/bishop/Documents/GitHub/SnipersRUs
python3 run_free_crypto_llm_bot.py



