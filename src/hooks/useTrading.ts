import { useState, useEffect, useCallback } from 'react';
import type { Signal, Comment } from '@/types';

// Path to the signals JSON file (served from public folder)
const SIGNALS_JSON_PATH = '/signals.json';

export const useTrading = () => {
    const [signals, setSignals] = useState<Signal[]>([]);
    const [lastUpdated, setLastUpdated] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Fetch signals from JSON file
    const fetchSignals = useCallback(async () => {
        try {
            // Add cache-busting query param to always get fresh data
            const response = await fetch(`${SIGNALS_JSON_PATH}?t=${Date.now()}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.signals && Array.isArray(data.signals)) {
                setSignals(data.signals);
                setLastUpdated(data.lastUpdated);
            }
        } catch (error) {
            console.warn('Failed to fetch signals, using localStorage fallback:', error);

            // Fallback to localStorage if JSON file not available
            const stored = localStorage.getItem('sniper_signals_v2');
            if (stored) {
                try {
                    const parsed = JSON.parse(stored);
                    if (parsed.signals) {
                        setSignals(parsed.signals);
                    } else {
                        setSignals(parsed);
                    }
                } catch (e) {
                    console.error('Failed to parse stored signals:', e);
                }
            }
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Initial load
    useEffect(() => {
        fetchSignals();

        // Refresh signals every 30 seconds
        const interval = setInterval(fetchSignals, 30000);

        return () => clearInterval(interval);
    }, [fetchSignals]);

    // Simulate live price updates for active signals
    useEffect(() => {
        const interval = setInterval(() => {
            setSignals(prev => prev.map(sig => {
                if (sig.status !== 'ACTIVE') return sig;

                // Small random fluctuation to simulate live market
                const change = (Math.random() - 0.5) * 0.1;

                return {
                    ...sig,
                    pnl: (sig.pnl || 0) + change
                };
            }));
        }, 3000);

        return () => clearInterval(interval);
    }, []);

    const addCommentToSignal = useCallback((signalId: string, body: string, author: { id: string, name: string, avatar: string }) => {
        const newComment: Comment = {
            id: `c_${Date.now()}`,
            body,
            authorId: author.id,
            authorName: author.name,
            authorAvatar: author.avatar,
            upvotes: 0,
            downvotes: 0,
            createdAt: Date.now(),
            replies: []
        };

        setSignals(prev => prev.map(sig => {
            if (sig.id === signalId) {
                return { ...sig, comments: [newComment, ...sig.comments] };
            }
            return sig;
        }));

        // Save to localStorage for persistence
        localStorage.setItem('sniper_signals_v2', JSON.stringify({ signals, lastUpdated }));
    }, [signals, lastUpdated]);

    const voteSignal = useCallback((signalId: string, type: 'bullish' | 'bearish') => {
        setSignals(prev => prev.map(sig => {
            if (sig.id === signalId) {
                return {
                    ...sig,
                    sentiment: {
                        ...sig.sentiment,
                        [type]: sig.sentiment[type] + 1
                    }
                };
            }
            return sig;
        }));

        // Save to localStorage for persistence
        localStorage.setItem('sniper_signals_v2', JSON.stringify({ signals, lastUpdated }));
    }, [signals, lastUpdated]);

    // Paper Trading State
    const [balance, setBalance] = useState(10000);
    // Add selectedAsset here, defaulting to BTC
    const [selectedAsset, setSelectedAsset] = useState('BTC');
    const [positions, setPositions] = useState<any[]>([]);
    const [tradeHistory, setTradeHistory] = useState<any[]>([]);

    useEffect(() => {
        // Load paper trading state
        const stored = localStorage.getItem('sniper_paper_trading');
        if (stored) {
            const data = JSON.parse(stored);
            setBalance(data.balance || 10000);
            setPositions(data.positions || []);
            setTradeHistory(data.tradeHistory || []);
        }
    }, []);

    const savePaperState = (newBalance: number, newPositions: any[], newHistory: any[]) => {
        localStorage.setItem('sniper_paper_trading', JSON.stringify({
            balance: newBalance,
            positions: newPositions,
            tradeHistory: newHistory
        }));
    };

    // Fetch real-time price from OKX
    const fetchEntryPrice = async (asset: string): Promise<number> => {
        try {
            const instId = `${asset}-USDT-SWAP`;
            const response = await fetch(`https://www.okx.com/api/v5/market/ticker?instId=${instId}`);
            const data = await response.json();
            if (data.code === '0' && data.data && data.data[0]) {
                return parseFloat(data.data[0].last);
            }
        } catch (err) {
            console.error('Failed to fetch price:', err);
        }
        return 0;
    };

    const executeTrade = useCallback(async (asset: string, qty: number, side: 'LONG' | 'SHORT') => {
        const entryPrice = await fetchEntryPrice(asset);
        if (entryPrice === 0) {
            alert('Failed to fetch market price. Please try again.');
            return;
        }
        
        const newPos = {
            id: `pos_${Date.now()}`,
            asset,
            qty,
            side,
            entryPrice,
            livePnl: 0,
            startTime: Date.now()
        };

        const newPositions = [newPos, ...positions];
        setPositions(newPositions);
        savePaperState(balance, newPositions, tradeHistory);
    }, [balance, positions, tradeHistory]);

    const closePosition = useCallback((id: string) => {
        const pos = positions.find(p => p.id === id);
        if (!pos) return;

        const pnl = pos.livePnl || 0;
        const newBalance = balance + pnl;

        const historyItem = {
            id: `trade_${Date.now()}`,
            asset: pos.asset,
            side: pos.side,
            qty: pos.qty,
            entryPrice: pos.entryPrice,
            exitPrice: pos.entryPrice + (pos.side === 'LONG' ? pnl : -pnl), // Approx
            pnl,
            closedAt: Date.now()
        };

        const newHistory = [historyItem, ...tradeHistory];
        const newPositions = positions.filter(p => p.id !== id);

        setBalance(newBalance);
        setPositions(newPositions);
        setTradeHistory(newHistory);
        savePaperState(newBalance, newPositions, newHistory);
    }, [balance, positions, tradeHistory]);

    const getWinRate = useCallback(() => {
        if (tradeHistory.length === 0) return 0;
        const wins = tradeHistory.filter(t => t.pnl > 0).length;
        return Math.round((wins / tradeHistory.length) * 100);
    }, [tradeHistory]);

    // Update PnL with real-time prices from OKX
    useEffect(() => {
        const updatePnL = async () => {
            if (positions.length === 0) return;
            
            const updatedPositions = await Promise.all(
                positions.map(async (pos) => {
                    try {
                        const instId = `${pos.asset}-USDT-SWAP`;
                        const response = await fetch(`https://www.okx.com/api/v5/market/ticker?instId=${instId}`);
                        const data = await response.json();
                        
                        if (data.code === '0' && data.data && data.data[0]) {
                            const currentPrice = parseFloat(data.data[0].last);
                            const priceDiff = currentPrice - pos.entryPrice;
                            const pnl = pos.side === 'LONG' 
                                ? priceDiff * pos.qty 
                                : -priceDiff * pos.qty;
                            return { ...pos, livePnl: pnl };
                        }
                    } catch (err) {
                        console.error('Failed to update PnL:', err);
                    }
                    return pos;
                })
            );
            
            setPositions(updatedPositions);
        };

        // Update every 5 seconds
        const interval = setInterval(updatePnL, 5000);
        updatePnL(); // Initial update
        
        return () => clearInterval(interval);
    }, [positions.length]);

    return {
        signals,
        isLoading,
        lastUpdated,
        addCommentToSignal,
        voteSignal,
        refreshSignals: fetchSignals,

        // Paper Trading
        balance,
        selectedAsset,
        setSelectedAsset,
        positions,
        tradeHistory,
        executeTrade,
        closePosition,
        getWinRate
    };
};
