#!/bin/bash
# Force fix script - tries multiple approaches

echo "🔧 Force Fix: Message Content Intent"
echo "====================================="
echo ""

echo "This script will help you fix the intent issue step by step."
echo ""

# Step 1: Open the page
echo "📋 Step 1: Opening Discord Developer Portal..."
open "https://discord.com/developers/applications/1454983045089333382/bot" 2>/dev/null

echo ""
echo "⏳ Please do the following in the browser that just opened:"
echo ""
echo "1. Scroll ALL THE WAY DOWN the page"
echo "2. Find 'Privileged Gateway Intents' section"
echo "3. Toggle 'MESSAGE CONTENT INTENT' OFF"
echo "4. Scroll to bottom and click 'Save Changes'"
echo "5. Wait 5 seconds"
echo "6. Toggle 'MESSAGE CONTENT INTENT' ON"
echo "7. Scroll to bottom and click 'Save Changes' again"
echo "8. Wait 30 seconds"
echo ""
read -p "Press Enter when you've completed all steps above..."

# Step 2: Re-invite bot
echo ""
echo "📋 Step 2: Re-inviting bot (sometimes required after enabling intents)..."
open "https://discord.com/oauth2/authorize?client_id=1454983045089333382&permissions=67584&integration_type=0&scope=bot" 2>/dev/null

echo ""
echo "In the browser:"
echo "1. Select your Discord server"
echo "2. Click 'Authorize'"
echo ""
read -p "Press Enter when bot is re-invited..."

# Step 3: Wait and test
echo ""
echo "⏳ Waiting 10 seconds for Discord API to update..."
sleep 10

echo ""
echo "🧪 Testing connection..."
python3 free_crypto_llm_bot/test_connection.py



