import { useState, useEffect } from 'react';
import { Menu, X, Terminal, Zap, Bot, Wallet, Coins, Radio, User, Target } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTerminal } from '@/TerminalContext';

export const Navigation = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [scrolled, setScrolled] = useState(false);
    const { agent } = useTerminal();

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const scrollToSection = (id: string) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
            setIsOpen(false);
        }
    };

    const navItems = [
        { id: 'zoid-token', label: 'ZOID', icon: Coins, external: false },
        { id: 'tiers', label: 'TIERS', icon: Wallet, external: false },
        { id: 'free-signals', label: 'FREE', icon: Radio, external: false },
        { id: 'sniper-guru', label: 'TRACKER', icon: User, external: false },
        { id: 'clawrma', label: 'CLAWrMA', icon: Target, external: true, url: 'https://clawrma.com' },
        { id: 'agent-console', label: 'DEPLOY', icon: Bot, external: false },
        { id: 'terminal', label: 'TERMINAL', icon: Terminal, external: false },
        { id: 'trading', label: 'TRADE', icon: Zap, external: false },
        { id: 'fuel-cluster', label: 'FUEL', icon: Zap, external: false },
    ];

    return (
        <nav className={cn(
            "fixed top-0 w-full z-50 transition-all duration-300 border-b border-transparent",
            (scrolled || isOpen) ? "bg-black/80 backdrop-blur-md border-white/10" : ""
        )}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    <div className="flex items-center gap-2 cursor-pointer" onClick={() => scrollToSection('hero')}>
                        <span className="text-2xl font-orbitron font-bold bg-gradient-to-r from-sniper-purple to-sniper-green bg-clip-text text-transparent">
                            SNIPERS-R-US
                        </span>
                    </div>

                    <div className="hidden md:flex items-center space-x-1">
                        {navItems.map((item) => (
                            item.external ? (
                                <a
                                    key={item.id}
                                    href={item.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="px-3 py-2 text-[10px] font-mono font-bold text-cyan-400 hover:text-cyan-300 hover:bg-white/5 rounded transition-all uppercase tracking-wider flex items-center gap-1.5"
                                >
                                    <item.icon size={14} />
                                    {item.label}
                                </a>
                            ) : (
                                <button
                                    key={item.id}
                                    onClick={() => scrollToSection(item.id)}
                                    className="px-3 py-2 text-[10px] font-mono font-bold text-white/70 hover:text-sniper-green hover:bg-white/5 rounded transition-all uppercase tracking-wider flex items-center gap-1.5"
                                >
                                    <item.icon size={14} />
                                    {item.label}
                                </button>
                            )
                        ))}
                    </div>

                    <div className="hidden md:flex items-center gap-4">
                        {agent && (
                            <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-lg border border-white/10">
                                <span className="text-lg">{agent.avatar}</span>
                                <div className="text-right">
                                    <div className="text-[10px] font-mono text-white/50 leading-none">AGENT</div>
                                    <div className="text-xs font-bold font-orbitron text-sniper-green leading-none">{agent.name}</div>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="md:hidden">
                        <button onClick={() => setIsOpen(!isOpen)} className="text-white p-2">
                            {isOpen ? <X /> : <Menu />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile menu */}
            {isOpen && (
                <div className="md:hidden bg-black/95 backdrop-blur-xl border-b border-white/10">
                    <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                        {navItems.map((item) => (
                            item.external ? (
                                <a
                                    key={item.id}
                                    href={item.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="block w-full text-left px-3 py-4 text-sm font-mono font-bold text-cyan-400 hover:text-cyan-300 hover:bg-white/5 rounded-lg transition-all flex items-center gap-3"
                                >
                                    <item.icon size={18} />
                                    {item.label}
                                </a>
                            ) : (
                                <button
                                    key={item.id}
                                    onClick={() => scrollToSection(item.id)}
                                    className="block w-full text-left px-3 py-4 text-sm font-mono font-bold text-white/70 hover:text-sniper-green hover:bg-white/5 rounded-lg transition-all flex items-center gap-3"
                                >
                                    <item.icon size={18} />
                                    {item.label}
                                </button>
                            )
                        ))}
                    </div>
                </div>
            )}
        </nav>
    );
};
