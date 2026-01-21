"""
Sniper Guru - Technical Analysis Indicators
Implements: Channeller, GPS, and Piv X Pro logic
"""

import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum


class SignalType(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


@dataclass
class ChannelData:
    """Regression channel data"""
    valid: bool = False
    slope: float = 0.0
    intercept: float = 0.0
    r2: float = 0.0
    support: float = 0.0
    resistance: float = 0.0
    width: float = 0.0
    is_bullish: bool = True


@dataclass
class GoldenPocket:
    """Golden Pocket zone data"""
    high: float
    low: float
    timeframe: str
    is_touched: bool = False


@dataclass
class TradeSignal:
    """Complete trade signal with reasoning"""
    symbol: str
    signal_type: SignalType
    probability: float
    entry_price: float
    stop_loss: float
    target_1: float
    target_2: float
    confluence_score: int
    reasons: List[str]
    timestamp: str


class Indicators:
    """Technical indicator calculations"""
    
    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        return tr.rolling(window=period).mean()
    
    @staticmethod
    def adx(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Average Directional Index - returns (ADX, +DI, -DI)"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate +DM and -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        # Calculate TR
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Smooth with Wilder's method
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
        
        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(alpha=1/period, adjust=False).mean()
        
        return adx, plus_di, minus_di
    
    @staticmethod
    def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Williams %R"""
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        
        wr = ((highest_high - df['close']) / (highest_high - lowest_low)) * -100
        return wr
    
    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return series.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return series.rolling(window=period).mean()
    
    @staticmethod
    def vwap(df: pd.DataFrame) -> pd.Series:
        """Volume Weighted Average Price"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        return (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    
    @staticmethod
    def pivot_highs(df: pd.DataFrame, left: int = 10, right: int = 10) -> pd.Series:
        """Detect pivot highs"""
        highs = df['high']
        pivots = pd.Series(index=df.index, dtype=float)
        
        for i in range(left, len(df) - right):
            window_left = highs.iloc[i-left:i]
            window_right = highs.iloc[i+1:i+right+1]
            current = highs.iloc[i]
            
            if current > window_left.max() and current > window_right.max():
                pivots.iloc[i] = current
        
        return pivots
    
    @staticmethod
    def pivot_lows(df: pd.DataFrame, left: int = 10, right: int = 10) -> pd.Series:
        """Detect pivot lows"""
        lows = df['low']
        pivots = pd.Series(index=df.index, dtype=float)
        
        for i in range(left, len(df) - right):
            window_left = lows.iloc[i-left:i]
            window_right = lows.iloc[i+1:i+right+1]
            current = lows.iloc[i]
            
            if current < window_left.min() and current < window_right.min():
                pivots.iloc[i] = current
        
        return pivots


class Channeller:
    """
    Multi-pivot regression channel detection
    Based on: Channeller Pro indicator
    """
    
    def __init__(self, min_pivots: int = 3, max_pivots: int = 5, 
                 min_r2: float = 0.7, require_hl_lh: bool = True):
        self.min_pivots = min_pivots
        self.max_pivots = max_pivots
        self.min_r2 = min_r2
        self.require_hl_lh = require_hl_lh
    
    def _linear_regression(self, x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
        """Calculate linear regression with R² score"""
        if len(x) < 2:
            return 0.0, 0.0, 0.0
        
        slope, intercept, r_value, _, _ = stats.linregress(x, y)
        r2 = r_value ** 2
        
        return slope, intercept, r2
    
    def _is_higher_lows(self, prices: List[float]) -> bool:
        """Check if prices form higher lows pattern"""
        if len(prices) < 2:
            return True
        return all(prices[i] > prices[i-1] for i in range(1, len(prices)))
    
    def _is_lower_highs(self, prices: List[float]) -> bool:
        """Check if prices form lower highs pattern"""
        if len(prices) < 2:
            return True
        return all(prices[i] < prices[i-1] for i in range(1, len(prices)))
    
    def detect_channel(self, df: pd.DataFrame, is_bullish: bool = True) -> ChannelData:
        """
        Detect regression channel from pivot points
        
        Args:
            df: OHLCV DataFrame
            is_bullish: True for bull channel (from lows), False for bear (from highs)
        
        Returns:
            ChannelData with channel properties
        """
        left_bars = 10
        right_bars = 10
        
        if is_bullish:
            pivots = Indicators.pivot_lows(df, left_bars, right_bars)
        else:
            pivots = Indicators.pivot_highs(df, left_bars, right_bars)
        
        # Get valid pivot points
        pivot_mask = ~pivots.isna()
        pivot_prices = pivots[pivot_mask].values[-self.max_pivots:]
        pivot_indices = np.where(pivot_mask)[0][-self.max_pivots:]
        
        if len(pivot_prices) < self.min_pivots:
            return ChannelData(valid=False)
        
        # Check HL/LH pattern
        if self.require_hl_lh:
            if is_bullish and not self._is_higher_lows(list(pivot_prices)):
                return ChannelData(valid=False)
            if not is_bullish and not self._is_lower_highs(list(pivot_prices)):
                return ChannelData(valid=False)
        
        # Calculate regression
        slope, intercept, r2 = self._linear_regression(pivot_indices, pivot_prices)
        
        # Validate slope direction
        if is_bullish and slope <= 0:
            return ChannelData(valid=False)
        if not is_bullish and slope >= 0:
            return ChannelData(valid=False)
        
        # Check R² threshold
        if r2 < self.min_r2:
            return ChannelData(valid=False)
        
        # Calculate channel width
        current_idx = len(df) - 1
        base_price = slope * current_idx + intercept
        
        # Find channel width from extremes
        start_idx = pivot_indices[0]
        end_idx = pivot_indices[-1]
        
        if is_bullish:
            # Width from highest high in range
            max_high = df['high'].iloc[start_idx:end_idx+1].max()
            width = max_high - (slope * df['high'].iloc[start_idx:end_idx+1].idxmax() + intercept)
            support = base_price
            resistance = base_price + width
        else:
            # Width from lowest low in range
            min_low = df['low'].iloc[start_idx:end_idx+1].min()
            width = min_low - (slope * df['low'].iloc[start_idx:end_idx+1].idxmin() + intercept)
            resistance = base_price
            support = base_price + width  # width is negative for bear channels
        
        return ChannelData(
            valid=True,
            slope=slope,
            intercept=intercept,
            r2=r2,
            support=support,
            resistance=resistance,
            width=abs(width),
            is_bullish=is_bullish
        )
    
    def is_at_support(self, df: pd.DataFrame, channel: ChannelData, tolerance_atr: float = 0.3) -> bool:
        """Check if price is at channel support"""
        if not channel.valid:
            return False
        
        atr = Indicators.atr(df).iloc[-1]
        current_low = df['low'].iloc[-1]
        current_close = df['close'].iloc[-1]
        
        return current_low <= channel.support + atr * tolerance_atr and current_close > channel.support
    
    def is_at_resistance(self, df: pd.DataFrame, channel: ChannelData, tolerance_atr: float = 0.3) -> bool:
        """Check if price is at channel resistance"""
        if not channel.valid:
            return False
        
        atr = Indicators.atr(df).iloc[-1]
        current_high = df['high'].iloc[-1]
        current_close = df['close'].iloc[-1]
        
        return current_high >= channel.resistance - atr * tolerance_atr and current_close < channel.resistance


class GPS:
    """
    Golden Pocket Syndicate - Fibonacci Golden Pocket detection
    Based on: GPS Pro indicator
    """
    
    def __init__(self, gp_high_fib: float = 0.618, gp_low_fib: float = 0.65,
                 touch_tolerance_pct: float = 0.5):
        self.gp_high_fib = gp_high_fib
        self.gp_low_fib = gp_low_fib
        self.touch_tolerance = touch_tolerance_pct / 100
    
    def calculate_gp(self, high: float, low: float, timeframe: str) -> GoldenPocket:
        """Calculate Golden Pocket levels from high/low range"""
        gp_high = high - (high - low) * self.gp_high_fib
        gp_low = high - (high - low) * self.gp_low_fib
        
        return GoldenPocket(high=gp_high, low=gp_low, timeframe=timeframe)
    
    def get_golden_pockets(self, df: pd.DataFrame, 
                           daily_df: Optional[pd.DataFrame] = None,
                           weekly_df: Optional[pd.DataFrame] = None,
                           monthly_df: Optional[pd.DataFrame] = None) -> List[GoldenPocket]:
        """
        Get Golden Pocket zones from multiple timeframes
        
        Uses current timeframe data and optional higher timeframe data
        """
        pockets = []
        
        # Current timeframe GP (from recent swing)
        lookback = min(50, len(df))
        period_high = df['high'].iloc[-lookback:].max()
        period_low = df['low'].iloc[-lookback:].min()
        pockets.append(self.calculate_gp(period_high, period_low, "current"))
        
        # Daily GP
        if daily_df is not None and len(daily_df) > 0:
            d_high = daily_df['high'].iloc[-1]
            d_low = daily_df['low'].iloc[-1]
            pockets.append(self.calculate_gp(d_high, d_low, "daily"))
        
        # Weekly GP
        if weekly_df is not None and len(weekly_df) > 0:
            w_high = weekly_df['high'].iloc[-1]
            w_low = weekly_df['low'].iloc[-1]
            pockets.append(self.calculate_gp(w_high, w_low, "weekly"))
        
        # Monthly GP
        if monthly_df is not None and len(monthly_df) > 0:
            m_high = monthly_df['high'].iloc[-1]
            m_low = monthly_df['low'].iloc[-1]
            pockets.append(self.calculate_gp(m_high, m_low, "monthly"))
        
        return pockets
    
    def is_near_gp(self, price: float, gp: GoldenPocket) -> bool:
        """Check if price is near a Golden Pocket zone"""
        tolerance = price * self.touch_tolerance
        return (price >= gp.low - tolerance and price <= gp.high + tolerance)
    
    def check_gp_confluence(self, df: pd.DataFrame, pockets: List[GoldenPocket]) -> Tuple[bool, int, List[str]]:
        """
        Check for Golden Pocket confluence
        
        Returns:
            Tuple of (is_near_any_gp, confluence_score, reasons)
        """
        current_price = df['close'].iloc[-1]
        current_low = df['low'].iloc[-1]
        current_high = df['high'].iloc[-1]
        
        score = 0
        reasons = []
        near_any = False
        
        timeframe_scores = {
            "current": 15,
            "daily": 20,
            "weekly": 25,
            "monthly": 30
        }
        
        for gp in pockets:
            # Check if price is in or touching GP zone
            in_zone = (current_low <= gp.high and current_high >= gp.low)
            near_zone = self.is_near_gp(current_price, gp)
            
            if in_zone or near_zone:
                near_any = True
                score += timeframe_scores.get(gp.timeframe, 15)
                reasons.append(f"Near {gp.timeframe} GP ({gp.low:.2f}-{gp.high:.2f})")
        
        return near_any, score, reasons


class PivX:
    """
    Pivot X Pro - Pivot quality scoring and Williams %R divergence
    Based on: Piv X Pro indicator
    """
    
    def __init__(self, willr_length: int = 14, ob_level: int = -20, 
                 os_level: int = -80, min_score: int = 60):
        self.willr_length = willr_length
        self.ob_level = ob_level
        self.os_level = os_level
        self.min_score = min_score
    
    def detect_williams_divergence(self, df: pd.DataFrame) -> Tuple[bool, bool, List[str]]:
        """
        Detect Williams %R divergences
        
        Returns:
            Tuple of (bullish_div, bearish_div, reasons)
        """
        willr = Indicators.williams_r(df, self.willr_length)
        
        # Get pivot points for both price and Williams %R
        lookback = 5
        price_pivot_lows = Indicators.pivot_lows(df, lookback, lookback)
        price_pivot_highs = Indicators.pivot_highs(df, lookback, lookback)
        
        # Create Williams %R dataframe for pivot detection
        willr_df = pd.DataFrame({'high': willr, 'low': willr, 'close': willr}, index=df.index)
        willr_pivot_lows = Indicators.pivot_lows(willr_df, lookback, lookback)
        willr_pivot_highs = Indicators.pivot_highs(willr_df, lookback, lookback)
        
        bullish_div = False
        bearish_div = False
        reasons = []
        
        # Check for bullish divergence (price lower low, Williams higher low)
        price_lows = price_pivot_lows.dropna()
        willr_lows = willr_pivot_lows.dropna()
        
        if len(price_lows) >= 2 and len(willr_lows) >= 2:
            # Get last two lows
            if price_lows.iloc[-1] < price_lows.iloc[-2]:  # Price making lower low
                # Find corresponding Williams %R values
                idx1 = price_lows.index[-2]
                idx2 = price_lows.index[-1]
                
                if idx1 in willr.index and idx2 in willr.index:
                    willr_at_low1 = willr.loc[idx1]
                    willr_at_low2 = willr.loc[idx2]
                    
                    if willr_at_low2 > willr_at_low1:  # Williams making higher low
                        if willr_at_low2 <= self.os_level or willr_at_low1 <= self.os_level:
                            bullish_div = True
                            reasons.append(f"Williams %R bullish divergence (oversold)")
        
        # Check for bearish divergence (price higher high, Williams lower high)
        price_highs = price_pivot_highs.dropna()
        willr_highs = willr_pivot_highs.dropna()
        
        if len(price_highs) >= 2 and len(willr_highs) >= 2:
            if price_highs.iloc[-1] > price_highs.iloc[-2]:  # Price making higher high
                idx1 = price_highs.index[-2]
                idx2 = price_highs.index[-1]
                
                if idx1 in willr.index and idx2 in willr.index:
                    willr_at_high1 = willr.loc[idx1]
                    willr_at_high2 = willr.loc[idx2]
                    
                    if willr_at_high2 < willr_at_high1:  # Williams making lower high
                        if willr_at_high2 >= self.ob_level or willr_at_high1 >= self.ob_level:
                            bearish_div = True
                            reasons.append(f"Williams %R bearish divergence (overbought)")
        
        return bullish_div, bearish_div, reasons
    
    def calculate_pivot_score(self, df: pd.DataFrame, is_low: bool = True) -> Tuple[int, List[str]]:
        """
        Calculate pivot quality confluence score
        
        Returns:
            Tuple of (score, reasons)
        """
        score = 10  # Base score
        reasons = []
        
        # Volume confirmation
        vol_avg = df['volume'].rolling(20).mean().iloc[-1]
        current_vol = df['volume'].iloc[-1]
        
        if current_vol > vol_avg * 1.5:
            score += 15
            reasons.append("High volume confirmation")
        
        # RSI extremes
        rsi = Indicators.rsi(df).iloc[-1]
        
        if is_low and rsi <= 30:
            score += 25
            reasons.append(f"RSI oversold ({rsi:.1f})")
        elif not is_low and rsi >= 70:
            score += 25
            reasons.append(f"RSI overbought ({rsi:.1f})")
        
        # Williams divergence
        bull_div, bear_div, div_reasons = self.detect_williams_divergence(df)
        
        if is_low and bull_div:
            score += 15
            reasons.extend(div_reasons)
        elif not is_low and bear_div:
            score += 15
            reasons.extend(div_reasons)
        
        # Sweep detection (liquidity grab)
        lookback = 36
        if is_low:
            prev_low = df['low'].iloc[-lookback:-1].min()
            current_low = df['low'].iloc[-1]
            current_close = df['close'].iloc[-1]
            
            if current_low < prev_low and current_close > prev_low:
                score += 15
                reasons.append("Liquidity sweep (stop hunt)")
        else:
            prev_high = df['high'].iloc[-lookback:-1].max()
            current_high = df['high'].iloc[-1]
            current_close = df['close'].iloc[-1]
            
            if current_high > prev_high and current_close < prev_high:
                score += 15
                reasons.append("Liquidity sweep (stop hunt)")
        
        return score, reasons
    
    def detect_choch(self, df: pd.DataFrame) -> Tuple[bool, bool, List[str]]:
        """
        Detect Change of Character (CHoCH) / Market Structure Shift
        
        Returns:
            Tuple of (choch_up, choch_down, reasons)
        """
        pivot_lows = Indicators.pivot_lows(df, 5, 5).dropna()
        pivot_highs = Indicators.pivot_highs(df, 5, 5).dropna()
        
        choch_up = False
        choch_down = False
        reasons = []
        
        # CHoCH Up: Current pivot low > previous pivot low (higher low)
        if len(pivot_lows) >= 2:
            if pivot_lows.iloc[-1] > pivot_lows.iloc[-2]:
                choch_up = True
                reasons.append("CHoCH Up - Higher low formed")
        
        # CHoCH Down: Current pivot high < previous pivot high (lower high)
        if len(pivot_highs) >= 2:
            if pivot_highs.iloc[-1] < pivot_highs.iloc[-2]:
                choch_down = True
                reasons.append("CHoCH Down - Lower high formed")
        
        return choch_up, choch_down, reasons


class TrinityAnalyzer:
    """
    Combined analyzer using Channeller + GPS + PivX
    Produces ranked trade signals with reasoning
    """
    
    def __init__(self, min_confluence: int = 3, adx_threshold: float = 20.0):
        self.channeller = Channeller()
        self.gps = GPS()
        self.pivx = PivX()
        self.min_confluence = min_confluence
        self.adx_threshold = adx_threshold
    
    def analyze(self, symbol: str, df: pd.DataFrame,
                daily_df: Optional[pd.DataFrame] = None,
                weekly_df: Optional[pd.DataFrame] = None,
                monthly_df: Optional[pd.DataFrame] = None) -> Optional[TradeSignal]:
        """
        Perform full Trinity analysis on a symbol
        
        Returns:
            TradeSignal if valid setup found, None otherwise
        """
        if len(df) < 50:
            return None
        
        # Calculate base indicators
        atr = Indicators.atr(df).iloc[-1]
        adx, plus_di, minus_di = Indicators.adx(df)
        current_adx = adx.iloc[-1]
        
        # Skip if no trend
        if current_adx < self.adx_threshold:
            return None
        
        current_price = df['close'].iloc[-1]
        current_time = df.index[-1].strftime("%Y-%m-%d %H:%M") if hasattr(df.index[-1], 'strftime') else str(df.index[-1])
        
        # Initialize confluence tracking
        bull_confluence = 0
        bear_confluence = 0
        bull_reasons = []
        bear_reasons = []
        
        # ===== CHANNELLER ANALYSIS =====
        bull_channel = self.channeller.detect_channel(df, is_bullish=True)
        bear_channel = self.channeller.detect_channel(df, is_bullish=False)
        
        if bull_channel.valid:
            if self.channeller.is_at_support(df, bull_channel):
                bull_confluence += 1
                bull_reasons.append(f"At bull channel support (R²:{bull_channel.r2:.2f})")
        
        if bear_channel.valid:
            if self.channeller.is_at_resistance(df, bear_channel):
                bear_confluence += 1
                bear_reasons.append(f"At bear channel resistance (R²:{bear_channel.r2:.2f})")
        
        # ===== GPS ANALYSIS =====
        golden_pockets = self.gps.get_golden_pockets(df, daily_df, weekly_df, monthly_df)
        near_gp, gp_score, gp_reasons = self.gps.check_gp_confluence(df, golden_pockets)
        
        if near_gp and gp_score >= 40:
            bull_confluence += 1
            bear_confluence += 1
            bull_reasons.extend(gp_reasons)
            bear_reasons.extend(gp_reasons)
        
        # ===== PIVX ANALYSIS =====
        
        # Williams divergence
        bull_div, bear_div, div_reasons = self.pivx.detect_williams_divergence(df)
        
        if bull_div:
            bull_confluence += 1
            bull_reasons.extend([r for r in div_reasons if "bullish" in r.lower()])
        
        if bear_div:
            bear_confluence += 1
            bear_reasons.extend([r for r in div_reasons if "bearish" in r.lower()])
        
        # Pivot quality
        low_score, low_reasons = self.pivx.calculate_pivot_score(df, is_low=True)
        high_score, high_reasons = self.pivx.calculate_pivot_score(df, is_low=False)
        
        if low_score >= 60:
            bull_confluence += 1
            bull_reasons.extend(low_reasons)
        
        if high_score >= 60:
            bear_confluence += 1
            bear_reasons.extend(high_reasons)
        
        # CHoCH
        choch_up, choch_down, choch_reasons = self.pivx.detect_choch(df)
        
        if choch_up:
            bull_confluence += 1
            bull_reasons.extend([r for r in choch_reasons if "Up" in r])
        
        if choch_down:
            bear_confluence += 1
            bear_reasons.extend([r for r in choch_reasons if "Down" in r])
        
        # ===== MARKET STRUCTURE =====
        # Simple HH/HL or LL/LH detection
        highs = df['high'].iloc[-20:]
        lows = df['low'].iloc[-20:]
        
        recent_high = highs.iloc[-5:].max()
        prev_high = highs.iloc[-15:-5].max()
        recent_low = lows.iloc[-5:].min()
        prev_low = lows.iloc[-15:-5].min()
        
        # Higher high + higher low = bullish structure
        if recent_high > prev_high and recent_low > prev_low:
            bull_confluence += 1
            bull_reasons.append("Bullish market structure (HH+HL)")
        
        # Lower low + lower high = bearish structure
        if recent_low < prev_low and recent_high < prev_high:
            bear_confluence += 1
            bear_reasons.append("Bearish market structure (LL+LH)")
        
        # ===== DETERMINE SIGNAL =====
        
        # Calculate probability (confluence / max possible * 100)
        max_confluence = 6
        bull_probability = (bull_confluence / max_confluence) * 100
        bear_probability = (bear_confluence / max_confluence) * 100
        
        # Determine signal type
        if bull_confluence >= self.min_confluence and bull_confluence > bear_confluence:
            signal_type = SignalType.LONG
            probability = bull_probability
            confluence = bull_confluence
            reasons = list(set(bull_reasons))  # Remove duplicates
            
            stop_loss = current_price - atr * 1.5
            target_1 = current_price + atr * 2.0
            target_2 = current_price + atr * 4.0
            
        elif bear_confluence >= self.min_confluence and bear_confluence > bull_confluence:
            signal_type = SignalType.SHORT
            probability = bear_probability
            confluence = bear_confluence
            reasons = list(set(bear_reasons))
            
            stop_loss = current_price + atr * 1.5
            target_1 = current_price - atr * 2.0
            target_2 = current_price - atr * 4.0
            
        else:
            return None
        
        return TradeSignal(
            symbol=symbol,
            signal_type=signal_type,
            probability=probability,
            entry_price=current_price,
            stop_loss=stop_loss,
            target_1=target_1,
            target_2=target_2,
            confluence_score=confluence,
            reasons=reasons,
            timestamp=current_time
        )
