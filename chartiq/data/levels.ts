export interface Question {
  id: number;
  level: string;
  topic: string;
  image_url: string;
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export const level1Data: Question[] = [
  {
    id: 101,
    level: "Candlestick Basics",
    topic: "Reversals",
    image_url: "/assets/charts/hammer.svg",
    question: "Identify this single candle pattern found at the bottom of a downtrend:",
    options: [
      "Shooting Star",
      "Hammer",
      "Doji"
    ],
    correct_index: 1,
    explanation: "Correct! This is a **Hammer**. It has a small body and a long lower wick. It signals that sellers pushed price down hard, but buyers pushed it back up, suggesting a potential bullish reversal."
  },
  {
    id: 102,
    level: "Candlestick Basics",
    topic: "Reversals",
    image_url: "/assets/charts/shooting-star.svg",
    question: "What does this candle suggest about price action?",
    options: [
      "Strong bullish momentum",
      "Indecision in the market",
      "Potential bearish reversal"
    ],
    correct_index: 2,
    explanation: "Right! This is a **Shooting Star**. It appears at the top of an uptrend. The long upper wick shows buyers tried to push higher but were rejected, signaling a possible drop."
  },
  {
    id: 103,
    level: "Candlestick Basics",
    topic: "Momentum",
    image_url: "/assets/charts/bullish-engulfing.svg",
    question: "Identify this 2-candle pattern:",
    options: [
      "Bearish Engulfing",
      "Bullish Engulfing",
      "Tweezer Bottom"
    ],
    correct_index: 1,
    explanation: "Correct! A **Bullish Engulfing** pattern occurs when a large green candle completely 'eats' the body of the previous small red candle. This indicates strong buying pressure entering the market."
  },
  {
    id: 104,
    level: "Candlestick Basics",
    topic: "Indecision",
    image_url: "/assets/charts/doji.svg",
    question: "This candle has almost no body. What does it represent?",
    options: [
      "Market Indecision / Neutrality",
      "Explosive Volatility",
      "Bearish Breakdown"
    ],
    correct_index: 0,
    explanation: "Exactly! This is a **Doji**. The open and close prices are virtually the same. It means neither buyers nor sellers are in control. The trend is likely to pause or reverse."
  },
  {
    id: 105,
    level: "Candlestick Basics",
    topic: "Continuation",
    image_url: "/assets/charts/marubozu.svg",
    question: "This candle has a large body and almost no wicks. What is its name?",
    options: [
      "Spinning Top",
      "Marubozu",
      "Gravestone Doji"
    ],
    correct_index: 1,
    explanation: "Nice! This is a **Marubozu**. It represents extreme control. A green Marobozu means buyers controlled the price from the open to the close with no rejection."
  },
  {
    id: 106,
    level: "Candlestick Basics",
    topic: "Reversals",
    image_url: "/assets/charts/three-black-crows.svg",
    question: "Identify this bearish pattern:",
    options: [
      "Three White Soldiers",
      "Three Black Crows",
      "Morning Star"
    ],
    correct_index: 1,
    explanation: "Correct! **Three Black Crows** consists of three long red candles that close progressively lower. It is a strong signal that the downtrend is likely to continue."
  }
];
