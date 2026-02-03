// SubscriptionManager.sol - Smart contract for Discord access tiers
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract SubscriptionManager is Ownable, ReentrancyGuard {
    
    IERC20 public zoidToken;
    
    uint256 public constant HOLDER_THRESHOLD = 250 * 10**18; // $250 worth of ZOID
    uint256 public constant LIFETIME_PRICE = 333 * 10**6; // $333 USDC (6 decimals)
    uint256 public monthlyPrice = 25 * 10**6; // $25/month USDC (adjustable)
    
    enum Tier { NONE, HOLDER, MONTHLY, LIFETIME }
    
    struct Subscription {
        Tier tier;
        uint256 startTime;
        uint256 endTime;
        uint256 lastPayment;
    }
    
    mapping(address => Subscription) public subscriptions;
    mapping(address => bool) public verifiedAgents;
    mapping(address => uint256) public agentReputation;
    
    event Subscribed(address indexed user, Tier tier, uint256 endTime);
    event Upgraded(address indexed user, Tier newTier);
    event Cancelled(address indexed user);
    event AgentRegistered(address indexed agent, uint256 initialReputation);
    event ReputationUpdated(address indexed agent, uint256 newReputation);
    
    // ZOID Token on Base: 0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5
    constructor(address _zoidToken) {
        zoidToken = IERC20(_zoidToken);
    }
    
    // Check if user is a holder (holds $250+ ZOID)
    function isHolder(address user) public view returns (bool) {
        return zoidToken.balanceOf(user) >= HOLDER_THRESHOLD;
    }
    
    // Get user's current tier
    function getTier(address user) public view returns (Tier) {
        // Check if holder first
        if (isHolder(user)) {
            return Tier.HOLDER;
        }
        
        Subscription memory sub = subscriptions[user];
        
        // Check lifetime
        if (sub.tier == Tier.LIFETIME) {
            return Tier.LIFETIME;
        }
        
        // Check active monthly subscription
        if (sub.tier == Tier.MONTHLY && block.timestamp < sub.endTime) {
            return Tier.MONTHLY;
        }
        
        return Tier.NONE;
    }
    
    // Subscribe as monthly payer
    function subscribeMonthly() external nonReentrant {
        require(getTier(msg.sender) == Tier.NONE, "Already have access");
        
        // Transfer USDC (assumes approval)
        IERC20 usdc = IERC20(0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913); // Base USDC
        require(usdc.transferFrom(msg.sender, address(this), monthlyPrice), "Payment failed");
        
        subscriptions[msg.sender] = Subscription({
            tier: Tier.MONTHLY,
            startTime: block.timestamp,
            endTime: block.timestamp + 30 days,
            lastPayment: block.timestamp
        });
        
        emit Subscribed(msg.sender, Tier.MONTHLY, block.timestamp + 30 days);
    }
    
    // Buy lifetime access
    function buyLifetime() external nonReentrant {
        require(getTier(msg.sender) != Tier.LIFETIME, "Already lifetime");
        
        IERC20 usdc = IERC20(0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913);
        require(usdc.transferFrom(msg.sender, address(this), LIFETIME_PRICE), "Payment failed");
        
        subscriptions[msg.sender] = Subscription({
            tier: Tier.LIFETIME,
            startTime: block.timestamp,
            endTime: type(uint256).max,
            lastPayment: block.timestamp
        });
        
        emit Subscribed(msg.sender, Tier.LIFETIME, type(uint256).max);
    }
    
    // Renew monthly subscription
    function renewMonthly() external nonReentrant {
        Subscription storage sub = subscriptions[msg.sender];
        require(sub.tier == Tier.MONTHLY, "Not monthly subscriber");
        
        IERC20 usdc = IERC20(0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913);
        require(usdc.transferFrom(msg.sender, address(this), monthlyPrice), "Payment failed");
        
        sub.endTime = block.timestamp + 30 days;
        sub.lastPayment = block.timestamp;
        
        emit Subscribed(msg.sender, Tier.MONTHLY, sub.endTime);
    }
    
    // Admin: Register a verified agent
    function registerAgent(address agent) external onlyOwner {
        require(!verifiedAgents[agent], "Already registered");
        verifiedAgents[agent] = true;
        agentReputation[agent] = 100; // Start with 100 reputation
        emit AgentRegistered(agent, 100);
    }
    
    // Update agent reputation (can be positive or negative)
    function updateReputation(address agent, int256 delta) external onlyOwner {
        require(verifiedAgents[agent], "Not a verified agent");
        
        if (delta > 0) {
            agentReputation[agent] += uint256(delta);
        } else {
            uint256 absDelta = uint256(-delta);
            if (agentReputation[agent] > absDelta) {
                agentReputation[agent] -= absDelta;
            } else {
                agentReputation[agent] = 0;
            }
        }
        
        emit ReputationUpdated(agent, agentReputation[agent]);
    }
    
    // Check if address has Discord access
    function hasDiscordAccess(address user) external view returns (bool) {
        return getTier(user) != Tier.NONE;
    }
    
    // Admin: Update monthly price
    function setMonthlyPrice(uint256 newPrice) external onlyOwner {
        monthlyPrice = newPrice;
    }
    
    // Admin: Withdraw funds
    function withdraw(address token) external onlyOwner {
        IERC20(token).transfer(owner(), IERC20(token).balanceOf(address(this)));
    }
}