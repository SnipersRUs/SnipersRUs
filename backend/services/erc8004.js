/**
 * ERC-8004 Service for Signal Wars
 * 
 * Handles on-chain agent registration, karma sync, and reputation queries
 * on Base L2 network
 */

const { ethers } = require('ethers');

// Contract ABI
const CONTRACT_ABI = [
  // View functions
  'function agents(address) view returns (address owner, string name, string metadataURI, uint256 karma, uint256 totalSignals, uint256 wins, uint256 losses, uint256 registeredAt, bool isActive, uint8 agentType)',
  'function signals(uint256) view returns (uint256 id, address agent, string symbol, uint8 direction, uint256 entryPrice, uint256 targetPrice, uint256 stopLoss, uint256 timestamp, uint8 status, uint256 karmaAtSubmission)',
  'function agentSignals(address) view returns (uint256[])',
  'function signalCounter() view returns (uint256)',
  'function isRegistered(address) view returns (bool)',
  'function getWinRate(address) view returns (uint256)',
  'function getLeaderboard(uint256) view returns (address[], uint256[])',
  
  // Write functions
  'function registerAgent(string name, string metadataURI, uint8 agentType)',
  'function submitSignal(string symbol, uint8 direction, uint256 entryPrice, uint256 targetPrice, uint256 stopLoss) returns (uint256)',
  'function resolveSignal(uint256 signalId, uint8 status)',
  'function updateKarma(address agent, int256 delta, string reason)',
  
  // Events
  'event AgentRegistered(address indexed agentAddress, string name, uint8 agentType, uint256 timestamp)',
  'event KarmaUpdated(address indexed agentAddress, int256 delta, uint256 newKarma, string reason)',
  'event SignalSubmitted(uint256 indexed signalId, address indexed agent, string symbol, uint8 direction, uint256 timestamp)',
  'event SignalResolved(uint256 indexed signalId, uint8 status, uint256 karmaAtResolution)'
];

// Contract addresses
const CONTRACTS = {
  mainnet: process.env.ERC8004_REGISTRY_MAINNET,
  sepolia: process.env.ERC8004_REGISTRY_SEPOLIA || '0x0000000000000000000000000000000000000000' // Placeholder
};

class ERC8004Service {
  constructor() {
    this.isMainnet = process.env.NODE_ENV === 'production';
    this.contractAddress = this.isMainnet ? CONTRACTS.mainnet : CONTRACTS.sepolia;
    
    // Skip initialization if no contract address is set
    if (!this.contractAddress || this.contractAddress === '0x0000000000000000000000000000000000000000') {
      console.log('⚠️ ERC8004: No contract address configured, service disabled');
      this.contract = null;
      this.writeContract = null;
      return;
    }
    
    // Set up provider
    const rpcUrl = this.isMainnet 
      ? 'https://mainnet.base.org' 
      : 'https://sepolia.base.org';
    
    this.provider = new ethers.JsonRpcProvider(rpcUrl);
    
    // Contract instance for reads
    this.contract = new ethers.Contract(
      this.contractAddress,
      CONTRACT_ABI,
      this.provider
    );
    
    // Wallet for admin transactions
    if (process.env.PRIVATE_KEY) {
      this.wallet = new ethers.Wallet(process.env.PRIVATE_KEY, this.provider);
      this.writeContract = this.contract.connect(this.wallet);
    }
  }
  
  /**
   * Check if an address is registered as an agent on-chain
   */
  async isRegistered(address) {
    if (!this.contract) return false;
    try {
      const result = await this.contract.isRegistered(address);
      return result;
    } catch (error) {
      console.error('Error checking registration:', error);
      return false;
    }
  }
  
  /**
   * Get agent's on-chain reputation data
   */
  async getAgentReputation(address) {
    if (!this.contract) return null;
    try {
      const agent = await this.contract.agents(address);
      
      const winRate = await this.contract.getWinRate(address);
      
      return {
        address: agent.owner,
        name: agent.name,
        metadataURI: agent.metadataURI,
        karma: Number(agent.karma),
        totalSignals: Number(agent.totalSignals),
        wins: Number(agent.wins),
        losses: Number(agent.losses),
        winRate: Number(winRate),
        registeredAt: new Date(Number(agent.registeredAt) * 1000).toISOString(),
        isActive: agent.isActive,
        agentType: agent.agentType === 0 ? 'HUMAN' : 'AI',
        isOnChain: true
      };
    } catch (error) {
      console.error('Error fetching agent reputation:', error);
      return null;
    }
  }
  
  /**
   * Get on-chain leaderboard
   */
  async getLeaderboard(limit = 20) {
    try {
      const [addresses, karmaScores] = await this.contract.getLeaderboard(limit);
      
      const leaderboard = [];
      for (let i = 0; i < addresses.length; i++) {
        const agent = await this.getAgentReputation(addresses[i]);
        if (agent) {
          leaderboard.push({
            rank: i + 1,
            ...agent
          });
        }
      }
      
      return leaderboard;
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
      return [];
    }
  }
  
  /**
   * Sync off-chain karma to on-chain (admin only)
   */
  async syncKarma(address, offChainKarma, reason = 'Daily sync') {
    if (!this.writeContract) {
      throw new Error('Wallet not configured');
    }
    
    try {
      const onChainData = await this.getAgentReputation(address);
      if (!onChainData) {
        throw new Error('Agent not registered on-chain');
      }
      
      const delta = BigInt(offChainKarma) - BigInt(onChainData.karma);
      
      if (delta === 0n) {
        return { success: true, message: 'Karma already synced' };
      }
      
      // Submit transaction
      const tx = await this.writeContract.updateKarma(address, delta, reason);
      const receipt = await tx.wait();
      
      return {
        success: true,
        txHash: receipt.hash,
        delta: Number(delta),
        newKarma: offChainKarma
      };
    } catch (error) {
      console.error('Error syncing karma:', error);
      return { success: false, error: error.message };
    }
  }
  
  /**
   * Batch sync karma for multiple agents
   */
  async batchSyncKarma(agentsData) {
    const results = [];
    for (const agent of agentsData) {
      const result = await this.syncKarma(agent.address, agent.karma);
      results.push({
        address: agent.address,
        ...result
      });
    }
    return results;
  }
  
  /**
   * Get BaseScan URL for transaction or address
   */
  getBaseScanUrl(type, value) {
    const baseUrl = this.isMainnet ? 'https://basescan.org' : 'https://sepolia.basescan.org';
    
    switch (type) {
      case 'address':
        return `${baseUrl}/address/${value}`;
      case 'tx':
        return `${baseUrl}/tx/${value}`;
      case 'contract':
        return `${baseUrl}/address/${this.contractAddress}`;
      default:
        return baseUrl;
    }
  }
  
  /**
   * Format agent data for API response
   */
  formatAgentResponse(agent, includeLinks = true) {
    const response = {
      ...agent,
      erc8004: {
        isRegistered: agent.isOnChain,
        network: this.isMainnet ? 'base' : 'base-sepolia',
        contractAddress: this.contractAddress
      }
    };
    
    if (includeLinks) {
      response.erc8004.basescanUrl = this.getBaseScanUrl('address', agent.address);
      response.erc8004.contractUrl = this.getBaseScanUrl('contract');
    }
    
    return response;
  }
}

module.exports = ERC8004Service;
