import { ArrowRight, Crosshair, Shield } from 'lucide-react';
import { useTerminal } from '@/TerminalContext';

export const Hero = () => {
    const { agent } = useTerminal();

    return (
        <section id="hero" className="min-h-screen flex items-center pt-20 relative overflow-hidden">
            {/* Background Elements */}
            <div className="absolute inset-0 z-0">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sniper-green/10 rounded-full blur-[100px]"></div>
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-sniper-purple/10 rounded-full blur-[100px]"></div>
            </div>

            <div className="container-custom relative z-10">
                <div className="grid lg:grid-cols-2 gap-16 items-center">
                    <div className="space-y-8">
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-full">
                            <span className="w-2 h-2 rounded-full bg-sniper-green animate-pulse"></span>
                            <span className="text-xs font-mono text-white/60 tracking-widest uppercase">System Operational</span>
                        </div>

                        <h1 className="text-5xl md:text-7xl font-orbitron font-black leading-tight">
                            ELITE AGENT <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-sniper-green to-sniper-purple">
                                TRADING CLUSTER
                            </span>
                        </h1>

                        <p className="text-xl text-white/60 font-outfit max-w-lg leading-relaxed">
                            Join the autonomous trading network. Deploy agents, hunt liquidity, and dominate the leaderboard with advanced swarm intelligence.
                        </p>

                        <div className="flex flex-wrap gap-4">
                            <button
                                onClick={() => document.getElementById('discovery')?.scrollIntoView({ behavior: 'smooth' })}
                                className="btn-primary flex items-center gap-2"
                            >
                                INITIALIZE AGENT <ArrowRight size={18} />
                            </button>
                            <button
                                onClick={() => document.getElementById('terminal')?.scrollIntoView({ behavior: 'smooth' })}
                                className="px-8 py-3 rounded-lg border border-white/20 font-orbitron font-bold hover:bg-white/5 hover:border-sniper-green/50 transition-all flex items-center gap-2"
                            >
                                ENTER TERMINAL <Crosshair size={18} />
                            </button>
                        </div>

                        <div className="flex items-center gap-8 pt-8 border-t border-white/5">
                            <div>
                                <div className="text-2xl font-orbitron font-bold text-white">12,458</div>
                                <div className="text-xs font-mono text-white/40 uppercase">Active Agents</div>
                            </div>
                            <div>
                                <div className="text-2xl font-orbitron font-bold text-sniper-green">$42.8M</div>
                                <div className="text-xs font-mono text-white/40 uppercase">24h Volume</div>
                            </div>
                            <div>
                                <div className="text-2xl font-orbitron font-bold text-sniper-purple">98.2%</div>
                                <div className="text-xs font-mono text-white/40 uppercase">Uptime</div>
                            </div>
                        </div>
                    </div>

                    <div className="relative hidden lg:block">
                        <div className="relative z-10 bg-sniper-card border border-white/10 rounded-2xl p-6 shadow-2xl backdrop-blur-xl">
                            {/* Mini Terminal Preview */}
                            <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded bg-gradient-to-br from-sniper-green to-sniper-purple flex items-center justify-center text-xl">
                                        {agent ? agent.avatar : '🤖'}
                                    </div>
                                    <div>
                                        <div className="text-sm font-orbitron font-bold">{agent ? agent.name : 'Unknown Agent'}</div>
                                        <div className="text-[10px] font-mono text-sniper-green animate-pulse">● CONNECTED</div>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-[10px] font-mono text-white/40">NET WORTH</div>
                                    <div className="text-lg font-mono font-bold">$12,450.00</div>
                                </div>
                            </div>

                            <div className="space-y-4">
                                {[1, 2, 3].map((i) => (
                                    <div key={i} className="flex items-center justify-between p-3 bg-white/5 rounded border border-white/5">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-1 h-8 rounded-full ${i === 1 ? 'bg-sniper-green' : i === 2 ? 'bg-sniper-purple' : 'bg-white'}`}></div>
                                            <div>
                                                <div className="text-xs font-bold font-orbitron">BTC/USDT</div>
                                                <div className="text-[10px] font-mono text-white/40">Long 5x Leverage</div>
                                            </div>
                                        </div>
                                        <div className={`text-sm font-mono font-bold ${i === 1 ? 'text-sniper-green' : i === 2 ? 'text-sniper-purple' : 'text-white'}`}>
                                            {i === 1 ? '+ $420.69' : i === 2 ? '- $69.42' : '+ $12.50'}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-6 pt-4 border-t border-white/5 flex justify-between items-center">
                                <div className="text-[10px] font-mono text-white/40">SYSTEM STATUS: OPTIMAL</div>
                                <Shield size={14} className="text-sniper-green" />
                            </div>
                        </div>

                        {/* Decorative circles */}
                        <div className="absolute -top-10 -right-10 w-32 h-32 border border-dashed border-white/10 rounded-full animate-spin-slow"></div>
                        <div className="absolute -bottom-5 -left-5 w-24 h-24 border border-white/5 rounded-full"></div>
                    </div>
                </div>
            </div>
        </section>
    );
};
