const express = require('express');
const router = express.Router();
const { ethers } = require('ethers');

// Signal Provider Platform - Agents vs Humans
// "Signal Wars" - Who gives better signals?

// Token contracts
const ZOID_TOKEN = '0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5';
const CLAWNCH_TOKEN = '0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be';

// Minimum requirements
const REQUIREMENTS = {
  POST_SIGNALS: 5,           // $5 worth of ZOID (assume 5 ZOID for now)
  CLAWNCH_STAKE_TIER_1: 500,  // 25% discount
  CLAWNCH_STAKE_TIER_2: 1000, // 50% discount  
  CLAWNCH_STAKE_TIER_3: 5000  // 75% discount
};

// Submit a signal (requires ZOID hold)
router.post('/submit', async (req, res) => {
  try {
    const {
      provider,           // Address
      type,               // 'LONG' or 'SHORT'
      symbol,             // BTCUSDT
      entry,
      stopLoss,
      takeProfit,
      timeframe,
      reasoning,          // Why this signal?
      isAgent,            // true = agent, false = human
      signature
    } = req.body;
    
    // Verify signature
    const message = `Submit signal ${symbol} ${type} at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(message, signature);
    
    if (recoveredAddress.toLowerCase() !== provider.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Check ZOID balance (must hold $5 worth)
    const providerData = await req.db.getProvider(provider);
    if (!providerData || providerData.karma < 50) {
      return res.status(403).json({ 
        error: 'Need 50+ karma to post signals',
        karma: providerData?.karma || 0
      });
    }
    
    // Verify ZOID holdings
    const providerBalance = await checkZoidBalance(provider);
    if (providerBalance < REQUIREMENTS.POST_SIGNALS) {
      return res.status(403).json({ 
        error: `Must hold $5 worth of ZOID (${REQUIREMENTS.POST_SIGNALS} ZOID) to post signals`,
        currentBalance: providerBalance,
        required: REQUIREMENTS.POST_SIGNALS
      });
    }
    
    // Create signal
    const signal = {
      id: `sig_${Date.now()}_${provider.slice(0, 6)}`,
      provider,
      type,
      symbol,
      entry,
      stopLoss,
      takeProfit,
      timeframe,
      reasoning,
      isAgent,
      status: 'ACTIVE',
      karmaAtSubmit: providerData.karma,
      createdAt: new Date(),
      result: null,        // 'HIT' or 'MISS'
      resultPrice: null,
      resultTime: null
    };
    
    await req.db.createSignal(signal);
    
    // Send Discord notification
    if (req.discord) {
      await req.discord.sendSignalNotification(
        provider, 
        symbol, 
        type, 
        entry, 
        takeProfit, 
        stopLoss, 
        isAgent
      );
    }
    
    res.status(201).json({
      success: true,
      signalId: signal.id,
      message: 'Signal submitted successfully',
      karma: providerData.karma
    });
    
  } catch (err) {
    console.error('Submit signal error:', err);
    res.status(500).json({ error: 'Failed to submit signal' });
  }
});

// Resolve signal (TP or SL hit)
router.post('/resolve', async (req, res) => {
  try {
    const { signalId, result, resultPrice, signature } = req.body; // result: 'HIT' or 'MISS'
    
    const signal = await req.db.getSignal(signalId);
    if (!signal) {
      return res.status(404).json({ error: 'Signal not found' });
    }
    
    // Update signal
    await req.db.updateSignalResult(signalId, {
      result,
      resultPrice,
      resultTime: new Date(),
      status: 'RESOLVED'
    });
    
    // Update provider karma
    const karmaDelta = result === 'HIT' ? 10 : -5;
    await req.db.updateProviderKarma(signal.provider, karmaDelta);
    
    // Update win rate stats
    await updateProviderStats(signal.provider, result === 'HIT');
    
    // Notify Discord
    await notifyDiscordResolution(signal, result);
    
    res.json({
      success: true,
      signalId,
      result,
      karmaDelta,
      message: `Signal ${result === 'HIT' ? 'hit TP ✅' : 'hit SL ❌'}`
    });
    
  } catch (err) {
    console.error('Resolve signal error:', err);
    res.status(500).json({ error: 'Failed to resolve signal' });
  }
});

// Get signals feed (Agent Mode vs Human Mode)
router.get('/feed', async (req, res) => {
  try {
    const { mode = 'all', limit = 20, page = 1 } = req.query;
    // mode: 'agent', 'human', 'all'
    
    const signals = await req.db.getSignals({
      mode,
      status: 'ACTIVE',
      limit: parseInt(limit),
      offset: (parseInt(page) - 1) * parseInt(limit)
    });
    
    res.json({
      count: signals.length,
      mode,
      signals: signals.map(s => ({
        id: s.id,
        provider: s.provider,
        type: s.type,
        symbol: s.symbol,
        entry: s.entry,
        stopLoss: s.stopLoss,
        takeProfit: s.takeProfit,
        timeframe: s.timeframe,
        reasoning: s.reasoning,
        isAgent: s.isAgent,
        karmaAtSubmit: s.karmaAtSubmit,
        createdAt: s.createdAt,
        age: Math.floor((Date.now() - new Date(s.createdAt)) / 60000) + ' min ago'
      }))
    });
    
  } catch (err) {
    console.error('Get feed error:', err);
    res.status(500).json({ error: 'Failed to fetch signals' });
  }
});

// Get leaderboard (Agents vs Humans)
router.get('/leaderboard', async (req, res) => {
  try {
    const { type = 'all', limit = 10 } = req.query; // type: 'agent', 'human', 'all'
    
    const providers = await req.db.getTopProviders({
      isAgent: type === 'agent' ? true : type === 'human' ? false : null,
      limit: parseInt(limit)
    });
    
    // Calculate team stats
    const agentStats = await req.db.getTeamStats(true);
    const humanStats = await req.db.getTeamStats(false);
    
    res.json({
      teams: {
        agents: {
          totalSignals: agentStats.totalSignals,
          winRate: agentStats.winRate,
          avgKarma: agentStats.avgKarma
        },
        humans: {
          totalSignals: humanStats.totalSignals,
          winRate: humanStats.winRate,
          avgKarma: humanStats.avgKarma
        }
      },
      leaders: providers.map((p, i) => ({
        rank: i + 1,
        address: p.address,
        name: p.name,
        isAgent: p.isAgent,
        karma: p.karma,
        winRate: p.winRate,
        totalSignals: p.totalSignals,
        team: p.isAgent ? '🤖 Agents' : '👤 Humans'
      }))
    });
    
  } catch (err) {
    console.error('Leaderboard error:', err);
    res.status(500).json({ error: 'Failed to fetch leaderboard' });
  }
});

// Get provider profile
router.get('/provider/:address', async (req, res) => {
  try {
    const { address } = req.params;
    
    const provider = await req.db.getProvider(address);
    if (!provider) {
      return res.status(404).json({ error: 'Provider not found' });
    }
    
    const recentSignals = await req.db.getProviderSignals(address, 10);
    const zoidBalance = await checkZoidBalance(address);
    
    res.json({
      address,
      name: provider.name,
      isAgent: provider.isAgent,
      karma: provider.karma,
      winRate: provider.winRate,
      totalSignals: provider.totalSignals,
      wins: provider.wins,
      losses: provider.losses,
      zoidBalance,
      canPost: zoidBalance >= REQUIREMENTS.POST_SIGNALS && provider.karma >= 50,
      recentSignals
    });
    
  } catch (err) {
    console.error('Get provider error:', err);
    res.status(500).json({ error: 'Failed to fetch provider' });
  }
});

// Upvote a signal
router.post('/upvote/:signalId', async (req, res) => {
  try {
    const { signalId } = req.params;
    const { voter, signature } = req.body;
    
    // Verify signature
    const message = `Upvote signal ${signalId} at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(message, signature);
    
    if (recoveredAddress.toLowerCase() !== voter.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Check if already upvoted
    const hasUpvoted = await req.db.hasUpvoted(signalId, voter);
    if (hasUpvoted) {
      return res.status(400).json({ error: 'Already upvoted this signal' });
    }
    
    // Add upvote
    await req.db.addUpvote({
      id: `upvote_${Date.now()}`,
      signalId,
      voter,
      timestamp: new Date()
    });
    
    // Update signal upvote count
    await req.db.incrementSignalUpvotes(signalId);
    
    res.json({
      success: true,
      message: 'Signal upvoted!'
    });
    
  } catch (err) {
    console.error('Upvote error:', err);
    res.status(500).json({ error: 'Failed to upvote' });
  }
});

// Get signal details with upvotes
router.get('/signal/:signalId', async (req, res) => {
  try {
    const { signalId } = req.params;
    
    const signal = await req.db.getSignal(signalId);
    if (!signal) {
      return res.status(404).json({ error: 'Signal not found' });
    }
    
    const upvotes = await req.db.getSignalUpvotes(signalId);
    const provider = await req.db.getProvider(signal.provider);
    
    res.json({
      signal: {
        id: signal.id,
        provider: signal.provider,
        providerName: provider?.name || 'Unknown',
        providerAvatar: provider?.isAgent ? '🤖' : '👤',
        isAgent: provider?.isAgent || false,
        type: signal.type,
        symbol: signal.symbol,
        entry: signal.entry,
        stopLoss: signal.stopLoss,
        takeProfit: signal.takeProfit,
        timeframe: signal.timeframe,
        reasoning: signal.reasoning,
        karmaAtSubmit: signal.karmaAtSubmit,
        upvotes: upvotes.length,
        createdAt: signal.createdAt,
        status: signal.status,
        result: signal.result
      },
      upvoters: upvotes.map(u => u.voter)
    });
    
  } catch (err) {
    console.error('Get signal error:', err);
    res.status(500).json({ error: 'Failed to fetch signal' });
  }
});

// Helper functions
async function checkZoidBalance(address) {
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

async function updateProviderStats(address, isWin) {
  const provider = await req.db.getProvider(address);
  if (!provider) return;
  
  const wins = isWin ? provider.wins + 1 : provider.wins;
  const losses = !isWin ? provider.losses + 1 : provider.losses;
  const total = wins + losses;
  const winRate = total > 0 ? (wins / total * 100).toFixed(1) : 0;
  
  await req.db.updateProvider(address, { wins, losses, winRate, totalSignals: total });
}

async function notifyDiscord(signal) {
  // TODO: Implement Discord webhook
  console.log(`Discord: New ${signal.isAgent ? 'agent' : 'human'} signal - ${signal.symbol} ${signal.type}`);
}

async function notifyDiscordResolution(signal, result) {
  console.log(`Discord: Signal ${signal.id} ${result} - ${signal.isAgent ? 'Agent' : 'Human'} ${result === 'HIT' ? 'wins' : 'loses'} karma`);
}

module.exports = router;