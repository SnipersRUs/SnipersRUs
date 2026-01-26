# Telegram Setup Guide for Pocket Option Scanner

Complete step-by-step guide to set up Telegram notifications for the Pocket Option scanner bot.

## 📱 Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start a chat** with @BotFather
3. **Send the command**: `/newbot`
4. **Follow the prompts**:
   - Choose a name for your bot (e.g., "Pocket Option Scanner")
   - Choose a username (must end in `bot`, e.g., `pocket_option_scanner_bot`)
5. **Copy the bot token** that @BotFather gives you
   - It will look like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
   - **Save this token** - you'll need it later

## 🆔 Step 2: Get Your Chat ID

You have two options: get your personal chat ID or create a group chat ID.

### Option A: Personal Chat (Easier)

1. **Search for your new bot** in Telegram (use the username you created)
2. **Start a conversation** with your bot
3. **Send any message** to your bot (e.g., "/start" or "Hello")
4. **Get your chat ID**:
   - Open this URL in your browser (replace `YOUR_BOT_TOKEN` with your actual token):
     ```
     https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
     ```
   - Look for `"chat":{"id":123456789}` in the JSON response
   - The number after `"id":` is your chat ID
   - **Note**: If you get `"ok":false`, send another message to your bot first

**Example JSON response:**
```json
{
  "ok": true,
  "result": [{
    "message": {
      "chat": {
        "id": 123456789,
        "first_name": "Your Name",
        "type": "private"
      }
    }
  }]
}
```

### Option B: Group Chat

1. **Create a Telegram group**
2. **Add your bot to the group**
   - Click on the group name → "Add Members"
   - Search for your bot and add it
3. **Send a message** in the group (any message)
4. **Get the group chat ID**:
   - Open this URL:
     ```
     https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
     ```
   - Look for `"chat":{"id":-123456789}` (group IDs are negative)
   - The number after `"id":` is your group chat ID

## 🚀 Step 3: Configure the Bot

### Method 1: Command Line Arguments

```bash
python pocket_option_scanner.py \
  --telegram-token "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz" \
  --telegram-chat-id "123456789" \
  --symbols "BTC/USDT,ETH/USDT"
```

### Method 2: Environment Variables (Recommended)

```bash
# Set environment variables
export TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="123456789"

# Run the bot
python pocket_option_scanner.py
```

### Method 3: .env File (If using python-dotenv)

Create a `.env` file:
```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
```

Then load it in your script or use:
```bash
export $(cat .env | xargs)
python pocket_option_scanner.py
```

## 🧪 Step 4: Test Your Setup

Run a test scan to make sure notifications work:

```bash
python pocket_option_scanner.py \
  --telegram-token "YOUR_TOKEN" \
  --telegram-chat-id "YOUR_CHAT_ID" \
  --oneshot
```

If configured correctly, when signals are found, you'll receive a formatted message in Telegram!

## 📱 Example Telegram Message

When a signal is detected, you'll receive a message like this:

```
🟢 Pocket Option Signal

Symbol: BTC/USDT
Direction: 📈 CALL (UP)
Grade: A+ | Confidence: 85%

Entry Price: $43,250.50000
Timeframe: 5m
Confluence: 85/100

Signal Types:
ORB_BULLISH, SFP_SUPPORT, VOLUME, FVG_BULLISH

Reasons:
• ORB High Breakout
• Strong Support SFP (2 touches)
• High Volume (2.3x avg)
• Bullish FVG Formed

Timestamp: 2024-01-15 14:30:00 UTC
```

## ⚙️ Advanced Configuration

### Send to Multiple Telegram Chats

You can modify the code to send to multiple chat IDs:

```python
# In pocket_option_scanner.py, modify send_telegram_notification:
telegram_chat_ids = [chat_id1, chat_id2, chat_id3]
for chat_id in telegram_chat_ids:
    # Send to each chat
```

### Customize Message Format

Edit the `send_telegram_notification` method in `pocket_option_scanner.py` to customize the message format.

### Combine Discord + Telegram

You can use both notifications at the same time:

```bash
python pocket_option_scanner.py \
  --telegram-token "YOUR_TOKEN" \
  --telegram-chat-id "YOUR_CHAT_ID" \
  --webhook "YOUR_DISCORD_WEBHOOK"
```

## 🔒 Security Tips

1. **Never commit your bot token** to Git
   - Add `.env` to `.gitignore`
   - Don't share your token publicly

2. **Keep your token secure**
   - Store it in environment variables or secure vaults
   - Rotate your token if it's ever exposed

3. **Limit bot permissions**
   - Your bot only needs to send messages
   - Don't give it admin permissions in groups unless necessary

## 🐛 Troubleshooting

### "Chat not found" error
- Make sure you sent at least one message to the bot first
- Verify the chat ID is correct (check the sign - personal chats are positive, groups are negative)

### "Unauthorized" error
- Check that your bot token is correct
- Make sure there are no extra spaces in the token

### Bot not receiving messages
- Make sure your bot is added to the group (for group chats)
- Verify the chat ID format (numbers only, no quotes in env var)

### Messages not formatted correctly
- Check that `parse_mode: "HTML"` is being used
- Verify special characters are escaped if needed

## ✅ Quick Test Script

Create a file `test_telegram.py`:

```python
import requests
import os

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

if not bot_token or not chat_id:
    print("❌ Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID first!")
    exit(1)

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
payload = {
    "chat_id": chat_id,
    "text": "✅ Telegram setup working! Your bot is configured correctly.",
    "parse_mode": "HTML"
}

r = requests.post(url, json=payload)
if r.status_code == 200:
    print("✅ Test message sent! Check your Telegram.")
else:
    print(f"❌ Error: {r.status_code} - {r.text}")
```

Run it:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
python test_telegram.py
```

---

**That's it!** Your Pocket Option scanner will now send signals directly to your Telegram! 🎉








