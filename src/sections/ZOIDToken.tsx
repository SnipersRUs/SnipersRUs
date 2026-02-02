import { useState } from 'react';
import { ExternalLink, Copy, CheckCircle, Coins, TrendingUp, ShoppingCart } from 'lucide-react';
import { cn } from '@/lib/utils';

export const ZOIDToken = () => {
    const [copied, setCopied] = useState(false);
    
    // These will be updated after token launch
    const TOKEN_ADDRESS = "0x..."; // Update after launch
    const CLANKER_URL = "https://clanker.world"; // Update after launch
    const UNISWAP_URL = "https://app.uniswap.org"; // Update after launch
    const DEXSCREENER_URL = "https://dexscreener.com/base"; // Update after launch
    
    const handleCopy = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const buyLinks = [
        {
            name: "Clanker",
            desc: "Launch Platform",
            url: CLANKER_URL,
            icon: Coins,
            color: "bg-purple-500/20 text-purple-400"
        },
        {
            name: "Uniswap",
            desc: "Trade on Base",
            url: UNISWAP_URL,
            icon: TrendingUp,
            color: "bg-pink-500/20 text-pink-400"
        },
        {
            name: "DexScreener",
            desc: "Chart & Analytics",
            url: DEXSCREENER_URL,
            icon: ShoppingCart,
            color: "bg-green-500/20 text-green-400"
        }
    ];

    return (
        <section id="zoid-token" className="py-24 px-4 bg-gradient-to-b from-black via-sniper-purple/5 to-black">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="text-center mb-16">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sniper-purple/10 border border-sniper-purple/20 mb-6">
                        <Coins size={16} className="text-sniper-purple" />
                        <span className="text-[10px] font-mono text-sniper-purple uppercase tracking-widest">
                            Utility Token
                        </span>
                    </div>
                    <h2 className="text-4xl md:text-5xl font-bold font-orbitron text-white mb-4">
                        $ZOID <span className="text-sniper-purple">TOKEN</span>
                    </h2>
                    <p className="text-white/60 max-w-2xl mx-auto text-lg">
                        The official currency of the Sniper ecosystem. Buy ZOID to unlock 
                        premium trading signals and bot access.
                    </p>
                </div>

                {/* Token Card */}
                <div className="grid lg:grid-cols-2 gap-8 mb-12">
                    {/* Image Side */}
                    <div className="relative group">
                        <div className="absolute inset-0 bg-sniper-purple/20 blur-3xl rounded-full opacity-50 group-hover:opacity-70 transition-opacity" />
                        <div className="relative p-8 rounded-2xl bg-black/50 border border-white/10 backdrop-blur-sm">
                            <img 
                                src="https://iili.io/fZS63tR.jpg" 
                                alt="ZOID Token" 
                                className="w-full max-w-md mx-auto rounded-xl shadow-2xl"
                            />
                            <div className="mt-6 text-center">
                                <div className="text-2xl font-bold font-orbitron text-white">ZOID</div>
                                <div className="text-sniper-green text-sm">Base Network</div>
                            </div>
                        </div>
                    </div>

                    {/* Info Side */}
                    <div className="space-y-6">
                        {/* Contract Address */}
                        <div className="p-6 rounded-xl bg-black/50 border border-white/10">
                            <div className="text-white/50 text-sm mb-2 font-mono">CONTRACT ADDRESS</div>
                            <div className="flex items-center gap-3">
                                <code className="flex-1 p-3 rounded bg-black/50 text-sniper-green text-sm font-mono break-all">
                                    {TOKEN_ADDRESS}
                                </code>
                                <button
                                    onClick={() => handleCopy(TOKEN_ADDRESS)}
                                    className="p-3 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
                                >
                                    {copied ? <CheckCircle size={20} className="text-sniper-green" /> : <Copy size={20} className="text-white" />}
                                </button>
                            </div>
                            <p className="mt-2 text-white/40 text-xs">
                                ⚠️ Always verify the contract address before trading
                            </p>
                        </div>

                        {/* Token Stats */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 rounded-xl bg-black/30 border border-white/10">
                                <div className="text-white/50 text-xs font-mono mb-1">NETWORK</div>
                                <div className="text-white font-bold">Base</div>
                            </div>
                            <div className="p-4 rounded-xl bg-black/30 border border-white/10">
                                <div className="text-white/50 text-xs font-mono mb-1">SYMBOL</div>
                                <div className="text-white font-bold">ZOID</div>
                            </div>
                            <div className="p-4 rounded-xl bg-black/30 border border-white/10">
                                <div className="text-white/50 text-xs font-mono mb-1">DECIMALS</div>
                                <div className="text-white font-bold">18</div>
                            </div>
                            <div className="p-4 rounded-xl bg-black/30 border border-white/10">
                                <div className="text-white/50 text-xs font-mono mb-1">TYPE</div>
                                <div className="text-white font-bold">ERC-20</div>
                            </div>
                        </div>

                        {/* Quick Links */}
                        <div className="space-y-3">
                            <div className="text-white/50 text-sm font-mono">QUICK LINKS</div>
                            <div className="grid gap-3">
                                {buyLinks.map((link, idx) => (
                                    <a
                                        key={idx}
                                        href={link.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-4 p-4 rounded-xl bg-black/30 border border-white/10 hover:border-sniper-purple/50 hover:bg-sniper-purple/5 transition-all group"
                                    >
                                        <div className={cn("p-3 rounded-lg", link.color)}>
                                            <link.icon size={20} />
                                        </div>
                                        <div className="flex-1">
                                            <div className="text-white font-bold">{link.name}</div>
                                            <div className="text-white/50 text-sm">{link.desc}</div>
                                        </div>
                                        <ExternalLink size={18} className="text-white/30 group-hover:text-sniper-purple transition-colors" />
                                    </a>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* How to Use */}
                <div className="p-8 rounded-2xl bg-gradient-to-r from-sniper-purple/10 to-sniper-green/10 border border-white/10">
                    <h3 className="text-2xl font-bold font-orbitron text-white mb-6 text-center">
                        How to Use $ZOID
                    </h3>
                    <div className="grid md:grid-cols-3 gap-6">
                        <div className="text-center">
                            <div className="w-12 h-12 rounded-full bg-sniper-purple/20 flex items-center justify-center text-sniper-purple font-bold text-xl mx-auto mb-4">
                                1
                            </div>
                            <h4 className="text-white font-bold mb-2">Buy ZOID</h4>
                            <p className="text-white/60 text-sm">
                                Purchase ZOID tokens on Uniswap or Clanker using ETH or USDC on Base network.
                            </p>
                        </div>
                        <div className="text-center">
                            <div className="w-12 h-12 rounded-full bg-sniper-purple/20 flex items-center justify-center text-sniper-purple font-bold text-xl mx-auto mb-4">
                                2
                            </div>
                            <h4 className="text-white font-bold mb-2">Choose Tier</h4>
                            <p className="text-white/60 text-sm">
                                Decide which signal tier you want: Scout (10K), Hunter (25K), or Elite (200K).
                            </p>
                        </div>
                        <div className="text-center">
                            <div className="w-12 h-12 rounded-full bg-sniper-purple/20 flex items-center justify-center text-sniper-purple font-bold text-xl mx-auto mb-4">
                                3
                            </div>
                            <h4 className="text-white font-bold mb-2">Send & Access</h4>
                            <p className="text-white/60 text-sm">
                                Send ZOID to our payment wallet and join Discord to activate your access.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};
