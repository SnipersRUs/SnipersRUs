import { useState, useEffect, useCallback } from 'react';
import type { ChatMessage } from '@/types';

const API_BASE = 'https://snipersrus-backend-production.up.railway.app/api';

export const useChat = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);

    const fetchMessages = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/chat`);
            if (response.ok) {
                const data = await response.json();
                setMessages(data);
            }
        } catch (err) {
            console.error('Failed to fetch messages:', err);
        }
    }, []);

    useEffect(() => {
        fetchMessages();
        const interval = setInterval(fetchMessages, 3000); // Poll every 3 seconds
        return () => clearInterval(interval);
    }, [fetchMessages]);

    const sendMessage = useCallback(async (text: string, userName: string, avatar: string) => {
        const tempId = `temp_${Date.now()}`;
        const newMessage: ChatMessage = {
            id: tempId,
            user: userName,
            text: text.trim(),
            avatar,
            timestamp: Date.now(),
        };

        // Optimistic update
        setMessages(prev => [...prev, newMessage]);

        try {
            const response = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user: userName, text: text.trim(), avatar }),
            });

            if (response.ok) {
                const savedMsg = await response.json();
                setMessages(prev => prev.map(m => m.id === tempId ? savedMsg : m));
            }
        } catch (err) {
            console.error('Failed to send message:', err);
        }

        return newMessage;
    }, []);

    const clearChat = useCallback(() => {
        setMessages([]);
    }, []);

    return {
        messages,
        sendMessage,
        clearChat,
    };
};
