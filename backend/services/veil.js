const axios = require('axios');
const WebSocket = require('ws');

class VeilService {
  constructor() {
    this.apiUrl = process.env.VEIL_API_URL || 'https://api.veil.markets/v1';
    this.wsUrl = process.env.VEIL_WS_URL || 'wss://api.veil.markets/ws';
    this.ws = null;
    this.apiKey = null;
    this.subscriptions = new Map();
  }

  isConnected() {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  // WebSocket Connection
  connectWebSocket() {
    try {
      this.ws = new WebSocket(this.wsUrl);

      this.ws.on('open', () => {
        console.log('✅ Connected to Veil WebSocket');
      });

      this.ws.on('message', (data) => {
        try {
          const message = JSON.parse(data);
          this.handleWebSocketMessage(message);
        } catch (err) {
          console.error('WebSocket message error:', err);
        }
      });

      this.ws.on('error', (err) => {
        console.error('WebSocket error:', err);
      });

      this.ws.on('close', () => {
        console.log('⚠️ Veil WebSocket disconnected. Reconnecting in 5s...');
        setTimeout(() => this.connectWebSocket(), 5000);
      });
    } catch (err) {
      console.error('Failed to connect WebSocket:', err);
    }
  }

  handleWebSocketMessage(message) {
    // Handle different message types from Veil
    if (message.type === 'market_update') {
      // Market price/volume updated
      console.log('Market update:', message.marketId);
    } else if (message.type === 'market_settled') {
      // Market settled - trigger settlement logic
      console.log('Market settled:', message.marketId, 'Outcome:', message.outcome);
      this.handleSettlement(message.marketId, message.outcome);
    }
  }

  // Subscribe to market updates
  subscribeToMarket(marketId, callback) {
    if (!this.isConnected()) {
      console.error('WebSocket not connected');
      return;
    }

    const message = {
      action: 'subscribe',
      channel: 'market',
      marketId: marketId
    };

    this.ws.send(JSON.stringify(message));
    this.subscriptions.set(marketId, callback);
    console.log(`📡 Subscribed to market: ${marketId}`);
  }

  // REST API Methods

  // 1. Get authentication challenge
  async getAuthChallenge() {
    try {
      const response = await axios.post(`${this.apiUrl}/auth/challenge`);
      return response.data;
    } catch (err) {
      console.error('Auth challenge error:', err.message);
      throw err;
    }
  }

  // 2. Verify signature and get API key
  async verifySignature(challenge, signature, address) {
    try {
      const response = await axios.post(`${this.apiUrl}/auth/verify`, {
        challenge,
        signature,
        address
      });
      this.apiKey = response.data.apiKey;
      return response.data;
    } catch (err) {
      console.error('Signature verification error:', err.message);
      throw err;
    }
  }

  // 3. Create prediction market
  async createMarket(signal) {
    try {
      const question = `Will ${signal.asset} reach $${signal.target} by ${signal.deadline}?`;
      
      const marketData = {
        question,
        category: 'crypto',
        resolutionSource: 'chainlink', // Using Chainlink oracle
        resolutionDate: signal.deadline,
        outcomes: ['Yes', 'No'],
        metadata: {
          signalId: signal.id,
          asset: signal.asset,
          entry: signal.entry,
          target: signal.target,
          stopLoss: signal.stopLoss,
          provider: signal.provider
        }
      };

      const response = await axios.post(
        `${this.apiUrl}/markets`,
        marketData,
        { headers: { 'Authorization': `Bearer ${this.apiKey}` } }
      );

      console.log('✅ Created Veil market:', response.data.id);
      return response.data;
    } catch (err) {
      console.error('Create market error:', err.message);
      throw err;
    }
  }

  // 4. Get market details
  async getMarket(marketId) {
    try {
      const response = await axios.get(`${this.apiUrl}/markets/${marketId}`);
      return response.data;
    } catch (err) {
      console.error('Get market error:', err.message);
      throw err;
    }
  }

  // 5. Get orderbook
  async getOrderbook(marketId) {
    try {
      const response = await axios.get(`${this.apiUrl}/markets/${marketId}/orderbook`);
      return response.data;
    } catch (err) {
      console.error('Get orderbook error:', err.message);
      throw err;
    }
  }

  // 6. Place order (bet)
  async placeOrder(marketId, outcome, amount, price, signature) {
    try {
      const orderData = {
        marketId,
        outcome, // 'Yes' or 'No'
        amount, // in USDC (6 decimals)
        price, // 0-1 (probability)
        signature // wallet signature
      };

      const response = await axios.post(
        `${this.apiUrl}/orders`,
        orderData,
        { headers: { 'Authorization': `Bearer ${this.apiKey}` } }
      );

      console.log('✅ Placed order:', response.data.id);
      return response.data;
    } catch (err) {
      console.error('Place order error:', err.message);
      throw err;
    }
  }

  // 7. Get user positions
  async getUserPositions(address) {
    try {
      const response = await axios.get(
        `${this.apiUrl}/user/${address}/positions`,
        { headers: { 'Authorization': `Bearer ${this.apiKey}` } }
      );
      return response.data;
    } catch (err) {
      console.error('Get positions error:', err.message);
      throw err;
    }
  }

  // Handle settlement (called when market settles)
  async handleSettlement(veilMarketId, outcome) {
    // This would be called by WebSocket when Veil settles
    console.log(`🎯 Market ${veilMarketId} settled with outcome: ${outcome}`);
    
    // Update database, distribute payouts, update karma
    // This will be implemented in the settlement route
  }

  // Helper: Format USDC amount (6 decimals)
  formatUSDC(amount) {
    return Math.floor(amount * 1_000_000);
  }

  // Helper: Parse USDC amount
  parseUSDC(amount) {
    return amount / 1_000_000;
  }
}

module.exports = VeilService;
