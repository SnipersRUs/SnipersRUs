# 🚀 Quick Start Guide - Enhanced MM Trading Bot

## 🎯 Getting Started in Cursor

### 1. Open the Workspace
- Open `mm-trading-bot.code-workspace` in Cursor
- Or open the project folder directly

### 2. Install Dependencies
- Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
- Type "Tasks: Run Task"
- Select "Install Dependencies"

### 3. Test Discord Integration
- Press `F5` or use "Run and Debug" panel
- Select "Test Discord Webhook"
- Click the play button

### 4. Run the Trading Bot
- Press `F5` or use "Run and Debug" panel  
- Select "Run MM Trading Bot"
- Click the play button

## 🔧 Available Tasks

### Install Dependencies
```bash
Cmd+Shift+P → Tasks: Run Task → Install Dependencies
```

### Test Discord Webhook
```bash
Cmd+Shift+P → Tasks: Run Task → Test Discord
```

### Run Trading Bot
```bash
Cmd+Shift+P → Tasks: Run Task → Run MM Bot
```

### Format Code
```bash
Cmd+Shift+P → Tasks: Run Task → Format Code
```

## 🐛 Debugging

### Debug Configurations
1. **Run MM Trading Bot** - Main bot execution
2. **Test Discord Webhook** - Test Discord integration
3. **Debug MM Detector** - Debug MM detection logic

### Setting Breakpoints
- Click in the left margin next to line numbers
- Red dots indicate breakpoints
- Use F5 to start debugging

## 📁 Project Structure

```
SnipersRUs/
├── src/
│   ├── mm_detector.py          # Enhanced MM detection
│   ├── trading_system.py       # Trading system logic
│   ├── mm_config.py           # Configuration management
│   ├── discord_integration.py # Discord webhook integration
│   ├── mm_trading_bot.py      # Main bot integration
│   ├── run_mm_bot.py          # Entry point
│   ├── test_discord.py        # Discord test script
│   └── requirements.txt       # Dependencies
├── .vscode/                   # Cursor/VS Code configuration
├── config.py                  # Your configuration
└── mm-trading-bot.code-workspace
```

## ⚙️ Configuration

### Discord Webhook
Your webhook is already configured in `src/mm_config.py`:
```python
discord_webhook = "..."
```

### Trading Parameters
Edit `src/mm_config.py` to adjust:
- Position size ($1000 per trade)
- Risk per trade (10%)
- Leverage limits (BTC: 20x, ETH/SOL: 10x)
- MM detection thresholds

## 🚨 Important Notes

1. **Test First**: Always run `test_discord.py` before running the main bot
2. **Monitor Logs**: Check console output for any errors
3. **Discord Alerts**: You'll receive alerts in your Discord channel
4. **State Persistence**: Bot saves state automatically

## 🆘 Troubleshooting

### Common Issues
1. **Import Errors**: Run "Install Dependencies" task
2. **Discord Not Working**: Check webhook URL in config
3. **Python Path**: Ensure correct Python interpreter is selected

### Getting Help
- Check console output for error messages
- Verify Discord webhook URL is correct
- Ensure all dependencies are installed

## 🎉 You're Ready!

Your Enhanced MM Trading Bot is now set up in Cursor and ready to detect market maker patterns and execute trades automatically!