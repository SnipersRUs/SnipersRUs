import { useState } from 'react';
import { useTerminal } from '@/TerminalContext';
import { Zap, TrendingUp, TrendingDown, XCircle } from 'lucide-react';

export const PaperTrading = () => {
    const { balance, positions, tradeHistory, executeTrade, closePosition, getWinRate, agent, selectedAsset, setSelectedAsset } = useTerminal();
    const [amount, setAmount] = useState(1);

    const handleTrade = (side: 'LONG' | 'SHORT') => {
        if (!agent) {
            alert("Please initialize your agent identity first.");
            return;
        }
        executeTrade(selectedAsset, amount, side);
        // Visual feedback or toast could be added here
    };

    return (
        <section id="trading" className="py-20 border-t border-white/5">
            <div className="container-custom">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-6">
                    <div>
                        <h2 className="text-3xl font-orbitron font-bold flex items-center gap-3">
                            <Zap className="text-sniper-green" /> PAPER TRADING
                        </h2>
                        <p className="text-white/50 font-mono text-sm mt-2">Simulated Environment • Zero Risk • infinite Leverage</p>
                    </div>
                    <div className="bg-sniper-card border border-white/10 rounded-xl p-4 flex gap-8">
                        <div>
                            <div className="text-[10px] font-mono text-white/40 uppercase">Cluster Balance</div>
                            <div className="text-2xl font-mono font-bold text-white">${(balance ?? 10000).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                        </div>
                        <div>
                            <div className="text-[10px] font-mono text-white/40 uppercase">Win Rate</div>
                            <div className="text-2xl font-mono font-bold text-sniper-purple">{getWinRate()}%</div>
                        </div>
                    </div>
                </div>

                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Controls */}
                    <div className="bg-sniper-card border border-white/5 rounded-2xl p-6">
                        <div className="mb-6">
                            <label className="text-xs font-mono text-white/40 uppercase mb-2 block">Select Asset</label>
                            <div className="grid grid-cols-3 gap-2">
                                {['BTC', 'ETH', 'SOL'].map(asset => (
                                    <button
                                        key={asset}
                                        onClick={() => setSelectedAsset(asset)}
                                        className={`py-3 rounded-lg font-bold font-orbitron text-sm border transition-all ${selectedAsset === asset ? 'bg-white/10 border-sniper-green text-sniper-green' : 'bg-black/30 border-white/5 text-white/50 hover:bg-white/5'}`}
                                    >
                                        {asset}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="mb-8">
                            <label className="text-xs font-mono text-white/40 uppercase mb-2 block">Position Size (Contracts)</label>
                            <input
                                type="number"
                                value={amount}
                                onChange={(e) => setAmount(parseFloat(e.target.value))}
                                className="w-full bg-black/30 border border-white/10 rounded-lg py-3 px-4 font-mono font-bold text-white focus:border-sniper-green/50 focus:outline-none"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <button
                                onClick={() => handleTrade('LONG')}
                                className="py-4 rounded-xl bg-sniper-green/10 border border-sniper-green/50 text-sniper-green font-bold font-orbitron hover:bg-sniper-green hover:text-black transition-all flex items-center justify-center gap-2"
                            >
                                <TrendingUp size={20} /> LONG
                            </button>
                            <button
                                onClick={() => handleTrade('SHORT')}
                                className="py-4 rounded-xl bg-sniper-purple/10 border border-sniper-purple/50 text-sniper-purple font-bold font-orbitron hover:bg-sniper-purple hover:text-white transition-all flex items-center justify-center gap-2"
                            >
                                <TrendingDown size={20} /> SHORT
                            </button>
                        </div>
                    </div>

                    {/* Active Positions */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="bg-sniper-card border border-white/5 rounded-2xl p-6 min-h-[200px]">
                            <h3 className="text-lg font-orbitron font-bold mb-4 flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-sniper-green animate-pulse"></span>
                                ACTIVE POSITIONS
                            </h3>
                            <div className="space-y-3">
                                {(positions ?? []).length === 0 ? (
                                    <div className="text-center py-10 text-white/20 font-mono text-sm italic">
                                        No active grid coordinates initialized.
                                    </div>
                                ) : (
                                    (positions ?? []).map((pos) => (
                                        <div key={pos.id} className="flex items-center justify-between p-4 bg-white/2 rounded-xl border border-white/5 hover:border-white/10 transition-all">
                                            <div className="flex items-center gap-4">
                                                <div className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${pos.side === 'LONG' ? 'bg-sniper-green/20 text-sniper-green' : 'bg-sniper-purple/20 text-sniper-purple'}`}>
                                                    {pos.side}
                                                </div>
                                                <div className="text-sm font-orbitron font-bold">{pos.qty} {pos.asset}</div>
                                            </div>
                                            <div className="flex items-center gap-6">
                                                <div className="text-right">
                                                    <div className="text-[10px] text-white/40 uppercase font-mono">Entry: ${pos.entryPrice.toFixed(2)}</div>
                                                    <div className={`text-sm font-mono font-bold ${pos.livePnl >= 0 ? 'text-sniper-green' : 'text-sniper-purple'}`}>
                                                        {pos.livePnl >= 0 ? '+' : ''}{pos.livePnl.toFixed(2)}
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => closePosition(pos.id)}
                                                    className="p-2 hover:bg-white/10 rounded-lg text-white/40 hover:text-white transition-all"
                                                >
                                                    <XCircle size={18} />
                                                </button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>

                        {/* Recent History Preview */}
                        <div className="bg-sniper-card border border-white/5 rounded-2xl p-6">
                            <h3 className="text-sm font-orbitron font-bold mb-4 text-white/50">RECENT EXECUTIONS</h3>
                            <div className="space-y-2">
                                {(tradeHistory ?? []).slice(0, 3).map((trade) => (
                                    <div key={trade.id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0 text-sm">
                                        <div className="font-mono text-white/60">
                                            <span className={trade.side === 'LONG' ? 'text-sniper-green' : 'text-sniper-purple'}>{trade.side}</span> {trade.asset}
                                        </div>
                                        <div className={`font-mono font-bold ${trade.pnl >= 0 ? 'text-sniper-green' : 'text-sniper-purple'}`}>
                                            {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                                        </div>
                                    </div>
                                ))}
                                {(tradeHistory ?? []).length === 0 && <span className="text-white/20 text-xs italic">No history logged.</span>}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};
