# 🚀 Step-by-Step Setup Guide

Complete walkthrough to get your Free Crypto LLM Discord Bot running!

---

## 📋 Prerequisites Checklist

Before starting, make sure you have:
- [ ] Python 3.8 or higher installed
- [ ] Terminal/Command Prompt access
- [ ] Discord account and server
- [ ] Internet connection

---

## Step 1: Install Ollama (Local LLM)

### macOS:
```bash
# Option A: Using Homebrew (recommended)
brew install ollama

# Option B: Download from website
# Go to https://ollama.com and download the macOS installer
# Double-click to install
```

### Linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows:
1. Go to https://ollama.com
2. Click "Download for Windows"
3. Run the installer
4. Follow the installation wizard

**Verify Installation:**
```bash
ollama --version
```
You should see a version number like `ollama version is 0.x.x`

---

## Step 2: Start Ollama Server

Open a terminal/command prompt and run:

```bash
ollama serve
```

**Keep this terminal window open!** Ollama needs to stay running.

You should see output like:
```
2024/01/15 10:00:00 routes.go:1008: INFO server config env="map[OLLAMA_HOST:0.0.0.0:11434]"
2024/01/15 10:00:00 routes.go:1016: INFO starting server...
```

✅ **Success indicator:** The terminal shows "starting server..." and stays running.

---

## Step 3: Download a Model (In a NEW Terminal)

**Open a NEW terminal window** (keep Ollama running in the first one!)

### Choose a model:

**Option A: Mistral (Recommended - Fast & Good)**
```bash
ollama pull mistral
```
- Size: ~4GB
- Download time: 5-15 minutes (depends on internet speed)
- Best for: General use, good balance of speed and quality

**Option B: Llama 3 (Alternative)**
```bash
ollama pull llama3
```
- Size: ~4.7GB
- Download time: 10-20 minutes
- Best for: Similar quality, slightly different responses

**What's happening:**
- You'll see download progress like: `pulling manifest...`, `downloading...`, `verifying...`
- Wait until you see: `success`

**Verify the model downloaded:**
```bash
ollama list
```
You should see your model listed (e.g., `mistral` or `llama3`)

---

## Step 4: Test Ollama is Working

In the same terminal (where you pulled the model), test it:

```bash
ollama run mistral "What is Bitcoin?"
```

Or if you pulled llama3:
```bash
ollama run llama3 "What is Bitcoin?"
```

**Expected output:** The model should respond with an explanation about Bitcoin.

✅ **If you see a response, Ollama is working!**

---

## Step 5: Install Python Dependencies

**Open a NEW terminal** (you can close the test terminal, but keep Ollama running!)

Navigate to your project:
```bash
cd /Users/bishop/Documents/GitHub/SnipersRUs
```

Install required packages:

```bash
pip install discord.py python-dotenv requests feedparser vaderSentiment textblob
```

**Or if you prefer using requirements.txt:**
```bash
pip install -r requirements.txt
```

**What's being installed:**
- `discord.py` - Discord bot library
- `python-dotenv` - Load environment variables
- `requests` - HTTP requests for APIs
- `feedparser` - Parse RSS feeds
- `vaderSentiment` - Sentiment analysis
- `textblob` - Alternative sentiment analysis

**Verify installation:**
```bash
python3 -c "import discord; print('✅ discord.py installed')"
python3 -c "import dotenv; print('✅ python-dotenv installed')"
```

---

## Step 6: Verify Bot Configuration

Check that your bot is configured correctly:

```bash
cd free_crypto_llm_bot
python3 verify_setup.py
```

**Expected output:**
```
🔍 Verifying Free Crypto LLM Bot Setup
==================================================
✅ .env file found
✅ DISCORD_TOKEN configured
✅ Ollama URL: http://localhost:11434
✅ Ollama Model: mistral
...
✅ Setup verification complete!
```

✅ **If you see all green checkmarks, you're ready!**

---

## Step 7: Invite Bot to Your Discord Server

1. **Open this link in your browser:**
   ```
   https://discord.com/oauth2/authorize?client_id=1454983045089333382&permissions=67584&integration_type=0&scope=bot
   ```

2. **Select your Discord server** from the dropdown

3. **Click "Authorize"**

4. **Complete any CAPTCHA** if prompted

5. **Verify the bot appears** in your server's member list

