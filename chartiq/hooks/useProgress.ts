'use client';

import { useState, useEffect } from 'react';

export interface UserStats {
  xp: number;
  streak: number;
  lastLogin: string;
  level: number;
  totalCorrect: number;
  totalAnswered: number;
}

const STORAGE_KEY = 'chartiq_stats';

export function useProgress() {
  const [stats, setStats] = useState<UserStats>({
    xp: 0,
    streak: 0,
    lastLogin: '',
    level: 1,
    totalCorrect: 0,
    totalAnswered: 0,
  });

  // Load stats from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setStats(parsed);
      } catch (e) {
        console.error('Failed to parse saved stats:', e);
      }
    }
  }, []);

  // Save stats to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stats));
  }, [stats]);

  const updateStreak = () => {
    const today = new Date().toDateString();
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayString = yesterday.toDateString();

    if (stats.lastLogin === today) {
      // Already played today, don't update streak
      return;
    }

    if (stats.lastLogin === yesterdayString) {
      // Played yesterday, increment streak
      setStats(prev => ({ ...prev, streak: prev.streak + 1, lastLogin: today }));
    } else {
      // Streak broken or first time playing
      setStats(prev => ({ ...prev, streak: 1, lastLogin: today }));
    }
  };

  const addXP = (amount: number) => {
    setStats(prev => {
      const newXP = prev.xp + amount;
      const newLevel = Math.floor(newXP / 100) + 1; // New level every 100 XP
      return {
        ...prev,
        xp: newXP,
        level: newLevel,
      };
    });
  };

  const recordAnswer = (correct: boolean) => {
    setStats(prev => ({
      ...prev,
      totalAnswered: prev.totalAnswered + 1,
      totalCorrect: correct ? prev.totalCorrect + 1 : prev.totalCorrect,
    }));

    if (correct) {
      addXP(10);
    }
  };

  const getAccuracy = () => {
    if (stats.totalAnswered === 0) return 0;
    return Math.round((stats.totalCorrect / stats.totalAnswered) * 100);
  };

  const resetProgress = () => {
    const resetStats: UserStats = {
      xp: 0,
      streak: 0,
      lastLogin: '',
      level: 1,
      totalCorrect: 0,
      totalAnswered: 0,
    };
    setStats(resetStats);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(resetStats));
  };

  return {
    stats,
    addXP,
    updateStreak,
    recordAnswer,
    getAccuracy,
    resetProgress,
  };
}
