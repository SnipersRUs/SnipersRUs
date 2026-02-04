const express = require('express');
const router = express.Router();
const { ethers } = require('ethers');

// Sniper Guru Premium Scanner
// Pay ZOID per signal - Simple model

const ZOID_TOKEN = '0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5';
const DEV_WALLET = '0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5';
const BURN_ADDRESS = '0x000000000000000000000000000000000000dEaD';

// Signal prices in ZOID
const SIGNAL_PRICES = {
  SINGLE: 5,      // 5 ZOID for one signal
  BUNDLE_5: 20,   // 20 ZOID for 5 signals (20% discount)
  BUNDLE_10: 35,  // 35 ZOID for 10 signals (30% discount)
  UNLIMITED_DAY: 50  // 50 ZOID for unlimited signals for 24h
};

// Purchase signal access with ZOID
router.post('/purchase', async (req, res) => {
  try {
    const {
      buyer,           // Wallet address
      package: pkg,    // 'SINGLE', 'BUNDLE_5', 'BUNDLE_10', 'UNLIMITED_DAY'
      signature,
      txHash           // On-chain transaction hash
    } = req.body;

    // Verify signature
    const message = `Purchase ${pkg} signal package at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(message, signature);

    if (recoveredAddress.toLowerCase() !== buyer.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const price = SIGNAL_PRICES[pkg];
    if (!price) {
      return res.status(400).json({ error: 'Invalid package' });
    }

    // Calculate distribution
    const burnAmount = Math.floor(price * 0.25);  // 25% burn
    const devAmount = price - burnAmount;           // 75% to dev

    // Create purchase record
    const purchase = {
      id: `purchase_${Date.now()}_${buyer.slice(0, 6)}`,
      buyer,
      package: pkg,
      price,
      burnAmount,
      devAmount,
      txHash,
      signalsRemaining: getSignalCount(pkg),
      expiresAt: pkg === 'UNLIMITED_DAY' ? new Date(Date.now() + 24 * 60 * 60 * 1000) : null,
      timestamp: new Date(),
      status: 'ACTIVE'
    };

    await req.db.createSignalPurchase(purchase);

    // Send Discord notification
    if (req.discord) {
      await req.discord.sendPurchaseNotification(buyer, pkg, price, purchase.signalsRemaining);
    }

    res.json({
      success: true,
      purchaseId: purchase.id,
      package: pkg,
      price,
      signalsRemaining: purchase.signalsRemaining,
      expiresAt: purchase.expiresAt,
      message: `Purchased ${pkg} package. ${purchase.signalsRemaining} signals available.`
    });

  } catch (err) {
    console.error('Purchase error:', err);
    res.status(500).json({ error: 'Purchase failed' });
  }
});

// Check purchase status
router.get('/status/:address', async (req, res) => {
  try {
    const { address } = req.params;

    const activePurchases = await req.db.getActivePurchases(address);
    const totalRemaining = activePurchases.reduce((sum, p) => sum + p.signals_remaining, 0);

    res.json({
      address,
      hasAccess: totalRemaining > 0,
      totalRemaining,
      purchases: activePurchases.map(p => ({
        id: p.id,
        package: p.package,
        signalsRemaining: p.signals_remaining,
        expiresAt: p.expires_at,
        purchasedAt: p.timestamp
      }))
    });

  } catch (err) {
    console.error('Status check error:', err);
    res.status(500).json({ error: 'Failed to check status' });
  }
});

// Get signal (requires purchase)
router.get('/signal/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const { address } = req.query;

    // Check if user has active purchases
    const activePurchases = await req.db.getActivePurchases(address);
    const totalRemaining = activePurchases.reduce((sum, p) => sum + p.signals_remaining, 0);

    if (totalRemaining <= 0) {
      return res.status(403).json({
        error: 'No signal credits available',
        message: 'Purchase ZOID to get signals',
        prices: SIGNAL_PRICES
      });
    }

    // Deduct one signal from the oldest active purchase
    const purchaseToUse = activePurchases[0];
    await req.db.useSignalCredit(purchaseToUse.id);

    // Generate signal
    const signal = await generateSignal(symbol);

    // Record signal delivery
    await req.db.recordSignalDelivery({
      id: `delivery_${Date.now()}`,
      purchaseId: purchaseToUse.id,
      buyer: address,
      symbol,
      signalId: signal.id,
      timestamp: new Date()
    });

    res.json({
      signal,
      remainingCredits: totalRemaining - 1,
      purchaseUsed: purchaseToUse.id
    });

  } catch (err) {
    console.error('Signal error:', err);
    res.status(500).json({ error: 'Failed to get signal' });
  }
});

// Bot pushes a real signal (no purchase required for the bot itself)
router.post('/bot-signal', async (req, res) => {
  try {
    const {
      symbol,
      direction,
      style,
      entry,
      stopLoss,
      takeProfit,
      confidence,
      analysis,
      apiKey // For security
    } = req.body;

    // TODO: Verify apiKey

    const signal = {
      id: `sig_${Date.now()}_${symbol}`,
      provider: 'Sniper Guru',
      symbol,
      direction,
      style,
      entry,
      stopLoss,
      takeProfit,
      confidence,
      analysis,
      timestamp: new Date()
    };

    await req.db.createSniperGuruSignal(signal);

    // Notify Discord
    if (req.discord) {
      await req.discord.sendSignalNotification(
        'Sniper Guru',
        symbol,
        direction,
        entry,
        takeProfit,
        stopLoss,
        true
      );
    }

    res.status(201).json({
      success: true,
      signalId: signal.id,
      message: 'Signal received and broadcasted'
    });
  } catch (err) {
    console.error('Bot signal error:', err);
    res.status(500).json({ error: 'Failed to process bot signal' });
  }
});

// Get all available signals (public feed)
router.get('/feed', async (req, res) => {
  try {
    const { limit = 20, page = 1 } = req.query;

    const signals = await req.db.getPublicSignals({
      limit: parseInt(limit),
      offset: (parseInt(page) - 1) * parseInt(limit)
    });

    res.json({
      count: signals.length,
      signals: signals.map(s => ({
        id: s.id,
        symbol: s.symbol,
        direction: s.direction,
        style: s.style,
        entry: s.entry,
        stopLoss: s.stopLoss,
        takeProfit: s.takeProfit,
        confidence: s.confidence,
        timestamp: s.timestamp,
        result: s.result
      }))
    });

  } catch (err) {
    console.error('Feed error:', err);
    res.status(500).json({ error: 'Failed to fetch feed' });
  }
});

// Get pricing info
router.get('/pricing', async (req, res) => {
  res.json({
    prices: SIGNAL_PRICES,
    description: {
      SINGLE: '1 signal - 5 ZOID',
      BUNDLE_5: '5 signals - 20 ZOID (Save 5 ZOID)',
      BUNDLE_10: '10 signals - 35 ZOID (Save 15 ZOID)',
      UNLIMITED_DAY: 'Unlimited for 24h - 50 ZOID'
    },
    distribution: {
      toDev: '75%',
      toBurn: '25%'
    },
    devWallet: DEV_WALLET,
    burnAddress: BURN_ADDRESS
  });
});

// Add comment to signal
router.post('/comment/:signalId', async (req, res) => {
  try {
    const { signalId } = req.params;
    const { authorName, authorAvatar, body } = req.body;

    const comment = await req.db.createSignalComment({
      signalId,
      authorName,
      authorAvatar,
      body
    });

    res.status(201).json(comment);
  } catch (err) {
    console.error('Comment error:', err);
    res.status(500).json({ error: 'Failed to add comment' });
  }
});

// Update signal sentiment (bullish/bearish)
router.post('/vote/:signalId', async (req, res) => {
  try {
    const { signalId } = req.params;
    const { type } = req.body; // 'bullish' or 'bearish'

    // For now we'll just return success to make frontend happy
    res.json({ success: true, signalId, type });
  } catch (err) {
    res.status(500).json({ error: 'Vote failed' });
  }
});

// Helper functions
function getSignalCount(pkg) {
  switch (pkg) {
    case 'SINGLE': return 1;
    case 'BUNDLE_5': return 5;
    case 'BUNDLE_10': return 10;
    case 'UNLIMITED_DAY': return 9999; // Unlimited marker
    default: return 0;
  }
}

async function generateSignal(symbol) {
  // Mock signal generation
  const currentPrice = Math.random() * 100000;
  const entry = currentPrice * (0.98 + Math.random() * 0.04);
  const isLong = Math.random() > 0.5;

  return {
    id: `sig_${Date.now()}_${symbol}`,
    symbol,
    direction: isLong ? 'LONG' : 'SHORT',
    style: Math.abs((currentPrice - entry) / entry * 100) > 2 ? 'SWING' : 'SCALP',
    entry: entry.toFixed(2),
    stopLoss: (entry * (isLong ? 0.97 : 1.03)).toFixed(2),
    takeProfit: (entry * (isLong ? 1.03 : 0.97)).toFixed(2),
    confidence: Math.floor(Math.random() * 30) + 70,
    timestamp: new Date().toISOString()
  };
}

module.exports = router;