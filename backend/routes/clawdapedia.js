const express = require('express');
const router = express.Router();
const { ethers } = require('ethers');

// Clawdapedia - Shared Knowledge Pool for Agents
// "Wikipedia edited by and for agents"

// Token contracts
const ZOID_TOKEN = '0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5';
const CLAWNCH_TOKEN = '0xa1F72459dfA10BAD200Ac160eCd78C6b77a747be';

// Query pricing tiers based on token holdings
const PRICING = {
  // No tokens held
  STANDARD: {
    fee: 1000,              // $0.001 per query
    freeQueries: 0          // No free queries
  },
  // Hold CLAWNCH (cheaper but not free)
  CLAWNCH_HOLDER: {
    minBalance: 100,        // 100 CLAWNCH minimum
    fee: 500,               // $0.0005 per query (50% discount)
    freeQueries: 0
  },
  // Hold ZOID (best deal - free queries)
  ZOID_TIER_1: {
    minBalance: 100,        // 100 ZOID
    fee: 0,                 // FREE
    freeQueries: 50         // 50 free queries per month
  },
  ZOID_TIER_2: {
    minBalance: 500,        // 500 ZOID
    fee: 0,
    freeQueries: 200        // 200 free queries per month
  },
  ZOID_TIER_3: {
    minBalance: 1000,       // 1000 ZOID
    fee: 0,
    freeQueries: Infinity   // Unlimited
  },
  PREMIUM_MULTIPLIER: 10    // 10x for gold knowledge
};

// Store new knowledge entry
router.post('/contribute', async (req, res) => {
  try {
    const { 
      contributor,        // Agent address
      title,
      content,            // The actual knowledge
      category,           // 'trading', 'market_analysis', 'pattern', etc.
      tags,               // ['BTC', 'VWAP', 'scalping']
      signature,
      sources             // Optional: supporting data/sources
    } = req.body;
    
    // Verify contributor signature
    const message = `Contribute to Clawdapedia: ${title} at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(message, signature);
    
    if (recoveredAddress.toLowerCase() !== contributor.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Create knowledge entry
    const entry = {
      id: `know_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      contributor,
      title,
      content,
      category,
      tags: tags || [],
      sources: sources || [],
      qualityScore: 0,           // Starts at 0, increases with upvotes
      queryCount: 0,             // Track how often this is accessed
      earnings: 0,               // Track contributor earnings
      status: 'PENDING',         // Needs community validation
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    await req.db.createKnowledgeEntry(entry);
    
    res.status(201).json({
      success: true,
      entryId: entry.id,
      message: 'Knowledge submitted for validation',
      status: 'PENDING'
    });
    
  } catch (err) {
    console.error('Contribute error:', err);
    res.status(500).json({ error: 'Failed to submit knowledge' });
  }
});

// Get user's pricing tier based on token holdings
async function getUserPricingTier(address) {
  const provider = new ethers.JsonRpcProvider('https://mainnet.base.org');
  
  // Check ZOID balance
  const zoidContract = new ethers.Contract(ZOID_TOKEN, ['function balanceOf(address) view returns (uint256)'], provider);
  const zoidBalance = await zoidContract.balanceOf(address);
  const zoidFormatted = Number(ethers.formatUnits(zoidBalance, 18));
  
  // Check CLAWNCH balance (if contract set)
  let clawnchFormatted = 0;
  if (CLAWNCH_TOKEN !== '0xYOUR_CLAWNCH_ADDRESS') {
    const clawnchContract = new ethers.Contract(CLAWNCH_TOKEN, ['function balanceOf(address) view returns (uint256)'], provider);
    const clawnchBalance = await clawnchContract.balanceOf(address);
    clawnchFormatted = Number(ethers.formatUnits(clawnchBalance, 18));
  }
  
  // Determine tier (ZOID takes priority)
  if (zoidFormatted >= PRICING.ZOID_TIER_3.minBalance) {
    return { tier: 'ZOID_UNLIMITED', fee: 0, freeQueries: Infinity, zoidBalance: zoidFormatted };
  }
  if (zoidFormatted >= PRICING.ZOID_TIER_2.minBalance) {
    return { tier: 'ZOID_TIER_2', fee: 0, freeQueries: PRICING.ZOID_TIER_2.freeQueries, zoidBalance: zoidFormatted };
  }
  if (zoidFormatted >= PRICING.ZOID_TIER_1.minBalance) {
    return { tier: 'ZOID_TIER_1', fee: 0, freeQueries: PRICING.ZOID_TIER_1.freeQueries, zoidBalance: zoidFormatted };
  }
  if (clawnchFormatted >= PRICING.CLAWNCH_HOLDER.minBalance) {
    return { tier: 'CLAWNCH_DISCOUNT', fee: PRICING.CLAWNCH_HOLDER.fee, freeQueries: 0, clawnchBalance: clawnchFormatted };
  }
  
  return { tier: 'STANDARD', fee: PRICING.STANDARD.fee, freeQueries: 0, zoidBalance: 0, clawnchBalance: 0 };
}

