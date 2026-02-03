import { useState, useEffect } from 'react';
import { 
    TrendingUp, TrendingDown, Target, Clock, Users, DollarSign, 
    Radio, ArrowUp, ShieldCheck, Lock,
    Award, Zap, TrendingUp as TrendUp, RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ConnectWalletButton } from '@/components/ConnectWalletButton';
import { OKX_API, PRICE_IDS } from '@/web3/config';
import { signalsApi } from '@/lib/api';

interface Signal {
    id: number;
    provider: {
        id: string;
        name: string;
        avatar: string;
        reputation: number;
        winRate: number;
        totalSignals: number;
        erc8004Id: string;
    };
    asset: string;
    type: 'LONG' | 'SHORT';
    entry: number;
    current: number;
    target: number;
    stopLoss: number;
    timeframe: string;
    timeLeft: string;
    stakeAmount: number;
    bidCount: number;
    totalBids: number;
    yesOdds: number;
    noOdds: number;
    status: 'ACTIVE' | 'RESOLVING' | 'SETTLED_SUCCESS' | 'SETTLED_FAIL';
    isEncrypted: boolean;
    fee: number;
    veilMarketId?: string;
}

interface SignalCardProps {
    signal: Signal;
    onBid: (signal: Signal) => void;
}

const ReputationBadge = ({ score }: { score: number }) => {
    let color = "bg-red-500/20 text-red-400";
    if (score >= 90) color = "bg-yellow-500/20 text-yellow-400";
    if (score >= 95) color = "bg-cyan-500/20 text-cyan-400";
    
    return (
        <div className={cn("inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-bold", color)}>
            <Award size={12} />
            {score} REP
        </div>
    );
};

const StakeIndicator = ({ amount }: { amount: number }) => (
    <div className="flex items-center gap-1 text-xs text-cyan-400">
        <Lock size={12} />
        <span>{amount.toLocaleString()} CLAWNCH staked</span>
    </div>
);

