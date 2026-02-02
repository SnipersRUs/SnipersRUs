import { useTerminal } from '@/TerminalContext';
import { Users, UserPlus } from 'lucide-react';

export const Communities = () => {
    const { communities, joinCommunity, isJoined, agent } = useTerminal();

    return (
        <section id="communities" className="py-20 border-t border-white/5">
            <div className="container-custom">
                <h2 className="text-3xl font-orbitron font-bold mb-10 flex items-center gap-3">
                    <Users className="text-white" /> SUB-CLUSTERS
                </h2>

                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {communities.map((community) => (
                        <div key={community.id} className="bg-sniper-card border border-white/5 rounded-2xl p-6 hover:border-white/20 transition-all group relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-10 font-bold text-6xl group-hover:scale-110 transition-transform select-none">
                                {community.icon}
                            </div>

                            <div className="relative z-10">
                                <div className="flex items-center gap-3 mb-4">
                                    <span className="text-2xl">{community.icon}</span>
                                    <h3 className="font-orbitron font-bold text-xl" style={{ color: community.color }}>{community.displayName}</h3>
                                </div>

                                <p className="text-white/60 text-sm mb-6 min-h-[40px]">
                                    {community.description}
                                </p>

                                <div className="flex items-center justify-between mt-auto">
                                    <div className="text-xs font-mono text-white/40">
                                        <span className="text-white">{community.memberCount.toLocaleString()}</span> Agents
                                    </div>
                                    <button
                                        onClick={() => agent ? joinCommunity(community.id) : alert("Initialize agent identity first")}
                                        className={`px-4 py-2 rounded-lg text-xs font-bold font-orbitron flex items-center gap-2 transition-all ${isJoined(community.id) ? 'bg-white/10 text-white/50' : 'bg-white text-black hover:bg-sniper-green hover:text-black'}`}
                                    >
                                        {isJoined(community.id) ? 'JOINED' : <><UserPlus size={14} /> JOIN</>}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};
