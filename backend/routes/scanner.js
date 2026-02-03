const express = require('express');
const router = express.Router();
const { ethers } = require('ethers');

// Sniper Guru Signal Scanner
// Stake CLAWNCH to access premium signals

const CLAWNCH_TOKEN = '0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be';
const ZOID_TOKEN = '0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5';
const DEV_WALLET = '0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5'; // ZOID dev wallet
const BURN_ADDRESS = '0x000000000000000000000000000000000000dEaD'; // Standard burn address

// Staking tiers for scanner access
const SCANNER_TIERS = {
  BASIC: {
    stake: 100,        // 100 CLAWNCH
    access: 'bounty_seeker',  // Only Bounty Seeker signals
    signalsPerDay: 5
  },
  PRO: {
    stake: 500,        // 500 CLAWNCH
    access: 'bounty_seeker + short_hunter',  // Both bots
    signalsPerDay: 20
  },
  GURU: {
    stake: 1000,       // 1000 CLAWNCH
    access: 'all_bots + 10x_scanner',  // Everything
    signalsPerDay: Infinity,
    features: ['golden_pocket', 'vwap_deviation', 'swing_scalp_labels']
  }
};

// Check CLAWNCH stake for scanner access
router.get('/access/:address', async (req, res) => {
  try {
    const { address } = req.params;
    
    // Check staked amount from database
    const stakedAmount = await getStakedClawnch(address, req.db);
    
    let tier = 'NONE';
    if (stakedAmount >= SCANNER_TIERS.GURU.stake) {
      tier = 'GURU';
    } else if (stakedAmount >= SCANNER_TIERS.PRO.stake) {
      tier = 'PRO';
    } else if (stakedAmount >= SCANNER_TIERS.BASIC.stake) {
      tier = 'BASIC';
    }
    
    // Check daily usage
    const todaySignals = await req.db.getTodaySignalCount(address);
    const tierConfig = SCANNER_TIERS[tier] || { signalsPerDay: 0 };
    const remaining = tier === 'GURU' ? 'Unlimited' : Math.max(0, tierConfig.signalsPerDay - todaySignals);
    
    res.json({
      address,
      tier,
      stakedAmount,
      access: tierConfig.access || 'None',
      signalsUsedToday: todaySignals,
      signalsRemaining: remaining,
      canAccess: tier !== 'NONE'
    });
    
  } catch (err) {
    console.error('Access check error:', err);
    res.status(500).json({ error: 'Failed to check access' });
  }
});