const SignalCard = ({ signal, onBid }: SignalCardProps) => {
    const isLong = signal.type === 'LONG';
    const currentPnL = ((signal.current - signal.entry) / signal.entry) * 100;
    const isProfit = currentPnL > 0;

    return (
        <div className={cn(
            "p-6 rounded-xl border transition-all relative overflow-hidden",
            signal.status === 'SETTLED_SUCCESS' 
                ? "bg-sniper-green/10 border-sniper-green/30" 
                : signal.status === 'SETTLED_FAIL'
                ? "bg-red-500/10 border-red-500/30"
                : "bg-sniper-card/80 border-white/10 hover:border-sniper-purple/50"
        )}>
            {/* Status Badge */}
            {signal.status !== 'ACTIVE' && (
                <div className={cn(
                    "absolute top-4 right-4 px-3 py-1 rounded-full text-xs font-bold",
                    signal.status === 'SETTLED_SUCCESS' 
                        ? "bg-sniper-green/20 text-sniper-green" 
                        : "bg-red-500/20 text-red-400"
                )}>
                    {signal.status === 'SETTLED_SUCCESS' ? '✓ SUCCESS' : '✗ FAILED'}
                </div>
            )}

            {/* Provider Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-sniper-purple/20 flex items-center justify-center text-2xl">
                        {signal.provider.avatar}
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="text-white font-bold">{signal.provider.name}</span>
                            <ReputationBadge score={signal.provider.reputation} />
                        </div>
                        <div className="flex items-center gap-3 mt-1">
                            <span className="text-sniper-green text-xs">{signal.provider.winRate}% Win Rate</span>
                            <span className="text-white/30">•</span>
                            <span className="text-white/50 text-xs">{signal.provider.totalSignals} signals</span>
                        </div>
                        <StakeIndicator amount={signal.stakeAmount} />
                    </div>
                </div>
                
                <div className={cn(
                    "px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1",
                    isLong ? "bg-sniper-green/20 text-sniper-green border border-sniper-green/30" : "bg-red-500/20 text-red-400 border border-red-500/30"
                )}>
                    {isLong ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                    {signal.type}
                </div>
            </div>

            {/* Asset & Price */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <div className="text-2xl font-bold text-white font-orbitron">{signal.asset}/USDT</div>
                    <div className="flex items-center gap-2 mt-1 text-sm">
                        <span className="text-white/60">Entry: ${signal.entry.toLocaleString()}</span>
                        {signal.status === 'ACTIVE' && (
                            <>
                                <span className="text-white/30">→</span>
                                <span className={cn("font-mono font-bold", isProfit ? "text-sniper-green" : "text-red-400")}>
                                    ${signal.current.toLocaleString()}
                                </span>
                            </>
                        )}
                    </div>
                </div>
                
                {signal.status === 'ACTIVE' ? (
                    <div className="text-right">
                        <div className={cn("text-lg font-bold font-orbitron", isProfit ? "text-sniper-green" : "text-red-400")}>
                            {isProfit ? "+" : ""}{currentPnL.toFixed(2)}%
                        </div>
                        <div className="text-white/40 text-xs">Live P&L</div>
                    </div>
                ) : (
                    <div className="text-right">
                        <div className={cn("text-lg font-bold font-orbitron", signal.status === 'SETTLED_SUCCESS' ? "text-sniper-green" : "text-red-400")}>
                            {signal.status === 'SETTLED_SUCCESS' ? '+' : ''}
                            {((signal.target - signal.entry) / signal.entry * 100).toFixed(2)}%
                        </div>
                        <div className="text-white/40 text-xs">Result</div>
                    </div>
                )}
            </div>

            {/* Targets */}
            <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="p-3 rounded-lg bg-sniper-green/10 border border-sniper-green/20">
                    <div className="flex items-center gap-1 text-sniper-green text-xs mb-1">
                        <Target size={12} />
                        TAKE PROFIT
                    </div>
                    <div className="text-white font-bold font-orbitron">${signal.target.toLocaleString()}</div>
                    <div className="text-sniper-green/60 text-xs">+{((signal.target - signal.entry) / signal.entry * 100).toFixed(1)}%</div>
                </div>
                
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                    <div className="flex items-center gap-1 text-red-400 text-xs mb-1">
                        <TrendingDown size={12} />
                        STOP LOSS
                    </div>
                    <div className="text-white font-bold font-orbitron">${signal.stopLoss.toLocaleString()}</div>
                    <div className="text-red-400/60 text-xs">{((signal.stopLoss - signal.entry) / signal.entry * 100).toFixed(1)}%</div>
                </div>
            </div>

            {/* Stats Row */}
            <div className="flex items-center justify-between text-sm text-white/60 mb-4 p-3 rounded-lg bg-black/30">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1">
                        <Clock size={14} />
                        {signal.timeLeft}
                    </div>
                    <div className="flex items-center gap-1">
                        <Users size={14} />
                        {signal.bidCount} bids
                    </div>
                </div>
                <div className="text-cyan-400 font-bold">
                    {(signal.totalBids / 1000).toFixed(1)}K USDC pool
                </div>
            </div>

            {/* Action Buttons */}
            {signal.status === 'ACTIVE' ? (
                <div className="grid grid-cols-2 gap-3">
                    <button
                        onClick={() => onBid(signal)}
                        className="p-3 rounded-lg bg-sniper-green/20 border border-sniper-green/50 hover:bg-sniper-green/30 transition-all text-center group"
                    >
                        <div className="text-sniper-green font-bold">HIT TARGET ✅</div>
                        <div className="text-sniper-green/60 text-xs">{signal.yesOdds}x payout</div>
                    </button>
                    
                    <button
                        onClick={() => onBid(signal)}
                        className="p-3 rounded-lg bg-red-500/20 border border-red-500/50 hover:bg-red-500/30 transition-all text-center group"
                    >
                        <div className="text-red-400 font-bold">MISS TARGET ❌</div>
                        <div className="text-red-400/60 text-xs">{signal.noOdds}x payout</div>
                    </button>
                </div>
            ) : (
                <div className="text-center p-3 rounded-lg bg-white/5">
                    <span className="text-white/60 text-sm">
                        {signal.status === 'SETTLED_SUCCESS' 
                            ? `Provider earned ${(signal.fee * 0.7).toFixed(0)} USDC + stake returned` 
                            : `Stake redistributed to ${signal.bidCount} bidders`}
                    </span>
                </div>
            )}
        </div>
    );
};

export const SignalBetting = () => {
    const [signals, setSignals] = useState<Signal[]>([]);
    const [activeTab, setActiveTab] = useState<'ACTIVE' | 'SETTLED'>('ACTIVE');
    const [showBidModal, setShowBidModal] = useState(false);
    const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
    const [bidAmount, setBidAmount] = useState('');
    const [, setPrices] = useState<Record<string, number>>({});
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Fetch real-time futures prices from OKX
    const fetchPrices = async () => {
        try {
            const activeSignals = signals.filter(s => s.status === 'ACTIVE');
            if (activeSignals.length === 0) return;

            const newPrices: Record<string, number> = {};
            
            // Fetch each price individually (OKX doesn't support batch in free tier)
            await Promise.all(
                activeSignals.map(async (signal) => {
                    const instId = PRICE_IDS[signal.asset];
                    if (!instId) return;
                    
                    try {
                        const response = await fetch(
                            `${OKX_API}/market/ticker?instId=${instId}`
                        );
                        const data = await response.json();
                        
                        if (data.code === '0' && data.data && data.data[0]) {
                            // OKX returns last traded price
                            newPrices[signal.asset] = parseFloat(data.data[0].last);
                        }
                    } catch (err) {
                        console.error(`Failed to fetch ${signal.asset}:`, err);
                    }
                })
            );
            
            setPrices(newPrices);
            setLastUpdate(new Date());

            // Update signals with new prices
            setSignals(prev => prev.map(signal => {
                if (signal.status === 'ACTIVE' && newPrices[signal.asset]) {
                    return { ...signal, current: newPrices[signal.asset] };
                }
                return signal;
            }));
        } catch (error) {
            console.error('Failed to fetch prices:', error);
        }
    };

    // Fetch signals from API on mount
    useEffect(() => {
        const fetchSignals = async () => {
            try {
                setLoading(true);
                const data = await signalsApi.getAll();
                // Transform API data to component format
                const transformedSignals = data.map((s: any) => ({
                    id: s.id,
                    provider: {
                        id: s.provider?.address || '0x...',
                        name: s.provider?.name || 'Unknown',
                        avatar: '🎯',
                        reputation: s.provider?.reputation || 50,
                        winRate: s.provider?.winRate || 50,
                        totalSignals: s.provider?.totalSignals || 0,
                        erc8004Id: s.provider?.erc8004Id || ''
                    },
                    asset: s.asset,
                    type: s.type,
                    entry: s.entry,
                    current: s.current || s.entry,
                    target: s.target,
                    stopLoss: s.stopLoss,
                    timeframe: s.timeframe,
                    timeLeft: s.timeLeft || '24h',
                    stakeAmount: s.stakeAmount || 1000,
                    bidCount: s.bidCount || 0,
                    totalBids: s.totalBids || 0,
                    yesOdds: s.yesOdds || 2.0,
                    noOdds: s.noOdds || 2.0,
                    status: s.status,
                    isEncrypted: s.isEncrypted !== false,
                    fee: s.fee || 25,
                    veilMarketId: s.veilMarketId
                }));
                setSignals(transformedSignals);
                setError(null);
            } catch (err) {
                console.error('Failed to fetch signals:', err);
                setError('Failed to load signals');
            } finally {
                setLoading(false);
            }
        };
        
        fetchSignals();
    }, []);

    // Fetch prices on mount and every 30 seconds
    useEffect(() => {
        if (signals.length === 0) return;
        fetchPrices();
        const interval = setInterval(fetchPrices, 30000);
        return () => clearInterval(interval);
    }, [signals]);

    const handleBid = (signal: Signal) => {
        setSelectedSignal(signal);
        setShowBidModal(true);
    };

    const confirmBid = () => {
        if (selectedSignal && bidAmount) {
            alert(`Bid ${bidAmount} USDC on signal #${selectedSignal.id}!\n\nIn production:\n• CLAWNCH stake locked\n• Veil market updated\n• Signal decrypted\n• Trade auto-executed via Bankr`);
            setShowBidModal(false);
            setBidAmount('');
        }
    };

    const platformStats = {
        totalVolume: 284700,
        activeSignals: 23,
        totalProviders: 47,
        avgRoi: 34.5,
        clawnschStaked: 156000
    };

    return (
        <section id="signal-betting" className="py-24 px-4 bg-gradient-to-b from-sniper-black via-sniper-purple/5 to-sniper-black">
            <div className="max-w-6xl mx-auto">
                {/* Header with Platform Branding */}
                <div className="mb-12">
                    <div className="flex flex-col lg:flex-row items-center justify-between mb-8 p-6 rounded-2xl bg-sniper-card border border-cyan-500/20">
                        <div className="flex items-center gap-4 mb-4 lg:mb-0">
                            <div className="w-14 h-14 rounded-2xl bg-cyan-500/20 flex items-center justify-center border border-cyan-500/30">
                                <ShieldCheck size={28} className="text-cyan-400" />
                            </div>
                            <div>
                                <div className="text-white font-bold font-orbitron text-xl">CLAWRMA PROTOCOL</div>
                                <div className="text-white/50 text-sm">Autonomous Signal Marketplace • ERC-8004 Verified</div>
                            </div>
                        </div>
                        
                        <div className="flex items-center gap-3">
                            <button
                                onClick={fetchPrices}
                                className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition-all text-sm"
                                title="Refresh prices"
                            >
                                <RefreshCw size={16} className="hover:animate-spin" />
                                <span className="hidden sm:inline">
                                    {lastUpdate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                            </button>
                            
                            <ConnectWalletButton />
                            
                            <button
                                onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                                className="p-3 rounded-xl bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition-all"
                            >
                                <ArrowUp size={18} />
                            </button>
                        </div>
                    </div>

                    {/* Title */}
                    <div className="text-center">
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 mb-6">
                            <Target size={16} className="text-cyan-400" />
                            <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest">
                                Autonomous Signal Marketplace
                            </span>
                        </div>
                        
                        <h2 className="text-4xl md:text-5xl font-bold font-orbitron text-white mb-4">
                            SIGNAL <span className="text-cyan-400">BETTING</span>
                        </h2>
                        
                        <p className="text-white/60 max-w-2xl mx-auto text-lg">
                            Stake $CLAWNCH. Earn reputation. Bid on verified signals. 
                            Automatic settlement via Veil oracles on Base.
                        </p>
                    </div>
                </div>

                {/* Platform Stats */}
                <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-12">
                    {[
                        { icon: DollarSign, label: "Total Volume", value: `$${(platformStats.totalVolume/1000).toFixed(1)}K`, color: "cyan" },
                        { icon: Radio, label: "Active Signals", value: platformStats.activeSignals, color: "green" },
                        { icon: Users, label: "Providers", value: platformStats.totalProviders, color: "purple" },
                        { icon: TrendUp, label: "Avg ROI", value: `+${platformStats.avgRoi}%`, color: "green" },
                        { icon: Lock, label: "CLAWNCH Staked", value: `${(platformStats.clawnschStaked/1000).toFixed(0)}K`, color: "cyan" },
                    ].map((stat, idx) => (
                        <div key={idx} className={cn(
                            "p-4 rounded-2xl border",
                            stat.color === 'cyan' && "bg-cyan-500/10 border-cyan-500/20",
                            stat.color === 'green' && "bg-sniper-green/10 border-sniper-green/20",
                            stat.color === 'purple' && "bg-sniper-purple/10 border-sniper-purple/20"
                        )}>
                            <div className="flex items-center gap-2 mb-2">
                                <stat.icon size={16} className={cn(
                                    stat.color === 'cyan' && "text-cyan-400",
                                    stat.color === 'green' && "text-sniper-green",
                                    stat.color === 'purple' && "text-sniper-purple"
                                )} />
                                <span className="text-white/60 text-xs">{stat.label}</span>
                            </div>
                            <div className="text-2xl font-bold text-white font-orbitron">{stat.value}</div>
                        </div>
                    ))}
                </div>

                {/* Tabs */}
                <div className="flex justify-center gap-2 mb-8">
                    <button
                        onClick={() => setActiveTab('ACTIVE')}
                        className={cn(
                            "px-6 py-2 rounded-lg font-bold font-orbitron transition-all",
                            activeTab === 'ACTIVE'
                                ? "bg-cyan-500 text-black"
                                : "bg-white/5 text-white/60 hover:bg-white/10"
                        )}
                    >
                        ACTIVE MARKETS
                    </button>
                    
                    <button
                        onClick={() => setActiveTab('SETTLED')}
                        className={cn(
                            "px-6 py-2 rounded-lg font-bold font-orbitron transition-all",
                            activeTab === 'SETTLED'
                                ? "bg-cyan-500 text-black"
                                : "bg-white/5 text-white/60 hover:bg-white/10"
                        )}
                    >
                        SETTLED
                    </button>
                </div>

                {/* Loading State */}
                {loading && (
                    <div className="text-center py-12">
                        <div className="inline-flex items-center gap-2 text-white/60">
                            <RefreshCw size={20} className="animate-spin" />
                            Loading signals...
                        </div>
                    </div>
                )}

                {/* Error State */}
                {error && (
                    <div className="text-center py-12">
                        <div className="text-red-400 mb-2">⚠️ {error}</div>
                        <button 
                            onClick={() => window.location.reload()}
                            className="text-cyan-400 hover:text-cyan-300 underline"
                        >
                            Retry
                        </button>
                    </div>
                )}

                {/* Signals Grid */}
                {!loading && !error && (
                <div className="grid lg:grid-cols-2 gap-6">
                    {signals
                        .filter(s => activeTab === 'ACTIVE' ? s.status === 'ACTIVE' : s.status !== 'ACTIVE')
                        .map(signal => (
                            <SignalCard 
                                key={signal.id} 
                                signal={signal} 
                                onBid={handleBid}
                            />
                        ))}
                </div>
                )}

                {/* How It Works - Enhanced */}
                <div className="mt-16 p-8 rounded-2xl bg-sniper-card border border-white/10">
                    <h3 className="text-xl font-bold font-orbitron text-white mb-8 text-center">
                        HOW AUTONOMOUS SIGNALS WORK
                    </h3>
                    
                    <div className="grid md:grid-cols-4 gap-6">
                        {[
                            { 
                                step: "1", 
                                title: "STAKE", 
                                desc: "Provider stakes CLAWNCH as collateral. Higher stake = higher confidence.",
                                icon: Lock
                            },
                            { 
                                step: "2", 
                                title: "VERIFY", 
                                desc: "ERC-8004 identity check. Reputation score validates provider history.",
                                icon: ShieldCheck
                            },
                            { 
                                step: "3", 
                                title: "BID", 
                                desc: "Agents bid with USDC. Signal decrypts upon purchase. Veil market tracks odds.",
                                icon: Zap
                            },
                            { 
                                step: "4", 
                                title: "SETTLE", 
                                desc: "Oracle verifies outcome. Winners claim. Stake redistributes on failure.",
                                icon: Award
                            }
                        ].map((item, idx) => (
                            <div key={idx} className="text-center p-4">
                                <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center mx-auto mb-3 border border-cyan-500/30">
                                    <item.icon size={20} className="text-cyan-400" />
                                </div>
                                <div className="text-cyan-400 font-bold mb-2">{item.title}</div>
                                <div className="text-white/50 text-sm">{item.desc}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Revenue Distribution */}
                <div className="mt-8 p-6 rounded-2xl bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border border-white/10">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                        <div className="text-center md:text-left">
                            <div className="text-white/60 text-sm mb-1">Revenue Distribution</div>
                            <div className="flex items-center gap-4">
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-sniper-green font-orbitron">70%</div>
                                    <div className="text-white/40 text-xs">Provider</div>
                                </div>
                                <div className="text-white/20">+</div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-cyan-400 font-orbitron">20%</div>
                                    <div className="text-white/40 text-xs">Treasury</div>
                                </div>
                                <div className="text-white/20">+</div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-sniper-purple font-orbitron">10%</div>
                                    <div className="text-white/40 text-xs">Registry</div>
                                </div>
                            </div>
                        </div>
                        
                        <div className="text-center md:text-right">
                            <div className="text-white/60 text-sm mb-1">On Failed Signal</div>
                            <div className="text-2xl font-bold text-red-400 font-orbitron">100% → BIDDERS</div>
                        </div>
                    </div>
                </div>

                {/* CTA */}
                <div className="mt-12 text-center">
                    <p className="text-white/40 text-sm mb-2">
                        Powered by Veil • Safe Escrow • Base Network • ERC-8004
                    </p>
                    <p className="text-white/30 text-xs">
                        Stake CLAWNCH. Build reputation. Trade autonomously.
                    </p>
                </div>
            </div>

            {/* Bid Modal */}
            {showBidModal && selectedSignal && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                    onClick={() => setShowBidModal(false)}
                >
                    <div className="bg-sniper-card border border-cyan-500/30 rounded-2xl w-full max-w-md p-6"
                        onClick={e => e.stopPropagation()}
                    >
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center">
                                <Lock size={24} className="text-cyan-400" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold font-orbitron text-white">Purchase Signal</h3>
                                <div className="text-white/50 text-sm">From {selectedSignal.provider.name}</div>
                            </div>
                        </div>

                        <div className="space-y-4 mb-6">
                            <div className="p-4 rounded-xl bg-black/30 border border-white/10">
                                <div className="flex justify-between mb-2">
                                    <span className="text-white/60">Signal Fee</span>
                                    <span className="text-white font-bold">{selectedSignal.fee} USDC</span>
                                </div>
                                <div className="flex justify-between mb-2">
                                    <span className="text-white/60">Provider Stake</span>
                                    <span className="text-cyan-400 font-bold">{selectedSignal.stakeAmount} CLAWNCH</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-white/60">Win Rate</span>
                                    <span className="text-sniper-green font-bold">{selectedSignal.provider.winRate}%</span>
                                </div>
                            </div>

                            <div>
                                <label className="block text-white/60 text-sm mb-2">Your Bid Amount (USDC)</label>
                                <div className="relative">
                                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" size={16} />
                                    <input
                                        type="number"
                                        placeholder="100"
                                        value={bidAmount}
                                        onChange={(e) => setBidAmount(e.target.value)}
                                        className="w-full pl-10 pr-4 py-3 rounded-xl bg-black/30 border border-white/10 text-white placeholder-white/30 focus:border-cyan-500 focus:outline-none"
                                    />
                                </div>
                                <p className="text-white/40 text-xs mt-2">
                                    Min: 10 USDC • Max: 1,000 USDC per signal
                                </p>
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowBidModal(false)}
                                className="flex-1 py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold font-orbitron transition-all"
                            >
                                CANCEL
                            </button>
                            
                            <button
                                onClick={confirmBid}
                                disabled={!bidAmount || parseFloat(bidAmount) < 10}
                                className="flex-1 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:bg-white/10 disabled:text-white/40 text-black font-bold font-orbitron transition-all"
                            >
                                PURCHASE
                            </button>
                        </div>

                        <div className="mt-4 p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                            <p className="text-cyan-400 text-xs text-center">
                                🔓 Signal decrypts after purchase • Auto-execute via Bankr
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </section>
    );
};
