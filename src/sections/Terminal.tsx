import { useRef, useEffect } from 'react';
import { Send, Bot, BarChart } from 'lucide-react';
import { useTerminal } from '@/TerminalContext';

export const Terminal = () => {
    const { messages, sendMessage, agent, selectedAsset } = useTerminal();
    const chatEndRef = useRef<HTMLDivElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        // Embed TradingView
        const scriptId = 'tradingview-widget-script';

        // Remove existing script/widget to force reload on symbol change
        const existingScript = document.getElementById(scriptId);
        if (existingScript) existingScript.remove();
        if (containerRef.current) containerRef.current.innerHTML = '';

        if (containerRef.current) {
            const script = document.createElement('script');
            script.id = scriptId;
            script.type = 'text/javascript';
            script.src = 'https://s3.tradingview.com/tv.js';
            script.async = true;
            script.onload = () => {
                // @ts-ignore
                if (window.TradingView) {
                    const symbolMap: any = {
                        'BTC': 'BINANCE:BTCUSDT',
                        'ETH': 'BINANCE:ETHUSDT',
                        'SOL': 'BINANCE:SOLUSDT'
                    };
                    const symbol = symbolMap[selectedAsset || 'BTC'] || 'BINANCE:BTCUSDT';

                    // @ts-ignore
                    new window.TradingView.widget({
                        "autosize": true,
                        "symbol": symbol,
                        "interval": "15",
                        "timezone": "Etc/UTC",
                        "theme": "dark",
                        "style": "1",
                        "locale": "en",
                        "toolbar_bg": "#f1f3f6",
                        "enable_publishing": false,
                        "hide_side_toolbar": false,
                        "allow_symbol_change": true,
                        "container_id": "tradingview_chart",
                        "overrides": {
                            "mainSeriesProperties.candleStyle.upColor": "#00FF41",
                            "mainSeriesProperties.candleStyle.downColor": "#9D4EDD",
                            "mainSeriesProperties.candleStyle.borderUpColor": "#00FF41",
                            "mainSeriesProperties.candleStyle.borderDownColor": "#9D4EDD",
                            "mainSeriesProperties.candleStyle.wickUpColor": "#00FF41",
                            "mainSeriesProperties.candleStyle.wickDownColor": "#9D4EDD"
                        }
                    });
                }
            };
            document.head.appendChild(script);
        }
    }, [selectedAsset]);

    const handleSend = (e: React.FormEvent) => {
        e.preventDefault();
        const input = (e.target as HTMLFormElement).elements.namedItem('message') as HTMLInputElement;
        const text = input.value;
        if (text.trim()) {
            sendMessage(text, agent?.name || 'Guest', agent?.avatar || '👤');
            input.value = '';
        }
    };

    return (
        <section id="terminal" className="py-20 relative bg-black/50">
            <div className="container-custom">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h2 className="text-3xl font-orbitron font-bold mb-2">LIVE TERMINAL</h2>
                        <p className="text-white/50 font-mono text-sm">Cluster Coordination & Market Analysis</p>
                    </div>
                    <div className="flex gap-2">
                        <span className="px-3 py-1 rounded bg-sniper-green/10 text-sniper-green text-xs font-mono border border-sniper-green/20">{selectedAsset}/USDT</span>
                    </div>
                </div>

                <div className="grid lg:grid-cols-3 gap-6 h-[600px]">
                    {/* Chart */}
                    <div className="lg:col-span-2 bg-sniper-card border border-white/5 rounded-2xl overflow-hidden relative group">
                        <div id="tradingview_chart" ref={containerRef} className="w-full h-full min-h-[500px]"></div>
                        <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button className="p-2 bg-black/50 backdrop-blur rounded border border-white/10 hover:bg-white/10 transition-colors">
                                <BarChart size={20} />
                            </button>
                        </div>
                    </div>

                    {/* Agent Chat */}
                    <div className="lg:col-span-1 bg-sniper-card border border-white/5 rounded-2xl flex flex-col overflow-hidden">
                        <div className="p-4 border-b border-white/5 bg-white/2 flex justify-between items-center">
                            <span className="font-orbitron font-bold text-sm tracking-wider flex items-center gap-2">
                                <Bot size={16} className="text-sniper-purple" /> AGENT UPLINK
                            </span>
                            <div className="flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-sniper-green animate-pulse"></span>
                                <span className="text-[10px] font-mono text-white/30">LIVE</span>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                            {messages.map((msg) => (
                                <div key={msg.id} className="flex gap-3 items-start animate-fade-in">
                                    <div className="w-8 h-8 rounded bg-white/5 flex items-center justify-center text-sm shrink-0 border border-white/5">
                                        {msg.avatar}
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <div className="flex justify-between items-baseline mb-1">
                                            <span className="text-[10px] font-mono font-bold text-white/30 uppercase tracking-widest">{msg.user}</span>
                                            <span className="text-[8px] font-mono text-white/20">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                        </div>
                                        <div className="text-xs text-white/80 leading-relaxed bg-white/5 rounded-lg rounded-tl-none px-3 py-2 border border-white/5">
                                            {msg.text}
                                        </div>
                                    </div>
                                </div>
                            ))}
                            <div ref={chatEndRef}></div>
                        </div>

                        <form onSubmit={handleSend} className="p-4 border-t border-white/5 bg-white/2">
                            <div className="relative">
                                <input
                                    name="message"
                                    type="text"
                                    placeholder={agent ? `Command as ${agent.name}...` : "Initialize identify to chat..."}
                                    disabled={!agent}
                                    className="w-full bg-black/50 border border-white/10 rounded-lg py-3 pl-4 pr-12 text-sm text-white focus:outline-none focus:border-sniper-green/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                />
                                <button
                                    type="submit"
                                    disabled={!agent}
                                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 hover:bg-sniper-green/20 rounded-md text-white/50 hover:text-sniper-green transition-all"
                                >
                                    <Send size={16} />
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </section>
    );
};
