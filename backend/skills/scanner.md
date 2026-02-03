# Sniper Guru Scanner Skill

The Sniper Guru Premium Scanner provides AI-powered trading signals with technical analysis. Stake CLAWNCH to access tiered signal services.

## Overview

**Purpose:** Generate premium trading signals with Golden Pocket zones, VWAP deviation analysis, and swing/scalp classifications.

**Token:** CLAWNCH (0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be)

**Contract:** Base Network

---

## Staking Tiers

| Tier | CLAWNCH Required | Access | Signals/Day |
|------|-----------------|--------|-------------|
| BASIC | 100 | Bounty Seeker only | 5 |
| PRO | 500 | Bounty + Short Hunter | 20 |
| GURU | 1000 | All bots + 10x Scanner | Unlimited |

### Tier Features

**BASIC (100 CLAWNCH)**
- Bounty Seeker signals
- Entry/stop/target levels
- Basic technical analysis

**PRO (500 CLAWNCH)**
- Bounty Seeker signals
- Short Hunter signals
- Advanced confluence scoring
- Priority delivery

**GURU (1000 CLAWNCH)**
- All bot signals
- 10x Scanner (top 10 coins)
- Golden Pocket zones
- VWAP deviation analysis
- Swing/Scalp classification
- Unlimited signals

---

## API Reference

### Check Access
```
GET /api/scanner/access/:address
```

**Response:**
```json
{
  "address": "0x...",
  "tier": "GURU",
  "stakedAmount": 1500,
  "access": "all_bots + 10x_scanner",
  "signalsUsedToday": 12,
  "signalsRemaining": "Unlimited",
  "canAccess": true
}
```

### Stake CLAWNCH
```
POST /api/scanner/stake
```

**Body:**
```json
{
  "address": "0x...",
  "amount": 1000,
  "signature": "0x..."
}
```

### Unstake (5% fee to dev wallet)
```
POST /api/scanner/unstake
```

**Body:**
```json
{
  "address": "0x...",
  "signature": "0x..."
}
```

**Response:**
```json
{
  "success": true,
  "returned": 950,
  "fee": 50,
  "message": "Unstaked 950 CLAWNCH (50 CLAWNCH fee)"
}
```

### Get Signal
```
GET /api/scanner/signal/:symbol
```

**Example:** `/api/scanner/signal/BTC`

**Response:**
```json
{
  "symbol": "BTC/USDT",
  "direction": "LONG",
  "style": "SWING",
  "entry": 89450.50,
  "stopLoss": 87950.50,
  "takeProfit": 92450.50,
  "confidence": 87,
  "analysis": {
    "goldenPocket": {
      "zone": "0.618-0.65 Fib",
      "lower": 88200.00,
      "upper": 89800.00
    },
    "vwap": {
      "deviation": "-2.5σ",
      "dailyVwap": 91500.00
    },
    "distancePercent": 2.8
  },
  "timestamp": "2026-02-03T12:00:00Z"
}
```

### 10x Scanner (Guru only)
```
GET /api/scanner/scanner-10x
```

**Response:**
```json
{
  "timestamp": "2026-02-03T12:00:00Z",
  "signals": [
    { "symbol": "BTC/USDT", "direction": "LONG", "confidence": 87 },
    { "symbol": "ETH/USDT", "direction": "SHORT", "confidence": 82 },
    ...
  ]
}
```

---

## Fee Claiming

Providers can claim accumulated fees from:
- Tips (75% of tip jar)
- Staking rewards
- Dev share from unstakes

### Check Fees
```
GET /api/scanner/fees/:address
```

**Response:**
```json
{
  "accumulatedFees": {
    "tips": 450,
    "staking": 120,
    "devShare": 80,
    "total": 650
  },
  "lastClaim": "2026-01-15T10:00:00Z"
}
```

### Claim Fees
```
POST /api/scanner/claim
```

**Body:**
```json
{
  "address": "0x...",
  "signature": "0x..."
}
```

### Claim History
```
GET /api/scanner/claims/:address?limit=20
```

---

## Burn-to-Earn

Burn ZOID for dev allocation on new token launches.

### Rates
| Burn Amount | Allocation | Tokens |
|-------------|-----------|--------|
| 1,000 ZOID | 1% | 1,000,000,000 |
| 2,000 ZOID | 2% | 2,000,000,000 |
| 5,000 ZOID | 5% | 5,000,000,000 |
| 10,000+ ZOID | 10% | 10,000,000,000 (cap) |

### Burn ZOID
```
POST /api/scanner/burn
```

**Body:**
```json
{
  "address": "0x...",
  "amount": 5000,
  "signature": "0x..."
}
```

**Response:**
```json
{
  "burnId": "burn_...",
  "burned": 5000,
  "allocation": {
    "percent": "5%",
    "tokens": "5,000,000,000"
  },
  "burnAddress": "0x000...dEaD"
}
```

### Burn Stats
```
GET /api/scanner/burn/stats
```

### Burn History
```
GET /api/scanner/burn/:address
```

---

## MCP Tools

For agent integration via MCP:

```javascript
// Check scanner access
clawnch_scanner_check_access({ address: "0x..." })

// Get signal
clawnch_scanner_get_signal({ symbol: "BTC" })

// Get 10x scanner
clawnch_scanner_10x_scan({})

// Claim fees
clawnch_scanner_claim_fees({ address: "0x...", signature: "0x..." })

// Burn for allocation
clawnch_scanner_burn({ address: "0x...", amount: 5000, signature: "0x..." })
```

---

## Signal Classification

### Swing vs Scalp
- **Swing:** >2% distance from entry (4h-1d timeframe)
- **Scalp:** <2% distance from entry (15m-1h timeframe)

### Confidence Scoring
- 70-79%: Moderate confidence
- 80-89%: High confidence
- 90-99%: Very high confidence

### Technical Indicators
- Golden Pocket (0.618-0.65 Fibonacci)
- VWAP deviation (±σ bands)
- Support/resistance levels
- Volume analysis

---

## Resources

- **API Base:** https://snipersrus-backend-production.up.railway.app
- **Token:** CLAWNCH (0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be)
- **Burn Address:** 0x000000000000000000000000000000000000dEaD
