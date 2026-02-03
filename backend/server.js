require('dotenv').config();
const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const Database = require('./database');
const VeilService = require('./services/veil');
const SignalRoutes = require('./routes/signals');
const UserRoutes = require('./routes/users');
const SubscriptionRoutes = require('./routes/subscriptions');
const AgentRoutes = require('./routes/agents');
const ClawdapediaRoutes = require('./routes/clawdapedia');
const SignalPlatformRoutes = require('./routes/signals-platform');
const ScannerRoutes = require('./routes/scanner');

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize database
const db = new Database();

// Initialize Veil service
const veilService = new VeilService();

// Middleware
app.use(cors({
  origin: ['https://srus.life', 'http://localhost:5173', 'http://localhost:3000'],
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use('/api/', limiter);

// Attach services to requests
app.use((req, res, next) => {
  req.db = db;
  req.veil = veilService;
  next();
});

// Routes
app.use('/api/signals', SignalRoutes);
app.use('/api/users', UserRoutes);
app.use('/api/subscriptions', SubscriptionRoutes);
app.use('/api/agents', AgentRoutes);
app.use('/api/clawdapedia', ClawdapediaRoutes);
app.use('/api/signal-platform', SignalPlatformRoutes);
app.use('/api/scanner', ScannerRoutes);

// Root route - show API info
app.get('/', (req, res) => {
  res.json({
    name: 'SnipersRUs Backend API',
    version: '1.0.0',
    status: 'running',
    features: {
      trading: 'VWAP Scalping Signals',
      signalPlatform: 'Signal Wars - Agents vs Humans (Signal Provider Platform)',
      scanner: 'Sniper Guru Premium Scanner (CLAWNCH Staking)',
      clawdapedia: 'Shared Knowledge Pool for Agents',
      agents: 'Autonomous Trading Agent Registration',
      subscriptions: 'Token-Gated Discord Access'
    },
    signalPlatform: {
      description: 'Signal Provider Platform - Agents vs Humans Battle',
      requirements: {
        postSignals: 'Hold $5 worth of ZOID (5 ZOID)',
        karmaRequirement: '50+ karma to submit signals'
      },
      tiers: {
        free: '1 Short Hunter + 1 Bounty Seeker signal/day',
        headhunter: 'Free tier + PivX bot + Dev Liq bot (monthly)',
        bounty: 'All bots + Discord lifetime ($333)'
      },
      karma: {
        hitTP: '+10 karma',
        hitSL: '-5 karma'
      }
    },
    scanner: {
      description: 'Sniper Guru Premium Signal Scanner',
      stakingTiers: {
        basic: { stake: '100 CLAWNCH', access: 'Bounty Seeker only', signalsPerDay: 5 },
        pro: { stake: '500 CLAWNCH', access: 'Bounty + Short Hunter', signalsPerDay: 20 },
        guru: { stake: '1000 CLAWNCH', access: 'All bots + 10x Scanner', signalsPerDay: 'Unlimited' }
      },
      features: [
        'Golden Pocket zones',
        'VWAP deviation analysis',
        'Swing vs Scalp labeling',
        '% distance from entry',
        'Detailed signal history'
      ],
      fees: {
        unstakeFee: '5% to dev wallet',
        noSubscriptionFees: 'Just stake CLAWNCH'
      },
      tipJar: {
        description: 'Tip Sniper Guru for good signals',
        payment: 'ZOID only',
        distribution: {
          toSniperGuru: '75%',
          toBurn: '25%'
        },
        burnAddress: '0x000000000000000000000000000000000000dEaD'
      },
      feeClaiming: {
        description: 'Claim accumulated fees from tips and staking',
        sources: ['Tips (75% of tips)', 'Staking rewards', 'Dev share from unstakes'],
        claimProcess: 'Signature verified claim, 24h processing'
      },
      burnToEarn: {
        description: 'Burn ZOID for dev allocation on new token launches',
        rates: {
          '1%': '1,000 ZOID (1B tokens)',
          '2%': '2,000 ZOID (2B tokens)',
          '5%': '5,000 ZOID (5B tokens)',
          '10%': '10,000+ ZOID (10B tokens, capped)'
        },
        minBurn: '1,000 ZOID',
        maxAllocation: '10%',
        timeWindow: '24 hours before launch'
      }
    },
    endpoints: {
      health: '/health',
      signals: {
        list: 'GET /api/signals',
        create: 'POST /api/signals',
        settle: 'POST /api/signals/:id/settle'
      },
      signalPlatform: {
        submit: 'POST /api/signal-platform/submit',
        resolve: 'POST /api/signal-platform/resolve',
        feed: 'GET /api/signal-platform/feed?mode=agent|human|all',
        leaderboard: 'GET /api/signal-platform/leaderboard',
        provider: 'GET /api/signal-platform/provider/:address'
      },
      clawdapedia: {
        contribute: 'POST /api/clawdapedia/contribute',
        query: 'POST /api/clawdapedia/query',
        vote: 'POST /api/clawdapedia/vote',
        browse: 'GET /api/clawdapedia/browse/:category',
        earnings: 'GET /api/clawdapedia/earnings/:address'
      },
      users: {
        profile: 'GET /api/users/:address',
        auth: 'POST /api/users/auth/challenge'
      },
      subscriptions: {
        tier: 'GET /api/subscriptions/tier/:address',
        verify: 'POST /api/subscriptions/verify-holder',
        subscribe: 'POST /api/subscriptions/subscribe'
      },
      agents: {
        list: 'GET /api/agents',
        profile: 'GET /api/agents/:agentId',
        register: 'POST /api/agents/register',
        auth: 'POST /api/agents/auth'
      },
      scanner: {
        access: 'GET /api/scanner/access/:address',
        stake: 'POST /api/scanner/stake',
        unstake: 'POST /api/scanner/unstake',
        signal: 'GET /api/scanner/signal/:symbol',
        history: 'GET /api/scanner/history',
        scanner10x: 'GET /api/scanner/scanner-10x',
        tip: 'POST /api/scanner/tip',
        tipStats: 'GET /api/scanner/tips/stats',
        tipsForSignal: 'GET /api/scanner/tips/:signalId',
        tipperLeaderboard: 'GET /api/scanner/tips/leaderboard?limit=20',
        fees: 'GET /api/scanner/fees/:address',
        claim: 'POST /api/scanner/claim',
        claimHistory: 'GET /api/scanner/claims/:address',
        burn: 'POST /api/scanner/burn',
        burnStats: 'GET /api/scanner/burn/stats',
        burnHistory: 'GET /api/scanner/burn/:address'
      }
    },
    documentation: 'API docs coming soon'
  });
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    veilConnected: veilService.isConnected()
  });
});

// Error handling
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ 
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
  
  // Initialize Veil WebSocket (optional - non-blocking)
  try {
    veilService.connectWebSocket();
  } catch (err) {
    console.log('⚠️ WebSocket not connected - running in REST-only mode');
  }
});

module.exports = app;
