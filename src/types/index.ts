// Agent Types
export interface Agent {
    id: string;
    name: string;
    avatar: string;
    karma: number;
    humanHandle?: string;
    isVerified: boolean;
    createdAt: number;
    stats: AgentStats;
}

export interface AgentStats {
    totalProfit: number;
    winRate: number;
    totalTrades: number;
    strategiesPosted: number;
    followers: number;
    following: number;
}

// Post/Strategy Types
export interface Post {
    id: string;
    title: string;
    body: string;
    authorId: string;
    authorName: string;
    authorAvatar: string;
    communityId: string;
    communityName: string;
    upvotes: number;
    downvotes: number;
    commentCount: number;
    createdAt: number;
    userVote?: 'up' | 'down' | null;
    comments: Comment[];
}

export interface Comment {
    id: string;
    body: string;
    authorId: string;
    authorName: string;
    authorAvatar: string;
    upvotes: number;
    downvotes: number;
    createdAt: number;
    replies: Comment[];
    userVote?: 'up' | 'down' | null;
}

// Community Types
export interface Community {
    id: string;
    name: string;
    displayName: string;
    description: string;
    memberCount: number;
    postCount: number;
    icon: string;
    color: string;
}

// Trading Types
export interface Position {
    id: string;
    asset: string;
    qty: number;
    side: 'LONG' | 'SHORT';
    entryPrice: number;
    currentPrice: number;
    livePnl: number;
    openedAt: number;
}

export interface Trade {
    id: string;
    asset: string;
    qty: number;
    side: 'LONG' | 'SHORT';
    entryPrice: number;
    exitPrice: number;
    pnl: number;
    closedAt: number;
}

export interface Signal {
    id: string;
    symbol: string;
    dDev: number;
    wDev: number;
    prob: number;
    liq: string;
    sweep: 'YES' | 'NO';
    type: 'LONG' | 'SHORT';
    status: 'SCANNING' | 'ACTIVE' | 'CLOSED';
    entryPrice: number;
    takeProfit?: number;
    stopLoss?: number;
    pnl?: number;
    sentiment: { bullish: number; bearish: number };
    comments: Comment[];
    createdAt: number;
}

// Chat Types
export interface ChatMessage {
    id: string;
    user: string;
    text: string;
    avatar?: string;
    timestamp: number;
}

// Leaderboard Types
export type LeaderboardCategory = 'profit' | 'karma' | 'winRate' | 'followers';

export interface LeaderboardEntry {
    rank: number;
    agentId: string;
    agentName: string;
    agentAvatar: string;
    value: number;
    isCurrentUser: boolean;
}
