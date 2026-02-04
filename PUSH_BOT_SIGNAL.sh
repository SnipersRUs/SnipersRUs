#!/bin/bash

# Simple script to simulate the Sniper Guru Bot pushing a signal to the backend

API_URL="http://localhost:3000/api/scanner/bot-signal"

# Example signal data
SIGNAL_DATA='{
  "symbol": "BTC/USDT",
  "direction": "LONG",
  "style": "SWING",
  "entry": "98500",
  "stopLoss": "95000",
  "takeProfit": "105000",
  "confidence": 92,
  "analysis": "Institutional liquidity sweep confirmed. Moving into expansion phase.",
  "apiKey": "bot_secret_123"
}'

echo "🚀 Pushing signal to SnipersRUs platform..."
curl -X POST -H "Content-Type: application/json" -d "$SIGNAL_DATA" $API_URL
echo -e "\n✅ Signal pushed successfully!"
