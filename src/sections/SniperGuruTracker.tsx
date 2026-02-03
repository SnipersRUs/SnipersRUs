import { useState, useEffect } from 'react';
import { Radio, TrendingUp, TrendingDown, Target, Shield, Zap, Activity, Clock, Award, Flame } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Trade {
    id: number;
    pair: string;
    type: 'LONG' | 'SHORT';
    entry: string;
    current: string;
    pnl: string;
    pnlPercent: number;
    status: 'ACTIVE' | 'CLOSED_TP' | 'CLOSED_SL';
    time: string;
    stopLoss: string;
    takeProfit: string;
}

// Real trades from backend - initially empty until data loads
const SNIPER_TRADES: Trade[] = [];

const SNIPER_STATS = {
    totalTrades: 0,
    winRate: 0,
    totalPnl: 0,
    currentStreak: 0,
    bestTrade: 0,
    avgTradeTime: "--",
    activeNow: 0,
    lastTrade: "--"
};

const TradeCard = ({ trade }: { trade: Trade }) => {
    const isLong = trade.type === "LONG";
    const isProfit = trade.pnlPercent > 0;
    
    return (
        <div className={cn(
            "p-4 rounded-xl border transition-all",
            trade.status === "CLOSED_TP" 
                ? "bg-sniper-green/10 border-sniper-green/30" 
                : trade.status === "CLOSED_SL"
                ? "bg-red-500/10 border-red-500/30"
                : "bg-black/40 border-white/10 hover:border-sniper-purple/30"
        )}>
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className={cn(
                        "w-10 h-10 rounded-full flex items-center justify-center",
                        isLong ? "bg-sniper-green/20" : "bg-red-500/20"
                    )}>
                        {isLong ? <TrendingUp size={20} className="text-sniper-green" /> : <TrendingDown size={20} className="text-red-400" />}
                    </div>
                    <div>
                        <div className="text-white font-bold">{trade.pair}</div>
                        <div className={cn(
                            "text-xs font-bold",
                            isLong ? "text-sniper-green" : "text-red-400"
                        )}>
                            {trade.type}
                        </div>
                    </div>
                </div>
                
                <div className="text-right">
                    {trade.status === "CLOSED_TP" ? (
                        <div className="flex items-center gap-1 text-sniper-green text-sm font-bold">
                            <Target size={14} />
                            TP HIT
                        </div>
                    ) : trade.status === "CLOSED_SL" ? (
                        <div className="flex items-center gap-1 text-red-400 text-sm font-bold">
                            <Shield size={14} />
                            SL HIT
                        </div>
                    ) : (
                        <div className={cn(
                            "text-lg font-bold font-orbitron",
                            isProfit ? "text-sniper-green" : "text-red-400"
                        )}>
                            {isProfit ? "+" : ""}{trade.pnlPercent.toFixed(2)}%
                        </div>
                    )}
                    <div className="text-white/40 text-xs">{trade.time}</div>
                </div>
            </div>
            
            <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="p-2 rounded bg-black/50">
                    <div className="text-white/40 text-[10px]">ENTRY</div>
                    <div className="text-white font-mono text-sm">${trade.entry}</div>
                </div>
                <div className="p-2 rounded bg-black/50">
                    <div className="text-white/40 text-[10px]">CURRENT</div>
                    <div className={cn(
                        "font-mono text-sm",
                        isProfit ? "text-sniper-green" : "text-white"
                    )}>
                        ${trade.current}
                    </div>
                </div>
                <div className="p-2 rounded bg-black/50">
                    <div className="text-white/40 text-[10px]">P&L</div>
                    <div className={cn(
                        "font-mono text-sm",
                        isProfit ? "text-sniper-green" : "text-red-400"
                    )}>
                        {isProfit ? "+" : ""}${trade.pnl}
                    </div>
                </div>
            </div>
            
            <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                    <Shield size={12} className="text-red-400" />
                    <span className="text-white/40">SL: ${trade.stopLoss}</span>
                </div>
                <div className="flex items-center gap-2">
                    <Target size={12} className="text-sniper-green" />
                    <span className="text-white/40">TP: ${trade.takeProfit}</span>
                </div>
            </div>
        </div>
    );
};

