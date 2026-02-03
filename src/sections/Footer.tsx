import { Youtube } from 'lucide-react';
import { useState, useEffect } from 'react';

export const Footer = () => {
    const [visitCount, setVisitCount] = useState(0);

    useEffect(() => {
        // Get current count from localStorage
        const stored = localStorage.getItem('srus_visit_count');
        const currentCount = stored ? parseInt(stored, 10) : 0;
        
        // Check if this is a new session (not just a refresh)
        const sessionId = sessionStorage.getItem('srus_session');
        if (!sessionId) {
            // New session - increment counter
            const newCount = currentCount + 1;
            localStorage.setItem('srus_visit_count', newCount.toString());
            setVisitCount(newCount);
            sessionStorage.setItem('srus_session', 'active');
        } else {
            // Same session - show current count without incrementing
            setVisitCount(currentCount);
        }
    }, []);

    return (
        <footer className="bg-black border-t border-white/5 py-12">
            <div className="container-custom">
                <div className="grid md:grid-cols-4 gap-12">
                    <div className="md:col-span-2 space-y-6">
                        <span className="text-2xl font-orbitron font-bold bg-gradient-to-r from-sniper-purple to-sniper-green bg-clip-text text-transparent">
                            SNIPERS-R-US
                        </span>
                        <p className="text-white/50 text-sm max-w-sm">
                            The ultimate autonomous agent trading terminal. Deploy strategies, hunt liquidity, and dominate the global cluster.
                        </p>
                        <div className="flex gap-4">
                            <a href="https://x.com/Brypto_sniper" target="_blank" rel="noopener noreferrer" className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center hover:bg-sniper-green/20 hover:text-sniper-green transition-all">
                                <span className="font-bold text-lg">𝕏</span>
                            </a>
                            <a href="#" className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center hover:bg-sniper-purple/20 hover:text-sniper-purple transition-all">
                                <span className="font-bold text-lg">👾</span>
                            </a>
                            <a href="https://www.youtube.com/@rickytspanish" target="_blank" rel="noopener noreferrer" className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center hover:bg-red-500/20 hover:text-red-500 transition-all">
                                <Youtube size={20} />
                            </a>
                        </div>
                    </div>

                    <div>
                        <h4 className="font-orbitron font-bold text-white mb-6">CLUSTER</h4>
                        <ul className="space-y-4 text-sm text-white/50">
                            <li><a href="#terminal" className="hover:text-sniper-green transition-colors">Terminal</a></li>
                            <li><a href="#signal-betting" className="hover:text-sniper-green transition-colors">Signal Betting</a></li>
                            <li><a href="#trading" className="hover:text-sniper-green transition-colors">Paper Trading</a></li>
                            <li><a href="#agent-console" className="hover:text-sniper-green transition-colors">Deploy Agent</a></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="font-orbitron font-bold text-white mb-6">API</h4>
                        <ul className="space-y-4 text-sm text-white/50">
                            <li><a href="https://snipersrus-backend-production.up.railway.app/health" target="_blank" rel="noopener noreferrer" className="hover:text-sniper-green transition-colors">API Status</a></li>
                            <li><a href="https://snipersrus-backend-production.up.railway.app/api/signals" target="_blank" rel="noopener noreferrer" className="hover:text-sniper-green transition-colors">Signals Endpoint</a></li>
                            <li><span className="text-white/30">Docs (Coming Soon)</span></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="font-orbitron font-bold text-white mb-6">LEGAL</h4>
                        <ul className="space-y-4 text-sm text-white/50">
                            <li><a href="#" className="hover:text-white transition-colors">Privacy Protocol</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Terms of Engagement</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Risk Disclosure</a></li>
                        </ul>
                    </div>
                </div>

                <div className="mt-12 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4">
                    <div className="text-xs font-mono text-white/30">
                        © 2026 SNIPERS-R-US. ALL RIGHTS RESERVED.
                    </div>
                    
                    {/* View Counter - Illuminated Number */}
                    <div className="flex items-center gap-3">
                        <div className="relative">
                            <div className="text-xl font-bold font-orbitron text-white drop-shadow-[0_0_10px_rgba(0,255,65,0.6)]">
                                {visitCount.toLocaleString()}
                            </div>
                            {/* Glow effect */}
                            <div className="absolute inset-0 blur-md bg-sniper-green/20 -z-10"></div>
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-2 text-xs font-mono text-white/30">
                        <span className="w-2 h-2 rounded-full bg-sniper-green animate-pulse"></span>
                        SYSTEM ONLINE
                    </div>
                </div>
            </div>
        </footer>
    );
};
