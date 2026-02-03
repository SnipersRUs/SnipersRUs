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

// Price feed mapping - OKX instId format (ALL major cryptos)
export const PRICE_IDS: Record<string, string> = {
  // Majors
  'BTC': 'BTC-USDT-SWAP',
  'ETH': 'ETH-USDT-SWAP',
  // Layer 1s
  'SOL': 'SOL-USDT-SWAP',
  'BNB': 'BNB-USDT-SWAP',
  'AVAX': 'AVAX-USDT-SWAP',
  'SUI': 'SUI-USDT-SWAP',
  'APT': 'APT-USDT-SWAP',
  'NEAR': 'NEAR-USDT-SWAP',
  'ARB': 'ARB-USDT-SWAP',
  'OP': 'OP-USDT-SWAP',
  'MATIC': 'MATIC-USDT-SWAP',
  'FTM': 'FTM-USDT-SWAP',
  // DeFi
  'LINK': 'LINK-USDT-SWAP',
  'AAVE': 'AAVE-USDT-SWAP',
  'UNI': 'UNI-USDT-SWAP',
  'MKR': 'MKR-USDT-SWAP',
  'LDO': 'LDO-USDT-SWAP',
  'CRV': 'CRV-USDT-SWAP',
  // Memes
  'DOGE': 'DOGE-USDT-SWAP',
  'SHIB': 'SHIB-USDT-SWAP',
  'PEPE': 'PEPE-USDT-SWAP',
  // Payments
  'XRP': 'XRP-USDT-SWAP',
  'ADA': 'ADA-USDT-SWAP',
  // Gaming/Metaverse
  'IMX': 'IMX-USDT-SWAP',
  'SAND': 'SAND-USDT-SWAP',
  'MANA': 'MANA-USDT-SWAP',
  'AXS': 'AXS-USDT-SWAP',
  // Infrastructure
  'TIA': 'TIA-USDT-SWAP',
  'SEI': 'SEI-USDT-SWAP',
  'INJ': 'INJ-USDT-SWAP',
  'RUNE': 'RUNE-USDT-SWAP',
  'DOT': 'DOT-USDT-SWAP',
  'ATOM': 'ATOM-USDT-SWAP',
  // Storage
  'FIL': 'FIL-USDT-SWAP',
  'AR': 'AR-USDT-SWAP',
  // Privacy
  'ZEC': 'ZEC-USDT-SWAP',
  'XMR': 'XMR-USDT-SWAP',
  // Stablecoins (for reference)
  'USDC': 'USDC-USDT-SWAP',
  'USDT': 'USDT-USD-SWAP'
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
