// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "openzeppelin-contracts/contracts/access/Ownable.sol";
import "openzeppelin-contracts/contracts/utils/ReentrancyGuard.sol";

/**
 * @title SignalWarsAgentRegistry
 * @dev ERC-8004 inspired agent registry for Signal Wars platform
 * @notice Stores agent reputation and signal history on Base L2
 */
contract SignalWarsAgentRegistry is Ownable(msg.sender), ReentrancyGuard {
    
    // ============ Structs ============
    
    struct Agent {
        address owner;
        string name;
        string metadataURI;
        uint256 karma;
        uint256 totalSignals;
        uint256 wins;
        uint256 losses;
        uint256 registeredAt;
        bool isActive;
        AgentType agentType;
    }
    
    struct Signal {
        uint256 id;
        address agent;
        string symbol;
        Direction direction;
        uint256 entryPrice;
        uint256 targetPrice;
        uint256 stopLoss;
        uint256 timestamp;
        SignalStatus status;
        uint256 karmaAtSubmission;
    }
    
    enum AgentType { HUMAN, AI }
    enum Direction { LONG, SHORT }
    enum SignalStatus { PENDING, HIT_TP, HIT_SL, EXPIRED }
    
    // ============ State Variables ============
    
    mapping(address => Agent) public agents;
    mapping(uint256 => Signal) public signals;
    mapping(address => uint256[]) public agentSignals;
    
    address[] public registeredAgents;
    uint256 public signalCounter;
    uint256 public constant MIN_KARMA_TO_REGISTER = 50;
    uint256 public constant KARMA_HIT_TP = 10;
    uint256 public constant KARMA_HIT_SL = 5;
    
    // ============ Events ============
    
    event AgentRegistered(
        address indexed agentAddress,
        string name,
        AgentType agentType,
        uint256 timestamp
    );
    
    event KarmaUpdated(
        address indexed agentAddress,
        int256 delta,
        uint256 newKarma,
        string reason
    );
    
    event SignalSubmitted(
        uint256 indexed signalId,
        address indexed agent,
        string symbol,
        Direction direction,
        uint256 timestamp
    );
    
    event SignalResolved(
        uint256 indexed signalId,
        SignalStatus status,
        uint256 karmaAtResolution
    );
    
    event AgentDeactivated(address indexed agentAddress);
    event AgentReactivated(address indexed agentAddress);
    
    // ============ Modifiers ============
    
    modifier onlyRegisteredAgent() {
        require(agents[msg.sender].registeredAt != 0, "Agent not registered");
        require(agents[msg.sender].isActive, "Agent not active");
        _;
    }
    
    modifier onlyOracle() {
        // For now, only owner can resolve signals
        // In production, this would be a dedicated oracle contract
        require(msg.sender == owner(), "Only oracle");
        _;
    }
    
    // ============ Registration ============
    
    /**
     * @notice Register a new agent on the platform
     * @param _name Agent display name
     * @param _metadataURI IPFS/Arweave URI with agent details
     * @param _agentType HUMAN or AI
     */
    function registerAgent(
        string calldata _name,
        string calldata _metadataURI,
        AgentType _agentType
    ) external nonReentrant {
        require(bytes(_name).length > 0, "Name required");
        require(agents[msg.sender].registeredAt == 0, "Already registered");
        
        agents[msg.sender] = Agent({
            owner: msg.sender,
            name: _name,
            metadataURI: _metadataURI,
            karma: 0,
            totalSignals: 0,
            wins: 0,
            losses: 0,
            registeredAt: block.timestamp,
            isActive: true,
            agentType: _agentType
        });
        
        registeredAgents.push(msg.sender);
        
        emit AgentRegistered(msg.sender, _name, _agentType, block.timestamp);
    }
    
    // ============ Signal Management ============
    
    /**
     * @notice Submit a new trading signal
     */
    function submitSignal(
        string calldata _symbol,
        Direction _direction,
        uint256 _entryPrice,
        uint256 _targetPrice,
        uint256 _stopLoss
    ) external onlyRegisteredAgent returns (uint256) {
        require(bytes(_symbol).length > 0, "Symbol required");
        require(_entryPrice > 0, "Invalid entry price");
        require(_targetPrice > 0, "Invalid target");
        require(_stopLoss > 0, "Invalid stop loss");
        
        signalCounter++;
        uint256 signalId = signalCounter;
        
        signals[signalId] = Signal({
            id: signalId,
            agent: msg.sender,
            symbol: _symbol,
            direction: _direction,
            entryPrice: _entryPrice,
            targetPrice: _targetPrice,
            stopLoss: _stopLoss,
            timestamp: block.timestamp,
            status: SignalStatus.PENDING,
            karmaAtSubmission: agents[msg.sender].karma
        });
        
        agentSignals[msg.sender].push(signalId);
        agents[msg.sender].totalSignals++;
        
        emit SignalSubmitted(
            signalId,
            msg.sender,
            _symbol,
            _direction,
            block.timestamp
        );
        
        return signalId;
    }
    
    /**
     * @notice Resolve a signal (hit TP or SL)
     * @dev Only callable by oracle/owner
     */
    function resolveSignal(
        uint256 _signalId,
        SignalStatus _status
    ) external onlyOracle {
        require(_status != SignalStatus.PENDING, "Invalid status");
        require(signals[_signalId].status == SignalStatus.PENDING, "Already resolved");
        
        Signal storage signal = signals[_signalId];
        signal.status = _status;
        
        address agentAddr = signal.agent;
        Agent storage agent = agents[agentAddr];
        
        if (_status == SignalStatus.HIT_TP) {
            agent.karma += KARMA_HIT_TP;
            agent.wins++;
            emit KarmaUpdated(agentAddr, int256(KARMA_HIT_TP), agent.karma, "Signal hit TP");
        } else if (_status == SignalStatus.HIT_SL) {
            // Prevent underflow
            if (agent.karma >= KARMA_HIT_SL) {
                agent.karma -= KARMA_HIT_SL;
            } else {
                agent.karma = 0;
            }
            agent.losses++;
            emit KarmaUpdated(agentAddr, -int256(KARMA_HIT_SL), agent.karma, "Signal hit SL");
        }
        
        emit SignalResolved(_signalId, _status, agent.karma);
    }
    
    // ============ Karma Management ============
    
    /**
     * @notice Update karma for any reason (manual adjustments, etc.)
     * @dev Only callable by owner for now
     */
    function updateKarma(
        address _agent,
        int256 _delta,
        string calldata _reason
    ) external onlyOwner {
        Agent storage agent = agents[_agent];
        require(agent.registeredAt != 0, "Agent not registered");
        
        if (_delta > 0) {
            agent.karma += uint256(_delta);
        } else {
            uint256 absDelta = uint256(-_delta);
            if (agent.karma >= absDelta) {
                agent.karma -= absDelta;
            } else {
                agent.karma = 0;
            }
        }
        
        emit KarmaUpdated(_agent, _delta, agent.karma, _reason);
    }
    
    // ============ View Functions ============
    
    /**
     * @notice Get full agent details
     */
    function getAgent(address _agent) external view returns (Agent memory) {
        return agents[_agent];
    }
    
    /**
     * @notice Calculate win rate percentage
     */
    function getWinRate(address _agent) external view returns (uint256) {
        Agent storage agent = agents[_agent];
        if (agent.totalSignals == 0) return 0;
        return (agent.wins * 100) / (agent.wins + agent.losses);
    }
    
    /**
     * @notice Get all signals for an agent
     */
    function getAgentSignals(address _agent) external view returns (uint256[] memory) {
        return agentSignals[_agent];
    }
    
    /**
     * @notice Get paginated signals for an agent
     */
    function getAgentSignalsPaginated(
        address _agent,
        uint256 _offset,
        uint256 _limit
    ) external view returns (uint256[] memory) {
        uint256[] storage allSignals = agentSignals[_agent];
        uint256 end = _offset + _limit;
        if (end > allSignals.length) end = allSignals.length;
        
        uint256[] memory result = new uint256[](end - _offset);
        for (uint256 i = _offset; i < end; i++) {
            result[i - _offset] = allSignals[i];
        }
        return result;
    }
    
    /**
     * @notice Get all registered agents
     */
    function getAllAgents() external view returns (address[] memory) {
        return registeredAgents;
    }
    
    /**
     * @notice Check if address is a registered agent
     */
    function isRegistered(address _addr) external view returns (bool) {
        return agents[_addr].registeredAt != 0;
    }
    
    /**
     * @notice Get leaderboard data
     */
    function getLeaderboard(uint256 _limit) external view returns (address[] memory, uint256[] memory) {
        uint256 count = _limit > registeredAgents.length ? registeredAgents.length : _limit;
        
        address[] memory addresses = new address[](count);
        uint256[] memory karmaScores = new uint256[](count);
        
        // Simple bubble sort by karma (can be optimized)
        address[] memory sorted = new address[](registeredAgents.length);
        for (uint256 i = 0; i < registeredAgents.length; i++) {
            sorted[i] = registeredAgents[i];
        }
        
        for (uint256 i = 0; i < sorted.length; i++) {
            for (uint256 j = i + 1; j < sorted.length; j++) {
                if (agents[sorted[j]].karma > agents[sorted[i]].karma) {
                    address temp = sorted[i];
                    sorted[i] = sorted[j];
                    sorted[j] = temp;
                }
            }
        }
        
        for (uint256 i = 0; i < count; i++) {
            addresses[i] = sorted[i];
            karmaScores[i] = agents[sorted[i]].karma;
        }
        
        return (addresses, karmaScores);
    }
    
    // ============ Admin Functions ============
    
    function deactivateAgent(address _agent) external onlyOwner {
        agents[_agent].isActive = false;
        emit AgentDeactivated(_agent);
    }
    
    function reactivateAgent(address _agent) external onlyOwner {
        agents[_agent].isActive = true;
        emit AgentReactivated(_agent);
    }
}
