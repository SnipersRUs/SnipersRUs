#!/bin/bash
# Automated Installation Script for Free Crypto LLM Discord Bot
# This script installs everything needed and starts the bot

set -e  # Exit on error

echo "🚀 Free Crypto LLM Discord Bot - Automated Installation"
echo "========================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="/Users/bishop/Documents/GitHub/SnipersRUs"
cd "$PROJECT_DIR" || exit 1

# Step 1: Check/Install Ollama
echo -e "${BLUE}📦 Step 1: Checking Ollama installation...${NC}"
if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>&1)
    echo -e "${GREEN}✅ Ollama already installed: $OLLAMA_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama not found. Installing...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo "Installing via Homebrew..."
            brew install ollama
        else
            echo -e "${RED}❌ Homebrew not found. Please install Ollama manually:${NC}"
            echo "   Visit: https://ollama.com"
            echo "   Or install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Installing via install script..."
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo -e "${RED}❌ Unsupported OS. Please install Ollama manually from https://ollama.com${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Ollama installed!${NC}"
fi

# Step 2: Start Ollama in background
echo ""
echo -e "${BLUE}🚀 Step 2: Starting Ollama server...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama is already running${NC}"
else
    echo "Starting Ollama server in background..."
    # Start Ollama in background
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    echo "Ollama started with PID: $OLLAMA_PID"

    # Wait for Ollama to be ready
    echo "Waiting for Ollama to start..."
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Ollama is ready!${NC}"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""

    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${RED}❌ Ollama failed to start. Check /tmp/ollama.log for errors${NC}"
        exit 1
    fi
fi

# Step 3: Download model if needed
echo ""
echo -e "${BLUE}📥 Step 3: Checking for models...${NC}"
MODELS=$(ollama list 2>/dev/null | grep -v "NAME" | awk '{print $1}' | grep -v "^$" || echo "")
if echo "$MODELS" | grep -q "mistral"; then
    echo -e "${GREEN}✅ Mistral model already downloaded${NC}"
else
    echo -e "${YELLOW}⚠️  Mistral model not found. Downloading...${NC}"
    echo "This may take 5-15 minutes depending on your internet speed..."
    ollama pull mistral
    echo -e "${GREEN}✅ Model downloaded!${NC}"
fi

# Step 4: Install Python dependencies
echo ""
echo -e "${BLUE}📦 Step 4: Installing Python dependencies...${NC}"
python3 -m pip install --upgrade pip --quiet
pip3 install discord.py python-dotenv requests feedparser vaderSentiment textblob --quiet
echo -e "${GREEN}✅ Python dependencies installed${NC}"

# Step 5: Verify configuration
echo ""
echo -e "${BLUE}🔍 Step 5: Verifying bot configuration...${NC}"
cd free_crypto_llm_bot || exit 1
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Creating .env file with your Discord token..."
    cat > .env << 'ENVEOF'
# Discord Bot Configuration
DISCORD_TOKEN=MTQ1NDk4MzA0NTA4OTMzMzM4Mg.GGKdkF.BJCw_tyhVDYBLTP0COLv-3JXrMNvLXGJSPqSUM

# Ollama LLM Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Etherscan API (Free Tier)
ETHERSCAN_API_KEY=your_etherscan_api_key_here

# CoinGecko API (Optional - Free Tier)
COINGECKO_API_KEY=your_coingecko_api_key_here

# Solana RPC (Optional)
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
ENVEOF
    echo -e "${GREEN}✅ .env file created${NC}"
fi

python3 verify_setup.py

# Step 6: Check Discord bot permissions
echo ""
echo -e "${BLUE}🔐 Step 6: Discord Bot Setup Reminder${NC}"
echo -e "${YELLOW}⚠️  Make sure you've:${NC}"
echo "   1. Invited the bot to your server using this link:"
echo "      https://discord.com/oauth2/authorize?client_id=1454983045089333382&permissions=67584&integration_type=0&scope=bot"
echo ""
echo "   2. Enabled 'Message Content Intent' in Discord Developer Portal:"
echo "      https://discord.com/developers/applications/1454983045089333382/bot"
echo "      → Scroll to 'Privileged Gateway Intents'"
echo "      → Enable 'MESSAGE CONTENT INTENT'"
echo "      → Save changes"

# Step 7: Start the bot
echo ""
echo -e "${BLUE}🤖 Step 7: Starting Discord bot...${NC}"
echo ""
echo -e "${GREEN}========================================================"
echo "✅ Installation Complete!"
echo "========================================================"
echo ""
echo "The bot is starting now..."
echo "You should see: '✅ Bot logged in as YourBotName#1234'"
echo ""
echo "To stop the bot, press Ctrl+C"
echo ""
echo -e "${NC}"

cd "$PROJECT_DIR" || exit 1
python3 run_free_crypto_llm_bot.py



