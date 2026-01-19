# 🚀 START HERE - Quick Setup Checklist

Follow these steps in order. Check off each box as you complete it!

---

## ✅ Setup Checklist

### 1. Install Ollama
- [ ] **macOS**: `brew install ollama` OR download from https://ollama.com
- [ ] **Linux**: `curl -fsSL https://ollama.com/install.sh | sh`
- [ ] **Windows**: Download from https://ollama.com and install
- [ ] Verify: `ollama --version` shows a version number

### 2. Start Ollama Server
- [ ] Open terminal
- [ ] Run: `ollama serve`
- [ ] **Keep this terminal open!** (Don't close it)
- [ ] You should see "starting server..." message

### 3. Download a Model
- [ ] Open a **NEW terminal** (keep Ollama running in first one!)
- [ ] Run: `ollama pull mistral`
- [ ] Wait for download to complete (5-15 minutes)
- [ ] Verify: `ollama list` shows "mistral"

### 4. Test Ollama
- [ ] In the same terminal, run: `ollama run mistral "What is Bitcoin?"`
- [ ] You should see a response about Bitcoin
- [ ] ✅ If you see a response, Ollama is working!

### 5. Install Python Packages
- [ ] Open a **NEW terminal**
- [ ] Navigate: `cd /Users/bishop/Documents/GitHub/SnipersRUs`
- [ ] Run: `pip install discord.py python-dotenv requests feedparser vaderSentiment textblob`
- [ ] Wait for installation to complete

### 6. Verify Bot Setup
- [ ] Run: `cd free_crypto_llm_bot`
- [ ] Run: `python3 verify_setup.py`
- [ ] You should see all ✅ green checkmarks

### 7. Invite Bot to Discord
- [ ] Open this link: https://discord.com/oauth2/authorize?client_id=1454983045089333382&permissions=67584&integration_type=0&scope=bot
- [ ] Select your Discord server
- [ ] Click "Authorize"
- [ ] Bot should appear in your server member list

### 8. Run the Bot
- [ ] Open a terminal
- [ ] Navigate: `cd /Users/bishop/Documents/GitHub/SnipersRUs`
- [ ] Run: `python3 run_free_crypto_llm_bot.py`
- [ ] You should see: "✅ Bot logged in" and "🚀 Bot is ready!"
- [ ] **Keep this terminal open!**

### 9. Test in Discord
- [ ] Go to your Discord server
- [ ] Type: `!help`
- [ ] Bot should respond with command list
- [ ] Try: `!status`
- [ ] Try: `!ask What is Bitcoin?`

---

## 🎉 All Done!

If all steps are checked, your bot is running!

**Remember:**
- Keep Ollama running (`ollama serve` terminal)
- Keep bot running (`python3 run_free_crypto_llm_bot.py` terminal)

---

## 🆘 Having Issues?

### Bot doesn't respond?
1. Check "Message Content Intent" is enabled in Discord Developer Portal
2. Make sure bot has permissions in channel
3. Verify bot shows as "Online" in server

### LLM not available?
1. Make sure `ollama serve` is running
2. Verify model is downloaded: `ollama list`
3. Test: `ollama run mistral "test"`

### Import errors?
1. Install packages: `pip install discord.py python-dotenv requests feedparser vaderSentiment textblob`
2. Check Python version: `python3 --version` (need 3.8+)

---

## 📚 More Help

- **Detailed Guide**: See `STEP_BY_STEP_GUIDE.md`
- **Quick Script**: Run `./QUICK_START.sh` (automated setup)
- **Features**: See `FEATURES.md`
- **Full Docs**: See `README.md`

---

**Ready? Start with Step 1! 🚀**



