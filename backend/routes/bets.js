const express = require('express');
const router = express.Router();

// Place a bet
router.post('/', async (req, res) => {
  try {
    const { signalId, userAddress, outcome, amount, signature } = req.body;

    // Validate
    if (!signalId || !userAddress || !outcome || !amount) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Get signal
    const signal = await req.db.getSignal(signalId);
    if (!signal) {
      return res.status(404).json({ error: 'Signal not found' });
    }

    if (signal.status !== 'ACTIVE') {
      return res.status(400).json({ error: 'Signal is not active' });
    }

    if (!signal.veil_market_id) {
      return res.status(400).json({ error: 'Market not ready yet' });
    }

    // Get orderbook to determine price
    const orderbook = await req.veil.getOrderbook(signal.veil_market_id);
    
    // Calculate price based on current odds
    // In a real implementation, you'd use the orderbook to determine fair price
    const price = outcome === 'HIT' ? 0.6 : 0.4; // Simplified

    // Place order on Veil
    const veilOrder = await req.veil.placeOrder(
      signal.veil_market_id,
      outcome === 'HIT' ? 'Yes' : 'No',
      req.veil.formatUSDC(amount),
      price,
      signature
    );

    // Store bet in database
    const bet = await req.db.createBet({
      signalId,
      userAddress,
      outcome,
      amount,
      veilOrderId: veilOrder.id
    });

    // Update signal volume
    // In production, you'd update this periodically or via webhook

    res.status(201).json({
      message: 'Bet placed successfully',
      bet,
      veilOrder
    });
  } catch (err) {
    console.error('Place bet error:', err);
    res.status(500).json({ error: 'Failed to place bet' });
  }
});

// Get user's bets
router.get('/:userAddress', async (req, res) => {
  try {
    const { userAddress } = req.params;
    const bets = await req.db.getBetsByUser(userAddress);
    
    // Enrich with signal data
    const enrichedBets = await Promise.all(
      bets.map(async (bet) => {
        const signal = await req.db.getSignal(bet.signal_id);
        return { ...bet, signal };
      })
    );
    
    res.json(enrichedBets);
  } catch (err) {
    console.error('Get bets error:', err);
    res.status(500).json({ error: 'Failed to fetch bets' });
  }
});

// Get bet status
router.get('/:id/status', async (req, res) => {
  try {
    // In a real implementation, check Veil for order status
    res.json({ status: 'pending', message: 'Not implemented yet' });
  } catch (err) {
    console.error('Get bet status error:', err);
    res.status(500).json({ error: 'Failed to fetch bet status' });
  }
});

module.exports = router;
