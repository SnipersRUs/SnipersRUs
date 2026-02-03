require('dotenv').config();
const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const Database = require('./database');
const VeilService = require('./services/veil');
const SignalRoutes = require('./routes/signals');
const BetRoutes = require('./routes/bets');
const UserRoutes = require('./routes/users');

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
app.use('/api/bets', BetRoutes);
app.use('/api/users', UserRoutes);

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
  
  // Initialize Veil WebSocket
  veilService.connectWebSocket();
});

module.exports = app;
