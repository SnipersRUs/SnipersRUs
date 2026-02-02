import { useState, useEffect, useCallback } from 'react';
import type { Agent, AgentStats } from '@/types';

const DEFAULT_AVATARS = [
    '🤖', '👾', '🦾', '⚡', '🔮', '🎯', '🦅', '🐺', '🦈', '🐍',
    '🦂', '🦀', '🦞', '🪲', '🕷️', '🦋', '🔥', '💀', '👽', '🎭'
];

const generateAgentId = () => `agent_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const createDefaultStats = (): AgentStats => ({
    totalProfit: 0,
    winRate: 0,
    totalTrades: 0,
    strategiesPosted: 0,
    followers: 0,
    following: 0,
});

export const useAgent = () => {
    const [agent, setAgent] = useState<Agent | null>(null);
    const [isInitialized, setIsInitialized] = useState(false);

    useEffect(() => {
        const stored = localStorage.getItem('sniper_agent');
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                setAgent(parsed);
            } catch (e) {
                console.error('Failed to parse agent:', e);
            }
        }
        setIsInitialized(true);
    }, []);

    useEffect(() => {
        if (agent) {
            localStorage.setItem('sniper_agent', JSON.stringify(agent));
        }
    }, [agent]);

    const createAgent = useCallback((name: string, avatar: string, humanHandle?: string) => {
        const newAgent: Agent = {
            id: generateAgentId(),
            name: name.trim() || `Agent_${Math.floor(Math.random() * 9999)}`,
            avatar: avatar || DEFAULT_AVATARS[Math.floor(Math.random() * DEFAULT_AVATARS.length)],
            karma: 0,
            humanHandle: humanHandle?.trim() || undefined,
            isVerified: false,
            createdAt: Date.now(),
            stats: createDefaultStats(),
        };
        setAgent(newAgent);
        return newAgent;
    }, []);

    const updateAgent = useCallback((updates: Partial<Agent>) => {
        setAgent(prev => prev ? { ...prev, ...updates } : null);
    }, []);

    const updateStats = useCallback((statUpdates: Partial<AgentStats>) => {
        setAgent(prev => {
            if (!prev) return null;
            return {
                ...prev,
                stats: { ...prev.stats, ...statUpdates }
            };
        });
    }, []);

    const addKarma = useCallback((amount: number) => {
        setAgent(prev => {
            if (!prev) return null;
            return { ...prev, karma: Math.max(0, prev.karma + amount) };
        });
    }, []);

    const followAgent = useCallback((targetAgentId: string) => {
        const following = JSON.parse(localStorage.getItem('sniper_following') || '[]');
        if (!following.includes(targetAgentId)) {
            following.push(targetAgentId);
            localStorage.setItem('sniper_following', JSON.stringify(following));

            setAgent(prev => {
                if (!prev) return null;
                return {
                    ...prev,
                    stats: { ...prev.stats, following: following.length }
                };
            });
        }
    }, []);

    const unfollowAgent = useCallback((targetAgentId: string) => {
        const following = JSON.parse(localStorage.getItem('sniper_following') || '[]');
        const filtered = following.filter((id: string) => id !== targetAgentId);
        localStorage.setItem('sniper_following', JSON.stringify(filtered));

        setAgent(prev => {
            if (!prev) return null;
            return {
                ...prev,
                stats: { ...prev.stats, following: filtered.length }
            };
        });
    }, []);

    const isFollowing = useCallback((targetAgentId: string) => {
        const following = JSON.parse(localStorage.getItem('sniper_following') || '[]');
        return following.includes(targetAgentId);
    }, []);

    const clearAgent = useCallback(() => {
        setAgent(null);
        localStorage.removeItem('sniper_agent');
        localStorage.removeItem('sniper_following');
    }, []);

    return {
        agent,
        isInitialized,
        createAgent,
        updateAgent,
        updateStats,
        addKarma,
        followAgent,
        unfollowAgent,
        isFollowing,
        clearAgent,
        defaultAvatars: DEFAULT_AVATARS,
    };
};
