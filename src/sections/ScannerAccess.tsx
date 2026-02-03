import { useState, useEffect } from 'react';
import { Target, Zap, TrendingUp, Copy, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

const PACKAGES = [
    {
        name: 'SINGLE',
        price: 5,
        signals: 1,
        description: 'One premium signal',
        popular: false
    },
    {
        name: 'BUNDLE_5',
        price: 20,
        signals: 5,
        description: '5 signals (Save 5 ZOID)',
        popular: true
    },
    {
        name: 'BUNDLE_10',
        price: 35,
        signals: 10,
        description: '10 signals (Save 15 ZOID)',
        popular: false
    },
    {
        name: 'UNLIMITED_DAY',
        price: 50,
        signals: 'Unlimited',
        description: '24 hours of signals',
        popular: false
    }
];

export const ScannerAccess = () => {
    const [connected, setConnected] = useState(false);
    const [address, setAddress] = useState('');
    const [copied, setCopied] = useState(false);
    const [status, setStatus] = useState<{hasAccess: boolean; remaining: number} | null>(null);

    const DEV_WALLET = '0x9C23d0F34606204202a9b88B2CD8dBBa24192Ae5';
    const DISCORD_LINK = 'https://discord.gg/snipersrus';

    const connectWallet = async () => {
        try {
            if (typeof window.ethereum !== 'undefined') {
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                if (accounts.length > 0) {
                    setAddress(accounts[0]);
                    setConnected(true);
                    checkStatus(accounts[0]);
                }
            } else {
                alert('Please install MetaMask');
            }
        } catch (err) {
            console.error('Connection error:', err);
        }
    };

    const checkStatus = async (addr: string) => {
        try {
            const response = await fetch(`https://snipersrus-backend-production.up.railway.app/api/scanner/status/${addr}`);
            const data = await response.json();
            setStatus({ hasAccess: data.hasAccess, remaining: data.totalRemaining });
        } catch (err) {
            console.error('Status check failed:', err);
        }
    };

    const copyAddress = () => {
        navigator.clipboard.writeText(DEV_WALLET);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <section id="scanner" className="py-24 px-4">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="text-center mb-16">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sniper-green/10 border border-sniper-green/20 mb-6">
                        <Zap size={16} className="text-sniper-green" />
                        <span className="text-[10px] font-mono text-sniper-green uppercase tracking-widest">
                            Pay Per Signal
                        </span>
                    </div>
                    
                    <h2 className="text-4xl md:text-5xl font-bold font-orbitron text-white mb-4">
                        GET <span className="text-sniper-green">SIGNALS</span>
                    </h2>
                    
                    <p className="text-white/60 max-w-2xl mx-auto text-lg">
                        Simple pay-per-signal model. Send ZOID, get premium signals with 
                        Golden Pocket zones and VWAP analysis.
                    </p>
                </div>

                {/* Simple Steps */}
                <div className="grid md:grid-cols-3 gap-6 mb-12">
                    {[
                        { step: '1', title: 'Send ZOID', desc: 'Pay with ZOID to the address below' },
                        { step: '2', title: 'Share Address', desc: 'Post your wallet in Discord #signals channel' },
                        { step: '3', title: 'Get Signals', desc: 'Your credits are activated within minutes' }
                    ].map((item) => (
                        <div key={item.step} className="p-6 rounded-xl bg-white/5 border border-white/10 text-center">
                            <div className="w-10 h-10 rounded-full bg-sniper-green/20 flex items-center justify-center mx-auto mb-4">
                                <span className="text-sniper-green font-bold">{item.step}</span>
                            </div>
                            <h3 className="text-white font-bold mb-2">{item.title}</h3>
                            <p className="text-white/50 text-sm">{item.desc}</p>
                        </div>
                    ))}
                </div>

                {/* Payment Address */}
                <div className="mb-12 p-6 rounded-2xl bg-gradient-to-r from-sniper-green/10 to-cyan-500/10 border border-sniper-green/30">
                    <div className="text-center mb-4">
                        <h3 className="text-lg font-bold text-white mb-2">Send ZOID to this address:</h3>
                        <p className="text-white/60 text-sm">Include your Discord username in the memo</p>
                    </div>
                    
                    <div className="flex items-center gap-3 p-4 rounded-xl bg-black/50 border border-white/10">
                        <code className="flex-1 text-sniper-green font-mono text-sm break-all">
                            {DEV_WALLET}
                        </code>
                        <button
                            onClick={copyAddress}
                            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-all"
                        >
                            {copied ? <CheckCircle size={20} className="text-sniper-green" /> : <Copy size={20} />}
                        </button>
                    </div>
                </div>

                {/* Pricing */}
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
                    {PACKAGES.map((pkg) => (
                        <div
                            key={pkg.name}
                            className={cn(
                                "p-6 rounded-xl border transition-all",
                                pkg.popular 
                                    ? "bg-sniper-green/10 border-sniper-green/50 scale-105" 
                                    : "bg-white/5 border-white/10 hover:border-white/30"
                            )}
                        >
                            {pkg.popular && (
                                <div className="text-center mb-2">
                                    <span className="px-3 py-1 bg-sniper-green text-black text-xs font-bold rounded-full">POPULAR</span>
                                </div>
                            )}
                            
                            <div className="text-center mb-4">
                                <div className="text-3xl font-bold text-white">{pkg.price} ZOID</div>
                                <div className="text-sniper-green font-medium">{pkg.signals} Signals</div>
                            </div>
                            
                            <p className="text-white/60 text-sm text-center">{pkg.description}</p>
                        </div>
                    ))}
                </div>

                {/* Discord CTA */}
                <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-500/20 to-purple-500/20 border border-indigo-500/30">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-full bg-indigo-500/20 flex items-center justify-center">
                                <svg className="w-6 h-6 text-indigo-400" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z"/>
                                </svg>
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white">Join Discord</h3>
                                <p className="text-white/60 text-sm">Post your wallet in #signals after paying</p>
                            </div>
                        </div>
                        
                        <a
                            href={DISCORD_LINK}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-8 py-3 rounded-lg bg-indigo-500 hover:bg-indigo-400 text-white font-bold font-orbitron transition-all"
                        >
                            JOIN DISCORD
                        </a>
                    </div>
                </div>

                {/* Wallet Check */}
                <div className="mt-12 p-6 rounded-2xl bg-white/5 border border-white/10">
                    <h3 className="text-lg font-bold text-white mb-4 text-center">Check Your Signal Credits</h3>
                    
                    {!connected ? (
                        <div className="text-center">
                            <button
                                onClick={connectWallet}
                                className="px-8 py-3 rounded-lg bg-sniper-green hover:bg-sniper-green/80 text-black font-bold font-orbitron transition-all"
                            >
                                Connect Wallet
                            </button>
                        </div>
                    ) : (
                        <div className="text-center">
                            <div className="text-white font-mono mb-2">{address.slice(0, 6)}...{address.slice(-4)}</div>
                            {status && (
                                <div className="text-sniper-green font-bold text-xl mb-4">
                                    {status.hasAccess 
                                        ? `${status.remaining} signals remaining` 
                                        : 'No active purchases'}
                                </div>
                            )}
                            <button
                                onClick={() => checkStatus(address)}
                                className="px-6 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white font-bold transition-all"
                            >
                                Refresh
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
};
