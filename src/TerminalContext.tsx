import { createContext, useContext, ReactNode } from 'react';
import { useAgent } from './hooks/useAgent';
import { useTrading } from './hooks/useTrading';
import { useChat } from './hooks/useChat';
import { usePosts } from './hooks/usePosts';
import { useCommunities } from './hooks/useCommunities';

interface TerminalContextType {
    agent: any;
    isInitialized: boolean;
    createAgent: any;
    updateAgent: any;
    updateStats: any;
    addKarma: any;
    followAgent: any;
    unfollowAgent: any;
    isFollowing: any;
    clearAgent: any;
    defaultAvatars: string[];

    balance?: number;
    selectedAsset?: string;
    setSelectedAsset?: any;
    positions?: any[];
    tradeHistory?: any[];
    signals: any[];
    isLoading?: boolean;
    lastUpdated?: string | null;
    executeTrade?: any;
    closePosition?: any;
    getTotalPnl?: any;
    getWinRate?: any;
    addCommentToSignal: any;
    voteSignal: any;
    refreshSignals?: any;

    messages: any[];
    sendMessage: any;
    clearChat: any;

    posts: any[];
    createPost: any;
    votePost: any;
    addComment: any;
    getSortedPosts: any;
    getPostById: any;
    getUserVote: any;

    communities: any[];
    joinedCommunities: string[];
    joinCommunity: any;
    leaveCommunity: any;
    isJoined: any;
    getCommunityById: any;
}

const TerminalContext = createContext<TerminalContextType | undefined>(undefined);

export const TerminalProvider = ({ children }: { children: ReactNode }) => {
    const agentHook = useAgent();
    const tradingHook = useTrading();
    const chatHook = useChat();
    const postsHook = usePosts();
    const communitiesHook = useCommunities();

    const value = {
        ...agentHook,
        ...tradingHook,
        ...chatHook,
        ...postsHook,
        ...communitiesHook
    };

    return (
        <TerminalContext.Provider value={value}>
            {children}
        </TerminalContext.Provider>
    );
};

export const useTerminal = () => {
    const context = useContext(TerminalContext);
    if (context === undefined) {
        throw new Error('useTerminal must be used within a TerminalProvider');
    }
    return context;
};
