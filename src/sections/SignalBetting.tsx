import { useState } from 'react';
import { TrendingUp, TrendingDown, Target, Clock, Users, DollarSign, Shield, Radio, Wallet, ArrowUp, ShieldCheck } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Signal {
    id: number;
    trader: string;
    avatar: string;
    reputation: number;
    asset: string;
    type: 'LONG' | 'SHORT';
    entry: number;
    current: number;
    target: number;
    stopLoss: number;
    timeframe: string;
    timeLeft: string;
    totalBets: number;
    yesOdds: number;
    noOdds: number;
    status: 'ACTIVE' | 'CLOSED';
}

const MOCK_SIGNALS: Signal[] = [
    {
        id: 1,
        trader: "SniperGuru",
        avatar: "🎯",
        reputation: 94,
        asset: "BTC",
        type: "LONG",
        entry: 45200,
        current: 45800,
        target: 48000,
        stopLoss: 44000,
        timeframe: "24h",
        timeLeft: "18h 23m",
        totalBets: 152,
        yesOdds: 2.3,
        noOdds: 1.7,
        status: "ACTIVE"
    },
    {
        id: 2,
        trader: "AlphaWolf",
        avatar: "🐺",
        reputation: 87,
        asset: "ETH",
        type: "SHORT",
        entry: 2450,
        current: 2420,
        target: 2300,
        stopLoss: 2520,
        timeframe: "12h",
        timeLeft: "8h 45m",
        totalBets: 89,
        yesOdds: 1.9,
        noOdds: 2.1,
        status: "ACTIVE"
    },
    {
        id: 3,
        trader: "CryptoKing",
        avatar: "👑",
        reputation: 91,
        asset: "SOL",
        type: "LONG",
        entry: 98.5,
        current: 102.3,
        target: 110,
        stopLoss: 94,
        timeframe: "48h",
        timeLeft: "41h 12m",
        totalBets: 234,
        yesOdds: 2.1,
        noOdds: 1.8,
        status: "ACTIVE"
    }
];

interface SignalCardProps {
    signal: Signal;
    onBet: (signalId: number, bet: 'YES' | 'NO', amount: number) => void;
}

