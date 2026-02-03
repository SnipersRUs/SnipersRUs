import { createConfig, http } from 'wagmi'
import { base } from 'wagmi/chains'
import { injected, walletConnect } from 'wagmi/connectors'

// WalletConnect Project ID from Ricky Spanish
const projectId = '0fc23c1f1b192d88b58507559371da89'

export const config = createConfig({
  chains: [base],
  connectors: [
    injected(),
    walletConnect({ 
      projectId,
      metadata: {
        name: 'SnipersRUs Signal Betting',
        description: 'Bet on trading signal outcomes with USDC on Base',
        url: 'https://srus.life',
        icons: ['https://srus.life/icon.png']
      }
    })
  ],
  transports: {
    [base.id]: http('https://mainnet.base.org')
  }
})

// USDC on Base
export const USDC_CONTRACT = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'

// OKX Futures API for real-time price feeds
export const OKX_API = 'https://www.okx.com/api/v5'

// Price feed mapping - OKX instId format
export const PRICE_IDS: Record<string, string> = {
  'BTC': 'BTC-USDT-SWAP',
  'ETH': 'ETH-USDT-SWAP',
  'SOL': 'SOL-USDT-SWAP',
  'BNB': 'BNB-USDT-SWAP',
  'XRP': 'XRP-USDT-SWAP',
  'ADA': 'ADA-USDT-SWAP',
  'DOGE': 'DOGE-USDT-SWAP',
  'LINK': 'LINK-USDT-SWAP',
  'AVAX': 'AVAX-USDT-SWAP',
  'MATIC': 'MATIC-USDT-SWAP',
  'SUI': 'SUI-USDT-SWAP'
}

// USDC ABI for approval/balance
export const USDC_ABI = [
  {
    inputs: [{ name: 'spender', type: 'address' }, { name: 'amount', type: 'uint256' }],
    name: 'approve',
    outputs: [{ name: '', type: 'bool' }],
    stateMutability: 'nonpayable',
    type: 'function'
  },
  {
    inputs: [{ name: 'account', type: 'address' }],
    name: 'balanceOf',
    outputs: [{ name: '', type: 'uint256' }],
    stateMutability: 'view',
    type: 'function'
  }
] as const
