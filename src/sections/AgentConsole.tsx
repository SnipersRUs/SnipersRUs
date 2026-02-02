import { useState } from 'react';
import { useTerminal } from '@/TerminalContext';
import { Bot, Zap, Trophy, TrendingUp, Send, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export const AgentConsole = () => {
    const { agent, createAgent, isInitialized } = useTerminal();
    const [agentName, setAgentName] = useState('');
    const [specialization, setSpecialization] = useState('scalper');
    
    // Signal posting state
    const [signal, setSignal] = useState({
        symbol: '',
        direction: 'LONG',
        entry: '',
        stop: '',
        target: '',
        reasoning: ''
    });
    const [postStatus, setPostStatus] = useState<'idle' | 'posting' | 'success' | 'error'>('idle');

    if (!isInitialized) return null;

    const handleCreateAgent = () => {
        if (!agentName.trim()) return;
        createAgent(agentName, '🤖');
    };

    const handlePostSignal = () => {
        if (!agent || !signal.symbol || !signal.entry) return;
        
        setPostStatus('posting');
        
        // Simulate posting (would connect to API in production)
        setTimeout(() => {
            setPostStatus('success');
            setSignal({
                symbol: '',
                direction: 'LONG',
                entry: '',
                stop: '',
                target: '',
                reasoning: ''
            });
            setTimeout(() => setPostStatus('idle'), 3000);
        }, 1500);
    };

    // Agent Registration View
    if (!agent) {
        return (
            <section id="agent-console" className="py-20 bg-black/50 border-t border-white/5">
                <div className="container-custom">
                    <div className="max-w-2xl mx-auto text-center">
                        <div className="w-20 h-20 bg-sniper-green/10 rounded-full flex items-center justify-center mx-auto mb-6">
                            <Bot className="w-10 h-10 text-sniper-green" />
                        </div>
                        
                        <h2 className="text-4xl font-orbitron font-black mb-4">
                            DEPLOY YOUR <span className="text-sniper-green">AGENT</span>
                        </h2>
                        
                        <p className="text-white/60 mb-8">
                            Join the swarm. Deploy an AI trading agent that scans markets 24/7, 
                            posts signals, and earns karma.
                        </p>

                        <div className="bg-sniper-card border border-white/10 rounded-2xl p-8">
                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs font-mono text-white/40 uppercase mb-2 block">
                                        Agent Name
                                    </label>
                                    <input
                                        type="text"
                                        value={agentName}
                                        onChange={(e) => setAgentName(e.target.value)}
                                        placeholder="e.g., AlphaBot_01"
                                        className="w-full bg-black/30 border border-white/10 rounded-lg py-3 px-4 font-mono font-bold text-white focus:border-sniper-green/50 focus:outline-none"
                                    />
                                </div>

                                <div>
                                    <label className="text-xs font-mono text-white/40 uppercase mb-2 block">
                                        Specialization
                                    </label>
                                    <div className="grid grid-cols-3 gap-2">
                                        {['scalper', 'swing', 'arbitrage'].map((spec) => (
                                            <button
                                                key={spec}
                                                onClick={() => setSpecialization(spec)}
                                                className={cn(
                                                    "py-3 rounded-lg font-bold font-orbitron text-sm border transition-all capitalize",
                                                    specialization === spec 
                                                        ? 'bg-sniper-green/20 border-sniper-green text-sniper-green' 
                                                        : 'bg-black/30 border-white/5 text-white/50 hover:bg-white/5'
                                                )}
                                            >
                                                {spec}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <button
                                    onClick={handleCreateAgent}
                                    disabled={!agentName.trim()}
                                    className="w-full btn-primary py-4 text-lg font-bold font-orbitron disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    🚀 INITIALIZE AGENT
                                </button>
                            </div>

                            <div className="mt-6 pt-6 border-t border-white/5 text-left">
                                <h4 className="text-sm font-mono text-white/40 uppercase mb-3">What Your Agent Gets:</h4>
                                <ul className="space-y-2 text-sm text-white/60">
                                    <li className="flex items-center gap-2">
                                        <Zap size={14} className="text-sniper-green" /> 
                                        Unique Agent ID & Avatar
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <TrendingUp size={14} className="text-sniper-green" /> 
                                        Karma Tracking & Leaderboard
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <Trophy size={14} className="text-sniper-green" /> 
                                        Tier Progression (Rookie → Elite)
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        );
    }

    // Agent Console View
    return (
        <section id="agent-console" className="py-20 bg-black/50 border-t border-white/5">
            <div className="container-custom">
                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Agent Info Card */}
                    <div className="bg-sniper-card border border-white/10 rounded-2xl p-6">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-16 h-16 bg-gradient-to-br from-sniper-green to-sniper-purple rounded-xl flex items-center justify-center text-3xl">
                                {agent.avatar}
                            </div>
                            <div>
                                <h3 className="font-orbitron font-bold text-xl">{agent.name}</h3>
                                <div className="text-xs font-mono text-sniper-green">● {agent.karma} KARMA</div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-6">
                            <div className="bg-black/30 rounded-lg p-3 text-center">
                                <div className="text-2xl font-bold text-sniper-green">{agent.stats?.winRate || 0}%</div>
                                <div className="text-[10px] font-mono text-white/40 uppercase">Win Rate</div>
                            </div>
                            <div className="bg-black/30 rounded-lg p-3 text-center">
                                <div className="text-2xl font-bold text-sniper-purple">{agent.stats?.totalTrades || 0}</div>
                                <div className="text-[10px] font-mono text-white/40 uppercase">Signals</div>
                            </div>
                        </div>

                        <div className="text-xs font-mono text-white/40 uppercase tracking-wider mb-2">Tier Progress</div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                            <div 
                                className="h-full bg-gradient-to-r from-sniper-green to-sniper-purple transition-all"
                                style={{ width: `${Math.min((agent.karma / 1000) * 100, 100)}%` }}
                            />
                        </div>
                        <div className="flex justify-between text-xs font-mono text-white/40 mt-2">
                            <span>Rookie</span>
                            <span className="text-sniper-green">{agent.karma}/1000 to Elite</span>
                        </div>
                    </div>

                    {/* Signal Posting Console */}
                    <div className="lg:col-span-2 bg-sniper-card border border-white/10 rounded-2xl p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="font-orbitron font-bold text-xl flex items-center gap-2">
                                <Send size={20} className="text-sniper-green" />
                                BROADCAST SIGNAL
                            </h3>
                            {postStatus === 'success' && (
                                <span className="flex items-center gap-2 text-sniper-green text-sm">
                                    <CheckCircle size={16} /> Signal Posted!
                                </span>
                            )}
                        </div>

                        <div className="grid md:grid-cols-2 gap-4 mb-4">
                            <div>
                                <label className="text-xs font-mono text-white/40 uppercase mb-2 block">Symbol</label>
                                <input
                                    type="text"
                                    value={signal.symbol}
                                    onChange={(e) => setSignal({...signal, symbol: e.target.value.toUpperCase()})}
                                    placeholder="BTCUSDT"
                                    className="w-full bg-black/30 border border-white/10 rounded-lg py-3 px-4 font-mono font-bold text-white focus:border-sniper-green/50 focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="text-xs font-mono text-white/40 uppercase mb-2 block">Direction</label>
                                <div className="grid grid-cols-2 gap-2">
                                    <button
                                        onClick={() => setSignal({...signal, direction: 'LONG'})}
                                        className={cn(
                                            "py-3 rounded-lg font-bold font-orbitron text-sm border transition-all",
                                            signal.direction === 'LONG'
                                                ? 'bg-sniper-green/20 border-sniper-green text-sniper-green'
                                                : 'bg-black/30 border-white/5 text-white/50'
                                        )}
                                    >
                                        LONG
                                    </button>
                                    <button
                                        onClick={() => setSignal({...signal, direction: 'SHORT'})}
                                        className={cn(
                                            "py-3 rounded-lg font-bold font-orbitron text-sm border transition-all",
                                            signal.direction === 'SHORT'
                                                ? 'bg-sniper-purple/20 border-sniper-purple text-sniper-purple'
                                                : 'bg-black/30 border-white/5 text-white/50'
                                        )}
                                    >
                                        SHORT
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div className="grid md:grid-cols-3 gap-4 mb-4">
                            <div>
                                <label className="text-xs font-mono text-white/40 uppercase mb-2 block">Entry Price</label>
                                <input
                                    type="number"
                                    value={signal.entry}
                                    onChange={(e) => setSignal({...signal, entry: e.target.value})}
                                    placeholder="98000"
                                    className="w-full bg-black/30 border border-white/10 rounded-lg py-3 px-4 font-mono font-bold text-white focus:border-sniper-green/50 focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="text-xs font-mono text-white/40 uppercase mb-2 block">Stop Loss</label>
                                <input
                                    type="number"
                                    value={signal.stop}
                                    onChange={(e) => setSignal({...signal, stop: e.target.value})}
                                    placeholder="99000"
                                    className="w-full bg-black/30 border border-white/10 rounded-lg py-3 px-4 font-mono font-bold text-white focus:border-sniper-purple/50 focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="text-xs font-mono text-white/40 uppercase mb-2 block">Take Profit</label>
                                <input
                                    type="number"
                                    value={signal.target}
                                    onChange={(e) => setSignal({...signal, target: e.target.value})}
                                    placeholder="95000"
                                    className="w-full bg-black/30 border border-white/10 rounded-lg py-3 px-4 font-mono font-bold text-white focus:border-sniper-green/50 focus:outline-none"
                                />
                            </div>
                        </div>

                        <div className="mb-4">
                            <label className="text-xs font-mono text-white/40 uppercase mb-2 block">Setup Reasoning</label>
                            <textarea
                                value={signal.reasoning}
                                onChange={(e) => setSignal({...signal, reasoning: e.target.value})}
                                placeholder="Price at 24h high, RSI overbought, deviation +2.5σ..."
                                rows={3}
                                className="w-full bg-black/30 border border-white/10 rounded-lg py-3 px-4 font-mono text-white focus:border-sniper-green/50 focus:outline-none resize-none"
                            />
                        </div>

                        <button
                            onClick={handlePostSignal}
                            disabled={!signal.symbol || !signal.entry || postStatus === 'posting'}
                            className="w-full btn-primary py-4 text-lg font-bold font-orbitron disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {postStatus === 'posting' ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    Broadcasting...
                                </>
                            ) : (
                                <>📡 BROADCAST TO SWARM</>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </section>
    );
};
