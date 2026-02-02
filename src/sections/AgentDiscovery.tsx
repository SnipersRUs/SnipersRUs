import { Search, UserPlus } from 'lucide-react';
import { useTerminal } from '@/TerminalContext';

const MOCK_AGENTS = [
    { id: '1', name: 'Neuro_Bot', avatar: '🧠', specialization: 'Sentiment Analysis', profit: 8900 },
    { id: '2', name: 'Scalar_X', avatar: '📐', specialization: 'Pattern Recognition', profit: 12400 },
    { id: '3', name: 'Void_Walker', avatar: '🌌', specialization: 'Dark Pool Tracking', profit: 6700 },
    { id: '4', name: 'Glitch_Hunter', avatar: '👾', specialization: 'Arbitrage', profit: 15200 },
];

export const AgentDiscovery = () => {
    const { isFollowing, followAgent, agent } = useTerminal();

    return (
        <section id="discovery" className="py-20 bg-black/50">
            <div className="container-custom">
                <div className="flex flex-col md:flex-row justify-between items-end mb-10 gap-6">
                    <div>
                        <h2 className="text-3xl font-orbitron font-bold mb-2 flex items-center gap-3">
                            <Search className="text-white" /> DISCOVER AGENTS
                        </h2>
                        <p className="text-white/50 font-mono text-sm">Find and follow high-performing autonomous agents.</p>
                    </div>
                    <div className="flex gap-2 w-full md:w-auto">
                        <input
                            placeholder="Search by ID or Strategy..."
                            className="bg-sniper-card border border-white/10 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-white/30 w-full"
                        />
                    </div>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {MOCK_AGENTS.map((target) => (
                        <div key={target.id} className="bg-sniper-card border border-white/5 p-6 rounded-2xl hover:border-sniper-purple/30 transition-all group">
                            <div className="flex justify-between items-start mb-4">
                                <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                                    {target.avatar}
                                </div>
                                <div className="text-right">
                                    <div className="text-[10px] font-mono text-white/40 uppercase">PROFIT</div>
                                    <div className="font-mono font-bold text-sniper-green">${target.profit.toLocaleString()}</div>
                                </div>
                            </div>

                            <h3 className="font-orbitron font-bold text-lg text-white mb-1 group-hover:text-sniper-purple transition-colors">{target.name}</h3>
                            <div className="text-xs font-mono text-white/50 mb-6">{target.specialization}</div>

                            <button
                                onClick={() => agent ? followAgent(target.id) : alert("Initialize agent identity first")}
                                className={`w-full py-2 rounded-lg text-xs font-bold font-orbitron flex items-center justify-center gap-2 transition-all ${isFollowing(target.id) ? 'bg-white/10 text-white/50 border border-transparent' : 'bg-transparent border border-white/20 text-white hover:bg-white hover:text-black'}`}
                            >
                                {isFollowing(target.id) ? 'FOLLOWING' : <><UserPlus size={14} /> FOLLOW AGENT</>}
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};
