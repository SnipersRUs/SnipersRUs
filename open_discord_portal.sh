#!/bin/bash
# Simple script to open Discord Developer Portal

echo "🌐 Opening Discord Developer Portal..."
echo ""
echo "Once the page opens:"
echo "  1. Scroll to 'Privileged Gateway Intents'"
echo "  2. Enable 'MESSAGE CONTENT INTENT'"
echo "  3. Click 'Save Changes'"
echo "  4. Then run: python3 run_free_crypto_llm_bot.py"
echo ""

# Open the browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "https://discord.com/developers/applications/1454983045089333382/bot"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "https://discord.com/developers/applications/1454983045089333382/bot"
else
    # Windows or other
    echo "Please open this URL in your browser:"
    echo "https://discord.com/developers/applications/1454983045089333382/bot"
fi

echo ""
echo "✅ Browser should be opening now..."



