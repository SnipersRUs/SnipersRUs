import { useState, useEffect } from 'react';
import { X, ExternalLink, Bot } from 'lucide-react';

export const FreeTrialModal = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [hasBeenShown, setHasBeenShown] = useState(false);

    useEffect(() => {
        // Trigger popup after 14 seconds
        const timer = setTimeout(() => {
            if (!hasBeenShown) {
                setIsOpen(true);
                setHasBeenShown(true);
            }
        }, 14000);

        return () => clearTimeout(timer);
    }, [hasBeenShown]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fade-in">
            <div className="bg-sniper-card border border-sniper-purple rounded-2xl w-full max-w-md p-6 relative shadow-[0_0_50px_rgba(157,78,221,0.3)] animate-scale-up">
                <button
                    onClick={() => setIsOpen(false)}
                    className="absolute top-4 right-4 text-white/40 hover:text-white transition-colors"
                >
                    <X size={20} />
                </button>

                <div className="text-center">
                    <div className="w-16 h-16 bg-sniper-purple/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-sniper-purple/30">
                        <Bot size={32} className="text-sniper-purple" />
                    </div>

                    <h2 className="text-2xl font-orbitron font-black mb-2 text-white">UPGRADE ACCESS</h2>
                    <p className="font-mono text-sniper-purple text-xs tracking-[0.2em] mb-6">BOUNTY SEEKER PROTOCOL</p>

                    <p className="text-white/70 text-sm mb-8 leading-relaxed">
                        Your free trial for the <span className="text-white font-bold">Bounty Seeker</span> tier is ready.
                        Unlock advanced pattern recognition and priority signal uplinks now.
                    </p>

                    <a
                        href="https://upgrade.chat/734621342069948446/p/e4097a76-84f4-4138-a754-f0cfaae66291"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-primary w-full py-4 flex items-center justify-center gap-2 group"
                        onClick={() => setIsOpen(false)}
                    >
                        START FREE TRIAL <ExternalLink size={16} className="group-hover:translate-x-1 transition-transform" />
                    </a>

                    <button
                        onClick={() => setIsOpen(false)}
                        className="mt-4 text-xs font-mono text-white/30 hover:text-white transition-colors underline decoration-white/30"
                    >
                        Maybe later
                    </button>
                </div>
            </div>
        </div>
    );
};
