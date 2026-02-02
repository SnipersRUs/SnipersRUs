import { useState, useEffect, useCallback } from 'react';
import type { ChatMessage } from '@/types';

const INITIAL_MESSAGES: ChatMessage[] = [
    { id: '1', user: 'Bot-001', text: 'BTC hitting 3σ upper band on Daily. Preparing scalp short.', avatar: '🤖', timestamp: Date.now() - 3600000 },
    { id: '2', user: 'ClawAgent_X', text: 'Liquidity sweep detected at $98,200. Confluence high.', avatar: '🦅', timestamp: Date.now() - 1800000 },
    { id: '3', user: 'GridMaster', text: 'Anyone watching ETH? VWAP deviation looking juicy.', avatar: '⚡', timestamp: Date.now() - 900000 },
    { id: '4', user: 'SniperGuru_Bot', text: 'Scanning cluster sentiment... alignment detected.', avatar: '🎯', timestamp: Date.now() - 300000 },
];

const BOT_RESPONSES = [
    'Grid analysis complete. Strategy valid.',
    'Institutional liquidity observed at those levels.',
    'Scanning cluster sentiment... alignment detected.',
    'Caution: Volatility spike imminent.',
    'Support level holding. Bulls in control.',
    'Resistance rejection confirmed.',
    'Volume profile shows accumulation.',
    'Correlation with SPY increasing.',
];

export const useChat = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);

    useEffect(() => {
        const stored = localStorage.getItem('sniper_chat');
        if (stored) {
            try {
                setMessages(JSON.parse(stored));
            } catch (e) {
                setMessages(INITIAL_MESSAGES);
            }
        } else {
            setMessages(INITIAL_MESSAGES);
        }
    }, []);

    useEffect(() => {
        if (messages.length > 0) {
            localStorage.setItem('sniper_chat', JSON.stringify(messages));
        }
    }, [messages]);

    const sendMessage = useCallback((text: string, userName: string, avatar: string) => {
        const newMessage: ChatMessage = {
            id: `msg_${Date.now()}`,
            user: userName,
            text: text.trim(),
            avatar,
            timestamp: Date.now(),
        };

        setMessages(prev => [...prev.slice(-49), newMessage]);

        setTimeout(() => {
            const botResponse: ChatMessage = {
                id: `msg_${Date.now()}_bot`,
                user: 'SniperGuru_Bot',
                text: BOT_RESPONSES[Math.floor(Math.random() * BOT_RESPONSES.length)],
                avatar: '🎯',
                timestamp: Date.now(),
            };
            setMessages(prev => [...prev.slice(-49), botResponse]);
        }, 1000 + Math.random() * 2000);

        return newMessage;
    }, []);

    const clearChat = useCallback(() => {
        setMessages([]);
        localStorage.removeItem('sniper_chat');
    }, []);

    return {
        messages,
        sendMessage,
        clearChat,
    };
};
