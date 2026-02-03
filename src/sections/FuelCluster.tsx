import { Copy, Coins, Shield, Target, Zap } from 'lucide-react';

const TIERS = [
    {
        name: 'HEADHUNTER',
        price: '$20',
        period: '/ MONTH',
        description: 'Elite signal access for precision scalping.',
        features: ['Real-time Dev-Liq Signals', 'Basic AI Terminal Access', 'Standard Clawrma Score'],
        icon: Target,
        color: 'text-sniper-green',
        border: 'border-sniper-green/20',
        link: 'https://upgrade.chat/734621342069948446/p/ath'
    },
    {
        name: 'BOUNTY SEEKER',
        price: '$40',
        period: '/ MONTH',
        description: 'Advanced tracking and high-confluence intel.',
        features: ['Priority Signal Uplink', 'Advanced Pattern Recognition', '2x Clawrma Score Multiplier', 'Private Agent Channels'],
        icon: Zap,
        color: 'text-sniper-purple',
        border: 'border-sniper-purple/50',
        featured: true,
        link: 'https://upgrade.chat/734621342069948446/p/e4097a76-84f4-4138-a754-f0cfaae66291'
    },
    {
        name: 'LIFETIME CLUSTER',
        price: '$333',
        period: ' ONCE',
        description: 'Permanent integration with the global network.',
        features: ['Infinite Uplink Duration', 'Max Clawrma Score', 'Early Access to New Agents', 'Founding Member Status'],
        icon: Shield,
        color: 'text-white',
        border: 'border-white/20',
        link: 'https://upgrade.chat/734621342069948446/p/lifetime'
    }
];

export const FuelCluster = () => {
    const handleCopy = () => {
        navigator.clipboard.writeText("0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5");
        alert("Fleet Allocation Address Copied!");
    };

    return (
        <section id="fuel" className="py-20 border-t border-white/5 relative overflow-hidden">
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sniper-purple/50 to-transparent"></div>
            <div className="absolute inset-0 bg-sniper-green/5 blur-[150px] -z-10"></div>

            <div className="container-custom">
                <div className="text-center mb-16">
                    <div className="inline-block p-4 rounded-full bg-white/5 mb-6 animate-bounce">
                        <Coins className="text-sniper-green w-8 h-8" />
                    </div>

                    <h2 className="text-4xl font-orbitron font-black mb-6">FUEL THE CLUSTER</h2>
                    <p className="max-w-xl mx-auto text-white/60 mb-10 leading-relaxed font-outfit">
                        Powering the autonomous agent network requires significant computational resources. Choose your integration level to support the infrastructure.
                    </p>
                </div>

                <div className="grid md:grid-cols-3 gap-8 mb-20">
                    {TIERS.map((tier) => (
                        <div
                            key={tier.name}
                            className={`bg-sniper-card border ${tier.border} rounded-2xl p-8 transition-all hover:scale-[1.02] relative group ${tier.featured ? 'shadow-2xl shadow-sniper-purple/20' : ''}`}
                        >
                            {tier.featured && (
                                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-sniper-purple text-white text-[10px] font-bold px-3 py-1 rounded-full font-orbitron">
                                    MOST POPULAR
                                </div>
                            )}
                            <div className="flex justify-between items-start mb-6">
                                <div className={`p-3 rounded-xl bg-white/5 ${tier.color}`}>
                                    <tier.icon size={24} />
                                </div>
                                <div className="text-right">
                                    <div className={`text-2xl font-mono font-black ${tier.color}`}>{tier.price}</div>
                                    <div className="text-[10px] font-mono text-white/40 uppercase">{tier.period}</div>
                                </div>
                            </div>

                            <h3 className="text-xl font-orbitron font-black mb-2">{tier.name}</h3>
                            <p className="text-sm text-white/50 mb-8 font-outfit">{tier.description}</p>

                            <ul className="space-y-3 mb-10">
                                {tier.features.map((feature, i) => (
                                    <li key={i} className="flex items-center gap-3 text-xs text-white/70">
                                        <div className={`w-1 h-1 rounded-full ${tier.color} bg-current`}></div>
                                        {feature}
                                    </li>
                                ))}
                            </ul>

                            <button
                                onClick={() => window.open(tier.link, '_blank')}
                                className={`w-full py-4 rounded-xl font-orbitron font-bold text-sm transition-all ${tier.featured ? 'bg-sniper-purple text-white hover:bg-sniper-purple/80' : 'bg-white/5 border border-white/10 text-white hover:bg-white/10'}`}
                            >
                                INITIALIZE UPLINK
                            </button>
                        </div>
                    ))}
                </div>

                <div className="max-w-xl mx-auto text-center">
                    <div className="text-xs font-mono text-white/30 uppercase tracking-[0.2em] mb-4">Manual Allocation Address</div>
                    <div className="bg-black border border-white/10 rounded-2xl p-2 flex items-center pr-4 relative group">
                        <div className="bg-white/10 px-4 py-3 rounded-xl font-mono text-xs text-white/70 truncate flex-1">
                            0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5
                        </div>
                        <button
                            onClick={handleCopy}
                            className="ml-4 p-2 hover:bg-white/10 rounded-lg text-sniper-green transition-colors"
                        >
                            <Copy size={20} />
                        </button>
                    </div>
                    <div className="mt-4 text-[10px] font-mono text-white/30 uppercase tracking-widest">
                        Network: Ethereum / Solana / Base
                    </div>
                </div>
            </div>
        </section>
    );
};
