const express = require('express');
const router = express.Router();
const { ethers } = require('ethers');

// ZOID Token contract (Base network)
const ZOID_TOKEN = '0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5';

// Subscription Manager contract
const SUBSCRIPTION_MANAGER = '0xYOUR_SUBSCRIPTION_MANAGER_ADDRESS'; // Deploy this

// ABI for balance checking
const ERC20_ABI = [
  'function balanceOf(address owner) view returns (uint256)',
  'function decimals() view returns (uint8)',
  'function symbol() view returns (string)'
];

// Tier definitions
const TIER_THRESHOLDS = {
  HOLDER: 250, // $250 worth of ZOID
  LIFETIME: 333 // $333 USDC
};

// Get user's tier based on holdings
router.get('/tier/:address', async (req, res) => {
  try {
    const { address } = req.params;
    
    if (!ethers.isAddress(address)) {
      return res.status(400).json({ error: 'Invalid address' });
    }
    
    const provider = new ethers.JsonRpcProvider('https://mainnet.base.org');
    
    // Get ZOID balance
    const zoidContract = new ethers.Contract(ZOID_TOKEN, ERC20_ABI, provider);
    const balance = await zoidContract.balanceOf(address);
    const decimals = await zoidContract.decimals();
    const balanceFormatted = Number(ethers.formatUnits(balance, decimals));
    
    // Check if holder (assuming 1 ZOID = $1 for now, adjust with price oracle)
    const zoidPrice = await getZoidPrice(); // Implement price oracle
    const holdingValue = balanceFormatted * zoidPrice;
    
    // Determine tier
    let tier = 'NONE';
    if (holdingValue >= TIER_THRESHOLDS.HOLDER) {
      tier = 'HOLDER';
    }
    
    // Check subscription status from database
    const subscription = await req.db.getSubscription(address);
    if (subscription) {
      if (subscription.tier === 'LIFETIME') {
        tier = 'LIFETIME';
      } else if (subscription.tier === 'MONTHLY' && new Date() < new Date(subscription.endTime)) {
        tier = 'MONTHLY';
      }
    }
    
    res.json({
      address,
      tier,
      holdingValue,
      zoidBalance: balanceFormatted,
      hasDiscordAccess: tier !== 'NONE',
      expiresAt: subscription?.endTime || null
    });
    
  } catch (err) {
    console.error('Get tier error:', err);
    res.status(500).json({ error: 'Failed to check tier' });
  }
});

// Get ZOID price (implement with CoinGecko or DEX)
async function getZoidPrice() {
  // TODO: Implement actual price feed
  // For now, return placeholder
  return 1.0; // Assume $1 per ZOID, replace with actual price oracle
}

// Verify holder status for Discord bot
router.post('/verify-holder', async (req, res) => {
  try {
    const { address, signature, message } = req.body;
    
    // Verify signature proves ownership
    const recoveredAddress = ethers.verifyMessage(message, signature);
    if (recoveredAddress.toLowerCase() !== address.toLowerCase()) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Check tier
    const provider = new ethers.JsonRpcProvider('https://mainnet.base.org');
    const zoidContract = new ethers.Contract(ZOID_TOKEN, ERC20_ABI, provider);
    const balance = await zoidContract.balanceOf(address);
    const decimals = await zoidContract.decimals();
    const balanceFormatted = Number(ethers.formatUnits(balance, decimals));
    
    const zoidPrice = await getZoidPrice();
    const holdingValue = balanceFormatted * zoidPrice;
    
    const isHolder = holdingValue >= TIER_THRESHOLDS.HOLDER;
    
    if (isHolder) {
      // Update or create subscription record
      await req.db.upsertSubscription({
        address,
        tier: 'HOLDER',
        startTime: new Date(),
        endTime: null, // Never expires as long as holding
        verifiedAt: new Date()
      });
    }
    
    res.json({
      verified: isHolder,
      holdingValue,
      zoidBalance: balanceFormatted,
      message: isHolder ? 'Holder verified' : 'Insufficient balance'
    });
    
  } catch (err) {
    console.error('Verify holder error:', err);
    res.status(500).json({ error: 'Verification failed' });
  }
});

// Create subscription (for paid tiers)
router.post('/subscribe', async (req, res) => {
  try {
    const { address, tier, txHash } = req.body;
    
    // Verify transaction on-chain
    const provider = new ethers.JsonRpcProvider('https://mainnet.base.org');
    const receipt = await provider.getTransactionReceipt(txHash);
    
    if (!receipt || receipt.status !== 1) {
      return res.status(400).json({ error: 'Transaction failed or not found' });
    }
    
    // Create subscription record
    const subscription = {
      address,
      tier,
      txHash,
      startTime: new Date(),
      endTime: tier === 'LIFETIME' ? null : new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
      verifiedAt: new Date()
    };
    
    await req.db.createSubscription(subscription);
    
    res.json({
      success: true,
      subscription,
      message: `${tier} subscription activated`
    });
    
  } catch (err) {
    console.error('Subscribe error:', err);
    res.status(500).json({ error: 'Subscription failed' });
  }
});

module.exports = router;