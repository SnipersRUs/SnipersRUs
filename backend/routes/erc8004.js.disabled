/**
 * ERC-8004 Routes
 * 
 * Endpoints for on-chain agent registration and reputation
 */

const express = require('express');
const router = express.Router();
const ERC8004Service = require('../services/erc8004');

// Lazy initialization - only create service when needed
let erc8004 = null;
function getService() {
  if (!erc8004) {
    try {
      erc8004 = new ERC8004Service();
    } catch (err) {
      console.error('ERC8004 service initialization failed:', err.message);
      erc8004 = null;
    }
  }
  return erc8004;
}

/**
 * GET /api/erc8004/health
 * Check if ERC-8004 service is available
 */
router.get('/health', async (req, res) => {
  const service = getService();
  if (!service) {
    return res.status(503).json({
      status: 'unavailable',
      service: 'erc8004',
      message: 'Contract not configured'
    });
  }
  res.json({
    status: 'ok',
    service: 'erc8004',
    network: service.isMainnet ? 'base-mainnet' : 'base-sepolia',
    contractAddress: service.contractAddress
  });
});

/**
 * GET /api/erc8004/reputation/:address
 * Get on-chain reputation for an agent
 */
router.get('/reputation/:address', async (req, res) => {
  try {
    const service = getService();
    if (!service) {
      return res.status(503).json({ error: 'ERC8004 service unavailable' });
    }
    
    const { address } = req.params;
    
    if (!address || !/^0x[a-fA-F0-9]{40}$/.test(address)) {
      return res.status(400).json({ error: 'Invalid address' });
    }
    
    const reputation = await service.getAgentReputation(address);
    
    if (!reputation) {
      return res.status(404).json({ 
        error: 'Agent not registered on-chain',
        address,
        isRegistered: false
      });
    }
    
    res.json({
      success: true,
      data: reputation
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
    const service = getService();
    if (!service) {
      return res.status(503).json({ error: 'ERC8004 service unavailable' });
    }
    
    const { address } = req.params;
    
    if (!address || !/^0x[a-fA-F0-9]{40}$/.test(address)) {
      return res.status(400).json({ error: 'Invalid address' });
    }
    
    const isRegistered = await service.isRegistered(address);
    
    res.json({
      success: true,
      address,
      isRegistered,
      network: service.isMainnet ? 'base' : 'base-sepolia'
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
    const service = getService();
    if (!service) {
      return res.status(503).json({ error: 'ERC8004 service unavailable' });
    }
    
    const limit = Math.min(parseInt(req.query.limit) || 20, 100);
    
    const leaderboard = await service.getLeaderboard(limit);
    
    res.json({
      success: true,
      data: leaderboard,
      count: leaderboard.length,
      network: service.isMainnet ? 'base' : 'base-sepolia'
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
    const service = getService();
    if (!service) {
      return res.status(503).json({ error: 'ERC8004 service unavailable' });
    }
    
    const { address, karma } = req.body;
    
    if (!address || !/^0x[a-fA-F0-9]{40}$/.test(address)) {
      return res.status(400).json({ error: 'Invalid address' });
    }
    
    if (typeof karma !== 'number' || karma < 0) {
      return res.status(400).json({ error: 'Invalid karma value' });
    }
    
    // TODO: Add admin authentication
    // if (!req.isAdmin) return res.status(403).json({ error: 'Unauthorized' });
    
    const result = await service.syncKarma(address, karma);
    
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
    const service = getService();
    if (!service) {
      return res.status(503).json({ error: 'ERC8004 service unavailable' });
    }
    
    const { agents } = req.body;
    
    if (!Array.isArray(agents)) {
      return res.status(400).json({ error: 'Invalid agents array' });
    }
    
    // TODO: Add admin authentication
    
    const results = await service.batchSyncKarma(agents);
    
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
  const service = getService();
  if (!service) {
    return res.json({
      standard: 'ERC-8004',
      description: 'On-chain agent identity and reputation registry',
      status: 'unavailable',
      message: 'Contract not configured',
      features: [
        'On-chain agent registration',
        'Portable karma/reputation',
        'Immutable signal history',
        'Trustless verification'
      ]
    });
  }
  
  res.json({
    standard: 'ERC-8004',
    description: 'On-chain agent identity and reputation registry',
    network: {
      name: service.isMainnet ? 'Base Mainnet' : 'Base Sepolia',
      chainId: service.isMainnet ? 8453 : 84532
    },
    contract: {
      address: service.contractAddress
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
