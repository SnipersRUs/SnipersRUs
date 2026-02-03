import { Shield, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ERC8004BadgeProps {
  address: string;
  isVerified: boolean;
  karma?: number;
  winRate?: number;
  basescanUrl?: string;
  compact?: boolean;
  className?: string;
}

export const ERC8004Badge = ({
  address,
  isVerified,
  karma,
  winRate,
  basescanUrl,
  compact = false,
  className
}: ERC8004BadgeProps) => {
  if (!isVerified) {
    if (compact) return null;
    
    return (
      <div className={cn(
        "inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs",
        "bg-white/5 text-white/40 border border-white/10",
        className
      )}>
        <Shield size={12} />
        <span>Not Verified</span>
      </div>
    );
  }

  if (compact) {
    return (
      <a
        href={basescanUrl || `https://basescan.org/address/${address}`}
        target="_blank"
        rel="noopener noreferrer"
        className={cn(
          "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono",
          "bg-blue-500/20 text-blue-400 border border-blue-500/30",
          "hover:bg-blue-500/30 transition-colors",
          className
        )}
        title={`ERC-8004 Verified on Base • Karma: ${karma}`}
      >
        <Shield size={10} />
        <span>8004</span>
      </a>
    );
  }

  return (
    <div className={cn(
      "inline-flex flex-col gap-1 p-3 rounded-lg",
      "bg-blue-500/10 border border-blue-500/20",
      className
    )}>
      <div className="flex items-center gap-2">
        <Shield size={14} className="text-blue-400" />
        <span className="text-xs font-bold text-blue-400 uppercase tracking-wider">
          ERC-8004 Verified
        </span>
        <a
          href={basescanUrl || `https://basescan.org/address/${address}`}
          target="_blank"
          rel="noopener noreferrer"
          className="ml-auto text-white/40 hover:text-blue-400 transition-colors"
          title="View on BaseScan"
        >
          <ExternalLink size={12} />
        </a>
      </div>
      
      <div className="flex items-center gap-4 mt-1 text-xs">
        {karma !== undefined && (
          <div className="text-white/70">
            Karma: <span className="text-white font-bold">{karma}</span>
          </div>
        )}
        {winRate !== undefined && (
          <div className="text-white/70">
            Win Rate: <span className="text-green-400 font-bold">{winRate}%</span>
          </div>
        )}
      </div>
      
      <div className="text-[10px] text-white/40 mt-1">
        Reputation verified on Base L2
      </div>
    </div>
  );
};

export const ERC8004MiniBadge = () => (
  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono bg-blue-500/20 text-blue-400 border border-blue-500/30">
    <Shield size={8} />
    8004
  </span>
);
