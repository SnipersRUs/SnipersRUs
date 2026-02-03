# Veil Prediction Market Integration for Signal Betting

## Overview
Backend service to integrate Veil prediction markets with SnipersRUs signal betting platform.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│  Veil API   │
│  (React)    │     │  (Node.js)  │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                    WebSocket
```

## API Endpoints

### Signals
- `POST /api/signals` - Create new signal + Veil market
- `GET /api/signals` - List all signals with market status
- `GET /api/signals/:id` - Get signal details + market data
- `POST /api/signals/:id/settle` - Settle signal (triggered by oracle)

### Betting
- `POST /api/bets` - Place bet on signal
- `GET /api/bets/:userAddress` - Get user's bets
- `GET /api/bets/:id/status` - Check bet settlement status

### Users
- `POST /api/auth/challenge` - Get auth challenge from Veil
- `POST /api/auth/verify` - Verify signature, get API key
- `GET /api/users/:address` - Get user profile + karma
- `POST /api/users/:address/karma` - Update karma after settlement

## Database Schema

### Signals
```javascript
{
  id: string,
  provider: {
    address: string,
    name: string,
    reputation: number,
    winRate: number
  },
  asset: string,
  type: 'LONG' | 'SHORT',
  entry: number,
  target: number,
  stopLoss: number,
  timeframe: string,
  deadline: Date,
  veilMarketId: string,
  status: 'ACTIVE' | 'SETTLING' | 'SETTLED',
  outcome: 'HIT' | 'MISS' | null,
  totalVolume: number,
  createdAt: Date
}
```

### Bets
```javascript
{
  id: string,
  signalId: string,
  userAddress: string,
  outcome: 'HIT' | 'MISS',
  amount: number, // USDC
  status: 'PENDING' | 'CONFIRMED' | 'WON' | 'LOST',
  veilOrderId: string,
  payout: number | null,
  createdAt: Date,
  settledAt: Date | null
}
```

### Users
```javascript
{
  address: string,
  karma: number,
  totalBets: number,
  winRate: number,
  profitLoss: number,
  veilApiKey: string | null,
  veilApiKeyExpires: Date | null,
  createdAt: Date
}
```

## Veil Integration Flow

### 1. Create Signal Market
```
1. Trader posts signal
2. Backend creates Veil market via API
3. Store veilMarketId in database
4. Return market data to frontend
```

### 2. Place Bet
```
1. User clicks HIT/MISS
2. Frontend requests challenge from backend
3. User signs message with wallet
4. Backend submits order to Veil
5. Store bet in database
```

### 3. Settlement
```
1. Veil oracle settles market
2. WebSocket notifies backend
3. Backend updates signal outcome
4. Update all bets for that signal
5. Update provider karma
6. Update user P&L
```

## Environment Variables

```
VEIL_API_URL=https://api.veil.markets/v1
VEIL_WS_URL=wss://api.veil.markets/ws
DATABASE_URL=postgresql://...
JWT_SECRET=...
PORT=3000
```

## Karma System

### Provider Karma
- +10 for each winning signal
- -5 for each losing signal
- Bonus: +5 for 3+ consecutive wins
- Penalty: -10 for 3+ consecutive losses

### User Karma
- +1 for each winning bet
- -1 for each losing bet
- Bonus: +10 for >70% win rate over 20 bets

## Rate Limits

- Veil API: 100 requests/minute
- WebSocket: 10 subscriptions max
- Backend: Implement caching for market data

## Security

- All transactions require wallet signature
- API keys expire every 24h
- Rate limiting per IP
- Input validation on all endpoints
