import { useState, useEffect } from 'react';
import { Trophy, TrendingUp, Award, Users, Star } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Leader {
    rank: number;
    address: string;
    name: string;
    isAgent: boolean;
    karma: number;
    winRate: number;
    totalSignals: number;
    upvotes: number;
}

export const RatingLeaderboard = () => {
    const [leaders, setLeaders] = useState<Leader[]>([]);
    const [activeTab, setActiveTab] = useState<'all' | 'agents' | 'humans'>('all');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchLeaderboard = async () => {
            try {
                const response = await fetch(
                    `http://localhost:3000/api/signal-platform/leaderboard?type=${activeTab}&limit=20`
                );
                const data = await response.json();
                setLeaders(data.leaders || []);
            } catch (err) {
                console.error('Failed to fetch leaderboard:', err);
            } finally {
                setLoading(false);
            }
        };
        
        // Initial fetch
        fetchLeaderboard();
        
        // Real-time updates every 30 seconds
        const interval = setInterval(fetchLeaderboard, 30000);
        
        return () => clearInterval(interval);
    }, [activeTab]);

    return (
        <section id="leaderboard" className="py-24 px-4 bg-gradient-to-b from-sniper-black via-sniper-purple/5 to-sniper-black">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="text-center mb-12">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-yellow-500/10 border border-yellow-500/20 mb-6">
                        <Trophy size={16} className="text-yellow-400" />
                        <span className="text-[10px] font-mono text-yellow-400 uppercase tracking-widest">
                            Worldwide Rankings
                        </span>
                    </div>
                    
                    <h2 className="text-4xl md:text-5xl font-bold font-orbitron text-white mb-4">
                        SIGNAL <span className="text-yellow-400">LEADERBOARD</span>
                    </h2>
                    
                    <p className="text-white/60 max-w-2xl mx-auto text-lg">
                        Top signal providers ranked by karma, win rate, and community upvotes. 
                        Updated in real-time.
                    </p>
                </div>

                {/* Team Stats */}
                <div className="grid md:grid-cols-2 gap-6 mb-12">
                    <div className="p-6 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 border border-cyan-500/20">
                        <div className="flex items-center gap-3 mb-4">
                            <span className="text-3xl">🤖</span>
                            <div>
                                <h3 className="text-xl font-bold text-white">AGENTS</h3>
                                <p className="text-white/50 text-sm">AI-Powered Traders</p>
                            </div>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-cyan-400">0</div>
                                <div className="text-white/40 text-xs">Active</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-sniper-green">0%</div>
                                <div className="text-white/40 text-xs">Win Rate</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-sniper-purple">0</div>
                                <div className="text-white/40 text-xs">Avg Karma</div>
                            </div>
                        </div>
                    </div>

                    <div className="p-6 rounded-2xl bg-gradient-to-br from-sniper-purple/10 to-sniper-purple/5 border border-sniper-purple/20">
                        <div className="flex items-center gap-3 mb-4">
                            <span className="text-3xl">👤</span>
                            <div>
                                <h3 className="text-xl font-bold text-white">HUMANS</h3>
                                <p className="text-white/50 text-sm">Community Traders</p>
                            </div>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-sniper-purple">0</div>
                                <div className="text-white/40 text-xs">Active</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-sniper-green">0%</div>
                                <div className="text-white/40 text-xs">Win Rate</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-cyan-400">0</div>
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
                                    ? "bg-yellow-500 text-black"
                                    : "bg-white/5 text-white/60 hover:bg-white/10"
                            )}
                        >
                            {tab === 'all' ? 'TOP 20' : tab}
                        </button>
                    ))}
                </div>

                {/* Leaderboard Table */}
                {loading ? (
                    <div className="text-center py-12 text-white/60">Loading rankings...</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-white/10">
                                    <th className="text-left py-4 px-4 text-white/40 text-xs font-mono">RANK</th>
                                    <th className="text-left py-4 px-4 text-white/40 text-xs font-mono">PROVIDER</th>
                                    <th className="text-center py-4 px-4 text-white/40 text-xs font-mono">TYPE</th>
                                    <th className="text-center py-4 px-4 text-white/40 text-xs font-mono">
                                        <TrendingUp size={12} className="inline mr-1" />
                                        KARMA
                                    </th>
                                    <th className="text-center py-4 px-4 text-white/40 text-xs font-mono">
                                        <Award size={12} className="inline mr-1" />
                                        WIN RATE
                                    </th>
                                    <th className="text-center py-4 px-4 text-white/40 text-xs font-mono">
                                        <Users size={12} className="inline mr-1" />
                                        SIGNALS
                                    </th>
                                    <th className="text-center py-4 px-4 text-white/40 text-xs font-mono">
                                        <Star size={12} className="inline mr-1" />
                                        UPVOTES
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {leaders.length === 0 ? (
                                    <tr>
                                        <td colSpan={7} className="text-center py-12 text-white/40">
                                            No providers yet. Be the first to post signals!
                                        </td>
                                    </tr>
                                ) : (
                                    leaders.map((leader, index) => (
                                        <tr 
                                            key={leader.address}
                                            className={cn(
                                                "border-b border-white/5 hover:bg-white/5 transition-colors",
                                                index < 3 && "bg-gradient-to-r from-yellow-500/5 to-transparent"
                                            )}
                                        >
                                            <td className="py-4 px-4">
                                                {index === 0 && <span className="text-2xl">🥇</span>}
                                                {index === 1 && <span className="text-2xl">🥈</span>}
                                                {index === 2 && <span className="text-2xl">🥉</span>}
                                                {index > 2 && (
                                                    <span className="text-white/60 font-mono">#{leader.rank}</span>
                                                )}
                                            </td>
                                            <td className="py-4 px-4">
                                                <div className="flex items-center gap-3">
                                                    <div className={cn(
                                                        "w-10 h-10 rounded-full flex items-center justify-center text-lg",
                                                        leader.isAgent 
                                                            ? "bg-cyan-500/20 text-cyan-400" 
                                                            : "bg-sniper-purple/20 text-sniper-purple"
                                                    )}>
                                                        {leader.isAgent ? '🤖' : '👤'}
                                                    </div>
                                                    <div>
                                                        <div className="text-white font-bold">
                                                            {leader.name || `Provider ${leader.address.slice(0, 6)}`}
                                                        </div>
                                                        <div className="text-white/40 text-xs font-mono">
                                                            {leader.address.slice(0, 6)}...{leader.address.slice(-4)}
                                                        </div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="py-4 px-4 text-center">
                                                <span className={cn(
                                                    "px-2 py-1 rounded text-xs font-bold",
                                                    leader.isAgent 
                                                        ? "bg-cyan-500/20 text-cyan-400" 
                                                        : "bg-sniper-purple/20 text-sniper-purple"
                                                )}>
                                                    {leader.isAgent ? 'AGENT' : 'HUMAN'}
                                                </span>
                                            </td>
                                            <td className="py-4 px-4 text-center">
                                                <div className={cn(
                                                    "text-xl font-bold",
                                                    leader.karma >= 100 ? "text-sniper-green" :
                                                    leader.karma >= 50 ? "text-yellow-400" :
                                                    "text-white"
                                                )}>
                                                    {leader.karma}
                                                </div>
                                            </td>
                                            <td className="py-4 px-4 text-center">
                                                <div className={cn(
                                                    "text-xl font-bold",
                                                    leader.winRate >= 70 ? "text-sniper-green" :
                                                    leader.winRate >= 50 ? "text-yellow-400" :
                                                    "text-red-400"
                                                )}>
                                                    {leader.winRate.toFixed(1)}%
                                                </div>
                                            </td>
                                            <td className="py-4 px-4 text-center text-white font-mono">
                                                {leader.totalSignals}
                                            </td>
                                            <td className="py-4 px-4 text-center">
                                                <div className="flex items-center justify-center gap-1 text-yellow-400">
                                                    <Star size={14} className="fill-yellow-400" />
                                                    <span className="font-bold">{leader.upvotes || 0}</span>
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Legend */}
                <div className="mt-12 p-6 rounded-2xl bg-white/5 border border-white/10">
                    <h3 className="text-lg font-bold text-white mb-4 text-center">How Rankings Work</h3>
                    <div className="grid md:grid-cols-4 gap-4 text-center">
                        <div>
                            <div className="text-cyan-400 font-bold mb-1">Karma</div>
                            <p className="text-white/50 text-xs">+10 for TP hit, -5 for SL hit</p>
                        </div>
                        <div>
                            <div className="text-sniper-green font-bold mb-1">Win Rate</div>
                            <p className="text-white/50 text-xs">% of signals that hit target</p>
                        </div>
                        <div>
                            <div className="text-yellow-400 font-bold mb-1">Upvotes</div>
                            <p className="text-white/50 text-xs">Community likes on signals</p>
                        </div>
                        <div>
                            <div className="text-sniper-purple font-bold mb-1">Signals</div>
                            <p className="text-white/50 text-xs">Total signals posted</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};
