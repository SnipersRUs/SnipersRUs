import { useState, useEffect } from 'react';
import { Wallet, Shield, Crown, ArrowRight, CheckCircle, Copy, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TierCardProps {
    name: string;
    usdPrice: number;
    tokenAmount: string;
    features: string[];
    icon: React.ElementType;
    color: string;
    popular?: boolean;
}

const TierCard = ({ name, usdPrice, tokenAmount, features, icon: Icon, color, popular }: TierCardProps) => {
    const [copied, setCopied] = useState(false);
    const paymentAddress = "0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5"; // ZOID Payment Wallet

    const handleCopy = () => {
        navigator.clipboard.writeText(paymentAddress);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className={cn(
            "relative p-6 rounded-xl border transition-all duration-300",
            popular 
                ? "bg-gradient-to-b from-sniper-purple/20 to-black border-sniper-purple scale-105" 
                : "bg-black/50 border-white/10 hover:border-white/20"
        )}>
            {popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-sniper-purple text-white text-[10px] font-bold rounded-full uppercase tracking-wider">
                    Most Popular
                </div>
            )}
            
            <div className="flex items-center gap-3 mb-4">
                <div className={cn("p-3 rounded-lg", color)}>
                    <Icon size={24} className="text-white" />
                </div>
                <div>
                    <h3 className="text-xl font-bold font-orbitron text-white">{name}</h3>
                    <p className="text-sniper-green font-bold">${usdPrice} USD</p>
                </div>
            </div>

            <div className="mb-6 p-4 rounded-lg bg-sniper-green/10 border border-sniper-green/20">
                <div className="text-white/60 text-xs mb-2">Send this amount of ZOID:</div>
                <div className="text-3xl font-bold text-white mb-1">{tokenAmount}</div>
                <div className="text-sniper-green text-sm font-mono">ZOID Tokens</div>
                <div className="text-white/40 text-xs mt-2">= ${usdPrice} USD value</div>
            </div>

            <ul className="space-y-3 mb-6">
                {features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-white/70">
                        <CheckCircle size={16} className="text-sniper-green mt-0.5 shrink-0" />
                        <span>{feature}</span>
                    </li>
                ))}
            </ul>

            <button
                onClick={handleCopy}
                className={cn(
                    "w-full py-3 px-4 rounded-lg font-mono text-sm font-bold transition-all flex items-center justify-center gap-2",
                    popular
                        ? "bg-sniper-purple hover:bg-sniper-purple/80 text-white"
                        : "bg-white/10 hover:bg-white/20 text-white"
                )}
            >
                {copied ? (
                    <>
                        <CheckCircle size={16} />
                        COPIED!
                    </>
                ) : (
                    <>
                        <Copy size={16} />
                        COPY ADDRESS
                    </>
                )}
            </button>
        </div>
    );
};

