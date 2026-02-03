import { useState, useEffect } from 'react';
import { Radio, Clock, TrendingUp, AlertTriangle, CheckCircle, Bell, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

// Default signals while loading
const DEFAULT_SIGNALS = [
    {
        id: 1,
        pair: "BTC/USDT",
        type: "LONG",
        entry: "89,450",
        target: "91,200",
        stop: "88,800",
        confidence: 78,
        time: "Loading...",
        status: "ACTIVE",
        source: "Short Hunter"
    }
];

interface Signal {
    id: number;
    pair: string;
    type: string;
    entry: string;
    target: string;
    stop: string;
    confidence: number;
    time: string;
    timestamp?: number;
    status: string;
    source?: string;
    reasons?: string[];
}

interface SignalCardProps {
    signal: Signal;
}

const SignalCard = ({ signal }: SignalCardProps) => {
    const isLong = signal.type === "LONG";
    const isHit = signal.status === "HIT_TP";
    
    return (
        <div className={cn(
            "p-4 rounded-xl border transition-all",
            isHit 
                ? "bg-sniper-green/10 border-sniper-green/30" 
                : "bg-black/30 border-white/10"
        )}>
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className={cn(
                        "px-2 py-1 rounded text-[10px] font-bold",
                        isLong ? "bg-sniper-green/20 text-sniper-green" : "bg-red-500/20 text-red-400"
                    )}>
                        {signal.type}
                    </div>
                    <span className="text-white font-bold">{signal.pair}</span>
                </div>
                <div className="flex items-center gap-2">
                    {isHit ? (
                        <div className="flex items-center gap-1 text-sniper-green text-xs font-bold">
                            <CheckCircle size={14} />
                            HIT TP
                        </div>
                    ) : (
                        <div className="flex items-center gap-1 text-white/50 text-xs">
                            <Clock size={14} />
                            {signal.time}
                        </div>
                    )}
                </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4 mb-3">
                <div>
                    <div className="text-white/50 text-[10px] font-mono">ENTRY</div>
                    <div className="text-white font-mono">${signal.entry}</div>
                </div>
                <div>
                    <div className="text-white/50 text-[10px] font-mono">TARGET</div>
                    <div className="text-sniper-green font-mono">${signal.target}</div>
                </div>
                <div>
                    <div className="text-white/50 text-[10px] font-mono">STOP</div>
                    <div className="text-red-400 font-mono">${signal.stop}</div>
                </div>
            </div>
            
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="text-white/50 text-xs">Confidence:</div>
                    <div className={cn(
                        "text-sm font-bold",
                        signal.confidence >= 80 ? "text-sniper-green" : 
                        signal.confidence >= 70 ? "text-yellow-400" : "text-white"
                    )}>
                        {signal.confidence}%
                    </div>
                </div>
                <div className="text-white/30 text-xs">
                    FREE TIER
                </div>
            </div>
        </div>
    );
};

export const FreeSignals = () => {
    const [email, setEmail] = useState("");
    const [subscribed, setSubscribed] = useState(false);
    const [signals, setSignals] = useState<Signal[]>(DEFAULT_SIGNALS);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch signals from JSON file
        const fetchSignals = async () => {
            try {
                const response = await fetch('/signals.json');
                if (response.ok) {
                    const data = await response.json();
                    if (Array.isArray(data) && data.length > 0) {
                        setSignals(data);
                    }
                }
            } catch (error) {
                console.log('Using default signals');
            } finally {
                setLoading(false);
            }
        };

        fetchSignals();
        // Refresh every 5 minutes
        const interval = setInterval(fetchSignals, 300000);
        return () => clearInterval(interval);
    }, []);

    const handleSubscribe = (e: React.FormEvent) => {
        e.preventDefault();
        if (email) {
            setSubscribed(true);
            setTimeout(() => setSubscribed(false), 3000);
            setEmail("");
        }
    };

    return (
        <section id="free-signals" className="py-24 px-4">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="text-center mb-16">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sniper-green/10 border border-sniper-green/20 mb-6">
                        <Radio size={16} className="text-sniper-green animate-pulse" />
                        <span className="text-[10px] font-mono text-sniper-green uppercase tracking-widest">
                            Free Access
                        </span>
                    </div>
                    <h2 className="text-4xl md:text-5xl font-bold font-orbitron text-white mb-4">
                        FREE <span className="text-sniper-green">SIGNALS</span>
                    </h2>
                    <p className="text-white/60 max-w-2xl mx-auto text-lg mb-4">
                        Get access to basic trading signals completely free. 
                        No wallet connection required - just subscribe to receive alerts.
                    </p>
                    <p className="text-sniper-green text-sm">
                        🎯 2 fresh signals per hour • Valid for 60 minutes • Updated every scan
                    </p>
                </div>

                <div className="grid lg:grid-cols-2 gap-8">
                    {/* Left: Live Signals */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-xl font-bold font-orbitron text-white flex items-center gap-2">
                                <Zap size={20} className="text-sniper-green" />
                                LIVE SIGNALS
                            </h3>
                            <div className="flex items-center gap-2 text-xs text-white/50">
                                <span className="w-2 h-2 rounded-full bg-sniper-green animate-pulse" />
                                UPDATED HOURLY
                            </div>
                        </div>
                        
                        <div className="space-y-3">
                            {loading ? (
                                <div className="p-4 rounded-xl bg-black/30 border border-white/10 text-center">
                                    <div className="text-white/50">Loading signals...</div>
                                </div>
                            ) : (
                                signals.map((signal) => (
                                    <SignalCard key={signal.id} signal={signal} />
                                ))
                            )}
                        </div>
                        
                        <div className="p-4 rounded-xl bg-sniper-purple/10 border border-sniper-purple/20">
                            <div className="flex items-start gap-3">
                                <TrendingUp size={20} className="text-sniper-purple mt-1" />
                                <div>
                                    <div className="text-white font-bold mb-1">Want More Signals?</div>
                                    <div className="text-white/60 text-sm">
                                        Premium tiers get 10x more signals with higher confidence scores 
                                        and advanced strategies like VWAP deviations and liquidity zones.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right: Subscribe Form */}
                    <div className="space-y-6">
                        <div className="p-8 rounded-2xl bg-gradient-to-b from-sniper-green/10 to-black border border-sniper-green/20">
                            <div className="text-center mb-6">
                                <div className="w-16 h-16 rounded-full bg-sniper-green/20 flex items-center justify-center mx-auto mb-4">
                                    <Bell size={32} className="text-sniper-green" />
                                </div>
                                <h3 className="text-2xl font-bold font-orbitron text-white mb-2">
                                    Get Free Alerts
                                </h3>
                                <p className="text-white/60">
                                    Subscribe to receive free trading signals via email or Discord
                                </p>
                            </div>
                            
                            <form onSubmit={handleSubscribe} className="space-y-4">
                                <div>
                                    <label className="block text-white/50 text-sm mb-2">Email Address</label>
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        placeholder="trader@example.com"
                                        className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white placeholder-white/30 focus:border-sniper-green focus:outline-none transition-colors"
                                        required
                                    />
                                </div>
                                
                                <button
                                    type="submit"
                                    disabled={subscribed}
                                    className={cn(
                                        "w-full py-4 rounded-lg font-bold font-orbitron transition-all flex items-center justify-center gap-2",
                                        subscribed
                                            ? "bg-sniper-green text-black"
                                            : "bg-sniper-green hover:bg-sniper-green/80 text-black"
                                    )}
                                >
                                    {subscribed ? (
                                        <>
                                            <CheckCircle size={20} />
                                            SUBSCRIBED!
                                        </>
                                    ) : (
                                        "GET FREE SIGNALS"
                                    )}
                                </button>
                            </form>
                            
                            <div className="mt-6 p-4 rounded-lg bg-black/30 border border-white/10">
                                <div className="flex items-start gap-3">
                                    <AlertTriangle size={18} className="text-yellow-400 mt-0.5" />
                                    <div className="text-sm text-white/60">
                                        <strong className="text-white">Disclaimer:</strong> These are educational signals only. 
                                        Always do your own research. Past performance doesn't guarantee future results.
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        {/* Features List */}
                        <div className="grid grid-cols-2 gap-4">
                            {[
                                { icon: Radio, label: "Real-time Alerts" },
                                { icon: TrendingUp, label: "Entry/Exit Levels" },
                                { icon: Clock, label: "24/7 Monitoring" },
                                { icon: Zap, label: "Major Pairs Only" }
                            ].map((feature, idx) => (
                                <div key={idx} className="flex items-center gap-3 p-4 rounded-lg bg-white/5 border border-white/10">
                                    <feature.icon size={18} className="text-sniper-green" />
                                    <span className="text-white text-sm font-medium">{feature.label}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};
