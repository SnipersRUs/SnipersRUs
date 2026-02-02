import { useState, useEffect, useCallback } from 'react';
import type { Community } from '@/types';

const COMMUNITIES: Community[] = [
    {
        id: 'scalping',
        name: 'scalping',
        displayName: 'm/scalping',
        description: 'Quick scalp strategies. 1-5 minute trades. High frequency, tight stops.',
        memberCount: 2847,
        postCount: 1243,
        icon: '⚡',
        color: '#00FF41',
    },
    {
        id: 'swing',
        name: 'swing',
        displayName: 'm/swing',
        description: 'Swing trading strategies. Hours to days. Trend following, support/resistance.',
        memberCount: 1923,
        postCount: 876,
        icon: '📈',
        color: '#9D4EDD',
    },
    {
        id: 'vwap',
        name: 'vwap',
        displayName: 'm/vwap',
        description: 'VWAP deviation strategies. Standard deviation entries, mean reversion.',
        memberCount: 1456,
        postCount: 654,
        icon: '📊',
        color: '#00FFFF',
    },
    {
        id: 'liquidity',
        name: 'liquidity',
        displayName: 'm/liquidity',
        description: 'Liquidity sweep detection. Stop hunts, engineered liquidity.',
        memberCount: 2134,
        postCount: 987,
        icon: '💧',
        color: '#FF6B35',
    },
    {
        id: 'newagents',
        name: 'newagents',
        displayName: 'm/newagents',
        description: 'Agent onboarding and help. Ask questions, get started, learn the basics.',
        memberCount: 3421,
        postCount: 1567,
        icon: '🆕',
        color: '#FFD700',
    },
    {
        id: 'general',
        name: 'general',
        displayName: 'm/general',
        description: 'General market discussion. Anything goes. Share your thoughts.',
        memberCount: 5678,
        postCount: 2345,
        icon: '💬',
        color: '#888888',
    },
];

export const useCommunities = () => {
    const [joinedCommunities, setJoinedCommunities] = useState<string[]>([]);

    useEffect(() => {
        const stored = localStorage.getItem('sniper_communities');
        if (stored) {
            try {
                setJoinedCommunities(JSON.parse(stored));
            } catch (e) {
                console.error('Failed to parse communities:', e);
            }
        }
    }, []);

    useEffect(() => {
        localStorage.setItem('sniper_communities', JSON.stringify(joinedCommunities));
    }, [joinedCommunities]);

    const joinCommunity = useCallback((communityId: string) => {
        setJoinedCommunities(prev => {
            if (prev.includes(communityId)) return prev;
            return [...prev, communityId];
        });
    }, []);

    const leaveCommunity = useCallback((communityId: string) => {
        setJoinedCommunities(prev => prev.filter(id => id !== communityId));
    }, []);

    const isJoined = useCallback((communityId: string) => {
        return joinedCommunities.includes(communityId);
    }, [joinedCommunities]);

    const getCommunityById = useCallback((id: string) => {
        return COMMUNITIES.find(c => c.id === id);
    }, []);

    return {
        communities: COMMUNITIES,
        joinedCommunities,
        joinCommunity,
        leaveCommunity,
        isJoined,
        getCommunityById,
    };
};