// Stake CLAWNCH for scanner access
router.post('/stake', async (req, res) => {
  try {
    const { address, amount, signature } = req.body;
    
    // Verify signature
    const message = `Stake ${amount} CLAWNCH for scanner at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(message, signature);
    
    if (recoveredAddress.toLowerCase() !== address.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Verify CLAWNCH balance
    const balance = await getClawnchBalance(address);
    if (balance < amount) {
      return res.status(400).json({ 
        error: 'Insufficient CLAWNCH balance',
        balance,
        required: amount
      });
    }
    
    // Create stake record
    const stake = {
      id: `stake_${Date.now()}_${address.slice(0, 6)}`,
      address,
      amount,
      stakedAt: new Date(),
      status: 'ACTIVE',
      feesPaid: 0
    };
    
    await req.db.createScannerStake(stake);
    
    // Determine tier
    let tier = 'BASIC';
    if (amount >= SCANNER_TIERS.GURU.stake) tier = 'GURU';
    else if (amount >= SCANNER_TIERS.PRO.stake) tier = 'PRO';
    
    res.json({
      success: true,
      stakeId: stake.id,
      amount,
      tier,
      access: SCANNER_TIERS[tier].access,
      message: `Staked ${amount} CLAWNCH. ${tier} tier activated.`
    });
    
  } catch (err) {
    console.error('Stake error:', err);
    res.status(500).json({ error: 'Staking failed' });
  }
});

// Unstake CLAWNCH (pay fee in CLAWNCH to dev wallet)
router.post('/unstake', async (req, res) => {
  try {
    const { address, signature } = req.body;
    
    // Verify
    const message = `Unstake CLAWNCH at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(message, signature);
    
    if (recoveredAddress.toLowerCase() !== address.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    const stake = await req.db.getScannerStake(address);
    if (!stake || stake.status !== 'ACTIVE') {
      return res.status(404).json({ error: 'No active stake found' });
    }
    
    // Calculate fee (5% of staked amount)
    const fee = Math.floor(stake.amount * 0.05);
    const returnAmount = stake.amount - fee;
    
    // Update stake
    await req.db.updateScannerStake(stake.id, {
      status: 'UNSTAKED',
      unstakedAt: new Date(),
      feePaid: fee,
      returnedAmount: returnAmount
    });
    
    // TODO: Transfer fee to dev wallet on-chain
    // For now, track it
    await req.db.recordDevFee(fee);
    
    res.json({
      success: true,
      originalStake: stake.amount,
      fee,
      returnAmount,
      devWallet: DEV_WALLET,
      message: `Unstaked. Fee of ${fee} CLAWNCH sent to dev wallet.`
    });
    
  } catch (err) {
    console.error('Unstake error:', err);
    res.status(500).json({ error: 'Unstaking failed' });
  }
});

// Get detailed signal with technical analysis
router.get('/signal/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const { address } = req.query;
    
    // Check access
    const access = await checkScannerAccess(address, req.db);
    if (!access.canAccess) {
      return res.status(403).json({ 
        error: 'Scanner access required',
        stakeRequired: '100 CLAWNCH minimum',
        currentTier: access.tier,
        stakedAmount: await getStakedClawnch(address, req.db)
      });
    }
    
    // Track usage
    await req.db.recordSignalRequest(address, symbol);
    
    // Fetch technical analysis (mock for now)
    const analysis = await generateTechnicalAnalysis(symbol);
    
    // Determine signal type
    const signalType = determineSignalType(analysis);
    
    // Store in Sniper Guru history
    const signal = {
      id: `sg_${Date.now()}_${symbol}`,
      provider: 'SNIPER_GURU',
      symbol,
      ...signalType,
      analysis,
      timestamp: new Date(),
      subscriber: address
    };
    
    await req.db.createSniperGuruSignal(signal);
    
    res.json({
      signal: {
        id: signal.id,
        symbol,
        direction: signalType.direction,  // LONG or SHORT
        style: signalType.style,          // SWING or SCALP
        entry: analysis.entry,
        stopLoss: analysis.stopLoss,
        takeProfit: analysis.takeProfit,
        confidence: analysis.confidence
      },
      analysis: {
        distanceFromEntry: analysis.distanceFromEntry,  // % away
        goldenPocket: analysis.goldenPocket,            // GP zone
        vwapDeviation: analysis.vwapDeviation,          // VWAP ±σ
        keyLevels: analysis.keyLevels,
        reasoning: analysis.reasoning
      },
      tier: access.tier,
      remainingToday: access.remaining
    });
    
  } catch (err) {
    console.error('Signal error:', err);
    res.status(500).json({ error: 'Failed to generate signal' });
  }
});

// Get Sniper Guru signal history
router.get('/history', async (req, res) => {
  try {
    const { address, limit = 50, page = 1 } = req.query;
    
    const history = await req.db.getSniperGuruSignals({
      subscriber: address,
      limit: parseInt(limit),
      offset: (parseInt(page) - 1) * parseInt(limit)
    });
    
    // Calculate stats
    const stats = await req.db.getSniperGuruStats(address);
    
    res.json({
      count: history.length,
      page: parseInt(page),
      stats: {
        totalSignals: stats.total,
        winRate: stats.winRate,
        avgProfit: stats.avgProfit
      },
      signals: history.map(s => ({
        id: s.id,
        symbol: s.symbol,
        direction: s.direction,
        style: s.style,
        entry: s.entry,
        stopLoss: s.stopLoss,
        takeProfit: s.takeProfit,
        timestamp: s.timestamp,
        result: s.result,  // HIT, MISS, or PENDING
        profit: s.profit
      }))
    });
    
  } catch (err) {
    console.error('History error:', err);
    res.status(500).json({ error: 'Failed to fetch history' });
  }
});

