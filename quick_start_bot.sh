#!/bin/bash
# Quick start script with intent helper

cd /Users/bishop/Documents/GitHub/SnipersRUs

echo "🚀 Free Crypto LLM Discord Bot - Quick Start"
echo "=============================================="
echo ""

# Check if we should run the intent helper first
echo "This script will:"
echo "  1. Open Discord Developer Portal (if needed)"
echo "  2. Start the bot"
echo ""

# Try to start the bot, catch the error
python3 run_free_crypto_llm_bot.py 2>&1 | tee /tmp/bot_output.log

# Check if the error is about privileged intents
if grep -q "PrivilegedIntentsRequired" /tmp/bot_output.log; then
    echo ""
    echo "⚠️  Intent not enabled! Running helper..."
    echo ""
    python3 free_crypto_llm_bot/enable_intent_helper.py
fi



