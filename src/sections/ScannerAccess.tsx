import { useState } from 'react';
import { Shield, Lock, TrendingUp, Award, Flame } from 'lucide-react';
import { cn } from '@/lib/utils';

declare global {
  interface Window {
    ethereum?: {
      request: (args: { method: string }) => Promise<string[]>;
    };
  }
}

const TIERS = [
    {
        name: 'BASIC',
        stake: 100,
        icon: Shield,
        features: ['Bounty Seeker signals', '5 signals/day', 'Basic analysis'],
        color: 'from-blue-500/20 to-blue-500/5',
        borderColor: 'border-blue-500/30'
    },
    {
        name: 'PRO',
        stake: 500,
        icon: Lock,
        features: ['Bounty + Short Hunter', '20 signals/day', 'Advanced confluence'],
        color: 'from-sniper-purple/20 to-sniper-purple/5',
        borderColor: 'border-sniper-purple/30',
        popular: true
    },
    {
        name: 'GURU',
        stake: 1000,
        icon: Award,
        features: ['All bots + 10x Scanner', 'Unlimited signals', 'Golden Pocket zones', 'VWAP analysis'],
        color: 'from-yellow-500/20 to-yellow-500/5',
        borderColor: 'border-yellow-500/30'
    }
];

export const ScannerAccess = () => {
    const [address, setAddress] = useState('');
    const [selectedTier, setSelectedTier] = useState<string | null>(null);
    const [isConnecting, setIsConnecting] = useState(false);
    const [connected, setConnected] = useState(false);

    const connectWallet = async () => {
        setIsConnecting(true);
        try {
            if (typeof window.ethereum !== 'undefined') {
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                if (accounts.length > 0) {
                    setAddress(accounts[0]);
                    setConnected(true);
                    // Auto-check access after connection
                    checkAccess(accounts[0]);
                }
            } else {
                alert('Please install MetaMask or another Web3 wallet');
            }
        } catch (err) {
            console.error('Wallet connection error:', err);
        } finally {
            setIsConnecting(false);
        }
    };

    const disconnectWallet = () => {
        setAddress('');
        setConnected(false);
    };

    const checkAccess = async (addr?: string) => {
        const checkAddr = addr || address;
        if (!checkAddr) return;
        
        try {
            const response = await fetch(`https://snipersrus-backend-production.up.railway.app/api/scanner/access/${checkAddr}`);
            const data = await response.json();
            console.log('Access data:', data);
            alert(`Tier: ${data.tier}\nStaked: ${data.stakedAmount} CLAWNCH\nRemaining: ${data.signalsRemaining}`);
        } catch (err) {
            console.error('Failed to check access:', err);
        }
    };

    return (
        <section id="scanner" className="py-24 px-4">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="text-center mb-16">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sniper-green/10 border border-sniper-green/20 mb-6">
                        <Shield size={16} className="text-sniper-green" />
                        <span className="text-[10px] font-mono text-sniper-green uppercase tracking-widest">
                            Sniper Guru Premium
                        </span>
                    </div>
                    
                    <h2 className="text-4xl md:text-5xl font-bold font-orbitron text-white mb-4">
                        SCANNER <span className="text-sniper-green">ACCESS</span>
                    </h2>
                    
                    <p className="text-white/60 max-w-2xl mx-auto text-lg">
                        Stake CLAWNCH to unlock premium signals with Golden Pocket zones, 
                        VWAP deviation analysis, and swing/scalp classifications.
                    </p>
                </div>

                {/* Wallet Connection */}
                <div className="mb-12 p-6 rounded-2xl bg-white/5 border border-white/10">
                    {!connected ? (
                        <div className="text-center">
                            <button
                                onClick={connectWallet}
                                disabled={isConnecting}
                                className="px-8 py-4 rounded-lg bg-sniper-green hover:bg-sniper-green/80 text-black font-bold font-orbitron transition-all flex items-center gap-2 mx-auto"
                            >
                                {isConnecting ? 'Connecting...' : '🔗 Connect Wallet'}
                            </button>
                            <p className="text-white/50 text-sm mt-4">
                                Connect your wallet to check staking access and manage CLAWNCH
                            </p>
                        </div>
                    ) : (
                        <div className="flex flex-col md:flex-row items-center gap-4">
                            <div className="flex-1 px-4 py-3 rounded-lg bg-black/50 border border-sniper-green/50 text-white font-mono flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-sniper-green animate-pulse"></span>
                                {address.slice(0, 6)}...{address.slice(-4)}
                            </div>
                            <button
                                onClick={() => checkAccess()}
                                className="px-6 py-3 rounded-lg bg-sniper-green hover:bg-sniper-green/80 text-black font-bold font-orbitron transition-all"
                            >
                                CHECK ACCESS
                            </button>
                            <button
                                onClick={disconnectWallet}
                                className="px-6 py-3 rounded-lg bg-white/10 hover:bg-white/20 text-white font-bold font-orbitron transition-all"
                            >
                                DISCONNECT
                            </button>
                        </div>
                    )}
                </div>

                {/* Tier Cards */}
                <div className="grid md:grid-cols-3 gap-6 mb-12">
                    {TIERS.map((tier) => (
                        <div
                            key={tier.name}
                            className={cn(
                                "relative p-6 rounded-xl border transition-all cursor-pointer",
                                "bg-gradient-to-br",
                                tier.color,
                                tier.borderColor,
                                selectedTier === tier.name ? "scale-105 border-opacity-100" : "hover:border-opacity-70"
                            )}
                            onClick={() => setSelectedTier(tier.name)}
                        >
                            {tier.popular && (
                                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-sniper-purple text-white text-[10px] font-bold rounded-full">
                                    MOST POPULAR
                                </div>
                            )}

                            <div className="flex items-center gap-3 mb-4">
                                <div className={cn(
                                    "p-3 rounded-lg",
                                    tier.name === 'BASIC' && "bg-blue-500/20",
                                    tier.name === 'PRO' && "bg-sniper-purple/20",
                                    tier.name === 'GURU' && "bg-yellow-500/20"
                                )}>
                                    <tier.icon size={24} className={cn(
                                        tier.name === 'BASIC' && "text-blue-400",
                                        tier.name === 'PRO' && "text-sniper-purple",
                                        tier.name === 'GURU' && "text-yellow-400"
                                    )} />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-white">{tier.name}</h3>
                                    <div className="text-sniper-green font-bold">{tier.stake} CLAWNCH</div>
                                </div>
                            </div>

                            <ul className="space-y-2 mb-6">
                                {tier.features.map((feature, idx) => (
                                    <li key={idx} className="flex items-center gap-2 text-sm text-white/70">
                                        <TrendingUp size={14} className="text-sniper-green" />
                                        {feature}
                                    </li>
                                ))}
                            </ul>

                            <button
                                className={cn(
                                    "w-full py-3 rounded-lg font-bold font-orbitron transition-all",
                                    selectedTier === tier.name
                                        ? "bg-sniper-green text-black"
                                        : connected 
                                            ? "bg-white/10 hover:bg-white/20 text-white"
                                            : "bg-white/5 text-white/40 cursor-not-allowed"
                                )}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    if (!connected) {
                                        alert('Please connect your wallet first!');
                                        return;
                                    }
                                    alert(`To Stake ${tier.stake} CLAWNCH for ${tier.name}:\n\n1. You need CLAWNCH tokens in your wallet\n2. Sign a message to confirm staking\n3. Tokens are held in the staking contract\n4. Access unlocks immediately\n\nThis will be processed through your connected wallet.`);
                                }}
                                disabled={!connected}
                            >
                                {!connected ? 'CONNECT WALLET' : selectedTier === tier.name ? 'SELECTED' : 'STAKE'}
                            </button>
                        </div>
                    ))}
                </div>

                {/* Features */}
                <div className="grid md:grid-cols-4 gap-4 mb-12">
                    {[
                        { icon: TrendingUp, title: 'Golden Pocket', desc: '0.618-0.65 Fib zones' },
                        { icon: Shield, title: 'VWAP Deviation', desc: '±σ band analysis' },
                        { icon: Award, title: 'Swing/Scalp', desc: 'Auto classification' },
                        { icon: Lock, title: 'Confidence Score', desc: '70-99% rating' }
                    ].map((feature, idx) => (
                        <div key={idx} className="p-4 rounded-xl bg-white/5 border border-white/10 text-center">
                            <feature.icon size={24} className="mx-auto mb-2 text-sniper-green" />
                            <div className="text-white font-bold text-sm">{feature.title}</div>
                            <div className="text-white/50 text-xs">{feature.desc}</div>
                        </div>
                    ))}
                </div>

                {/* Tip Jar Promo */}
                <div className="p-6 rounded-2xl bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/20">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-full bg-yellow-500/20 flex items-center justify-center">
                                <Flame size={24} className="text-yellow-400" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white">Tip Sniper Guru</h3>
                                <p className="text-white/60 text-sm">Send ZOID tips for great signals • 75% to dev • 25% burned</p>
                            </div>
                        </div>
                        <button
                            onClick={() => alert('Tip feature coming soon! Connect wallet to tip Sniper Guru in ZOID.')}
                            className="px-6 py-2 rounded-lg bg-yellow-500 hover:bg-yellow-400 text-black font-bold font-orbitron transition-all"
                        >
                            SEND TIP
                        </button>
                    </div>
                </div>

                {/* How to Test */}
                <div className="mt-12 p-6 rounded-2xl bg-white/5 border border-white/10">
                    <h3 className="text-lg font-bold text-white mb-4">🧪 How to Test Staking</h3>
                    <div className="grid md:grid-cols-2 gap-4 text-sm text-white/70">
                        <div>
                            <div className="font-bold text-white mb-2">1. Check Access (No Stake)</div>
                            <code className="block p-2 rounded bg-black/50 font-mono text-xs">
curl https://api.../scanner/access/0xYOUR_ADDRESS
                            </code>
                            <div className="mt-1">Expected: tier: "NONE"</div>
                        </div>
                        
                        <div>
                            <div className="font-bold text-white mb-2">2. Stake CLAWNCH</div>
                            <code className="block p-2 rounded bg-black/50 font-mono text-xs">
{`curl -X POST https://api.../scanner/stake \\
  -d '{"amount":100,"signature":"0x..."}'`}
                            </code>
                            <div className="mt-1">Expected: stake confirmed</div>
                        </div>
                        
                        <div>
                            <div className="font-bold text-white mb-2">3. Verify Access</div>
                            <code className="block p-2 rounded bg-black/50 font-mono text-xs">
curl https://api.../scanner/access/0xYOUR_ADDRESS
                            </code>
                            <div className="mt-1">Expected: tier: "BASIC"</div>
                        </div>
                        
                        <div>
                            <div className="font-bold text-white mb-2">4. Get Signal</div>
                            <code className="block p-2 rounded bg-black/50 font-mono text-xs">
curl https://api.../scanner/signal/BTC
                            </code>
                            <div className="mt-1">Expected: signal data</div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};
