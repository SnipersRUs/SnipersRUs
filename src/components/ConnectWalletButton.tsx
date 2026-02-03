import { useAccount, useConnect, useDisconnect, useBalance, useReadContract } from 'wagmi'
import { base } from 'wagmi/chains'
import { Wallet, ChevronDown, LogOut, Loader2 } from 'lucide-react'
import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { USDC_CONTRACT, USDC_ABI } from '@/web3/config'

export const ConnectWalletButton = () => {
  const { address, isConnected, isConnecting } = useAccount()
  const { connect, connectors } = useConnect()
  const { disconnect } = useDisconnect()
  const [showDropdown, setShowDropdown] = useState(false)
  const [isFirstConnect, setIsFirstConnect] = useState(true)
  
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

  // Check if first time connecting (simulate with localStorage in real app)
  useEffect(() => {
    if (isConnected && address) {
      const hasConnectedBefore = localStorage.getItem(`connected_${address}`)
      if (!hasConnectedBefore) {
        setIsFirstConnect(true)
        localStorage.setItem(`connected_${address}`, 'true')
      } else {
        setIsFirstConnect(false)
      }
    }
  }, [isConnected, address])

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
          <div className="absolute right-0 top-full mt-2 w-72 bg-sniper-card border border-white/10 rounded-xl p-4 z-50 shadow-xl">
            {/* Net Worth Header */}
            <div className="flex items-center gap-3 mb-4 pb-4 border-b border-white/10">
              <div className="w-10 h-10 rounded-full bg-sniper-purple/20 flex items-center justify-center">
                <Wallet size={20} className="text-sniper-purple" />
              </div>
              <div className="flex-1">
                <div className="text-white font-bold">Trader</div>
                <div className="flex items-center gap-1 text-xs">
                  <span className="w-2 h-2 rounded-full bg-sniper-green"></span>
                  <span className="text-sniper-green">CONNECTED</span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-white/40 text-[10px] uppercase">Net Worth</div>
                <div className="text-white font-bold font-orbitron">
                  {isFirstConnect ? '$0.00' : `$${(Number(usdcBalance || 0) / 1_000_000 + (Number(ethBalance?.value || 0) / 1e18 * 3000)).toFixed(2)}`}
                </div>
              </div>
            </div>

            <div className="space-y-3 mb-4 pb-4 border-b border-white/10">
              <div className="flex justify-between items-center">
                <span className="text-white/60 text-sm">USDC Balance</span>
                <span className="text-white font-bold">
                  {isFirstConnect ? '$0.00' : `$${usdcBalance ? (Number(usdcBalance) / 1_000_000).toFixed(2) : '0.00'}`} USDC
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-white/60 text-sm">ETH Balance</span>
                <span className="text-white font-bold">
                  {isFirstConnect ? '0.0000' : (ethBalance ? (Number(ethBalance.value) / 1e18).toFixed(4) : '0.0000')} ETH
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
