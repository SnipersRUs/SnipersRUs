#!/bin/bash
# Quick fix and start script - installs missing pieces and starts the bot

set -e

echo "🔧 Quick Fix & Start Script"
echo "============================"
echo ""

cd /Users/bishop/Documents/GitHub/SnipersRUs

# Check and install Python packages
echo "📦 Checking Python packages..."
python3 -m pip install --upgrade pip --quiet 2>/dev/null || true

MISSING=()
for pkg in discord python-dotenv requests feedparser vaderSentiment textblob; do
    if ! python3 -c "import $pkg" 2>/dev/null; then
        MISSING+=("$pkg")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "Installing missing packages: ${MISSING[*]}"
    pip3 install discord.py python-dotenv requests feedparser vaderSentiment textblob --quiet
    echo "✅ Packages installed"
else
    echo "✅ All packages installed"
fi

# Check if model is downloaded
echo ""
echo "🤖 Checking Ollama model..."
if ollama list 2>/dev/null | grep -q "mistral"; then
    echo "✅ Mistral model found"
else
    echo "📥 Downloading mistral model (this may take a few minutes)..."
    ollama pull mistral
    echo "✅ Model downloaded"
fi

# Verify .env exists
echo ""
echo "🔍 Checking configuration..."
cd free_crypto_llm_bot
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
DISCORD_TOKEN=MTQ1NDk4MzA0NTA4OTMzMzM4Mg.GGKdkF.BJCw_tyhVDYBLTP0COLv-3JXrMNvLXGJSPqSUM
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
ETHERSCAN_API_KEY=your_etherscan_api_key_here
COINGECKO_API_KEY=your_coingecko_api_key_here
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
EOF
    echo "✅ .env file created"
fi

# Critical: Check Message Content Intent
echo ""
echo "⚠️  IMPORTANT: Discord Bot Configuration"
echo "======================================="
echo ""
echo "The bot needs 'Message Content Intent' enabled to read your messages!"
echo ""
echo "🔗 Go to this URL and enable it:"
echo "   https://discord.com/developers/applications/1454983045089333382/bot"
echo ""
echo "Steps:"
echo "   1. Scroll down to 'Privileged Gateway Intents'"
echo "   2. Enable 'MESSAGE CONTENT INTENT'"
echo "   3. Click 'Save Changes'"
echo "   4. Restart the bot (this script will start it)"
echo ""
read -p "Press Enter after you've enabled Message Content Intent, or Ctrl+C to exit..."

# Start the bot
echo ""
echo "🚀 Starting bot..."
echo ""
cd ..
python3 run_free_crypto_llm_bot.py



