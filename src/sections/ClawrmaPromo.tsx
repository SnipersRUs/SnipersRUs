import { Shield, ArrowRight, TrendingUp, Target, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

export const ClawrmaPromo = () => {
    const scrollToSignalBetting = () => {
        const element = document.getElementById('signal-betting');
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    };

    return (
        <section className="py-16 px-4 relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-cyan-500/10" />
            <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent" />
            <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent" />
            
            <div className="max-w-6xl mx-auto relative">
                <div className={cn(
                    "p-8 md:p-12 rounded-3xl relative overflow-hidden",
                    "bg-gradient-to-br from-cyan-500/10 via-black/80 to-purple-500/10",
                    "border border-cyan-500/30",
                    "hover:border-cyan-500/50 transition-all duration-500"
                )}>
                    {/* Animated Background Grid */}
                    <div className="absolute inset-0 opacity-20">
                        <div className="absolute inset-0" style={{
                            backgroundImage: `
                                linear-gradient(cyan 1px, transparent 1px),
                                linear-gradient(90deg, cyan 1px, transparent 1px)
                            `,
                            backgroundSize: '40px 40px',
                            opacity: 0.1
                        }} />
                    </div>

                    {/* Glow Effects */}
                    <div className="absolute -top-20 -right-20 w-64 h-64 bg-cyan-500/20 rounded-full blur-3xl" />
                    <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-purple-500/20 rounded-full blur-3xl" />

                    <div className="relative z-10 flex flex-col lg:flex-row items-center gap-8">
                        {/* Left: Brand */}
                        <div className="flex-1 text-center lg:text-left">
                            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/30 mb-6">
                                <Shield size={16} className="text-cyan-400" />
                                <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest">
                                    Powered by Clawrma
                                </span>
                            </div>

                            <h2 className="text-4xl md:text-5xl font-bold font-orbitron mb-4">
                                <span className="text-white">SIGNAL</span>{' '}
                                <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                                    BETTING
                                </span>
                            </h2>

                            <p className="text-white/60 text-lg mb-6 max-w-xl">
                                Bet on whether trading signals hit their targets. 
                                Real USDC payouts on Base. Verified by Clawrma.
                            </p>

                            <div className="flex flex-wrap gap-4 justify-center lg:justify-start">
                                <a
                                    href="https://clawrma.com"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className={cn(
                                        "group inline-flex items-center gap-3 px-8 py-4",
                                        "bg-gradient-to-r from-cyan-500 to-purple-500",
                                        "hover:from-cyan-400 hover:to-purple-400",
                                        "text-white font-bold font-orbitron rounded-xl",
                                        "transition-all duration-300 hover:scale-105",
                                        "shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40"
                                    )}
                                >
                                    CLAWrMA
                                    <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                                </a>
                                <button
                                    onClick={scrollToSignalBetting}
                                    className={cn(
                                        "inline-flex items-center gap-3 px-8 py-4",
                                        "bg-white/10 hover:bg-white/20",
                                        "text-white font-bold font-orbitron rounded-xl",
                                        "transition-all duration-300",
                                        "border border-white/20"
                                    )}
                                >
                                    VIEW SIGNALS
                                </button>
                            </div>
                        </div>

                        {/* Right: Features */}
                        <div className="flex-1 w-full max-w-md">
                            <div className="grid grid-cols-1 gap-4">
                                {[
                                    { 
                                        icon: Target, 
                                        title: "HIT or MISS", 
                                        desc: "Bet on signal outcomes",
                                        color: "cyan"
                                    },
                                    { 
                                        icon: TrendingUp, 
                                        title: "Real Odds", 
                                        desc: "2.1x average payout",
                                        color: "green"
                                    },
                                    { 
                                        icon: Zap, 
                                        title: "USDC on Base", 
                                        desc: "Instant settlements",
                                        color: "purple"
                                    },
                                ].map((feature, idx) => (
                                    <div
                                        key={idx}
                                        className={cn(
                                            "flex items-center gap-4 p-4 rounded-xl",
                                            "bg-white/5 border border-white/10",
                                            "hover:bg-white/10 transition-all"
                                        )}
                                    >
                                        <div className={cn(
                                            "w-12 h-12 rounded-xl flex items-center justify-center",
                                            feature.color === 'cyan' && "bg-cyan-500/20 text-cyan-400",
                                            feature.color === 'green' && "bg-sniper-green/20 text-sniper-green",
                                            feature.color === 'purple' && "bg-sniper-purple/20 text-sniper-purple"
                                        )}>
                                            <feature.icon size={24} />
                                        </div>
                                        <div>
                                            <div className="text-white font-bold">{feature.title}</div>
                                            <div className="text-white/50 text-sm">{feature.desc}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};