const SignalCard = ({ signal, onBet }: SignalCardProps) => {
    const [showBetModal, setShowBetModal] = useState(false);
    const [betAmount, setBetAmount] = useState('');
    const [betSide, setBetSide] = useState<'YES' | 'NO' | null>(null);

    const isLong = signal.type === 'LONG';
    const currentPnL = ((signal.current - signal.entry) / signal.entry) * 100;
    const isProfit = currentPnL > 0;

    const handlePlaceBet = () => {
        if (betSide && betAmount) {
            onBet(signal.id, betSide, parseFloat(betAmount));
            setShowBetModal(false);
            setBetAmount('');
            setBetSide(null);
        }
    };

    return (
        <>
            <div className={cn(
                "p-6 rounded-xl border transition-all",
                "bg-sniper-card/80 border-white/10 hover:border-sniper-purple/50"
            )}>
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-sniper-purple/20 flex items-center justify-center text-xl">
                            {signal.avatar}
                        </div>
                        <div>
                            <div className="text-white font-bold">{signal.trader}</div>
                            <div className="flex items-center gap-1 text-xs">
                                <span className="text-sniper-green">{signal.reputation}% Win Rate</span>
                            </div>
                        </div>
                    </div>
                    
                    <div className={cn(
                        "px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1",
                        isLong ? "bg-sniper-green/20 text-sniper-green border border-sniper-green/30" : "bg-sniper-red/20 text-sniper-red border border-sniper-red/30"
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
                            <span className="text-white/30">→</span>
                            <span className={cn(
                                "font-mono font-bold",
                                isProfit ? "text-sniper-green" : "text-sniper-red"
                            )}>
                                ${signal.current.toLocaleString()}
                            </span>
                        </div>
                    </div>
                    
                    <div className="text-right">
                        <div className={cn(
                            "text-lg font-bold font-orbitron",
                            isProfit ? "text-sniper-green" : "text-sniper-red"
                        )}>
                            {isProfit ? "+" : ""}{currentPnL.toFixed(2)}%
                        </div>
                        <div className="text-white/40 text-xs">Live P&L</div>
                    </div>
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
                    
                    <div className="p-3 rounded-lg bg-sniper-red/10 border border-sniper-red/20">
                        <div className="flex items-center gap-1 text-sniper-red text-xs mb-1">
                            <TrendingDown size={12} />
                            STOP LOSS
                        </div>
                        <div className="text-white font-bold font-orbitron">${signal.stopLoss.toLocaleString()}</div>
                        <div className="text-sniper-red/60 text-xs">{((signal.stopLoss - signal.entry) / signal.entry * 100).toFixed(1)}%</div>
                    </div>
                </div>

                {/* Time & Bets */}
                <div className="flex items-center justify-between text-sm text-white/60 mb-4">
                    <div className="flex items-center gap-1">
                        <Clock size={14} />
                        {signal.timeLeft} left
                    </div>
                    <div className="flex items-center gap-1">
                        <Users size={14} />
                        {signal.totalBets} bets
                    </div>
                </div>

                {/* Bet Buttons */}
                <div className="grid grid-cols-2 gap-3">
                    <button
                        onClick={() => {
                            setBetSide('YES');
                            setShowBetModal(true);
                        }}
                        className="p-3 rounded-lg bg-sniper-green/20 border border-sniper-green/50 hover:bg-sniper-green/30 transition-all text-center"
                    >
                        <div className="text-sniper-green font-bold">HIT TARGET ✅</div>
                        <div className="text-sniper-green/60 text-xs">{signal.yesOdds}x payout</div>
                    </button>
                    
                    <button
                        onClick={() => {
                            setBetSide('NO');
                            setShowBetModal(true);
                        }}
                        className="p-3 rounded-lg bg-sniper-red/20 border border-sniper-red/50 hover:bg-sniper-red/30 transition-all text-center"
                    >
                        <div className="text-sniper-red font-bold">MISS TARGET ❌</div>
                        <div className="text-sniper-red/60 text-xs">{signal.noOdds}x payout</div>
                    </button>
                </div>
            </div>

            {/* Bet Modal */}
            {showBetModal && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                    onClick={() => setShowBetModal(false)}>
                    <div className="bg-sniper-black border border-white/10 rounded-2xl w-full max-w-md p-6"
                        onClick={e => e.stopPropagation()}>
                        <h3 className="text-xl font-bold font-orbitron text-white mb-4">
                            Place Bet
                        </h3>

                        <div className="mb-6">
                            <div className="text-white/60 text-sm mb-2">Betting on:</div>
                            <div className={cn(
                                "text-lg font-bold",
                                betSide === 'YES' ? "text-sniper-green" : "text-sniper-red"
                            )}>
                                {betSide === 'YES' ? 'Signal WILL hit target' : 'Signal will NOT hit target'}
                            </div>
                            <div className="text-white/40 text-sm">
                                Odds: {betSide === 'YES' ? signal.yesOdds : signal.noOdds}x
                            </div>
                        </div>

                        <div className="mb-6">
                            <label className="block text-white/60 text-sm mb-2">Bet Amount (USDC)</label>
                            <div className="relative">
                                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" size={16} />
                                <input
                                    type="number"
                                    placeholder="10"
                                    value={betAmount}
                                    onChange={(e) => setBetAmount(e.target.value)}
                                    className="w-full pl-10 pr-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-sniper-purple focus:outline-none"
                                />
                            </div>
                            
                            {betAmount && (
                                <div className="mt-2 text-sm">
                                    <span className="text-white/60">Potential win: </span>
                                    <span className="text-sniper-green font-bold">
                                        ${(parseFloat(betAmount || '0') * (betSide === 'YES' ? signal.yesOdds : signal.noOdds)).toFixed(2)} USDC
                                    </span>
                                </div>
                            )}
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowBetModal(false)}
                                className="flex-1 py-3 rounded-lg bg-white/10 hover:bg-white/20 text-white font-bold font-orbitron transition-all"
                            >
                                CANCEL
                            </button>
                            
                            <button
                                onClick={handlePlaceBet}
                                disabled={!betAmount || parseFloat(betAmount) <= 0}
                                className="flex-1 py-3 rounded-lg bg-sniper-purple hover:bg-sniper-purple/80 disabled:bg-white/10 disabled:text-white/40 text-white font-bold font-orbitron transition-all"
                            >
                                CONFIRM BET
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export const SignalBetting = () => {
    const [signals] = useState<Signal[]>(MOCK_SIGNALS);
    const [activeTab, setActiveTab] = useState<'ACTIVE' | 'CLOSED'>('ACTIVE');

    const handleBet = (signalId: number, bet: 'YES' | 'NO', amount: number) => {
        console.log(`Bet placed: Signal ${signalId}, ${bet}, $${amount}`);
        alert(`Bet placed: $${amount} USDC on ${bet === 'YES' ? 'HIT' : 'MISS'}!`);
    };

    return (
        <section id="signal-betting" className="py-24 px-4 bg-gradient-to-b from-sniper-black via-sniper-purple/5 to-sniper-black">
            <div className="max-w-6xl mx-auto">
                {/* Header with Clawrma Branding */}
                <div className="mb-12">
                    {/* Top Bar with Connect Wallet */}
                    <div className="flex flex-col md:flex-row items-center justify-between mb-8 p-4 rounded-2xl bg-sniper-card border border-white/10">
                        <div className="flex items-center gap-3 mb-4 md:mb-0">
                            <div className="w-10 h-10 rounded-xl bg-cyan-500/20 flex items-center justify-center">
                                <ShieldCheck size={20} className="text-cyan-400" />
                            </div>
                            <div>
                                <div className="text-white font-bold font-orbitron">CLAWRMA</div>
                                <div className="text-white/50 text-xs">Signal Verification Protocol</div>
                            </div>
                        </div>
                        
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => alert('Wallet connect coming soon!')}
                                className={cn(
                                    "flex items-center gap-2 px-6 py-3 rounded-xl",
                                    "bg-cyan-500 hover:bg-cyan-400",
                                    "text-black font-bold font-orbitron",
                                    "transition-all hover:scale-105"
                                )}
                            >
                                <Wallet size={18} />
                                CONNECT WALLET
                            </button>
                            
                            <button
                                onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                                className="p-3 rounded-xl bg-white/5 hover:bg-white/10 text-white/60 hover:text-white transition-all"
                                title="Back to top"
                            >
                                <ArrowUp size={18} />
                            </button>
                        </div>
                    </div>

                    {/* Title Section */}
                    <div className="text-center">
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 mb-6">
                            <Target size={16} className="text-cyan-400" />
                            <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest">
                                Prediction Markets on Base
                            </span>
                        </div>
                        
                        <h2 className="text-4xl md:text-5xl font-bold font-orbitron text-white mb-4">
                            SIGNAL <span className="text-cyan-400">BETTING</span>
                        </h2>
                        
                        <p className="text-white/60 max-w-2xl mx-auto text-lg">
                            Bet on whether trading signals hit their targets. 
                            Real USDC payouts. Powered by Veil + Safe on Base.
                        </p>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
                    <div className="p-6 rounded-2xl bg-sniper-purple/10 border border-sniper-purple/20">
                        <div className="flex items-center gap-2 mb-2">
                            <DollarSign size={18} className="text-sniper-purple" />
                            <span className="text-white/60 text-sm">Total Volume</span>
                        </div>
                        <div className="text-3xl font-bold text-white font-orbitron">$12.4K</div>
                    </div>
                    
                    <div className="p-6 rounded-2xl bg-sniper-green/10 border border-sniper-green/20">
                        <div className="flex items-center gap-2 mb-2">
                            <Radio size={18} className="text-sniper-green" />
                            <span className="text-white/60 text-sm">Active Signals</span>
                        </div>
                        <div className="text-3xl font-bold text-sniper-green font-orbitron">89</div>
                    </div>
                    
                    <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                            <TrendingUp size={18} className="text-white" />
                            <span className="text-white/60 text-sm">Avg Odds</span>
                        </div>
                        <div className="text-3xl font-bold text-white font-orbitron">2.1x</div>
                    </div>
                    
                    <div className="p-6 rounded-2xl bg-sniper-green/10 border border-sniper-green/20">
                        <div className="flex items-center gap-2 mb-2">
                            <Shield size={18} className="text-sniper-green" />
                            <span className="text-white/60 text-sm">Win Rate</span>
                        </div>
                        <div className="text-3xl font-bold text-sniper-green font-orbitron">67%</div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex justify-center gap-2 mb-8">
                    <button
                        onClick={() => setActiveTab('ACTIVE')}
                        className={cn(
                            "px-6 py-2 rounded-lg font-bold font-orbitron transition-all",
                            activeTab === 'ACTIVE'
                                ? "bg-sniper-purple text-white"
                                : "bg-white/5 text-white/60 hover:bg-white/10"
                        )}
                    >
                        ACTIVE SIGNALS
                    </button>
                    
                    <button
                        onClick={() => setActiveTab('CLOSED')}
                        className={cn(
                            "px-6 py-2 rounded-lg font-bold font-orbitron transition-all",
                            activeTab === 'CLOSED'
                                ? "bg-sniper-purple text-white"
                                : "bg-white/5 text-white/60 hover:bg-white/10"
                        )}
                    >
                        SETTLED
                    </button>
                </div>

                {/* Signals List */}
                <div className="grid lg:grid-cols-2 gap-6">
                    {signals
                        .filter(s => s.status === activeTab)
                        .map(signal => (
                            <SignalCard 
                                key={signal.id} 
                                signal={signal} 
                                onBet={handleBet}
                            />
                        ))}
                </div>

                {/* How It Works */}
                <div className="mt-16 p-8 rounded-2xl bg-sniper-card border border-white/10">
                    <h3 className="text-xl font-bold font-orbitron text-white mb-6 text-center">
                        HOW IT WORKS
                    </h3>
                    
                    <div className="grid md:grid-cols-4 gap-4">
                        {[
                            { step: "1", title: "BROWSE", desc: "Find signals from top traders" },
                            { step: "2", title: "ANALYZE", desc: "Check entry, target, stop loss" },
                            { step: "3", title: "BET", desc: "Wager USDC on HIT or MISS" },
                            { step: "4", title: "WIN", desc: "Collect payout when settled" }
                        ].map((item, idx) => (
                            <div key={idx} className="text-center p-4">
                                <div className="w-10 h-10 rounded-full bg-sniper-purple/20 flex items-center justify-center text-sniper-purple font-bold mx-auto mb-3 font-orbitron">
                                    {item.step}
                                </div>
                                <div className="text-white font-bold mb-1">{item.title}</div>
                                <div className="text-white/50 text-sm">{item.desc}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* CTA */}
                <div className="mt-12 text-center">
                    <p className="text-white/40 text-sm mb-4">
                        Powered by Veil • Safe Escrow • Base Network
                    </p>
                </div>
            </div>
        </section>
    );
};
