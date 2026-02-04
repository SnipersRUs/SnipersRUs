import { TrendingUp, TrendingDown, Target } from 'lucide-react';

const trades = [
    { pair: 'JUP/USDT', direction: 'SHORT', leverage: '15X', pnl: '-5.81%', win: false },
    { pair: 'DOGE/USDT', direction: 'SHORT', leverage: '15X', pnl: '+36.05%', win: true },
    { pair: 'BTC/USDT', direction: 'LONG', leverage: '76X', pnl: '+62.11%', win: true },
    { pair: 'DOGE/USDT', direction: 'SHORT', leverage: '20X', pnl: '+56.48%', win: true },
    { pair: 'JUP/USDT', direction: 'SHORT', leverage: '15X', pnl: '+20.50%', win: true },
    { pair: 'PAXG/USDT', direction: 'LONG', leverage: '15X', pnl: '-7.57%', win: false },
    { pair: 'XRP/USDT', direction: 'SHORT', leverage: '25X', pnl: '+41.64%', win: true },
    { pair: 'BARD/USDT', direction: 'SHORT', leverage: '5X', pnl: '-0.56%', win: false },
    { pair: 'HYPE/USDT', direction: 'SHORT', leverage: '2X', pnl: '+10.71%', win: true },
    { pair: 'AT/USDT', direction: 'SHORT', leverage: '11X', pnl: '+37.93%', win: true },
    { pair: 'PAXG/USDT', direction: 'LONG', leverage: '15X', pnl: '+31.61%', win: true },
    { pair: 'ENJ/USDT', direction: 'SHORT', leverage: '15X', pnl: '-3.70%', win: false },
    { pair: 'DOGE/USDT', direction: 'SHORT', leverage: '15X', pnl: '+14.53%', win: true },
    { pair: 'HYPE/USDT', direction: 'SHORT', leverage: '15X', pnl: '+92.16%', win: true },
    { pair: 'DOGE/USDT', direction: 'LONG', leverage: '20X', pnl: '+49.10%', win: true },
];

export const RickyTrades = () => {
    const wins = trades.filter(t => t.win).length;
    const losses = trades.filter(t => !t.win).length;
    const avgPnL = (trades.reduce((acc, t) => acc + parseFloat(t.pnl), 0) / trades.length).toFixed(2);

    return (
        <section id="ricky-trades" className="py-20 bg-gradient-to-b from-black to-sniper-dark border-t border-white/5">
            <div className="container-custom">
                <div className="text-center mb-12">
                    <h2 className="text-3xl md:text-4xl font-orbitron font-bold mb-4">
                        <span className="bg-gradient-to-r from-sniper-green to-sniper-purple bg-clip-text text-transparent">
                            TRADES FROM RICKY SPANISH
                        </span>
                    </h2>
                    <p className="text-white/50 max-w-2xl mx-auto">
                        Real PnL from live trading sessions. These are actual trades executed by the founder.
                    </p>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-6 mb-12 max-w-2xl mx-auto">
                    <div className="bg-white/5 border border-white/10 rounded-xl p-6 text-center">
                        <div className="text-3xl font-bold text-sniper-green">{wins}</div>
                        <div className="text-sm text-white/50 mt-1">WINS</div>
                    </div>
                    <div className="bg-white/5 border border-white/10 rounded-xl p-6 text-center">
                        <div className="text-3xl font-bold text-sniper-red">{losses}</div>
                        <div className="text-sm text-white/50 mt-1">LOSSES</div>
                    </div>
                    <div className="bg-white/5 border border-white/10 rounded-xl p-6 text-center">
                        <div className="text-3xl font-bold text-sniper-green">{avgPnL}%</div>
                        <div className="text-sm text-white/50 mt-1">AVG PnL</div>
                    </div>
                </div>

                {/* Trades Grid */}
                <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 max-w-7xl mx-auto">
                    {trades.map((trade, index) => (
                        <div 
                            key={index}
                            className={`bg-white/5 border rounded-xl p-4 hover:bg-white/10 transition-all ${
                                trade.win ? 'border-sniper-green/30' : 'border-sniper-red/30'
                            }`}
                        >
                            <div className="flex items-center justify-between mb-3">
                                <span className="font-orbitron font-bold text-white">{trade.pair}</span>
                                {trade.win ? (
                                    <TrendingUp size={16} className="text-sniper-green" />
                                ) : (
                                    <TrendingDown size={16} className="text-sniper-red" />
                                )}
                            </div>
                            
                            <div className="flex items-center gap-2 mb-3">
                                <span className={`px-2 py-1 rounded text-xs font-bold ${
                                    trade.direction === 'LONG' 
                                        ? 'bg-sniper-green/20 text-sniper-green' 
                                        : 'bg-sniper-red/20 text-sniper-red'
                                }`}>
                                    {trade.direction}
                                </span>
                                <span className="text-xs text-white/50">{trade.leverage}</span>
                            </div>

                            <div className={`text-2xl font-bold ${trade.win ? 'text-sniper-green' : 'text-sniper-red'}`}>
                                {trade.pnl}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Contact CTA */}
                <div className="mt-12 text-center">
                    <p className="text-white/50 mb-4">
                        Want to learn the strategy behind these trades?
                    </p>
                    <a 
                        href="mailto:rickytspanish@gmail.com"
                        className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-sniper-purple to-sniper-green rounded-lg font-bold hover:opacity-90 transition-opacity"
                    >
                        <Target size={20} />
                        Contact Ricky Spanish
                    </a>
                </div>
            </div>
        </section>
    );
};
