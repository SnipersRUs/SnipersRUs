interface StatsDisplayProps {
  xp: number;
  streak: number;
  level: number;
}

export default function StatsDisplay({ xp, streak, level }: StatsDisplayProps) {
  return (
    <div className="flex items-center gap-6 bg-slate-800/50 backdrop-blur-sm rounded-2xl p-4 border border-slate-700">
      {/* XP */}
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30">
          <span className="text-2xl">⭐</span>
        </div>
        <div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">XP</p>
          <p className="text-xl font-bold text-white">{xp.toLocaleString()}</p>
        </div>
      </div>

      {/* Streak */}
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-600 rounded-xl flex items-center justify-center shadow-lg shadow-orange-500/30">
          <span className="text-2xl">🔥</span>
        </div>
        <div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Streak</p>
          <p className="text-xl font-bold text-white">{streak} day{streak !== 1 ? 's' : ''}</p>
        </div>
      </div>

      {/* Level */}
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg shadow-green-500/30">
          <span className="text-xl font-bold text-white">{level}</span>
        </div>
        <div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Level</p>
          <p className="text-xl font-bold text-white">Lvl {level}</p>
        </div>
      </div>
    </div>
  );
}
