#!/bin/bash
# Quick Start Script for Free Crypto LLM Discord Bot
# This script helps you get started quickly

set -e  # Exit on error

echo "🚀 Free Crypto LLM Discord Bot - Quick Start"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo "📋 Step 1: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Step 2: Check Ollama
echo ""
echo "📋 Step 2: Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version)
    echo -e "${GREEN}✅ Ollama found: $OLLAMA_VERSION${NC}"

    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama server is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Ollama server is not running${NC}"
        echo "   Please start Ollama in another terminal: ollama serve"
        read -p "   Press Enter when Ollama is running, or Ctrl+C to exit..."
    fi
else
    echo -e "${RED}❌ Ollama not found${NC}"
    echo "   Please install Ollama:"
    echo "   macOS: brew install ollama"
    echo "   Linux: curl -fsSL https://ollama.com/install.sh | sh"
    echo "   Windows: Download from https://ollama.com"
    exit 1
fi

# Step 3: Check if model is downloaded
echo ""
echo "📋 Step 3: Checking for downloaded models..."
MODELS=$(ollama list 2>/dev/null | grep -v "NAME" | awk '{print $1}' | grep -v "^$" || echo "")
if [ -z "$MODELS" ]; then
    echo -e "${YELLOW}⚠️  No models found${NC}"
    echo "   Downloading mistral model (this may take a few minutes)..."
    ollama pull mistral
    echo -e "${GREEN}✅ Model downloaded${NC}"
else
    echo -e "${GREEN}✅ Models found:${NC}"
    echo "$MODELS" | sed 's/^/   - /'
fi

# Step 4: Check dependencies
echo ""
echo "📋 Step 4: Checking Python dependencies..."
cd "$(dirname "$0")/.." || exit 1

MISSING_DEPS=()
for dep in discord python-dotenv requests feedparser vaderSentiment textblob; do
    if ! python3 -c "import $dep" 2>/dev/null; then
        MISSING_DEPS+=("$dep")
    fi
done

if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ All dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Missing dependencies: ${MISSING_DEPS[*]}${NC}"
    echo "   Installing missing dependencies..."
    pip install discord.py python-dotenv requests feedparser vaderSentiment textblob
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi

# Step 5: Verify configuration
echo ""
echo "📋 Step 5: Verifying bot configuration..."
cd free_crypto_llm_bot || exit 1
if [ -f ".env" ]; then
    if python3 verify_setup.py 2>/dev/null | grep -q "✅ DISCORD_TOKEN configured"; then
        echo -e "${GREEN}✅ Bot configuration verified${NC}"
    else
        echo -e "${YELLOW}⚠️  Configuration issue detected${NC}"
        python3 verify_setup.py
    fi
else
    echo -e "${RED}❌ .env file not found${NC}"
    echo "   Please run: python3 setup_env.py"
    exit 1
fi

# Step 6: Ready to run
echo ""
echo "=============================================="
echo -e "${GREEN}✅ All checks passed!${NC}"
echo ""
echo "🚀 Ready to start the bot!"
echo ""
echo "To start the bot, run:"
echo "  cd $(pwd)/.."
echo "  python3 run_free_crypto_llm_bot.py"
echo ""
echo "Or use this command:"
echo -e "${GREEN}  python3 run_free_crypto_llm_bot.py${NC}"
echo ""
read -p "Would you like to start the bot now? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting bot..."
    echo ""
    cd .. || exit 1
    python3 run_free_crypto_llm_bot.py
else
    echo "👋 Bot setup complete! Start it manually when ready."
fi