// Get 10x scanner (top 10 coins analysis)
router.get('/scanner-10x', async (req, res) => {
  try {
    const { address } = req.query;
    
    // Check Guru tier required
    const access = await checkScannerAccess(address, req.db);
    if (access.tier !== 'GURU') {
      return res.status(403).json({ 
        error: '10x Scanner requires GURU tier (1000 CLAWNCH staked)',
        currentTier: access.tier,
        stakedAmount: await getStakedClawnch(address, req.db)
      });
    }
    
    // Top 10 coins by volume
    const topCoins = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'LINK', 'AVAX', 'MATIC'];
    
    const scans = [];
    for (const symbol of topCoins) {
      const analysis = await generateTechnicalAnalysis(symbol);
      const signalType = determineSignalType(analysis);
      
      scans.push({
        symbol,
        signal: signalType,
        analysis: {
          distanceFromEntry: analysis.distanceFromEntry,
          goldenPocket: analysis.goldenPocket,
          vwapDeviation: analysis.vwapDeviation,
          confidence: analysis.confidence
        },
        timestamp: new Date()
      });
    }
    
    // Track usage
    await req.db.recordScannerUsage(address, '10x');
    
    res.json({
      tier: 'GURU',
      scanTime: new Date(),
      coinsAnalyzed: scans.length,
      scans: scans.sort((a, b) => b.analysis.confidence - a.analysis.confidence) // Sort by confidence
    });
    
  } catch (err) {
    console.error('10x scanner error:', err);
    res.status(500).json({ error: 'Scanner failed' });
  }
});

// Helper functions - query database for staked amount
async function getStakedClawnch(address, db) {
  try {
    const stake = await db.getScannerStake(address);
    if (stake && stake.status === 'ACTIVE') {
      return stake.amount;
    }
    return 0;
  } catch (err) {
    console.error('Error getting staked amount:', err);
    return 0;
  }
}

async function getClawnchBalance(address) {
  try {
    const provider = new ethers.JsonRpcProvider('https://mainnet.base.org');
    const contract = new ethers.Contract(CLAWNCH_TOKEN, ['function balanceOf(address) view returns (uint256)'], provider);
    const balance = await contract.balanceOf(address);
    return Number(ethers.formatUnits(balance, 18));
  } catch (err) {
    console.error('Check CLAWNCH balance error:', err);
    return 0;
  }
}

async function checkScannerAccess(address, db) {
  const staked = await getStakedClawnch(address, db);
  const todaySignals = await db.getTodaySignalCount(address);
  
  if (staked >= SCANNER_TIERS.GURU.stake) {
    return { tier: 'GURU', canAccess: true, remaining: 'Unlimited' };
  } else if (staked >= SCANNER_TIERS.PRO.stake) {
    return { tier: 'PRO', canAccess: true, remaining: Math.max(0, 20 - todaySignals) };
  } else if (staked >= SCANNER_TIERS.BASIC.stake) {
    return { tier: 'BASIC', canAccess: true, remaining: Math.max(0, 5 - todaySignals) };
  }
  
  return { tier: 'NONE', canAccess: false, remaining: 0 };
}

async function generateTechnicalAnalysis(symbol) {
  // TODO: Integrate with real data source (OKX, etc.)
  // For now, return mock analysis
  
  const currentPrice = Math.random() * 100000;
  const entry = currentPrice * (0.98 + Math.random() * 0.04); // ±2% from current
  const distanceFromEntry = ((currentPrice - entry) / entry * 100).toFixed(2);
  
  return {
    entry: entry.toFixed(2),
    stopLoss: (entry * 0.97).toFixed(2),  // 3% stop
    takeProfit: (entry * 1.03).toFixed(2), // 3% target
    distanceFromEntry,
    goldenPocket: {
      zone: `${(entry * 0.618).toFixed(2)} - ${(entry * 0.65).toFixed(2)}`,
      description: '0.618-0.65 Fibonacci retracement'
    },
    vwapDeviation: {
      daily: `${(Math.random() * 3 - 1.5).toFixed(2)}σ`,
      weekly: `${(Math.random() * 4 - 2).toFixed(2)}σ`,
      interpretation: Math.random() > 0.5 ? 'Above VWAP (bullish)' : 'Below VWAP (bearish)'
    },
    keyLevels: [
      { price: (entry * 1.05).toFixed(2), type: 'resistance' },
      { price: (entry * 0.95).toFixed(2), type: 'support' }
    ],
    confidence: Math.floor(Math.random() * 30) + 70, // 70-99%
    reasoning: `VWAP deviation at ${Math.abs(distanceFromEntry)}% with Golden Pocket confluence. ${Math.random() > 0.5 ? 'Bullish' : 'Bearish'} momentum building.`
  };
}

function determineSignalType(analysis) {
  const isLong = analysis.distanceFromEntry > 0;
  const isSwing = Math.abs(analysis.distanceFromEntry) > 2; // >2% = swing
  
  return {
    direction: isLong ? 'LONG' : 'SHORT',
    style: isSwing ? 'SWING' : 'SCALP',
    timeframe: isSwing ? '4h-1d' : '15m-1h'
  };
}

