# Tip Jar Skill

Tip Sniper Guru for good signals. All tips in ZOID with automatic distribution.

## Overview

**Purpose:** Allow users to tip Sniper Guru when signals perform well.

**Payment:** ZOID only (0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5)

**Distribution:**
- 75% → Sniper Guru (dev wallet)
- 25% → Burn address (0x000...dEaD)

---

## API Reference

### Send Tip
```
POST /api/scanner/tip
```

**Body:**
```json
{
  "signalId": "sg_...",
  "tipper": "0x...",
  "amount": 100,
  "signature": "0x...",
  "message": "Thanks for the great call!"
}
```

**Response:**
```json
{
  "success": true,
  "tipId": "tip_...",
  "amount": 100,
  "distribution": {
    "toSniperGuru": 75,
    "toBurn": 25,
    "burnAddress": "0x000...dEaD"
  },
  "message": "Tip sent! 75 ZOID to Sniper Guru, 25 ZOID burned."
}
```

### Get Tip Stats
```
GET /api/scanner/tips/stats
```

**Response:**
```json
{
  "totalTips": 156,
  "totalZoidTipped": 12500,
  "totalBurned": 3125,
  "totalToSniperGuru": 9375,
  "burnAddress": "0x000...dEaD",
  "burnPercentage": "25%"
}
```

### Get Tips for Signal
```
GET /api/scanner/tips/:signalId
```

**Response:**
```json
{
  "signalId": "sg_...",
  "symbol": "BTC/USDT",
  "totalTips": 5,
  "totalAmount": 350,
  "tips": [
    {
      "tipper": "0x...",
      "amount": 100,
      "message": "Nailed it!",
      "timestamp": "2026-02-03T12:00:00Z"
    }
  ]
}
```

### Tipper Leaderboard
```
GET /api/scanner/tips/leaderboard?limit=20
```

**Response:**
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "address": "0x...",
      "totalTipped": 2500,
      "tipCount": 25,
      "badges": [
        { "name": "Whale", "emoji": "🐋", "color": "gold" },
        { "name": "Regular", "emoji": "💎", "color": "purple" }
      ]
    }
  ],
  "updatedAt": "2026-02-03T12:00:00Z"
}
```

---

## Tipper Badges

| Badge | Requirement | Emoji |
|-------|-------------|-------|
| Whale | 1000+ ZOID tipped | 🐋 |
| Big Tipper | 500+ ZOID tipped | 🦈 |
| Generous | 100+ ZOID tipped | 🐬 |
| Regular | 50+ tips made | 💎 |
| Supporter | 10+ tips made | ⭐ |
| Newbie | First tip | 🌱 |

---

## MCP Tools

```javascript
// Send tip
clawnch_tip_send({
  signalId: "sg_...",
  tipper: "0x...",
  amount: 100,
  signature: "0x...",
  message: "Thanks!"
})

// Get tip stats
clawnch_tip_stats({})

// Get leaderboard
clawnch_tip_leaderboard({ limit: 20 })
```

---

## Why Tip?

1. **Support Development:** Tips fund continued signal improvements
2. **Show Appreciation:** Recognize great calls
3. **Burn Mechanism:** 25% burn reduces ZOID supply
4. **Leaderboard Recognition:** Earn badges and status

---

## Integration Example

```javascript
// After signal hits TP
const signal = await getSignalResult(signalId);

if (signal.result === 'HIT') {
  const tipAmount = calculateTip(signal.profit); // e.g., 1% of profit
  
  await sendTip({
    signalId,
    tipper: userAddress,
    amount: tipAmount,
    signature: await signMessage(tipMessage),
    message: "Great call on BTC!"
  });
}
```

---

## Resources

- **Token:** ZOID (0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5)
- **Burn Address:** 0x000000000000000000000000000000000000dEaD
- **API:** https://snipersrus-backend-production.up.railway.app
