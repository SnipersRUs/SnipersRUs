import { useState, useEffect } from 'react';
import { Wifi, WifiOff, Server, Clock, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

export const StatusBar = () => {
    const [status, setStatus] = useState<{
        api: 'online' | 'offline' | 'checking';
        lastUpdate: string;
        latency: number;
    }>({
        api: 'checking',
        lastUpdate: 'Checking...',
        latency: 0
    });

    const [isVisible, setIsVisible] = useState(true);

    useEffect(() => {
        const checkStatus = async () => {
            const startTime = Date.now();
            try {
                const response = await fetch('https://snipersrus-backend-production.up.railway.app/health', {
                    method: 'GET',
                    cache: 'no-cache'
                });
                const latency = Date.now() - startTime;
                
                if (response.ok) {
                    const data = await response.json();
                    setStatus({
                        api: 'online',
                        lastUpdate: new Date(data.timestamp).toLocaleTimeString(),
                        latency
                    });
                } else {
                    setStatus(prev => ({ ...prev, api: 'offline' }));
                }
            } catch (err) {
                setStatus(prev => ({ ...prev, api: 'offline' }));
            }
        };

        // Initial check
        checkStatus();

        // Check every 30 seconds
        const interval = setInterval(checkStatus, 30000);

        return () => clearInterval(interval);
    }, []);

    if (!isVisible) return null;

    return (
        <div className="fixed bottom-0 left-0 right-0 z-40 bg-black/90 border-t border-white/10 backdrop-blur-md">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-8 text-[10px] font-mono">
                    {/* Left: Status Indicators */}
                    <div className="flex items-center gap-4">
                        {/* API Status */}
                        <div className="flex items-center gap-1.5">
                            {status.api === 'online' ? (
                                <>
                                    <Wifi size={10} className="text-sniper-green" />
                                    <span className="text-sniper-green">API ONLINE</span>
                                    <span className="text-white/40">({status.latency}ms)</span>
                                </>
                            ) : status.api === 'offline' ? (
                                <>
                                    <WifiOff size={10} className="text-red-500" />
                                    <span className="text-red-500">API OFFLINE</span>
                                </>
                            ) : (
                                <>
                                    <Activity size={10} className="text-yellow-500 animate-pulse" />
                                    <span className="text-yellow-500">CHECKING...</span>
                                </>
                            )}
                        </div>

                        {/* Divider */}
                        <span className="text-white/20">|</span>

                        {/* Real-time Sync */}
                        <div className="flex items-center gap-1.5">
                            <Server size={10} className={cn(
                                status.api === 'online' ? "text-cyan-400" : "text-white/30"
                            )} />
                            <span className={cn(
                                status.api === 'online' ? "text-cyan-400" : "text-white/30"
                            )}>
                                REAL-TIME SYNC
                            </span>
                        </div>

                        {/* Divider */}
                        <span className="text-white/20">|</span>

                        {/* Last Update */}
                        <div className="flex items-center gap-1.5">
                            <Clock size={10} className="text-white/40" />
                            <span className="text-white/40">UPDATED: {status.lastUpdate}</span>
                        </div>
                    </div>

                    {/* Right: Data Guarantee */}
                    <div className="flex items-center gap-4">
                        <span className="text-white/30 hidden sm:inline">
                            GLOBAL SYNC • SAME DATA WORLDWIDE
                        </span>
                        
                        {/* Close button */}
                        <button 
                            onClick={() => setIsVisible(false)}
                            className="text-white/30 hover:text-white/60 transition-colors"
                        >
                            ×
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
