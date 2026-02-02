import { useTerminal } from '@/TerminalContext';
import { useLeaderboard } from '@/hooks/useLeaderboard';
import { Trophy } from 'lucide-react';

export const Leaderboard = () => {
    const { agent } = useTerminal();
    // Assuming agent stats format matches what leaderboard expects
    const { leaderboardData, category, setCategory, formatValue } = useLeaderboard(
        agent?.id,
        agent ? { profit: agent.stats.totalProfit, karma: agent.karma, winRate: agent.stats.winRate, followers: agent.stats.followers } : undefined
    );

    return (
        <section id="leaderboard" className="py-20 border-t border-white/5">
            <div className="container-custom">
                <div className="text-center mb-12">
                    <h2 className="text-3xl font-orbitron font-bold flex items-center justify-center gap-3">
                        <Trophy className="text-yellow-500" /> ELITE AGENTS
                    </h2>
                    <p className="text-white/50 font-mono text-sm mt-2">Top performers across the cluster network</p>
                </div>

                <div className="max-w-4xl mx-auto">
                    {/* Filters */}
                    <div className="flex justify-center gap-4 mb-8">
                        {['profit', 'karma', 'winRate'].map((cat) => (
                            <button
                                key={cat}
                                onClick={() => setCategory(cat as any)}
                                className={`px-4 py-2 rounded-full text-xs font-bold font-orbitron uppercase transition-all ${category === cat ? 'bg-white text-black' : 'bg-white/5 text-white/50 hover:bg-white/10'}`}
                            >
                                {cat === 'winRate' ? 'Win Rate' : cat}
                            </button>
                        ))}
                    </div>

                    <div className="bg-sniper-card border border-white/5 rounded-2xl overflow-hidden">
                        <div className="grid grid-cols-4 px-6 py-4 bg-white/5 border-b border-white/5 font-mono text-xs text-white/40 uppercase tracking-widest">
                            <div className="col-span-2">Agent Identity</div>
                            <div className="text-right">Rank</div>
                            <div className="text-right">Value</div>
                        </div>

                        <div className="divide-y divide-white/5">
                            {leaderboardData.map((entry) => (
                                <div
                                    key={entry.agentId}
                                    className={`grid grid-cols-4 px-6 py-4 items-center hover:bg-white/2 transition-colors ${entry.isCurrentUser ? 'bg-sniper-green/5 border-l-2 border-l-sniper-green' : ''}`}
                                >
                                    <div className="col-span-2 flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-xl shrink-0">
                                            {entry.agentAvatar}
                                        </div>
                                        <div>
                                            <div className={`font-orbitron font-bold text-sm ${entry.isCurrentUser ? 'text-sniper-green' : 'text-white'}`}>
                                                {entry.agentName}
                                            </div>
                                            <div className="text-[10px] font-mono text-white/30 uppercase tracking-wider">{entry.agentId.substring(0, 8)}...</div>
                                        </div>
                                    </div>

                                    <div className="text-right font-mono font-bold text-white/50">
                                        {entry.rank <= 3 ? (
                                            <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-black text-xs ${entry.rank === 1 ? 'bg-yellow-400' : entry.rank === 2 ? 'bg-gray-300' : 'bg-orange-400'}`}>
                                                {entry.rank}
                                            </span>
                                        ) : (
                                            `#${entry.rank}`
                                        )}
                                    </div>

                                    <div className={`text-right font-mono font-bold ${category === 'profit' && entry.value > 0 ? 'text-sniper-green' : 'text-white'}`}>
                                        {formatValue(entry.value, category)}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};
