'use client';

import { useState, useEffect } from 'react';
import ChartCard from '@/components/ChartCard';
import ProgressBar from '@/components/ProgressBar';
import StatsDisplay from '@/components/StatsDisplay';
import { useProgress } from '@/hooks/useProgress';
import { level1Data } from '@/data/levels';

type GameState = 'menu' | 'playing' | 'completed' | 'failed';

export default function Home() {
  const [gameState, setGameState] = useState<GameState>('menu');
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [shuffledQuestions, setShuffledQuestions] = useState(level1Data);
  const [correctCount, setCorrectCount] = useState(0);
  const [wrongCount, setWrongCount] = useState(0);
  const MAX_WRONG_ANSWERS = 3; // Penalty threshold

  const { stats, updateStreak, recordAnswer, getAccuracy, resetProgress } = useProgress();

  useEffect(() => {
    if (gameState === 'playing') {
      updateStreak();
      shuffleQuestions();
    }
  }, [gameState]);

  const shuffleQuestions = () => {
    const shuffled = [...level1Data].sort(() => Math.random() - 0.5);
    setShuffledQuestions(shuffled);
  };

  const handleStart = () => {
    setGameState('playing');
    setCurrentQuestionIndex(0);
    setCorrectCount(0);
    setWrongCount(0);
    shuffleQuestions();
  };

  const handleAnswer = (correct: boolean) => {
    recordAnswer(correct);
    if (correct) {
      setCorrectCount(prev => prev + 1);
    } else {
      setWrongCount(prev => {
        const newWrong = prev + 1;
        // Check if penalty threshold reached
        if (newWrong >= MAX_WRONG_ANSWERS) {
          setTimeout(() => {
            setGameState('failed');
          }, 1500);
        }
        return newWrong;
      });
    }
  };

  const handleNext = () => {
    if (currentQuestionIndex < shuffledQuestions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      setGameState('completed');
    }
  };

  const handleQuit = () => {
    setGameState('menu');
  };

  const handleRetry = () => {
    setGameState('playing');
    setCurrentQuestionIndex(0);
    setCorrectCount(0);
    setWrongCount(0);
    shuffleQuestions();
  };

  const currentQuestion = shuffledQuestions[currentQuestionIndex];
  const remainingStrikes = MAX_WRONG_ANSWERS - wrongCount;

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0b0e11' }}>
      {/* Background grid pattern */}
      <div className="fixed inset-0 opacity-5 pointer-events-none">
        <div className="absolute inset-0" style={{
          backgroundImage: 'linear-gradient(rgba(232, 236, 239, .05) 1px, transparent 1px), linear-gradient(90deg, rgba(232, 236, 239, .05) 1px, transparent 1px)',
          backgroundSize: '50px 50px'
        }} />
      </div>

      {/* Main content */}
      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header */}
        <header className="border-b" style={{ backgroundColor: '#1e2329', borderColor: '#2b3139' }}>
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-2xl font-bold" style={{ color: '#0ecb81' }}>
                SnipersRUs
              </div>
              <span className="hidden sm:inline text-sm" style={{ color: '#848e9c' }}>
                Pattern Recognition Training
              </span>
            </div>

            {/* Lives indicator */}
            {gameState === 'playing' && (
              <div className="flex items-center gap-2">
                <span className="text-sm" style={{ color: '#848e9c' }}>Strikes:</span>
                <div className="flex gap-1">
                  {[...Array(MAX_WRONG_ANSWERS)].map((_, i) => (
                    <div
                      key={i}
                      className="w-8 h-3 rounded-full transition-all duration-300"
                      style={{
                        backgroundColor: i < wrongCount ? '#f6465d' : '#0ecb81',
                        opacity: i >= wrongCount ? '0.3' : '1'
                      }}
                    />
                  ))}
                </div>
              </div>
            )}

            {gameState !== 'menu' && (
              <button
                onClick={handleQuit}
                className="px-4 py-2 rounded-lg font-semibold text-sm transition-all duration-200 hover:opacity-80"
                style={{
                  backgroundColor: '#2b3139',
                  color: '#eaecef',
                  border: '1px solid #2b3139'
                }}
              >
                ← Quit
              </button>
            )}
          </div>
        </header>

        {/* Main content area */}
        <main className="flex-1 container mx-auto px-4 py-6">
          {/* Stats Display */}
          <div className="mb-6">
            <StatsDisplay
              xp={stats.xp}
              streak={stats.streak}
              level={stats.level}
            />
          </div>

          <div className="flex justify-center items-start min-h-[60vh]">
            {gameState === 'menu' && (
              <div className="rounded-2xl shadow-2xl p-8 max-w-2xl w-full text-center" style={{ backgroundColor: '#1e2329', border: '1px solid #2b3139' }}>
                <div className="mb-8">
                  <div className="text-8xl mb-4">🎯</div>
                  <h1 className="text-4xl font-bold mb-4" style={{ color: '#eaecef' }}>
                    Master Chart Patterns
                  </h1>
                  <p className="text-lg mb-6" style={{ color: '#848e9c' }}>
                    Learn to identify trading patterns through interactive quizzes
                  </p>

                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="rounded-xl p-4" style={{ backgroundColor: '#2b3139' }}>
                      <div className="text-3xl mb-2">📊</div>
                      <h3 className="font-semibold mb-1" style={{ color: '#eaecef' }}>Candlesticks</h3>
                      <p className="text-sm" style={{ color: '#848e9c' }}>Hammer, Doji, Engulfing</p>
                    </div>
                    <div className="rounded-xl p-4" style={{ backgroundColor: '#2b3139' }}>
                      <div className="text-3xl mb-2">📈</div>
                      <h3 className="font-semibold mb-1" style={{ color: '#eaecef' }}>Patterns</h3>
                      <p className="text-sm" style={{ color: '#848e9c' }}>Flags, Pennants, Wedges</p>
                    </div>
                    <div className="rounded-xl p-4" style={{ backgroundColor: '#2b3139' }}>
                      <div className="text-3xl mb-2">🎯</div>
                      <h3 className="font-semibold mb-1" style={{ color: '#eaecef' }}>Support & Resistance</h3>
                      <p className="text-sm" style={{ color: '#848e9c' }}>Double Bottom, Top</p>
                    </div>
                    <div className="rounded-xl p-4" style={{ backgroundColor: '#2b3139' }}>
                      <div className="text-3xl mb-2">🔄</div>
                      <h3 className="font-semibold mb-1" style={{ color: '#eaecef' }}>Reversals</h3>
                      <p className="text-sm" style={{ color: '#848e9c' }}>Head & Shoulders</p>
                    </div>
                  </div>

                  <div className="rounded-xl p-4 mb-8" style={{ backgroundColor: 'rgba(246, 70, 93, 0.15)', border: '1px solid rgba(246, 70, 93, 0.3)' }}>
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <span className="text-2xl">⚠️</span>
                      <h3 className="font-semibold" style={{ color: '#f6465d' }}>Penalty System</h3>
                    </div>
                    <p className="text-sm" style={{ color: '#848e9c' }}>
                      Complete the quiz with fewer than {MAX_WRONG_ANSWERS} wrong answers or try again!
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleStart}
                  className="w-full py-4 font-bold text-xl rounded-xl transition-all duration-200 hover:scale-[1.02]"
                  style={{
                    background: 'linear-gradient(135deg, #0ecb81 0%, #6c5ce7 100%)',
                    color: '#eaecef'
                  }}
                >
                  Start Training 🚀
                </button>

                {stats.totalAnswered > 0 && (
                  <button
                    onClick={resetProgress}
                    className="mt-4 text-sm underline transition-opacity hover:opacity-80"
                    style={{ color: '#848e9c' }}
                  >
                    Reset All Progress
                  </button>
                )}
              </div>
            )}

            {gameState === 'playing' && currentQuestion && (
              <div className="w-full">
                {/* Progress bar */}
                <div className="mb-6">
                  <ProgressBar
                    current={currentQuestionIndex + 1}
                    total={shuffledQuestions.length}
                    label="Progress"
                  />
                </div>

                {/* Warning when low on lives */}
                {remainingStrikes === 1 && (
                  <div className="mb-4 rounded-xl p-4 text-center animate-fadeIn" style={{ backgroundColor: 'rgba(246, 70, 93, 0.15)', border: '1px solid rgba(246, 70, 93, 0.3)' }}>
                    <span className="font-semibold" style={{ color: '#f6465d' }}>
                      ⚠️ Last Strike! One more wrong answer and you'll need to restart.
                    </span>
                  </div>
                )}

                {/* Chart card */}
                <ChartCard
                  question={currentQuestion}
                  onAnswer={handleAnswer}
                  onNext={handleNext}
                />
              </div>
            )}

            {gameState === 'completed' && (
              <div className="rounded-2xl shadow-2xl p-8 max-w-2xl w-full text-center animate-fadeIn" style={{ backgroundColor: '#1e2329', border: '1px solid #2b3139' }}>
                <div className="mb-8">
                  <div className="text-8xl mb-4">
                    {correctCount === shuffledQuestions.length ? '🏆' : correctCount > shuffledQuestions.length / 2 ? '🎯' : '💪'}
                  </div>
                  <h2 className="text-3xl font-bold mb-4" style={{ color: '#eaecef' }}>
                    {correctCount === shuffledQuestions.length
                      ? 'Perfect Score!'
                      : correctCount > shuffledQuestions.length / 2
                      ? 'Great Job!'
                      : 'Keep Practicing!'}
                  </h2>

                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(14, 203, 129, 0.15)', border: '1px solid rgba(14, 203, 129, 0.3)' }}>
                      <p className="text-4xl font-bold" style={{ color: '#0ecb81' }}>{correctCount}</p>
                      <p className="text-sm" style={{ color: '#848e9c' }}>Correct</p>
                    </div>
                    <div className="rounded-xl p-4" style={{ backgroundColor: 'rgba(14, 203, 129, 0.15)', border: '1px solid rgba(14, 203, 129, 0.3)' }}>
                      <p className="text-4xl font-bold" style={{ color: '#0ecb81' }}>+{correctCount * 10}</p>
                      <p className="text-sm" style={{ color: '#848e9c' }}>XP Earned</p>
                    </div>
                  </div>

                  <div className="rounded-xl p-6 mb-8" style={{ backgroundColor: '#2b3139' }}>
                    <div className="text-sm font-semibold mb-4" style={{ color: '#848e9c' }}>Session Stats</div>
                    <div className="flex justify-center gap-8">
                      <div>
                        <p className="text-2xl font-bold" style={{ color: '#eaecef' }}>{getAccuracy()}%</p>
                        <p className="text-xs" style={{ color: '#848e9c' }}>Accuracy</p>
                      </div>
                      <div>
                        <p className="text-2xl font-bold" style={{ color: '#eaecef' }}>{stats.xp.toLocaleString()}</p>
                        <p className="text-xs" style={{ color: '#848e9c' }}>Total XP</p>
                      </div>
                      <div>
                        <p className="text-2xl font-bold" style={{ color: '#eaecef' }}>{stats.streak} 🔥</p>
                        <p className="text-xs" style={{ color: '#848e9c' }}>Day Streak</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={handleQuit}
                    className="flex-1 py-4 rounded-xl font-semibold transition-all duration-200 hover:scale-[1.02]"
                    style={{
                      backgroundColor: '#2b3139',
                      color: '#eaecef',
                      border: '1px solid #2b3139'
                    }}
                  >
                    ← Back to Home
                  </button>
                  <button
                    onClick={handleRetry}
                    className="flex-1 py-4 rounded-xl font-bold transition-all duration-200 hover:scale-[1.02]"
                    style={{
                      background: 'linear-gradient(135deg, #0ecb81 0%, #6c5ce7 100%)',
                      color: '#eaecef'
                    }}
                  >
                    Practice Again 🔄
                  </button>
                </div>
              </div>
            )}

            {gameState === 'failed' && (
              <div className="rounded-2xl shadow-2xl p-8 max-w-2xl w-full text-center animate-fadeIn" style={{ backgroundColor: '#1e2329', border: '1px solid #2b3139' }}>
                <div className="mb-8">
                  <div className="text-8xl mb-4">💔</div>
                  <h2 className="text-3xl font-bold mb-4" style={{ color: '#f6465d' }}>
                    Lesson Failed
                  </h2>
                  <p className="text-lg mb-6" style={{ color: '#848e9c' }}>
                    You got {MAX_WRONG_ANSWERS} wrong answers. Don't worry, pattern recognition takes practice!
                  </p>

                  <div className="rounded-xl p-6 mb-8" style={{ backgroundColor: '#2b3139' }}>
                    <div className="text-sm font-semibold mb-4" style={{ color: '#848e9c' }}>Session Summary</div>
                    <div className="flex justify-center gap-8">
                      <div>
                        <p className="text-2xl font-bold" style={{ color: '#eaecef' }}>{correctCount}</p>
                        <p className="text-xs" style={{ color: '#848e9c' }}>Correct</p>
                      </div>
                      <div>
                        <p className="text-2xl font-bold" style={{ color: '#f6465d' }}>{wrongCount}</p>
                        <p className="text-xs" style={{ color: '#848e9c' }}>Wrong</p>
                      </div>
                      <div>
                        <p className="text-2xl font-bold" style={{ color: '#eaecef' }}>{currentQuestionIndex + 1} / {shuffledQuestions.length}</p>
                        <p className="text-xs" style={{ color: '#848e9c' }}>Questions</p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-xl p-4 mb-8" style={{ backgroundColor: 'rgba(108, 92, 231, 0.15)', border: '1px solid rgba(108, 92, 231, 0.3)' }}>
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-2xl">💡</span>
                      <h3 className="font-semibold" style={{ color: '#6c5ce7' }}>Pro Tip</h3>
                    </div>
                    <p className="text-sm mt-2" style={{ color: '#848e9c' }}>
                      Take your time with each question. Read the explanations carefully after each answer to learn the patterns better.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={handleQuit}
                    className="flex-1 py-4 rounded-xl font-semibold transition-all duration-200 hover:scale-[1.02]"
                    style={{
                      backgroundColor: '#2b3139',
                      color: '#eaecef',
                      border: '1px solid #2b3139'
                    }}
                  >
                    ← Back to Home
                  </button>
                  <button
                    onClick={handleRetry}
                    className="flex-1 py-4 rounded-xl font-bold transition-all duration-200 hover:scale-[1.02]"
                    style={{
                      background: 'linear-gradient(135deg, #0ecb81 0%, #6c5ce7 100%)',
                      color: '#eaecef'
                    }}
                  >
                    Try Again 🎯
                  </button>
                </div>
              </div>
            )}
          </div>
        </main>

        {/* Footer */}
        <footer className="py-6 text-center border-t" style={{ backgroundColor: '#1e2329', borderColor: '#2b3139' }}>
          <p className="text-sm" style={{ color: '#848e9c' }}>
            Made by <span style={{ color: '#0ecb81', fontWeight: 'bold' }}>SnipersRUs</span> • Master the charts, master the market
          </p>
        </footer>
      </div>
    </div>
  );
}
