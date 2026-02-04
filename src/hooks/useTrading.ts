import { useState, useEffect, useCallback } from 'react';
import type { Signal, Comment } from '@/types';

// Path to the signals JSON file (served from public folder)
const API_BASE = 'http://localhost:3000/api';

export const useTrading = () => {
    const [signals, setSignals] = useState<Signal[]>([]);
    const [lastUpdated, setLastUpdated] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Fetch signals from backend
    const fetchSignals = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/scanner/feed?t=${Date.now()}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.signals && Array.isArray(data.signals)) {
                const mappedSignals: Signal[] = data.signals.map((s: any) => ({
                    id: s.id,
                    symbol: s.symbol,
                    type: s.direction,
                    entryPrice: parseFloat(s.entry),
                    pnl: s.pnl || 0,
                    prob: s.confidence || 70,
                    status: s.result ? 'RESOLVED' : 'ACTIVE',
                    createdAt: new Date(s.timestamp).getTime(),
                    sentiment: s.sentiment || { bullish: 0, bearish: 0 },
                    comments: s.comments || []
                }));
                setSignals(mappedSignals);
                setLastUpdated(new Date().toISOString());
            }
        } catch (error) {
            console.warn('Failed to fetch signals from backend:', error);
            // Fallback to static file if backend fails
            try {
                const response = await fetch('/signals.json');
                const data = await response.json();
                setSignals(data);
            } catch (e) {
                console.error('Fallback fetch failed:', e);
            }
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Initial load
    useEffect(() => {
        fetchSignals();

        // Refresh signals every 10 seconds (faster for "real-time" feel)
        const interval = setInterval(fetchSignals, 10000);

        return () => clearInterval(interval);
    }, [fetchSignals]);

    // Update PnL for active signals using real market data
    useEffect(() => {
        const updateSignalPnL = async () => {
            if (signals.length === 0) return;

            const activeSignals = signals.filter(s => s.status === 'ACTIVE');
            if (activeSignals.length === 0) return;

            const updatedSignals = await Promise.all(signals.map(async (sig) => {
                if (sig.status !== 'ACTIVE') return sig;

                try {
                    // Extract base asset from symbol (e.g., BTC/USDT -> BTC)
                    const asset = sig.symbol.split('/')[0].split('USDT')[0];
                    const instId = `${asset}-USDT-SWAP`;
                    const response = await fetch(`https://www.okx.com/api/v5/market/ticker?instId=${instId}`);
                    const data = await response.json();

                    if (data.code === '0' && data.data && data.data[0]) {
                        const currentPrice = parseFloat(data.data[0].last);
                        const priceDiff = currentPrice - sig.entryPrice;
                        const pnlPercent = (priceDiff / sig.entryPrice) * 100 * (sig.type === 'LONG' ? 1 : -1);
                        return { ...sig, pnl: pnlPercent };
                    }
                } catch (err) {
                    // Silently fail and keep current pnl
                }
                return sig;
            }));

            setSignals(updatedSignals);
        };

        const interval = setInterval(updateSignalPnL, 10000); // Update every 10s
        updateSignalPnL();

        return () => clearInterval(interval);
    }, [signals.some(s => s.status === 'ACTIVE')]);

    const addCommentToSignal = useCallback(async (signalId: string, body: string, author: { id: string, name: string, avatar: string }) => {
        try {
            const response = await fetch(`${API_BASE}/scanner/comment/${signalId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    authorName: author.name,
                    authorAvatar: author.avatar,
                    body
                }),
            });

            if (response.ok) {
                const newComment = await response.json();
                setSignals(prev => prev.map(sig => {
                    if (sig.id === signalId) {
                        return { ...sig, comments: [newComment, ...(sig.comments || [])] };
                    }
                    return sig;
                }));
            }
        } catch (err) {
            console.error('Failed to add comment:', err);
        }
    }, [API_BASE]);

    const voteSignal = useCallback(async (signalId: string, type: 'bullish' | 'bearish') => {
        try {
            const response = await fetch(`${API_BASE}/scanner/vote/${signalId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type }),
            });

            if (response.ok) {
                setSignals(prev => prev.map(sig => {
                    if (sig.id === signalId) {
                        return {
                            ...sig,
                            sentiment: {
                                ...sig.sentiment,
                                [type]: (sig.sentiment[type] || 0) + 1
                            }
                        };
                    }
                    return sig;
                }));
            }
        } catch (err) {
            console.error('Failed to vote:', err);
        }
    }, [API_BASE]);

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
