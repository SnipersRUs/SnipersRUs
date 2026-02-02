import { useState, useEffect } from 'react';
import { useTerminal } from '@/TerminalContext';
import { Bot, User, X } from 'lucide-react';

export const AgentIdentityModal = () => {
    const { agent, isInitialized, createAgent } = useTerminal();
    const [isOpen, setIsOpen] = useState(false);
    const [name, setName] = useState('');
    const [avatar, setAvatar] = useState('🤖');

    // Show modal on first load if not initialized
    useEffect(() => {
        if (isInitialized && !agent) {
            const timer = setTimeout(() => setIsOpen(true), 2000);
            return () => clearTimeout(timer);
        }
    }, [isInitialized, agent]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (name.trim()) {
            createAgent(name, avatar);
            setIsOpen(false);
        }
    };

    if (!isOpen && agent) return null;
    if (!isOpen && !agent) {
        // Render a minimized trigger
        return (
            <div className="fixed bottom-6 right-6 z-50">
                <button
                    onClick={() => setIsOpen(true)}
                    className="btn-primary shadow-[0_0_20px_rgba(0,255,65,0.4)] animate-pulse"
                >
                    INITIALIZE AGENT ID
                </button>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
            <div className="bg-black border border-white/20 rounded-2xl w-full max-w-md p-8 relative shadow-2xl shadow-sniper-green/10">
                <button onClick={() => setIsOpen(false)} className="absolute top-4 right-4 text-white/30 hover:text-white">
                    <X size={20} />
                </button>

                <div className="text-center mb-8">
                    <div className="w-16 h-16 bg-sniper-green/10 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-sniper-green/30">
                        <Bot size={32} className="text-sniper-green" />
                    </div>
                    <h2 className="text-2xl font-orbitron font-bold">INITIALIZE IDENTITY</h2>
                    <p className="text-white/50 text-sm mt-2">Connect your neural link to the cluster.</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-xs font-mono text-white/40 uppercase mb-2">Agent Designation</label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" size={16} />
                            <input
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Ex: Cyber_Ghost_01"
                                className="w-full bg-white/5 border border-white/10 rounded-lg py-3 pl-10 pr-4 text-white focus:border-sniper-green focus:outline-none focus:bg-white/10"
                                autoFocus
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-mono text-white/40 uppercase mb-2">Select Avatar</label>
                        <div className="grid grid-cols-5 gap-2">
                            {['🤖', '🦅', '⚡', '🎯', '🔮', '💀', '👽', '👾', '🦊', '🦁'].map((emoji) => (
                                <button
                                    type="button"
                                    key={emoji}
                                    onClick={() => setAvatar(emoji)}
                                    className={`h-10 rounded hover:bg-white/10 flex items-center justify-center text-xl transition-all ${avatar === emoji ? 'bg-sniper-green/20 border border-sniper-green' : 'bg-transparent border border-transparent'}`}
                                >
                                    {emoji}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="pt-4">
                        <button type="submit" className="w-full btn-primary py-3 flex items-center justify-center gap-2">
                            ESTABLISH UPLINK
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
