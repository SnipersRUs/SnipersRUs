const express = require('express');
const router = express.Router();

// Get authentication challenge
router.post('/auth/challenge', async (req, res) => {
  try {
    const challenge = await req.veil.getAuthChallenge();
    res.json(challenge);
  } catch (err) {
    console.error('Auth challenge error:', err);
    res.status(500).json({ error: 'Failed to get challenge' });
  }
});

// Verify signature and get API key
router.post('/auth/verify', async (req, res) => {
  try {
    const { challenge, signature, address } = req.body;

    if (!challenge || !signature || !address) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Verify with Veil
    const authData = await req.veil.verifySignature(challenge, signature, address);

    // Create or update user
    let user = await req.db.getUser(address);
    if (!user) {
      user = await req.db.createUser(address);
    }

    // Store API key
    const expiresAt = new Date();
    expiresAt.setHours(expiresAt.getHours() + 24);
    await req.db.updateVeilApiKey(address, authData.apiKey, expiresAt.toISOString());

    res.json({
      message: 'Authenticated successfully',
      apiKey: authData.apiKey,
      expiresAt,
      user
    });
  } catch (err) {
    console.error('Auth verify error:', err);
    res.status(500).json({ error: 'Failed to verify signature' });
  }
});

// Get user profile
router.get('/:address', async (req, res) => {
  try {
    const { address } = req.params;
    let user = await req.db.getUser(address);
    
    if (!user) {
      // Return default profile for new users
      return res.json({
        address,
        karma: 0,
        total_bets: 0,
        win_rate: 0,
        profit_loss: 0,
        isNew: true
      });
    }

    // Get user's bets for stats
    const bets = await req.db.getBetsByUser(address);
    const wins = bets.filter(b => b.status === 'WON').length;
    const total = bets.filter(b => b.status === 'WON' || b.status === 'LOST').length;
    const winRate = total > 0 ? (wins / total) * 100 : 0;
    
    res.json({
      ...user,
      stats: {
        totalBets: bets.length,
        winRate: winRate.toFixed(1),
        profitLoss: bets.reduce((sum, b) => sum + (b.payout || 0) - b.amount, 0)
      }
    });
  } catch (err) {
    console.error('Get user error:', err);
    res.status(500).json({ error: 'Failed to fetch user' });
  }
});

// Update karma (internal use or admin)
router.post('/:address/karma', async (req, res) => {
  try {
    const { address } = req.params;
    const { delta } = req.body; // +10 for win, -5 for loss

    await req.db.updateUserKarma(address, delta);
    
    res.json({
      message: 'Karma updated',
      address,
      delta
    });
  } catch (err) {
    console.error('Update karma error:', err);
    res.status(500).json({ error: 'Failed to update karma' });
  }
});

module.exports = router;