✅ **Bot should now be in your server!** (It won't respond yet until we start it)

---

## Step 8: Run the Bot!

**Open a terminal** and navigate to your project:

```bash
cd /Users/bishop/Documents/GitHub/SnipersRUs
```

**Start the bot:**

```bash
python3 run_free_crypto_llm_bot.py
```

**Or alternatively:**
```bash
cd free_crypto_llm_bot
python3 bot.py
```

**Expected output:**
```
2024-01-15 10:00:00 - INFO - 🚀 Starting Free Crypto LLM Discord Bot...
2024-01-15 10:00:00 - INFO - ✅ Bot logged in as YourBotName#1234
2024-01-15 10:00:00 - INFO - 🤖 LLM Model: mistral
2024-01-15 10:00:00 - INFO - 🔗 LLM URL: http://localhost:11434
2024-01-15 10:00:00 - INFO - ✅ Ollama LLM is available
2024-01-15 10:00:00 - INFO - 🚀 Bot is ready!
```

✅ **Keep this terminal open!** The bot needs to stay running.

---

## Step 9: Test the Bot in Discord

Go to your Discord server and try these commands:

### Basic Commands:
```
!help
```
Should show all available commands.

```
!status
```
Should show bot status and API availability.

### LLM Commands:
```
!ask What is cryptocurrency?
```
The bot should respond with an AI-generated answer.

```
!askcrypto Explain DeFi
```
Crypto-specific question with expert context.

### Market Data:
```
!price bitcoin
```
Should show Bitcoin price, market cap, volume, 24h change.

```
!price ethereum
```
Ethereum price info.

```
!trending
```
Top trending cryptocurrencies.

### On-Chain Data:
```
!ethblock
```
Latest Ethereum block information.

```
!btcblock
```
Latest Bitcoin block information.

```
!solblock
```
Latest Solana block information.

### News & Sentiment:
```
!news
```
Latest crypto news from multiple sources.

```
!sentiment
```
Market sentiment analysis from recent news.

---

## 🎉 Success! Your Bot is Running!

If all commands work, congratulations! Your free crypto LLM bot is fully operational.

---

## 🔧 Troubleshooting

### Problem: "Bot doesn't respond to commands"

**Solutions:**
1. Check that "Message Content Intent" is enabled:
   - Go to https://discord.com/developers/applications
   - Select your bot application
   - Go to "Bot" tab
   - Scroll down to "Privileged Gateway Intents"
   - Enable "MESSAGE CONTENT INTENT"
   - Save changes
   - Restart the bot

2. Verify bot has permissions in the channel:
   - Right-click channel → Edit Channel → Permissions
   - Make sure bot has "Send Messages" and "Read Message History"

3. Check bot is online:
   - Look at server member list
   - Bot should show as "Online" (green dot)

### Problem: "LLM is not available" or "Cannot connect to Ollama"

**Solutions:**
1. Make sure Ollama is running:
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   ```
   If this fails, start Ollama: `ollama serve`

2. Verify model is downloaded:
   ```bash
   ollama list
   ```
   If model isn't listed, pull it: `ollama pull mistral`

3. Check OLLAMA_URL in `.env`:
   - Should be `http://localhost:11434`
   - If Ollama is on a different machine, update the URL

### Problem: "DISCORD_TOKEN not found"

**Solutions:**
1. Check `.env` file exists:
   ```bash
   ls free_crypto_llm_bot/.env
   ```

2. Verify token is in `.env`:
   ```bash
   cd free_crypto_llm_bot
   python3 verify_setup.py
   ```

3. Make sure you're running from the right directory

### Problem: "Module not found" or Import errors

**Solutions:**
1. Install missing packages:
   ```bash
   pip install discord.py python-dotenv requests feedparser vaderSentiment textblob
   ```

2. Use Python 3.8+:
   ```bash
   python3 --version
   ```

3. Try using virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Problem: Bot responds slowly

**This is normal!** Local LLMs are slower than cloud APIs. Expect 5-30 seconds for LLM responses depending on:
- Your computer's CPU/RAM
- Model size (larger = slower but better)
- Question complexity

**Tips to speed up:**
- Use smaller models (mistral is faster than llama3:70b)
- Close other applications
- Use a computer with more RAM

### Problem: API rate limits

**Solutions:**
1. **Etherscan**: Get free API key from https://etherscan.io/apis
2. **CoinGecko**: Get free API key from https://www.coingecko.com/en/api
3. Add keys to `.env` file:
   ```
   ETHERSCAN_API_KEY=your_key_here
   COINGECKO_API_KEY=your_key_here
   ```

---

## 📝 Running the Bot 24/7

To keep the bot running all the time:

### Option 1: Screen (Linux/macOS)
```bash
# Install screen
brew install screen  # macOS
# or
sudo apt-get install screen  # Linux

# Start bot in screen
screen -S crypto_bot
python3 run_free_crypto_llm_bot.py

# Detach: Press Ctrl+A, then D
# Reattach: screen -r crypto_bot
```

### Option 2: tmux (Linux/macOS)
```bash
# Install tmux
brew install tmux  # macOS

# Start bot in tmux
tmux new -s crypto_bot
python3 run_free_crypto_llm_bot.py

# Detach: Press Ctrl+B, then D
# Reattach: tmux attach -t crypto_bot
```

### Option 3: Systemd Service (Linux)
Create `/etc/systemd/system/crypto-bot.service`:
```ini
[Unit]
Description=Free Crypto LLM Discord Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/Users/bishop/Documents/GitHub/SnipersRUs
ExecStart=/usr/bin/python3 run_free_crypto_llm_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable crypto-bot
sudo systemctl start crypto-bot
```

---

## 🎓 Next Steps

Once your bot is running:

1. **Customize Commands**: Edit `free_crypto_llm_bot/bot.py` to add new commands
2. **Add More Models**: Try different Ollama models for different use cases
3. **Get API Keys**: Add Etherscan and CoinGecko keys for better rate limits
4. **Monitor Logs**: Check `free_crypto_llm_bot.log` for bot activity
5. **Join Community**: Share your bot and get help from others

---

## 📞 Need Help?

- Check the `README.md` for detailed documentation
- Review `FEATURES.md` for feature overview
- Check bot logs: `free_crypto_llm_bot.log`
- Verify setup: `python3 free_crypto_llm_bot/verify_setup.py`

---

**Happy Botting! 🚀💰**



