import { useAccount, useConnect, useDisconnect, useBalance, useReadContract } from 'wagmi'
import { base } from 'wagmi/chains'
import { Wallet, ChevronDown, LogOut, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { USDC_CONTRACT, USDC_ABI } from '@/web3/config'

export const ConnectWalletButton = () => {
  const { address, isConnected, isConnecting } = useAccount()
  const { connect, connectors } = useConnect()
  const { disconnect } = useDisconnect()
  const [showDropdown, setShowDropdown] = useState(false)
  
  const { data: usdcBalance } = useReadContract({
    address: USDC_CONTRACT,
    abi: USDC_ABI,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
    chainId: base.id
  })

  const { data: ethBalance } = useBalance({
    address,
    chainId: base.id
  })

  if (isConnected && address) {
    return (
      <div className="relative">
        <button 
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-xl",
            "bg-cyan-500/10 border border-cyan-500/30",
            "text-cyan-400 font-bold font-orbitron text-sm",
            "hover:bg-cyan-500/20 transition-all"
          )}
          onClick={() => setShowDropdown(!showDropdown)}
        >
          <Wallet size={16} />
          <span>{address.slice(0, 6)}...{address.slice(-4)}</span>
          <ChevronDown size={14} className={showDropdown ? 'rotate-180' : ''} />
        </button>

        {showDropdown && (
          <div className="absolute right-0 top-full mt-2 w-64 bg-sniper-card border border-white/10 rounded-xl p-4 z-50 shadow-xl">
            <div className="space-y-3 mb-4 pb-4 border-b border-white/10">
              <div className="flex justify-between items-center">
                <span className="text-white/60 text-sm">USDC Balance</span>
                <span className="text-white font-bold">
                  ${usdcBalance ? (Number(usdcBalance) / 1_000_000).toFixed(2) : '0.00'} USDC
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-white/60 text-sm">ETH Balance</span>
                <span className="text-white font-bold">
                  {ethBalance ? (Number(ethBalance.value) / 1e18).toFixed(4) : '0.0000'}
                </span>
              </div>
            </div>
            
            <button
              onClick={() => { disconnect(); setShowDropdown(false); }}
              className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 font-bold transition-all"
            >
              <LogOut size={16} />
              Disconnect
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <button
      onClick={() => connect({ connector: connectors[0] })}
      disabled={isConnecting}
      className={cn(
        "flex items-center gap-2 px-6 py-3 rounded-xl",
        "bg-cyan-500 hover:bg-cyan-400",
        "text-black font-bold font-orbitron",
        "transition-all hover:scale-105",
        "disabled:opacity-50 disabled:cursor-not-allowed"
      )}
    >
      {isConnecting ? (
        <>
          <Loader2 size={18} className="animate-spin" />
          Connecting...
        </>
      ) : (
        <>
          <Wallet size={18} />
          Connect Wallet
        </>
      )}
    </button>
  )
}