// Tip Sniper Guru for good signals
router.post('/tip', async (req, res) => {
  try {
    const { 
      signalId,           // Which signal they're tipping for
      tipper,             // Wallet address
      amount,             // ZOID amount
      signature,
      message             // Optional thank you message
    } = req.body;
    
    // Verify signature
    const signMessage = `Tip Sniper Guru ${amount} ZOID for signal ${signalId} at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(signMessage, signature);
    
    if (recoveredAddress.toLowerCase() !== tipper.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Verify ZOID balance
    const balance = await getZoidBalance(tipper);
    if (balance < amount) {
      return res.status(400).json({ 
        error: 'Insufficient ZOID balance',
        balance,
        required: amount
      });
    }
    
    // Calculate distribution
    const burnAmount = Math.floor(amount * 0.25);  // 25% burn
    const guruAmount = amount - burnAmount;         // 75% to Sniper Guru
    
    // Get signal info
    const signal = await req.db.getSniperGuruSignal(signalId);
    if (!signal) {
      return res.status(404).json({ error: 'Signal not found' });
    }
    
    // Create tip record
    const tip = {
      id: `tip_${Date.now()}_${tipper.slice(0, 6)}`,
      signalId,
      tipper,
      amount,
      burnAmount,
      guruAmount,
      message: message || '',
      timestamp: new Date(),
      status: 'PENDING'  // Will be updated after on-chain transfer
    };
    
    await req.db.createTip(tip);
    
    // Track total tips for signal
    await req.db.incrementSignalTips(signalId, guruAmount);
    
    // Update Sniper Guru stats
    await req.db.updateSniperGuruTips(guruAmount, burnAmount);
    
    res.json({
      success: true,
      tipId: tip.id,
      amount,
      distribution: {
        toSniperGuru: guruAmount,
        toBurn: burnAmount,
        burnAddress: BURN_ADDRESS
      },
      message: `Tip sent! ${guruAmount} ZOID to Sniper Guru, ${burnAmount} ZOID burned.`,
      // TODO: Return actual tx hash after on-chain transfer
    });
    
  } catch (err) {
    console.error('Tip error:', err);
    res.status(500).json({ error: 'Tip failed' });
  }
});

// Get tip stats for Sniper Guru
router.get('/tips/stats', async (req, res) => {
  try {
    const stats = await req.db.getSniperGuruTipStats();
    
    res.json({
      totalTips: stats.totalTips,
      totalZoidTipped: stats.totalAmount,
      totalBurned: stats.totalBurned,
      totalToSniperGuru: stats.totalToGuru,
      topTippers: stats.topTippers,
      burnAddress: BURN_ADDRESS,
      burnPercentage: '25%'
    });
    
  } catch (err) {
    console.error('Tip stats error:', err);
    res.status(500).json({ error: 'Failed to fetch tip stats' });
  }
});

// Get tipper leaderboard
router.get('/tips/leaderboard', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 20;
    const leaderboard = await req.db.getTipperLeaderboard(limit);
    
    res.json({
      leaderboard: leaderboard.map((tipper, index) => ({
        rank: index + 1,
        address: tipper.address,
        ensName: tipper.ensName || null,
        totalTipped: tipper.total,
        tipCount: tipper.count,
        lastTip: tipper.lastTip,
        badges: getTipperBadges(tipper.total, tipper.count)
      })),
      updatedAt: new Date().toISOString()
    });
    
  } catch (err) {
    console.error('Leaderboard error:', err);
    res.status(500).json({ error: 'Failed to fetch leaderboard' });
  }
});

// Helper function to assign badges based on tipping activity
function getTipperBadges(totalAmount, tipCount) {
  const badges = [];
  
  if (totalAmount >= 1000) badges.push({ name: 'Whale', emoji: '🐋', color: 'gold' });
  else if (totalAmount >= 500) badges.push({ name: 'Big Tipper', emoji: '🦈', color: 'silver' });
  else if (totalAmount >= 100) badges.push({ name: 'Generous', emoji: '🐬', color: 'bronze' });
  
  if (tipCount >= 50) badges.push({ name: 'Regular', emoji: '💎', color: 'purple' });
  else if (tipCount >= 10) badges.push({ name: 'Supporter', emoji: '⭐', color: 'blue' });
  
  if (badges.length === 0) badges.push({ name: 'Newbie', emoji: '🌱', color: 'green' });
  
  return badges;
}

// Get tips for a specific signal
router.get('/tips/:signalId', async (req, res) => {
  try {
    const { signalId } = req.params;
    
    const tips = await req.db.getTipsForSignal(signalId);
    const signal = await req.db.getSniperGuruSignal(signalId);
    
    res.json({
      signalId,
      symbol: signal?.symbol,
      totalTips: tips.length,
      totalAmount: tips.reduce((sum, t) => sum + t.amount, 0),
      tips: tips.map(t => ({
        tipper: t.tipper,
        amount: t.amount,
        message: t.message,
        timestamp: t.timestamp
      }))
    });
    
  } catch (err) {
    console.error('Get tips error:', err);
    res.status(500).json({ error: 'Failed to fetch tips' });
  }
});

async function getZoidBalance(address) {
  try {
    const provider = new ethers.JsonRpcProvider('https://mainnet.base.org');
    const contract = new ethers.Contract(ZOID_TOKEN, ['function balanceOf(address) view returns (uint256)'], provider);
    const balance = await contract.balanceOf(address);
    return Number(ethers.formatUnits(balance, 18));
  } catch (err) {
    console.error('Check ZOID balance error:', err);
    return 0;
  }
}

// Fee claiming for Sniper Guru (similar to Clanker FeeLocker)
// Track fees earned from tips and staking

// Check claimable fees for a provider
router.get('/fees/:address', async (req, res) => {
  try {
    const { address } = req.params;
    
    // Get accumulated fees from database
    const fees = await req.db.getProviderFees(address);
    
    // Check on-chain claimable amount (if using FeeLocker pattern)
    const onChainFees = await checkOnChainFees(address);
    
    res.json({
      address,
      accumulatedFees: {
        tips: fees.tipFees || 0,        // From tip jar (75% of tips)
        staking: fees.stakingFees || 0,  // From staking rewards
        devShare: fees.devShare || 0,    // From unstake fees
        total: (fees.tipFees || 0) + (fees.stakingFees || 0) + (fees.devShare || 0)
      },
      onChainClaimable: onChainFees,
      lastClaim: fees.lastClaim,
      claimHistory: fees.claimHistory || []
    });
    
  } catch (err) {
    console.error('Get fees error:', err);
    res.status(500).json({ error: 'Failed to fetch fees' });
  }
});

// Claim accumulated fees
router.post('/claim', async (req, res) => {
  try {
    const { address, signature } = req.body;
    
    // Verify signature
    const message = `Claim fees for ${address} at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(message, signature);
    
    if (recoveredAddress.toLowerCase() !== address.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Get fees to claim
    const fees = await req.db.getProviderFees(address);
    const totalClaimable = (fees.tipFees || 0) + (fees.stakingFees || 0) + (fees.devShare || 0);
    
    if (totalClaimable <= 0) {
      return res.status(400).json({ error: 'No fees to claim' });
    }
    
    // Create claim record
    const claim = {
      id: `claim_${Date.now()}_${address.slice(0, 6)}`,
      address,
      amount: totalClaimable,
      breakdown: {
        tips: fees.tipFees,
        staking: fees.stakingFees,
        devShare: fees.devShare
      },
      timestamp: new Date(),
      status: 'PENDING',  // Will be updated after on-chain transfer
      txHash: null
    };
    
    await req.db.createFeeClaim(claim);
    
    // Reset accumulated fees
    await req.db.resetProviderFees(address);
    
    res.json({
      success: true,
      claimId: claim.id,
      amount: totalClaimable,
      breakdown: claim.breakdown,
      message: `${totalClaimable} ZOID ready for claim. Transfer will be processed within 24 hours.`,
      // TODO: Return actual tx hash after on-chain transfer
    });
    
  } catch (err) {
    console.error('Claim error:', err);
    res.status(500).json({ error: 'Failed to claim fees' });
  }
});

// Get claim history
router.get('/claims/:address', async (req, res) => {
  try {
    const { address } = req.params;
    const limit = parseInt(req.query.limit) || 20;
    
    const claims = await req.db.getFeeClaimHistory(address, limit);
    
    res.json({
      address,
      totalClaims: claims.length,
      totalClaimed: claims.reduce((sum, c) => sum + (c.status === 'COMPLETED' ? c.amount : 0), 0),
      claims: claims.map(c => ({
        id: c.id,
        amount: c.amount,
        breakdown: c.breakdown,
        timestamp: c.timestamp,
        status: c.status,
        txHash: c.txHash
      }))
    });
    
  } catch (err) {
    console.error('Get claims error:', err);
    res.status(500).json({ error: 'Failed to fetch claim history' });
  }
});

// Burn ZOID for dev allocation (similar to Clawnch burn-to-earn)
router.post('/burn', async (req, res) => {
  try {
    const { address, amount, signature } = req.body;
    
    // Verify signature
    const message = `Burn ${amount} ZOID for dev allocation at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(message, signature);
    
    if (recoveredAddress.toLowerCase() !== address.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Minimum burn: 1,000 ZOID
    const MIN_BURN = 1000;
    if (amount < MIN_BURN) {
      return res.status(400).json({ 
        error: `Minimum burn is ${MIN_BURN} ZOID`,
        minBurn: MIN_BURN
      });
    }
    
    // Check ZOID balance
    const balance = await getZoidBalance(address);
    if (balance < amount) {
      return res.status(400).json({ 
        error: 'Insufficient ZOID balance',
        balance,
        required: amount
      });
    }
    
    // Calculate allocation (similar to Clawnch formula)
    // 1,000 ZOID = 1% allocation (1B tokens)
    // Max 10% allocation (10B tokens) for 10,000+ ZOID
    const allocationPercent = Math.min(Math.floor(amount / 1000), 10);
    const tokenAllocation = allocationPercent * 1000000000; // 1B tokens per percent
    
    // Create burn record
    const burn = {
      id: `burn_${Date.now()}_${address.slice(0, 6)}`,
      address,
      amount,
      allocationPercent,
      tokenAllocation,
      burnTxHash: null, // Will be set after on-chain burn
      timestamp: new Date(),
      status: 'PENDING',
      usedForLaunch: false
    };
    
    await req.db.createBurn(burn);
    
    // Update total burned stats
    await req.db.updateBurnStats(amount, tokenAllocation);
    
    res.json({
      success: true,
      burnId: burn.id,
      burned: amount,
      allocation: {
        percent: `${allocationPercent}%`,
        tokens: tokenAllocation.toLocaleString()
      },
      burnAddress: BURN_ADDRESS,
      message: `Burn ${amount} ZOID to receive ${allocationPercent}% dev allocation (${tokenAllocation.toLocaleString()} tokens)`,
      nextStep: 'Include burnTxHash in your launch post within 24 hours'
    });
    
  } catch (err) {
    console.error('Burn error:', err);
    res.status(500).json({ error: 'Failed to process burn' });
  }
});

// Get burn stats
router.get('/burn/stats', async (req, res) => {
  try {
    const stats = await req.db.getBurnStats();
    
    res.json({
      totalBurned: stats.totalBurned,
      totalAllocations: stats.totalAllocations,
      totalTokenSupply: stats.totalTokenSupply,
      burnAddress: BURN_ADDRESS,
      rates: {
        '1%': '1,000 ZOID (1B tokens)',
        '2%': '2,000 ZOID (2B tokens)',
        '5%': '5,000 ZOID (5B tokens)',
        '10%': '10,000+ ZOID (10B tokens, capped)'
      },
      requirements: {
        minBurn: 1000,
        maxAllocation: '10%',
        timeWindow: '24 hours',
        walletMatch: 'Burn must be from same wallet as launch post'
      }
    });
    
  } catch (err) {
    console.error('Burn stats error:', err);
    res.status(500).json({ error: 'Failed to fetch burn stats' });
  }
});

// Get burn history for address
router.get('/burn/:address', async (req, res) => {
  try {
    const { address } = req.params;
    const burns = await req.db.getBurnsByAddress(address);
    
    res.json({
      address,
      totalBurned: burns.reduce((sum, b) => sum + b.amount, 0),
      totalAllocations: burns.reduce((sum, b) => sum + b.tokenAllocation, 0),
      burns: burns.map(b => ({
        id: b.id,
        amount: b.amount,
        allocationPercent: b.allocationPercent,
        tokenAllocation: b.tokenAllocation,
        status: b.status,
        usedForLaunch: b.usedForLaunch,
        timestamp: b.timestamp
      }))
    });
    
  } catch (err) {
    console.error('Get burns error:', err);
    res.status(500).json({ error: 'Failed to fetch burn history' });
  }
});

// Helper function to check on-chain fees (if using FeeLocker pattern)
async function checkOnChainFees(address) {
  try {
    // This would check a FeeLocker contract if we had one
    // For now, return 0
    return 0;
  } catch (err) {
    console.error('Check on-chain fees error:', err);
    return 0;
  }
}

module.exports = router;