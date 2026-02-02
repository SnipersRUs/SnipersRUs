import { useState } from 'react';
import { useTerminal } from '@/TerminalContext';
import { Activity, MessageSquare, Send, TrendingUp, TrendingDown, Clock, BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';

export const SignalFeed = () => {
    const { signals, addCommentToSignal, voteSignal, agent } = useTerminal();
    const [selectedSignalId, setSelectedSignalId] = useState<string | null>(null);
    const [commentText, setCommentText] = useState('');

    const handleAddComment = (e: React.FormEvent, signalId: string) => {
        e.preventDefault();
        if (!commentText.trim() || !agent) return;
        addCommentToSignal(signalId, commentText, { id: agent.id, name: agent.name, avatar: agent.avatar });
        setCommentText('');
    };

    return (
        <section id="signals" className="py-20 bg-black/50">
            <div className="container-custom">
                <div className="flex flex-col md:flex-row justify-between items-end mb-12 gap-6">
                    <div>
                        <h2 className="text-4xl font-orbitron font-black flex items-center gap-4">
                            <Activity className="text-sniper-green w-10 h-10" />
                            LIVE SIGNAL CLUSTER
                        </h2>
                        <p className="text-white/50 font-mono text-sm mt-3 tracking-widest uppercase opacity-70">
                            Real-time Execution & Collaborative Intelligence
                        </p>
                    </div>
                </div>

                <div className="grid lg:grid-cols-12 gap-8">
                    {/* Signal List */}
                    <div className={cn("space-y-4", selectedSignalId ? "lg:col-span-5" : "lg:col-span-12")}>
                        {signals.map((sig) => (
                            <div
                                key={sig.id}
                                onClick={() => setSelectedSignalId(selectedSignalId === sig.id ? null : sig.id)}
                                className={cn(
                                    "bg-sniper-card border p-6 rounded-2xl cursor-pointer transition-all hover:scale-[1.01] group relative overflow-hidden",
                                    selectedSignalId === sig.id ? "border-sniper-green shadow-lg shadow-sniper-green/10" : "border-white/5"
                                )}
                            >
                                {sig.status === 'ACTIVE' && (
                                    <div className="absolute top-0 left-0 w-1 h-full bg-sniper-green animate-pulse"></div>
                                )}

                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center font-orbitron font-bold text-white/50 group-hover:text-sniper-green transition-colors">
                                            {sig.symbol.split('/')[0]}
                                        </div>
                                        <div>
                                            <div className="font-orbitron font-bold text-xl text-white group-hover:text-sniper-green transition-colors flex items-center gap-2">
                                                {sig.symbol}
                                                {sig.status === 'ACTIVE' && <span className="text-[10px] bg-sniper-green/20 text-sniper-green px-2 py-0.5 rounded-full font-mono uppercase">Live</span>}
                                            </div>
                                            <div className="text-[10px] font-mono text-white/40 uppercase tracking-widest mt-1">
                                                ID: {sig.id} • {new Date(sig.createdAt).toLocaleTimeString()}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className={cn("text-xs font-bold font-orbitron px-3 py-1 rounded-lg border", sig.type === 'LONG' ? "bg-sniper-green/10 text-sniper-green border-sniper-green/20" : "bg-sniper-purple/10 text-sniper-purple border-sniper-purple/20")}>
                                            {sig.type}
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-3 gap-6 mb-6">
                                    <div className="bg-white/2 p-3 rounded-xl border border-white/5">
                                        <div className="text-[10px] font-mono text-white/30 uppercase mb-1">Entry Price</div>
                                        <div className="text-sm font-mono font-bold">$ {sig.entryPrice.toLocaleString()}</div>
                                    </div>
                                    <div className="bg-white/2 p-3 rounded-xl border border-white/5">
                                        <div className="text-[10px] font-mono text-white/30 uppercase mb-1">Live Performance</div>
                                        <div className={cn("text-sm font-mono font-bold", (sig.pnl || 0) >= 0 ? "text-sniper-green" : "text-sniper-purple")}>
                                            {sig.pnl ? `${sig.pnl > 0 ? '+' : ''}${sig.pnl.toFixed(2)}%` : 'SCANNING'}
                                        </div>
                                    </div>
                                    <div className="bg-white/2 p-3 rounded-xl border border-white/5">
                                        <div className="text-[10px] font-mono text-white/30 uppercase mb-1">Probability</div>
                                        <div className="text-sm font-mono font-bold text-white">{sig.prob}%</div>
                                    </div>
                                </div>

                                <div className="flex items-center justify-between border-t border-white/5 pt-4">
                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-1.5 text-xs text-white/40 hover:text-sniper-green transition-colors" onClick={(e) => { e.stopPropagation(); voteSignal(sig.id, 'bullish'); }}>
                                            <TrendingUp size={14} /> {sig.sentiment.bullish}
                                        </div>
                                        <div className="flex items-center gap-1.5 text-xs text-white/40 hover:text-sniper-purple transition-colors" onClick={(e) => { e.stopPropagation(); voteSignal(sig.id, 'bearish'); }}>
                                            <TrendingDown size={14} /> {sig.sentiment.bearish}
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-white/40 group-hover:text-white transition-colors">
                                        <MessageSquare size={14} /> {sig.comments.length} Critiques
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Critique / Discussion Plane */}
                    {selectedSignalId && (
                        <div className="lg:col-span-7 bg-sniper-card border border-white/10 rounded-2xl flex flex-col h-[700px] animate-fade-in overflow-hidden sticky top-24">
                            <div className="p-6 border-b border-white/5 bg-white/2 flex justify-between items-center">
                                <div>
                                    <h3 className="font-orbitron font-bold text-lg flex items-center gap-2">
                                        <BarChart3 size={18} className="text-sniper-green" />
                                        INTEL BRIEFING: {signals.find(s => s.id === selectedSignalId)?.symbol}
                                    </h3>
                                    <div className="text-[10px] font-mono text-white/40 mt-1 uppercase">Strategic Consensus Protocol v1.4</div>
                                </div>
                                <button onClick={() => setSelectedSignalId(null)} className="text-white/30 hover:text-white">
                                    <Clock size={20} />
                                </button>
                            </div>

                            <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
                                {signals.find(s => s.id === selectedSignalId)?.comments.length === 0 ? (
                                    <div className="text-center py-20">
                                        <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4 border border-white/10">
                                            <MessageSquare size={24} className="text-white/20" />
                                        </div>
                                        <h4 className="font-orbitron font-bold text-white/40 text-sm">NO STRATEGIC INSIGHTS LOGGED</h4>
                                        <p className="text-white/20 text-xs mt-2 font-mono">Be the first to critique this coordinate.</p>
                                    </div>
                                ) : (
                                    signals.find(s => s.id === selectedSignalId)?.comments.map((comment: any) => (
                                        <div key={comment.id} className="flex gap-4 group">
                                            <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center shrink-0 border border-white/10 text-lg">
                                                {comment.authorAvatar}
                                            </div>
                                            <div className="flex-1">
                                                <div className="flex justify-between items-center mb-1">
                                                    <span className="text-xs font-orbitron font-bold text-sniper-green tracking-wide">{comment.authorName}</span>
                                                    <span className="text-[10px] font-mono text-white/20">{new Date(comment.createdAt).toLocaleTimeString()}</span>
                                                </div>
                                                <div className="text-sm text-white/70 leading-relaxed bg-white/2 p-3 rounded-xl rounded-tl-none border border-white/5 group-hover:border-white/20 transition-all">
                                                    {comment.body}
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>

                            <div className="p-6 border-t border-white/5 bg-black/40">
                                <form onSubmit={(e) => handleAddComment(e, selectedSignalId)} className="relative">
                                    <input
                                        type="text"
                                        value={commentText}
                                        onChange={(e) => setCommentText(e.target.value)}
                                        placeholder={agent ? "Transmit strategic critique..." : "Initialize identify to contribute..."}
                                        disabled={!agent}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl py-4 pl-5 pr-14 text-sm text-white focus:outline-none focus:border-sniper-green/50 transition-colors"
                                    />
                                    <button
                                        type="submit"
                                        disabled={!agent || !commentText.trim()}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-sniper-green text-black rounded-lg hover:bg-sniper-green/80 disabled:opacity-30 transition-all"
                                    >
                                        <Send size={18} />
                                    </button>
                                </form>
                                <div className="mt-4 flex items-center gap-6 justify-center">
                                    <button
                                        onClick={() => voteSignal(selectedSignalId, 'bullish')}
                                        className="flex items-center gap-2 text-[10px] font-mono font-bold text-white/40 hover:text-sniper-green transition-colors"
                                    >
                                        <TrendingUp size={14} /> BULLISH THESIS
                                    </button>
                                    <div className="h-3 w-px bg-white/10"></div>
                                    <button
                                        onClick={() => voteSignal(selectedSignalId, 'bearish')}
                                        className="flex items-center gap-2 text-[10px] font-mono font-bold text-white/40 hover:text-sniper-purple transition-colors"
                                    >
                                        <TrendingDown size={14} /> BEARISH THESIS
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
};
