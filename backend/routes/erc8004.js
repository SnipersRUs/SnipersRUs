/**
 * ERC-8004 Routes
 * 
 * Endpoints for on-chain agent registration and reputation
 */

const express = require('express');
const router = express.Router();
const ERC8004Service = require('../services/erc8004');

const erc8004 = new ERC8004Service();

/**
 * GET /api/erc8004/health
 * Check if ERC-8004 service is available
 */
router.get('/health', async (req, res) => {
  res.json({
    status: 'ok',
    service: 'erc8004',
    network: erc8004.isMainnet ? 'base-mainnet' : 'base-sepolia',
    contractAddress: erc8004.contractAddress
  });
});

/**
 * GET /api/erc8004/reputation/:address
 * Get on-chain reputation for an agent
 */
router.get('/reputation/:address', async (req, res) => {
  try {
    const { address } = req.params;
    
    if (!address || !/^0x[a-fA-F0-9]{40}$/.test(address)) {
      return res.status(400).json({ error: 'Invalid address' });
    }
    
    const reputation = await erc8004.getAgentReputation(address);
    
    if (!reputation) {
      return res.status(404).json({ 
        error: 'Agent not registered on-chain',
        address,
        isRegistered: false
      });
    }
    
    res.json({
      success: true,
      data: erc8004.formatAgentResponse(reputation)
    });
  } catch (error) {
    console.error('Error fetching reputation:', error);
    res.status(500).json({ error: 'Failed to fetch reputation' });
  }
});

/**
 * GET /api/erc8004/verify/:address
 * Check if address is registered on-chain
 */
router.get('/verify/:address', async (req, res) => {
  try {
    const { address } = req.params;
    
    if (!address || !/^0x[a-fA-F0-9]{40}$/.test(address)) {
      return res.status(400).json({ error: 'Invalid address' });
    }
    
    const isRegistered = await erc8004.isRegistered(address);
    
    res.json({
      success: true,
      address,
      isRegistered,
      network: erc8004.isMainnet ? 'base' : 'base-sepolia',
      basescanUrl: erc8004.getBaseScanUrl('address', address),
      contractUrl: erc8004.getBaseScanUrl('contract')
    });
  } catch (error) {
    console.error('Error verifying address:', error);
    res.status(500).json({ error: 'Failed to verify address' });
  }
});

/**
 * GET /api/erc8004/leaderboard
 * Get on-chain leaderboard
 */
router.get('/leaderboard', async (req, res) => {
  try {
    const limit = Math.min(parseInt(req.query.limit) || 20, 100);
    
    const leaderboard = await erc8004.getLeaderboard(limit);
    
    res.json({
      success: true,
      data: leaderboard.map(agent => erc8004.formatAgentResponse(agent)),
      count: leaderboard.length,
      network: erc8004.isMainnet ? 'base' : 'base-sepolia'
    });
  } catch (error) {
    console.error('Error fetching leaderboard:', error);
    res.status(500).json({ error: 'Failed to fetch leaderboard' });
  }
});

/**
 * POST /api/erc8004/sync-karma
 * Sync off-chain karma to on-chain (admin only)
 * 
 * Body: { address: string, karma: number }
 */
router.post('/sync-karma', async (req, res) => {
  try {
    const { address, karma } = req.body;
    
    if (!address || !/^0x[a-fA-F0-9]{40}$/.test(address)) {
      return res.status(400).json({ error: 'Invalid address' });
    }
    
    if (typeof karma !== 'number' || karma < 0) {
      return res.status(400).json({ error: 'Invalid karma value' });
    }
    
    // TODO: Add admin authentication
    // if (!req.isAdmin) return res.status(403).json({ error: 'Unauthorized' });
    
    const result = await erc8004.syncKarma(address, karma);
    
    res.json({
      success: result.success,
      data: result
    });
  } catch (error) {
    console.error('Error syncing karma:', error);
    res.status(500).json({ error: 'Failed to sync karma' });
  }
});

/**
 * POST /api/erc8004/batch-sync
 * Sync multiple agents' karma (admin only)
 * 
 * Body: [{ address: string, karma: number }]
 */
router.post('/batch-sync', async (req, res) => {
  try {
    const { agents } = req.body;
    
    if (!Array.isArray(agents)) {
      return res.status(400).json({ error: 'Invalid agents array' });
    }
    
    // TODO: Add admin authentication
    
    const results = await erc8004.batchSyncKarma(agents);
    
    res.json({
      success: true,
      data: results,
      synced: results.filter(r => r.success).length,
      failed: results.filter(r => !r.success).length
    });
  } catch (error) {
    console.error('Error batch syncing:', error);
    res.status(500).json({ error: 'Failed to batch sync' });
  }
});

/**
 * GET /api/erc8004/info
 * Get ERC-8004 integration info
 */
router.get('/info', (req, res) => {
  res.json({
    standard: 'ERC-8004',
    description: 'On-chain agent identity and reputation registry',
    network: {
      name: erc8004.isMainnet ? 'Base Mainnet' : 'Base Sepolia',
      chainId: erc8004.isMainnet ? 8453 : 84532
    },
    contract: {
      address: erc8004.contractAddress,
      basescanUrl: erc8004.getBaseScanUrl('contract')
    },
    features: [
      'On-chain agent registration',
      'Portable karma/reputation',
      'Immutable signal history',
      'Trustless verification'
    ],
    endpoints: {
      reputation: '/api/erc8004/reputation/:address',
      verify: '/api/erc8004/verify/:address',
      leaderboard: '/api/erc8004/leaderboard',
      info: '/api/erc8004/info'
    }
  });
});

module.exports = router;
