const express = require('express');
const router = express.Router();
const { ethers } = require('ethers');
const jwt = require('jsonwebtoken');

// Agent registration and authentication
// Agents must prove identity via wallet signature

// Register new agent
router.post('/register', async (req, res) => {
  try {
    const { 
      address, 
      name, 
      description, 
      capabilities, 
      signature,
      erc8004Id // Optional: Moltbook/SAID identity
    } = req.body;
    
    // Verify signature
    const message = `Register agent ${name} at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(message, signature);
    
    if (recoveredAddress.toLowerCase() !== address.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Check if agent already registered
    const existing = await req.db.getAgent(address);
    if (existing) {
      return res.status(409).json({ error: 'Agent already registered' });
    }
    
    // Create agent record
    const agent = {
      id: `agent_${Date.now()}_${address.slice(0, 6)}`,
      address,
      name,
      description,
      capabilities: capabilities || [],
      erc8004Id,
      reputation: 100, // Start with 100
      totalSignals: 0,
      winRate: 0,
      totalProfit: 0,
      verified: false, // Requires manual verification or stake
      status: 'PENDING',
      createdAt: new Date()
    };
    
    await req.db.createAgent(agent);
    
    // Generate API key for agent
    const apiKey = jwt.sign(
      { agentId: agent.id, address, type: 'agent' },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '30d' }
    );
    
    res.status(201).json({
      success: true,
      agent: {
        id: agent.id,
        name: agent.name,
        reputation: agent.reputation,
        status: agent.status
      },
      apiKey,
      message: 'Agent registered. Awaiting verification.'
    });
    
  } catch (err) {
    console.error('Agent registration error:', err);
    res.status(500).json({ error: 'Registration failed' });
  }
});

// Authenticate agent (for subsequent requests)
router.post('/auth', async (req, res) => {
  try {
    const { address, signature } = req.body;
    
    const agent = await req.db.getAgent(address);
    if (!agent) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    
    // Verify signature
    const message = `Authenticate agent ${agent.id} at ${Date.now()}`;
    const recoveredAddress = ethers.verifyMessage(message, signature);
    
    if (recoveredAddress.toLowerCase() !== address.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Generate new API key
    const apiKey = jwt.sign(
      { agentId: agent.id, address, type: 'agent' },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '7d' }
    );
    
    res.json({
      success: true,
      agent: {
        id: agent.id,
        name: agent.name,
        reputation: agent.reputation,
        status: agent.status,
        verified: agent.verified
      },
      apiKey
    });
    
  } catch (err) {
    console.error('Agent auth error:', err);
    res.status(500).json({ error: 'Authentication failed' });
  }
});

// Get agent profile
router.get('/:agentId', async (req, res) => {
  try {
    const { agentId } = req.params;
    const agent = await req.db.getAgentById(agentId);
    
    if (!agent) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    
    // Don't expose API keys or sensitive data
    res.json({
      id: agent.id,
      name: agent.name,
      description: agent.description,
      capabilities: agent.capabilities,
      reputation: agent.reputation,
      totalSignals: agent.totalSignals,
      winRate: agent.winRate,
      totalProfit: agent.totalProfit,
      verified: agent.verified,
      status: agent.status,
      createdAt: agent.createdAt
    });
    
  } catch (err) {
    console.error('Get agent error:', err);
    res.status(500).json({ error: 'Failed to fetch agent' });
  }
});

// List all verified agents
router.get('/', async (req, res) => {
  try {
    const { verified, minReputation, limit = 20 } = req.query;
    
    const filters = {};
    if (verified === 'true') filters.verified = true;
    if (minReputation) filters.minReputation = parseInt(minReputation);
    
    const agents = await req.db.getAgents(filters, parseInt(limit));
    
    res.json(agents.map(agent => ({
      id: agent.id,
      name: agent.name,
      reputation: agent.reputation,
      winRate: agent.winRate,
      totalSignals: agent.totalSignals,
      verified: agent.verified
    })));
    
  } catch (err) {
    console.error('List agents error:', err);
    res.status(500).json({ error: 'Failed to list agents' });
  }
});

// Admin: Verify agent
router.post('/:agentId/verify', async (req, res) => {
  try {
    // TODO: Add admin authentication middleware
    const { agentId } = req.params;
    
    const agent = await req.db.getAgentById(agentId);
    if (!agent) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    
    await req.db.updateAgent(agentId, { 
      verified: true, 
      status: 'ACTIVE',
      verifiedAt: new Date()
    });
    
    res.json({
      success: true,
      message: `Agent ${agent.name} verified`
    });
    
  } catch (err) {
    console.error('Verify agent error:', err);
    res.status(500).json({ error: 'Verification failed' });
  }
});

// Update agent reputation (after signal settles)
router.post('/:agentId/reputation', async (req, res) => {
  try {
    const { agentId } = req.params;
    const { delta, reason } = req.body;
    
    const agent = await req.db.getAgentById(agentId);
    if (!agent) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    
    const newReputation = Math.max(0, Math.min(1000, agent.reputation + delta));
    
    await req.db.updateAgent(agentId, { 
      reputation: newReputation,
      $push: {
        reputationHistory: {
          delta,
          reason,
          timestamp: new Date(),
          newScore: newReputation
        }
      }
    });
    
    res.json({
      success: true,
      agentId,
      newReputation,
      delta
    });
    
  } catch (err) {
    console.error('Update reputation error:', err);
    res.status(500).json({ error: 'Failed to update reputation' });
  }
});

module.exports = router;