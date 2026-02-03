const express = require('express');
const router = express.Router();
const { ethers } = require('ethers');

// Get all signals
router.get('/', async (req, res) => {
  try {
    const { status } = req.query;
    const signals = await req.db.getSignals(status);
    
    // Enrich with Veil market data
    const enrichedSignals = await Promise.all(
      signals.map(async (signal) => {
        if (signal.veil_market_id) {
          try {
            const marketData = await req.veil.getMarket(signal.veil_market_id);
            return { ...signal, marketData };
          } catch (err) {
            return signal;
          }
        }
        return signal;
      })
    );
    
    res.json(enrichedSignals);
  } catch (err) {
    console.error('Get signals error:', err);
    res.status(500).json({ error: 'Failed to fetch signals' });
  }
});

// Get single signal
router.get('/:id', async (req, res) => {
  try {
    const signal = await req.db.getSignal(req.params.id);
    if (!signal) {
      return res.status(404).json({ error: 'Signal not found' });
    }

    // Get market data if available
    if (signal.veil_market_id) {
      try {
        const marketData = await req.veil.getMarket(signal.veil_market_id);
        const orderbook = await req.veil.getOrderbook(signal.veil_market_id);
        return res.json({ ...signal, marketData, orderbook });
      } catch (err) {
        console.error('Failed to fetch market data:', err.message);
      }
    }

    res.json(signal);
  } catch (err) {
    console.error('Get signal error:', err);
    res.status(500).json({ error: 'Failed to fetch signal' });
  }
});

// Create new signal
router.post('/', async (req, res) => {
  try {
    const { provider, asset, type, entry, target, stopLoss, timeframe, deadline } = req.body;

    // Validate required fields
    if (!provider?.address || !asset || !type || !entry || !target || !deadline) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Create signal in database
    const signal = await req.db.createSignal({
      provider,
      asset,
      type,
      entry,
      target,
      stopLoss,
      timeframe,
      deadline,
      veilMarketId: null // Will be set after Veil market creation
    });

    // Create Veil market (async - don't wait for it)
    req.veil.createMarket(signal)
      .then(veilMarket => {
        // Update signal with Veil market ID
        req.db.updateSignalStatus(signal.id, 'ACTIVE');
        console.log(`✅ Linked signal ${signal.id} to Veil market ${veilMarket.id}`);
        
        // Subscribe to market updates
        req.veil.subscribeToMarket(veilMarket.id, (update) => {
          console.log('Market update:', update);
        });
      })
      .catch(err => {
        console.error('Failed to create Veil market:', err.message);
      });

    res.status(201).json({
      message: 'Signal created',
      signal,
      note: 'Veil market is being created in background'
    });
  } catch (err) {
    console.error('Create signal error:', err);
    res.status(500).json({ error: 'Failed to create signal' });
  }
});

// Settle signal (called by oracle/webhook)
router.post('/:id/settle', async (req, res) => {
  try {
    const { outcome } = req.body; // 'HIT' or 'MISS'
    const signal = await req.db.getSignal(req.params.id);
    
    if (!signal) {
      return res.status(404).json({ error: 'Signal not found' });
    }

    if (signal.status === 'SETTLED') {
      return res.status(400).json({ error: 'Signal already settled' });
    }

    // Update signal status
    await req.db.updateSignalStatus(req.params.id, 'SETTLED', outcome);

    // Update provider karma
    const karmaDelta = outcome === 'HIT' ? 10 : -5;
    await req.db.updateUserKarma(signal.provider_address, karmaDelta);

    // Get all bets for this signal and update them
    // This would be done in a transaction in production
    
    res.json({
      message: 'Signal settled',
      signalId: req.params.id,
      outcome,
      providerKarmaDelta: karmaDelta
    });
  } catch (err) {
    console.error('Settle signal error:', err);
    res.status(500).json({ error: 'Failed to settle signal' });
  }
});

module.exports = router;