export const Tiers = () => {
    const [zoidPrice, setZoidPrice] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);

    // Fixed USD prices (like credit card pricing)
    const USD_PRICES = {
        scout: 20,
        hunter: 40,
        elite: 333
    };

    // Fetch ZOID price
    useEffect(() => {
        const fetchPrice = async () => {
            try {
                // Try to get price from moltlaunch API or signals
                const response = await fetch('/signals.json');
                if (response.ok) {
                    // Current market cap ~4.31 ETH at launch
                    // Rough estimate: 1 ETH = $3000
                    // Need to calculate actual price per token
                    setZoidPrice(0.000431); // Approximate price per token in ETH
                }
            } catch (error) {
                console.log('Using default price');
                setZoidPrice(0.000431);
            } finally {
                setLoading(false);
            }
        };

        fetchPrice();
        // Refresh every 5 minutes
        const interval = setInterval(fetchPrice, 300000);
        return () => clearInterval(interval);
    }, []);

    // Calculate token amount needed for USD value
    const calculateTokenAmount = (usdValue: number): string => {
        if (!zoidPrice) return "Loading...";
        // zoidPrice is in ETH, ETH = $3000
        const ethValue = usdValue / 3000;
        const tokenAmount = ethValue / zoidPrice;
        return Math.round(tokenAmount).toLocaleString();
    };

    const tiers = [
        {
            name: "Scout",
            usdPrice: USD_PRICES.scout,
            tokenAmount: calculateTokenAmount(USD_PRICES.scout),
            features: [
                "Headhunter Basic Signals",
                "VWAP Deviation Alerts",
                "24/7 Discord Access",
                "30 Day Active Period"
            ],
            icon: Shield,
            color: "bg-blue-500/20"
        },
        {
            name: "Hunter",
            usdPrice: USD_PRICES.hunter,
            tokenAmount: calculateTokenAmount(USD_PRICES.hunter),
            features: [
                "Bounty Seeker Premium Signals",
                "All Scout Features",
                "Liquidity Zone Alerts",
                "Priority Signal Delivery",
                "30 Day Active Period"
            ],
            icon: Wallet,
            color: "bg-sniper-purple/20",
            popular: true
        },
        {
            name: "Elite",
            usdPrice: USD_PRICES.elite,
            tokenAmount: calculateTokenAmount(USD_PRICES.elite),
            features: [
                "Lifetime Access",
                "All Hunter Features",
                "Short Hunter Fleet Signals",
                "PIVX Signal Bot Access",
                "Direct Bot Integration",
                "Never Expires"
            ],
            icon: Crown,
            color: "bg-yellow-500/20"
        }
    ];

    return (
        <section id="tiers" className="py-24 px-4">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="text-center mb-16">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sniper-green/10 border border-sniper-green/20 mb-6">
                        <span className="w-2 h-2 rounded-full bg-sniper-green animate-pulse" />
                        <span className="text-[10px] font-mono text-sniper-green uppercase tracking-widest">
                            Pay With ZOID
                        </span>
                    </div>
                    <h2 className="text-4xl md:text-5xl font-bold font-orbitron text-white mb-4">
                        ACCESS <span className="text-sniper-purple">TIERS</span>
                    </h2>
                    <p className="text-white/60 max-w-2xl mx-auto text-lg">
                        Fixed USD prices - just like paying with a credit card. 
                        We calculate exactly how many ZOID tokens to send based on current price.
                    </p>
                    {loading ? (
                        <p className="text-white/40 text-sm mt-4">Calculating token amounts...</p>
                    ) : (
                        <div className="flex items-center justify-center gap-2 mt-4">
                            <TrendingUp size={16} className="text-sniper-green" />
                            <p className="text-sniper-green text-sm">
                                Live ZOID price • Updates every 5 minutes
                            </p>
                        </div>
                    )}
                </div>

                {/* How It Works */}
                <div className="mb-16 p-6 rounded-xl bg-white/5 border border-white/10">
                    <h3 className="text-lg font-bold font-orbitron text-white mb-6 text-center">HOW IT WORKS</h3>
                    <div className="grid md:grid-cols-4 gap-4">
                        {[
                            { step: "1", title: "CHOOSE TIER", desc: "Pick your plan: $20, $40, or $333" },
                            { step: "2", title: "BUY ZOID", desc: "Purchase tokens on Uniswap or Flaunch" },
                            { step: "3", title: "SEND AMOUNT", desc: "Send exact tokens shown (equals USD value)" },
                            { step: "4", title: "GET ACCESS", desc: "Join Discord & activate your tier" }
                        ].map((item, idx) => (
                            <div key={idx} className="flex items-start gap-3 p-4 rounded-lg bg-black/30">
                                <div className="w-8 h-8 rounded-full bg-sniper-purple/20 flex items-center justify-center text-sniper-purple font-bold text-sm shrink-0">
                                    {item.step}
                                </div>
                                <div>
                                    <div className="text-white font-bold text-sm">{item.title}</div>
                                    <div className="text-white/50 text-xs">{item.desc}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Tier Cards */}
                <div className="grid md:grid-cols-3 gap-6 mb-12">
                    {tiers.map((tier, idx) => (
                        <TierCard key={idx} {...tier} />
                    ))}
                </div>

                {/* Price Info Box */}
                <div className="mb-12 p-6 rounded-xl bg-sniper-green/5 border border-sniper-green/20">
                    <div className="text-center">
                        <h3 className="text-lg font-bold font-orbitron text-white mb-4">💡 HOW PRICING WORKS</h3>
                        <div className="grid md:grid-cols-3 gap-4 max-w-3xl mx-auto">
                            <div className="p-4 rounded-lg bg-black/30">
                                <div className="text-sniper-green font-bold text-xl">$20</div>
                                <div className="text-white/60 text-sm">Fixed Price</div>
                                <div className="text-white/40 text-xs mt-2">Like credit card</div>
                            </div>
                            <div className="p-4 rounded-lg bg-black/30">
                                <div className="text-sniper-green font-bold text-xl">Live Rate</div>
                                <div className="text-white/60 text-sm">ZOID Price</div>
                                <div className="text-white/40 text-xs mt-2">Updates every 5min</div>
                            </div>
                            <div className="p-4 rounded-lg bg-black/30">
                                <div className="text-sniper-green font-bold text-xl">Exact Amount</div>
                                <div className="text-white/60 text-sm">Tokens to Send</div>
                                <div className="text-white/40 text-xs mt-2">Auto-calculated</div>
                            </div>
                        </div>
                        
                        <p className="text-white/50 text-sm mt-6 max-w-2xl mx-auto">
                            <strong className="text-sniper-green">Example:</strong> If ZOID price goes up, you send fewer tokens. 
                            If price goes down, you send more tokens. <strong>Always equals $20/$40/$333 USD.</strong>
                        </p>
                    </div>
                </div>

                {/* Payment Info */}
                <div className="mb-12 p-6 rounded-xl bg-white/5 border border-white/10">
                    <div className="text-center">
                        <h3 className="text-lg font-bold font-orbitron text-white mb-4">PAYMENT WALLET</h3>
                        <code className="inline-block px-4 py-2 rounded-lg bg-black/50 text-sniper-green font-mono text-sm break-all">
                            0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5
                        </code>
                        <p className="text-white/50 text-sm mt-4">
                            Send the exact token amount shown above. We verify the USD value on our end.
                        </p>
                    </div>
                </div>

                {/* Discord CTA */}
                <div className="text-center">
                    <a
                        href="https://discord.gg/snipersrus"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-3 px-8 py-4 bg-[#5865F2] hover:bg-[#4752C4] text-white font-bold font-orbitron rounded-lg transition-all group"
                    >
                        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z"/>
                        </svg>
                        JOIN DISCORD TO ACTIVATE
                        <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                    </a>
                    <p className="mt-4 text-white/40 text-sm">
                        After sending payment, drop your wallet address in the #tier-activation channel
                    </p>
                </div>
            </div>
        </section>
    );
};
