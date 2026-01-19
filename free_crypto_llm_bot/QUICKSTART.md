# Quick Start Guide 🚀

Get your free crypto LLM Discord bot running in 5 minutes!

## Step 1: Install Ollama

**macOS:**
```bash
brew install ollama
# OR download from https://ollama.com
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from [ollama.com](https://ollama.com) and run the installer.

## Step 2: Pull a Model

```bash
ollama pull mistral
```

This downloads the Mistral 7B model (~4GB). Alternative: `ollama pull llama3` (~4.7GB)

## Step 3: Verify Ollama is Running

```bash
ollama serve
```

In another terminal:
```bash
curl http://localhost:11434/api/tags
```

You should see your models listed.

## Step 4: Create Discord Bot

1. Go to https://discord.com/developers/applications
2. Click **"New Application"** → Name it
3. Go to **"Bot"** tab → **"Add Bot"**
4. Click **"Reset Token"** → Copy token
5. Enable **"Message Content Intent"** (IMPORTANT!)
6. Go to **"OAuth2" → "URL Generator"**:
   - Select `bot` scope
   - Select permissions: `Send Messages`, `Read Message History`
   - Copy URL → Open in browser → Invite to server

## Step 5: Get API Keys (Optional)

**Etherscan (for Ethereum data):**
- Go to https://etherscan.io/apis
- Register → Get free API key

**CoinGecko (for better rate limits):**
- Go to https://www.coingecko.com/en/api
- Register → Get free API key

## Step 6: Setup Environment

```bash
cd free_crypto_llm_bot
cp env.example .env
```

Edit `.env` and add:
```
DISCORD_TOKEN=your_discord_bot_token_here
ETHERSCAN_API_KEY=your_key_here  # Optional
COINGECKO_API_KEY=your_key_here  # Optional
```

## Step 7: Install Dependencies

```bash
pip install discord.py python-dotenv requests feedparser vaderSentiment textblob
```

Or from project root:
```bash
pip install -r requirements.txt
```

## Step 8: Run the Bot

From project root:
```bash
python run_free_crypto_llm_bot.py
```

Or:
```bash
cd free_crypto_llm_bot
python bot.py
```

## Step 9: Test It!

In your Discord server:
```
!help
!ask What is Bitcoin?
!price ethereum
!ethblock
!news
```

## Troubleshooting

**Bot doesn't respond:**
- Check `Message Content Intent` is enabled
- Verify bot has permission in channel
- Check `.env` file has correct `DISCORD_TOKEN`

**LLM not available:**
- Make sure `ollama serve` is running
- Check `OLLAMA_URL` in `.env` matches your setup
- Verify model is pulled: `ollama list`

**Import errors:**
- Make sure you're in the right directory
- Install missing packages: `pip install <package>`

## That's It! 🎉

Your free crypto LLM bot is now running. Check `!help` for all commands!



