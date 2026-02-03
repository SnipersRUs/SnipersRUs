import { useState, useCallback } from 'react';

interface ERC8004Data {
  isRegistered: boolean;
  karma: number;
  winRate: number;
  totalSignals: number;
  wins: number;
  losses: number;
  agentType: 'HUMAN' | 'AI';
  registeredAt: string;
  basescanUrl: string;
}

export const useERC8004 = () => {
  const [verificationCache, setVerificationCache] = useState<Record<string, ERC8004Data>>({});

  const checkVerification = useCallback(async (address: string): Promise<ERC8004Data | null> => {
    // Return cached data if available and less than 5 minutes old
    if (verificationCache[address]) {
      return verificationCache[address];
    }

    try {
      const response = await fetch(
        `https://snipersrus-backend-production.up.railway.app/api/erc8004/reputation/${address}`
      );
      
      if (!response.ok) {
        return null;
      }

      const result = await response.json();
      
      if (result.success && result.data) {
        const data = result.data;
        setVerificationCache(prev => ({ ...prev, [address]: data }));
        return data;
      }
      
      return null;
    } catch (error) {
      console.error('Error checking ERC-8004 verification:', error);
      return null;
    }
  }, [verificationCache]);

  const getVerificationBadge = (address: string) => {
    const data = verificationCache[address];
    
    if (!data) {
      return {
        verified: false,
        badge: null,
        tooltip: 'Not verified on-chain'
      };
    }

    return {
      verified: true,
      badge: {
        icon: '🔗',
        text: 'ERC-8004',
        color: 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      },
      tooltip: `Verified on Base • Karma: ${data.karma} • Win Rate: ${data.winRate}%`,
      data
    };
  };

  return {
    checkVerification,
    getVerificationBadge,
    verificationCache
  };
};
