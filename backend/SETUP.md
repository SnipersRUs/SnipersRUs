# SnipersRUs Backend - Veil Integration

## Quick Start

### 1. Install Dependencies
```bash
cd backend
npm install
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Start Server
```bash
# Development (with auto-reload)
npm run dev

# Production
npm start
```

## API Endpoints

### Signals
- `GET /api/signals` - List all signals
- `GET /api/signals/:id` - Get signal details
- `POST /api/signals` - Create new signal
- `POST /api/signals/:id/settle` - Settle signal

### Bets
- `POST /api/bets` - Place bet
- `GET /api/bets/:userAddress` - Get user's bets

### Users
- `POST /api/users/auth/challenge` - Get auth challenge
- `POST /api/users/auth/verify` - Verify signature
- `GET /api/users/:address` - Get user profile

### Health
- `GET /health` - Server status

## Veil Integration Flow

1. **Create Signal**
   - User posts signal to backend
   - Backend creates Veil market
   - Returns signal ID

2. **Place Bet**
   - User requests auth challenge
   - User signs message with wallet
   - Backend places order on Veil
   - Stores bet in database

3. **Settlement**
   - Veil oracle settles market
   - WebSocket notifies backend
   - Backend updates bets/karma

## Database

SQLite database stored in `database.sqlite`

Tables:
- `signals` - All trading signals
- `bets` - User bets
- `users` - User profiles and karma

## Karma System

### Providers (Signal Creators)
- +10 for winning signal
- -5 for losing signal
- Bonus: +5 for 3+ consecutive wins

### Users (Bettors)
- +1 for winning bet
- -1 for losing bet
- Bonus: +10 for >70% win rate