export const SniperGuruTracker = () => {
    const [trades] = useState<Trade[]>(SNIPER_TRADES);
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);
        
        return () => clearInterval(interval);
    }, []);

    return (
        <section id="sniper-guru" className="py-24 px-4 bg-gradient-to-b from-black via-sniper-purple/5 to-black">
            <div className="max-w-6xl mx-auto">
                {/* SNIPER GURU PROFILE HEADER */}
                <div className="mb-16">
                    {/* Profile Card */}
                    <div className="relative p-8 rounded-3xl bg-gradient-to-br from-sniper-purple/20 via-black to-black border border-sniper-purple/30 overflow-hidden">
                        {/* Background glow */}
                        <div className="absolute top-0 right-0 w-96 h-96 bg-sniper-purple/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
                        
                        <div className="relative flex flex-col lg:flex-row items-center gap-8">
                            {/* PFP */}
                            <div className="relative">
                                <div className="w-32 h-32 lg:w-40 lg:h-40 rounded-full overflow-hidden border-4 border-sniper-purple/50 shadow-lg shadow-sniper-purple/20">
                                    <img 
                                        src="/sniper-guru-pfp.jpg" 
                                        alt="Sniper Guru"
                                        className="w-full h-full object-cover"
                                    />
                                </div>
                                {/* Online indicator */}
                                <div className="absolute -bottom-2 -right-2 flex items-center gap-2 bg-black border border-sniper-green/50 rounded-full px-3 py-1.5">
                                    <span className="w-3 h-3 rounded-full bg-sniper-green animate-pulse" />
                                    <span className="text-sniper-green text-xs font-bold">ALWAYS ONLINE</span>
                                </div>
                            </div>

                            {/* Info */}
                            <div className="flex-1 text-center lg:text-left">
                                <div className="flex flex-wrap items-center justify-center lg:justify-start gap-3 mb-2">
                                    <h2 className="text-3xl lg:text-4xl font-bold font-orbitron text-white">
                                        SNIPER GURU
                                    </h2>
                                    <div className="flex items-center gap-1 px-3 py-1 rounded-full bg-sniper-purple/20 border border-sniper-purple/30">
                                        <Award size={14} className="text-sniper-purple" />
                                        <span className="text-sniper-purple text-xs font-bold">PRO TRADER</span>
                                    </div>
                                </div>
                                
                                <p className="text-white/60 text-lg mb-4">
                                    VWAP Scalping Specialist • 24/7 Automated Trading
                                </p>

                                {/* Quick Stats Row */}
                                <div className="flex flex-wrap items-center justify-center lg:justify-start gap-4 text-sm">
                                    <div className="flex items-center gap-2 text-white/70">
                                        <Activity size={14} className="text-sniper-green" />
                                        <span>{SNIPER_STATS.activeNow} Active Trades</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-white/70">
                                        <Clock size={14} className="text-sniper-purple" />
                                        <span>Last trade {SNIPER_STATS.lastTrade}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-white/70">
                                        <Flame size={14} className="text-orange-400" />
                                        <span>{SNIPER_STATS.currentStreak} Win Streak</span>
                                    </div>
                                </div>
                            </div>

                            {/* Live Time */}
                            <div className="hidden lg:block text-right">
                                <div className="text-white/40 text-xs mb-1">Trading Session</div>
                                <div className="text-2xl font-mono text-white">
                                    {currentTime.toLocaleTimeString('en-US', { 
                                        hour: '2-digit', 
                                        minute: '2-digit', 
                                        second: '2-digit',
                                        hour12: false 
                                    })}
                                </div>
                                <div className="text-sniper-green text-xs font-bold mt-1">
                                    SESSION ACTIVE
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* PERFORMANCE STATS GRID */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
                    <div className="p-6 rounded-2xl bg-sniper-purple/10 border border-sniper-purple/20">
                        <div className="flex items-center gap-2 mb-2">
                            <Target size={18} className="text-sniper-purple" />
                            <span className="text-white/60 text-sm">Total Trades</span>
                        </div>
                        <div className="text-3xl font-bold text-white font-orbitron">
                            {SNIPER_STATS.totalTrades.toLocaleString()}
                        </div>
                        <div className="text-white/40 text-xs mt-1">All time</div>
                    </div>
                    
                    <div className="p-6 rounded-2xl bg-sniper-green/10 border border-sniper-green/20">
                        <div className="flex items-center gap-2 mb-2">
                            <TrendingUp size={18} className="text-sniper-green" />
                            <span className="text-white/60 text-sm">Win Rate</span>
                        </div>
                        <div className="text-3xl font-bold text-sniper-green font-orbitron">
                            {SNIPER_STATS.winRate}%
                        </div>
                        <div className="text-white/40 text-xs mt-1">Lifetime</div>
                    </div>
                    
                    <div className="p-6 rounded-2xl bg-gradient-to-br from-sniper-green/20 to-sniper-purple/20 border border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                            <Zap size={18} className="text-yellow-400" />
                            <span className="text-white/60 text-sm">Total P&L</span>
                        </div>
                        <div className="text-3xl font-bold text-sniper-green font-orbitron">
                            +{SNIPER_STATS.totalPnl}%
                        </div>
                        <div className="text-white/40 text-xs mt-1">Cumulative</div>
                    </div>
                    
                    <div className="p-6 rounded-2xl bg-orange-500/10 border border-orange-500/20">
                        <div className="flex items-center gap-2 mb-2">
                            <Award size={18} className="text-orange-400" />
                            <span className="text-white/60 text-sm">Best Trade</span>
                        </div>
                        <div className="text-3xl font-bold text-orange-400 font-orbitron">
                            +{SNIPER_STATS.bestTrade}%
                        </div>
                        <div className="text-white/40 text-xs mt-1">Single trade</div>
                    </div>
                </div>

                {/* ADDITIONAL STATS */}
                <div className="grid grid-cols-3 gap-4 mb-12">
                    <div className="text-center p-4 rounded-xl bg-black/30 border border-white/5">
                        <div className="text-2xl font-bold text-white font-orbitron">{SNIPER_STATS.avgTradeTime}</div>
                        <div className="text-white/40 text-xs mt-1">Avg Hold Time</div>
                    </div>
                    <div className="text-center p-4 rounded-xl bg-black/30 border border-white/5">
                        <div className="text-2xl font-bold text-sniper-green font-orbitron">{SNIPER_STATS.currentStreak}</div>
                        <div className="text-white/40 text-xs mt-1">Win Streak</div>
                    </div>
                    <div className="text-center p-4 rounded-xl bg-black/30 border border-white/5">
                        <div className="text-2xl font-bold text-sniper-purple font-orbitron">{SNIPER_STATS.activeNow}</div>
                        <div className="text-white/40 text-xs mt-1">Active Now</div>
                    </div>
                </div>

                {/* TRADES SECTION */}
                <div className="mb-8">
                    <div className="flex items-center justify-center gap-2 mb-8">
                        <Radio size={24} className="text-sniper-green animate-pulse" />
                        <h3 className="text-2xl font-bold font-orbitron text-white">
                            LIVE TRADES
                        </h3>
                        <span className="px-2 py-1 rounded bg-sniper-green/20 text-sniper-green text-xs font-bold">
                            REAL-TIME
                        </span>
                    </div>
                </div>

                {/* Live Trades Grid */}
                <div className="grid lg:grid-cols-2 gap-8">
                    <div>
                        <div className="flex items-center justify-between mb-6">
                            <h4 className="text-lg font-bold font-orbitron text-white flex items-center gap-2">
                                <Activity size={18} className="text-sniper-green" />
                                ACTIVE POSITIONS
                            </h4>
                            <div className="flex items-center gap-2 text-xs text-white/50">
                                <span className="w-2 h-2 rounded-full bg-sniper-green animate-pulse" />
                                SCANNING MARKETS
                            </div>
                        </div>
                        
                        <div className="space-y-4">
                            {trades.filter(t => t.status === "ACTIVE").map(trade => (
                                <TradeCard key={trade.id} trade={trade} />
                            ))}
                        </div>
                    </div>
                    
                    <div>
                        <div className="flex items-center justify-between mb-6">
                            <h4 className="text-lg font-bold font-orbitron text-white flex items-center gap-2">
                                <Target size={18} className="text-sniper-purple" />
                                RECENT HISTORY
                            </h4>
                        </div>
                        
                        <div className="space-y-4">
                            {trades.filter(t => t.status !== "ACTIVE").map(trade => (
                                <TradeCard key={trade.id} trade={trade} />
                            ))}
                        </div>
                    </div>
                </div>

                {/* Get Access CTA */}
                <div className="mt-16 p-8 rounded-2xl bg-gradient-to-r from-sniper-purple/10 via-black to-sniper-green/10 border border-white/10">
                    <div className="text-center">
                        <h3 className="text-2xl font-bold font-orbitron text-white mb-4">
                            Trade Alongside Sniper Guru
                        </h3>
                        
                        <p className="text-white/60 mb-6 max-w-xl mx-auto">
                            Get every entry, exit, and update in real-time. 
                            Join {SNIPER_STATS.totalTrades.toLocaleString()}+ trades worth of experience.
                        </p>
                        
                        <a
                            href="#tiers"
                            className="inline-flex items-center gap-2 px-8 py-4 bg-sniper-purple hover:bg-sniper-purple/80 text-white font-bold font-orbitron rounded-lg transition-all hover:scale-105"
                        >
                            GET SIGNALS WITH ZOID
                            <TrendingUp size={20} />
                        </a>
                    </div>
                </div>
            </div>
        </section>
    );
};