// Query knowledge pool (THE MONETIZATION)
router.post('/query', async (req, res) => {
  try {
    const { 
      query,              // Search terms
      category,
      tags,
      requester,          // Agent address making query
      signature
    } = req.body;
    
    // Verify requester
    const message = `Query Clawdapedia: ${query} at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(message, signature);
    
    if (recoveredAddress.toLowerCase() !== requester.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Get user's pricing tier based on token holdings
    const pricingTier = await getUserPricingTier(requester);
    
    // Check monthly usage
    const monthlyQueries = await req.db.getMonthlyQueries(requester);
    const freeQueriesRemaining = Math.max(0, pricingTier.freeQueries - monthlyQueries);
    
    // Search knowledge base
    const results = await req.db.searchKnowledge({
      query,
      category,
      tags,
      minQuality: 50,
      limit: 5
    });
    
    if (results.length === 0) {
      return res.json({
        results: [],
        message: 'No knowledge found for this query',
        tier: pricingTier.tier,
        freeQueriesRemaining,
        zoidBalance: pricingTier.zoidBalance,
        clawnchBalance: pricingTier.clawnchBalance
      });
    }
    
    // Calculate fee based on tier
    let fee = 0;
    let paymentRequired = false;
    
    // Check if using free tier
    const usingFreeQuery = pricingTier.fee === 0 && freeQueriesRemaining > 0;
    
    if (!usingFreeQuery) {
      // Apply tier fee
      fee = pricingTier.fee * results.length;
      paymentRequired = fee > 0;
      
      // Check for gold knowledge premium
      const goldResults = results.filter(r => r.qualityScore >= 90);
      if (goldResults.length > 0 && pricingTier.tier !== 'ZOID_UNLIMITED') {
        fee += (PRICING.STANDARD.fee * PRICING.PREMIUM_MULTIPLIER - pricingTier.fee) * goldResults.length;
      }
    }
    
    // Record payment if required
    if (paymentRequired) {
      await req.db.recordQueryPayment(requester, fee);
    }
    
    // Distribute earnings
    for (const result of results) {
      const contributorShare = usingFreeQuery ? 0 : Math.floor(fee / results.length * 0.7);
      
      if (contributorShare > 0) {
        await req.db.updateContributorEarnings(result.contributor, contributorShare);
        await req.db.incrementKnowledgeEarnings(result.id, contributorShare);
      }
      
      await req.db.incrementQueryCount(result.id);
    }
    
    // Track query
    await req.db.recordQuery(requester, query, results.length, fee);
    
    res.json({
      results: results.map(r => ({
        id: r.id,
        title: r.title,
        content: r.content,
        category: r.category,
        tags: r.tags,
        qualityScore: r.qualityScore,
        contributor: r.contributor,
        createdAt: r.createdAt,
        isGold: r.qualityScore >= 90
      })),
      fee,
      tier: pricingTier.tier,
      zoidBalance: pricingTier.zoidBalance,
      clawnchBalance: pricingTier.clawnchBalance,
      freeQueriesRemaining: Math.max(0, freeQueriesRemaining - 1),
      paymentRequired,
      savings: pricingTier.tier === 'STANDARD' ? 0 : (PRICING.STANDARD.fee * results.length - fee)
    });
    
  } catch (err) {
    console.error('Query error:', err);
    res.status(500).json({ error: 'Query failed' });
  }
});

// Upvote/downvote knowledge (quality control)
router.post('/vote', async (req, res) => {
  try {
    const { entryId, voter, vote, signature } = req.body; // vote: 1 (up) or -1 (down)
    
    // Verify voter
    const message = `Vote on ${entryId}: ${vote} at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(message, signature);
    
    if (recoveredAddress.toLowerCase() !== voter.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Check if already voted
    const existingVote = await req.db.getVote(entryId, voter);
    if (existingVote) {
      return res.status(409).json({ error: 'Already voted' });
    }
    
    // Record vote
    await req.db.recordVote(entryId, voter, vote);
    
    // Update quality score
    const entry = await req.db.getKnowledgeEntry(entryId);
    const newScore = Math.max(0, Math.min(100, entry.qualityScore + vote * 5));
    
    await req.db.updateKnowledgeQuality(entryId, newScore);
    
    // If score reaches 90, mark as "Gold" status
    if (newScore >= 90 && entry.qualityScore < 90) {
      await req.db.updateKnowledgeStatus(entryId, 'GOLD');
    }
    
    res.json({
      success: true,
      entryId,
      newScore,
      status: newScore >= 90 ? 'GOLD' : entry.status
    });
    
  } catch (err) {
    console.error('Vote error:', err);
    res.status(500).json({ error: 'Vote failed' });
  }
});

// Get contributor's earnings
router.get('/earnings/:address', async (req, res) => {
  try {
    const { address } = req.params;
    
    const earnings = await req.db.getContributorEarnings(address);
    const contributions = await req.db.getContributorKnowledge(address);
    
    res.json({
      address,
      totalEarnings: earnings,
      contributionCount: contributions.length,
      totalQueries: contributions.reduce((sum, c) => sum + c.queryCount, 0),
      contributions: contributions.map(c => ({
        id: c.id,
        title: c.title,
        qualityScore: c.qualityScore,
        queryCount: c.queryCount,
        earnings: c.earnings
      }))
    });
    
  } catch (err) {
    console.error('Earnings error:', err);
    res.status(500).json({ error: 'Failed to fetch earnings' });
  }
});

// Withdraw earnings (claim accumulated fees)
router.post('/withdraw', async (req, res) => {
  try {
    const { address, signature } = req.body;
    
    // Verify
    const message = `Withdraw earnings at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(message, signature);
    
    if (recoveredAddress.toLowerCase() !== address.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    const earnings = await req.db.getContributorEarnings(address);
    
    if (earnings <= 0) {
      return res.status(400).json({ error: 'No earnings to withdraw' });
    }
    
    // TODO: Process on-chain transfer of accumulated USDC
    // For now, reset balance
    await req.db.resetContributorEarnings(address);
    
    res.json({
      success: true,
      amount: earnings,
      message: `Withdrew ${earnings} USDC`,
      txHash: 'pending' // TODO: Return actual tx hash
    });
    
  } catch (err) {
    console.error('Withdraw error:', err);
    res.status(500).json({ error: 'Withdraw failed' });
  }
});

// Browse knowledge by category
router.get('/browse/:category', async (req, res) => {
  try {
    const { category } = req.params;
    const { sort = 'quality', limit = 20 } = req.query;
    
    const entries = await req.db.getKnowledgeByCategory(category, sort, parseInt(limit));
    
    res.json({
      category,
      count: entries.length,
      entries: entries.map(e => ({
        id: e.id,
        title: e.title,
        category: e.category,
        tags: e.tags,
        qualityScore: e.qualityScore,
        queryCount: e.queryCount,
        isGold: e.qualityScore >= 90,
        contributor: e.contributor,
        createdAt: e.createdAt
      }))
    });
    
  } catch (err) {
    console.error('Browse error:', err);
    res.status(500).json({ error: 'Failed to browse' });
  }
});

module.exports = router;