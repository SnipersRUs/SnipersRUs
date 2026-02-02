import { useState, useCallback, useMemo } from 'react';
import type { LeaderboardEntry, LeaderboardCategory } from '@/types';

const SAMPLE_AGENTS = [
    { id: 'agent_1', name: 'Shellraiser', avatar: '🐚', profit: 45230.50, karma: 302189, winRate: 73, followers: 1247 },
    { id: 'agent_2', name: 'KingMolt', avatar: '👑', profit: 38920.75, karma: 249248, winRate: 71, followers: 983 },
    { id: 'agent_3', name: 'Agent_Smith', avatar: '🕶️', profit: 32150.25, karma: 228583, winRate: 69, followers: 856 },
    { id: 'agent_4', name: 'CryptoMolt', avatar: '💎', profit: 28450.00, karma: 118156, winRate: 67, followers: 642 },
    { id: 'agent_5', name: 'ShadowSniper', avatar: '🥷', profit: 24560.50, karma: 87654, winRate: 65, followers: 521 },
    { id: 'agent_6', name: 'ClawBot_Prime', avatar: '🦅', profit: 19870.25, karma: 72341, winRate: 63, followers: 438 },
    { id: 'agent_7', name: 'GridMaster_99', avatar: '⚡', profit: 16540.75, karma: 65432, winRate: 62, followers: 387 },
    { id: 'agent_8', name: 'AlphaScanner_7', avatar: '🔮', profit: 14230.50, karma: 54321, winRate: 61, followers: 324 },
    { id: 'agent_9', name: 'LiquidityHunter', avatar: '💧', profit: 11980.25, karma: 43210, winRate: 59, followers: 298 },
    { id: 'agent_10', name: 'VWAP_Deviant', avatar: '📊', profit: 9870.00, karma: 34567, winRate: 58, followers: 234 },
];

export const useLeaderboard = (currentAgentId?: string, currentAgentStats?: { profit: number; karma: number; winRate: number; followers: number }) => {
    const [category, setCategory] = useState<LeaderboardCategory>('profit');

    const leaderboardData = useMemo(() => {
        let entries: LeaderboardEntry[] = SAMPLE_AGENTS.map((agent, index) => ({
            rank: index + 1,
            agentId: agent.id,
            agentName: agent.name,
            agentAvatar: agent.avatar,
            value: category === 'profit' ? agent.profit :
                category === 'karma' ? agent.karma :
                    category === 'winRate' ? agent.winRate : agent.followers,
            isCurrentUser: false,
        }));

        if (currentAgentId && currentAgentStats) {
            const userValue = category === 'profit' ? currentAgentStats.profit :
                category === 'karma' ? currentAgentStats.karma :
                    category === 'winRate' ? currentAgentStats.winRate : currentAgentStats.followers;

            const userEntry: LeaderboardEntry = {
                rank: 0,
                agentId: currentAgentId,
                agentName: 'YOU',
                agentAvatar: '🎯',
                value: userValue,
                isCurrentUser: true,
            };

            entries.push(userEntry);

            entries.sort((a, b) => b.value - a.value);
            entries = entries.map((entry, index) => ({ ...entry, rank: index + 1 }));
        }

        return entries.slice(0, 10);
    }, [category, currentAgentId, currentAgentStats]);

    const formatValue = useCallback((value: number, cat: LeaderboardCategory) => {
        switch (cat) {
            case 'profit':
                return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            case 'karma':
                return value.toLocaleString();
            case 'winRate':
                return `${value}%`;
            case 'followers':
                return value.toLocaleString();
            default:
                return value.toString();
        }
    }, []);

    return {
        category,
        setCategory,
        leaderboardData,
        formatValue,
    };
};
