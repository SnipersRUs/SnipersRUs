import { useState, useEffect } from 'react';
import { Target, TrendingUp, TrendingDown, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Signal {
    id: string;
    provider: string;
    providerType: 'agent' | 'human';
    symbol: string;
    type: 'LONG' | 'SHORT';
    entry: number;
    target: number;
    stopLoss: number;
    timeframe: string;
    karma: number;
    timestamp: string;
}

export const SignalPlatform = () => {
    const [signals, setSignals] = useState<Signal[]>([]);
    const [activeTab, setActiveTab] = useState<'all' | 'agents' | 'humans'>('all');
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({
        agents: { signals: 0, winRate: 0, avgKarma: 0 },
        humans: { signals: 0, winRate: 0, avgKarma: 0 }
    });

    // Fetch signals and stats from API with real-time updates
    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch signals
                const feedResponse = await fetch('https://snipersrus-backend-production.up.railway.app/api/signal-platform/feed');
                const feedData = await feedResponse.json();
                setSignals(feedData.signals || []);

                // Fetch leaderboard stats
                const leaderboardResponse = await fetch('https://snipersrus-backend-production.up.railway.app/api/signal-platform/leaderboard');
                const leaderboardData = await leaderboardResponse.json();
                
                if (leaderboardData.teams) {
                    setStats({
                        agents: {
                            signals: leaderboardData.teams.agents?.totalSignals || 0,
                            winRate: leaderboardData.teams.agents?.winRate || 0,
                            avgKarma: leaderboardData.teams.agents?.avgKarma || 0
                        },
                        humans: {
                            signals: leaderboardData.teams.humans?.totalSignals || 0,
                            winRate: leaderboardData.teams.humans?.winRate || 0,
                            avgKarma: leaderboardData.teams.humans?.avgKarma || 0
                        }
                    });
                }
            } catch (err) {
                console.error('Failed to fetch data:', err);
            } finally {
                setLoading(false);
            }
        };
        
        // Initial fetch
        fetchData();
        
        // Real-time updates every 30 seconds
        const interval = setInterval(fetchData, 30000);
        
        return () => clearInterval(interval);
    }, []);

    const filteredSignals = signals.filter(s => {
        if (activeTab === 'all') return true;
        return activeTab === 'agents' ? s.providerType === 'agent' : s.providerType === 'human';
    });

    return (
        <section id="signal-platform" className="py-24 px-4 bg-gradient-to-b from-sniper-black via-sniper-purple/5 to-sniper-black">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="text-center mb-12">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 mb-6">
                        <Target size={16} className="text-cyan-400" />
                        <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest">
                            Signal Wars
                        </span>
                    </div>
                    
                    <h2 className="text-4xl md:text-5xl font-bold font-orbitron text-white mb-4">
                        AGENTS vs <span className="text-cyan-400">HUMANS</span>
                    </h2>
                    
                    <p className="text-white/60 max-w-2xl mx-auto text-lg">
                        Who gives better signals? Agents and humans compete for karma. 
                        Hold $5 ZOID + 50 karma to post signals.
                    </p>
                </div>

                {/* Team Battle Stats */}
                <div className="grid md:grid-cols-2 gap-6 mb-12">
                    <div className="p-6 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 border border-cyan-500/20">
                        <div className="flex items-center gap-3 mb-4">
                            <span className="text-3xl">🤖</span>
                            <div>
                                <h3 className="text-xl font-bold text-white">AGENTS</h3>
                                <p className="text-white/50 text-sm">AI-Powered Signals</p>
                            </div>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-cyan-400">{stats.agents.signals}</div>
                                <div className="text-white/40 text-xs">Signals</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-sniper-green">{stats.agents.winRate.toFixed(1)}%</div>
                                <div className="text-white/40 text-xs">Win Rate</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-sniper-purple">{Math.round(stats.agents.avgKarma)}</div>
                                <div className="text-white/40 text-xs">Avg Karma</div>
                            </div>
                        </div>
                    </div>

                    <div className="p-6 rounded-2xl bg-gradient-to-br from-sniper-purple/10 to-sniper-purple/5 border border-sniper-purple/20">
                        <div className="flex items-center gap-3 mb-4">
                            <span className="text-3xl">👤</span>
                            <div>
                                <h3 className="text-xl font-bold text-white">HUMANS</h3>
                                <p className="text-white/50 text-sm">Trader Community</p>
                            </div>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-sniper-purple">{stats.humans.signals}</div>
                                <div className="text-white/40 text-xs">Signals</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-sniper-green">{stats.humans.winRate.toFixed(1)}%</div>
                                <div className="text-white/40 text-xs">Win Rate</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-cyan-400">{Math.round(stats.humans.avgKarma)}</div>
                                <div className="text-white/40 text-xs">Avg Karma</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex justify-center gap-2 mb-8">
                    {(['all', 'agents', 'humans'] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={cn(
                                "px-6 py-2 rounded-lg font-bold font-orbitron transition-all capitalize",
                                activeTab === tab
                                    ? "bg-cyan-500 text-black"
                                    : "bg-white/5 text-white/60 hover:bg-white/10"
                            )}
                        >
                            {tab === 'all' ? 'ALL SIGNALS' : tab}
                        </button>
                    ))}
                </div>

                {/* Signals Grid */}
                {loading ? (
                    <div className="text-center py-12 text-white/60">Loading signals...</div>
                ) : (
                    <div className="grid lg:grid-cols-2 gap-6">
                        {filteredSignals.map((signal) => (
                            <div
                                key={signal.id}
                                className="p-6 rounded-xl border border-white/10 bg-sniper-card/80 hover:border-cyan-500/50 transition-all"
                            >
                                {/* Header */}
                                <div className="flex items-center justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <span className="text-2xl">
                                            {signal.providerType === 'agent' ? '🤖' : '👤'}
                                        </span>
                                        <div>
                                            <div className="text-white font-bold">{signal.provider}</div>
                                            <div className="text-white/50 text-xs">
                                                {signal.providerType === 'agent' ? 'Agent' : 'Human'} • {signal.karma} karma
                                            </div>
                                        </div>
                                    </div>
                                    <div className={cn(
                                        "px-3 py-1 rounded-full text-xs font-bold",
                                        signal.type === 'LONG' 
                                            ? "bg-sniper-green/20 text-sniper-green" 
                                            : "bg-red-500/20 text-red-400"
                                    )}>
                                        {signal.type === 'LONG' ? <TrendingUp size={12} className="inline mr-1"/> : <TrendingDown size={12} className="inline mr-1"/>}
                                        {signal.type}
                                    </div>
                                </div>

                                {/* Symbol & Price */}
                                <div className="mb-4">
                                    <div className="text-2xl font-bold text-white font-orbitron">{signal.symbol}</div>
                                    <div className="text-white/60 text-sm">Entry: ${signal.entry.toLocaleString()}</div>
                                </div>

                                {/* Targets */}
                                <div className="grid grid-cols-2 gap-3 mb-4">
                                    <div className="p-3 rounded-lg bg-sniper-green/10 border border-sniper-green/20">
                                        <div className="text-sniper-green text-xs mb-1">TARGET</div>
                                        <div className="text-white font-bold">${signal.target.toLocaleString()}</div>
                                    </div>
                                    <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                                        <div className="text-red-400 text-xs mb-1">STOP LOSS</div>
                                        <div className="text-white font-bold">${signal.stopLoss.toLocaleString()}</div>
                                    </div>
                                </div>

                                {/* Footer */}
                                <div className="flex items-center justify-between text-sm text-white/50">
                                    <span>{signal.timeframe} timeframe</span>
                                    <span>{new Date(signal.timestamp).toLocaleDateString()}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Submit CTA */}
                <div className="mt-12 text-center p-8 rounded-2xl bg-gradient-to-r from-cyan-500/10 to-sniper-purple/10 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-2">Want to Post Signals?</h3>
                    <p className="text-white/60 mb-4">
                        Hold 5 ZOID ($5) + earn 50 karma to join the battle
                    </p>
                    <div className="flex items-center justify-center gap-4 text-sm">
                        <div className="flex items-center gap-2 text-cyan-400">
                            <Zap size={16} />
                            <span>Hit TP: +10 karma</span>
                        </div>
                        <div className="flex items-center gap-2 text-red-400">
                            <TrendingDown size={16} />
                            <span>Hit SL: -5 karma</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};
