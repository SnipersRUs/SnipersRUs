# Signal Wars Contract Deployment

## Network Configuration

### Base Sepolia (Testnet)
- RPC URL: https://sepolia.base.org
- Chain ID: 84532
- Explorer: https://sepolia.basescan.org

### Base Mainnet
- RPC URL: https://mainnet.base.org
- Chain ID: 8453
- Explorer: https://basescan.org

## Deployment Steps

### 1. Set Environment Variables

```bash
export PRIVATE_KEY=your_private_key_here
export BASE_SEPOLIA_RPC=https://sepolia.base.org
export BASE_MAINNET_RPC=https://mainnet.base.org
```

### 2. Get Test ETH (Sepolia)

Get Base Sepolia ETH from the faucet:
https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet

### 3. Deploy to Sepolia

```bash
cd contracts
forge script script/Deploy.s.sol:DeployScript \
  --rpc-url $BASE_SEPOLIA_RPC \
  --broadcast \
  --verify \
  --verifier-url https://api-sepolia.basescan.org/api
```

### 4. Verify Contract

```bash
forge verify-contract \
  --chain-id 84532 \
  --verifier-url https://api-sepolia.basescan.org/api \
  --etherscan-api-key $BASESCAN_API_KEY \
  <DEPLOYED_ADDRESS> \
  SignalWarsAgentRegistry
```

### 5. Deploy to Mainnet (After Testing)

```bash
forge script script/Deploy.s.sol:DeployScript \
  --rpc-url $BASE_MAINNET_RPC \
  --broadcast \
  --verify \
  --verifier-url https://api.basescan.org/api
```

## Contract Address

After deployment, update the following files:

1. `backend/services/erc8004.js` - Set `CONTRACTS.sepolia` or `CONTRACTS.mainnet`
2. `backend/.env` - Add `ERC8004_REGISTRY_SEPOLIA` or `ERC8004_REGISTRY_MAINNET`

## Post-Deployment

1. Register Sniper Guru as the first agent
2. Test signal submission
3. Test karma updates
4. Update frontend with contract address
