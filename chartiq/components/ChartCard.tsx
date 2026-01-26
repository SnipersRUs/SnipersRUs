'use client';

import { useState } from 'react';
import { Question } from '@/data/levels';

interface ChartCardProps {
  question: Question;
  onAnswer: (correct: boolean) => void;
  onNext: () => void;
}

export default function ChartCard({ question, onAnswer, onNext }: ChartCardProps) {
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [shake, setShake] = useState(false);

  const handleOptionClick = (index: number) => {
    if (selectedOption !== null) return; // Prevent multiple clicks

    setSelectedOption(index);
    const correct = index === question.correct_index;
    setIsCorrect(correct);
    onAnswer(correct);

    if (!correct) {
      setShake(true);
      setTimeout(() => setShake(false), 500);
    }

    setTimeout(() => {
      setShowExplanation(true);
    }, 300);
  };

  const handleNext = () => {
    setSelectedOption(null);
    setShowExplanation(false);
    setIsCorrect(null);
    setShake(false);
    onNext();
  };

  const getButtonStyle = (index: number) => {
    if (selectedOption === null) {
      return 'bg-slate-700 hover:bg-slate-600 border-slate-600';
    }

    if (index === question.correct_index) {
      return 'bg-green-500 border-green-600 shadow-lg shadow-green-500/50';
    }

    if (index === selectedOption && !isCorrect) {
      return 'bg-red-500 border-red-600 shake';
    }

    return 'bg-slate-700 border-slate-600 opacity-50';
  };

  const getIcon = (index: number) => {
    if (selectedOption === null) return null;
    if (index === question.correct_index) return '✓';
    if (index === selectedOption && !isCorrect) return '✗';
    return null;
  };

  return (
    <div className={`bg-slate-800 rounded-2xl shadow-2xl p-6 max-w-4xl w-full mx-auto ${shake ? 'shake' : ''}`}>
      {/* Progress indicator */}
      <div className="mb-4">
        <span className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
          {question.level} • {question.topic}
        </span>
      </div>

      {/* Chart image */}
      <div className="mb-6">
        <div className="relative bg-slate-900 rounded-xl overflow-hidden aspect-video flex items-center justify-center border-2 border-slate-700">
          <img
            src={question.image_url}
            alt="Chart pattern"
            className="w-full h-full object-contain"
            onError={(e) => {
              e.currentTarget.src = `data:image/svg+xml,${encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="800" height="450" viewBox="0 0 800 450">
                  <rect width="800" height="450" fill="#1e293b"/>
                  <text x="400" y="200" text-anchor="middle" fill="#64748b" font-size="24" font-family="Arial">
                    Chart Image
                  </text>
                  <text x="400" y="240" text-anchor="middle" fill="#64748b" font-size="16" font-family="Arial">
                    ${question.image_url.split('/').pop()}
                  </text>
                </svg>
              `)}`;
            }}
          />
        </div>
      </div>

      {/* Question */}
      <h2 className="text-2xl font-bold text-white mb-6 text-center">
        {question.question}
      </h2>

      {/* Options */}
      <div className="grid gap-4 mb-6">
        {question.options.map((option, index) => (
          <button
            key={index}
            onClick={() => handleOptionClick(index)}
            disabled={selectedOption !== null}
            className={`
              relative p-4 rounded-xl border-2 text-left text-lg font-semibold transition-all duration-200
              ${getButtonStyle(index)}
              ${selectedOption === null ? 'transform hover:scale-[1.02]' : ''}
              disabled:cursor-not-allowed
            `}
          >
            <span className={`mr-3 ${getIcon(index) ? '' : 'invisible'}`}>
              {getIcon(index)}
            </span>
            {option}
          </button>
        ))}
      </div>

      {/* Explanation */}
      {showExplanation && (
        <div className={`
          p-4 rounded-xl border-2 mb-6 animate-fadeIn
          ${isCorrect ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}
        `}>
          <p className={`text-sm font-semibold mb-2 ${isCorrect ? 'text-green-400' : 'text-red-400'}`}>
            {isCorrect ? 'Correct!' : 'Oops!'}
          </p>
          <p className="text-slate-300" dangerouslySetInnerHTML={{ __html: question.explanation }} />
        </div>
      )}

      {/* Next button */}
      {showExplanation && (
        <button
          onClick={handleNext}
          className="w-full py-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-bold text-lg rounded-xl 
                     hover:from-blue-600 hover:to-purple-700 transform hover:scale-[1.02] transition-all duration-200
                     shadow-lg shadow-purple-500/30"
        >
          Next Question →
        </button>
      )}
    </div>
  );
}
