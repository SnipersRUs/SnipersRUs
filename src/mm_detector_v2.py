#!/usr/bin/env python3
"""
Market Maker Detection & Analysis System v2
Enhanced version with monitoring capabilities
"""
import numpy as np
import time
import importlib.util
from dataclasses import dataclass
from typing import Dict, List, Tuple

# Load config (for timezone-independent constants; safe if absent)
try:
    spec = importlib.util.spec_from_file_location("cfg", "config/config.py")
    cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg)
    SENS = getattr(cfg, "SENSITIVITY", {})
except Exception:
    SENS = {}

# Defaults if config doesn't provide them
DIV_TH = float(SENS.get("DIVERGENCE_THRESHOLD", 20))
MM_CONF = float(SENS.get("MM_CONF_FOR_IDEA", 40))
EARLY_RR = float(SENS.get("EARLY_MIN_RR", 1.2))
USE_M15 = bool(SENS.get("M15_ENABLED", True))

@dataclass
class MarketState:
    symbol: str
    timestamp: float
    m15_bias: str
    h1_bias: str
    h4_bias: str
    bias_aligned: bool
    bias_strength: float
    mm_active: bool
    mm_side: str
    mm_confidence: float
    spot_pressure: float
    futures_pressure: float
    divergence: bool
    divergence_type: str
    support: float
    resistance: float
    pivot: float
    volume_profile: str
    liquidity_zones: List[float]
    entry: float
    stop_loss: float
    take_profit: List[float]
    risk_reward: float
    setup_mode: str  # "H1" | "EARLY_M15" | "NONE"

class MMDetectorWithMonitoring:
    def __init__(self):
        self.states = {}
        self.alerts = {}
        self.monitoring_active = True

    def analyze_mm_activity(self, symbol: str, spot_data: Dict, futures_data: Dict) -> MarketState:
        """Analyze market maker activity and return market state"""
        spot_pressure = self._calc_spot_pressure(spot_data['volumes'], spot_data['prices'], spot_data['trades'])
        futures_pressure = self._calc_futures_pressure(
            futures_data.get('open_interest', []),
            futures_data.get('funding_rate', 0.0),
            futures_data.get('volumes', [])
        )
        divergence, div_type = self._detect_divergence(spot_pressure, futures_pressure, spot_data['prices'])
        mm_pattern = self._identify_mm_pattern(spot_data, futures_data, divergence, div_type)

        # Biases
        m15_bias = self._bias_generic(spot_data['prices'], fast=5, slow=15, momentum_thr=0.2) if USE_M15 else "NEUTRAL"
        h1_bias = self._bias_generic(spot_data['prices'], fast=10, slow=20, momentum_thr=0.5)
        h4_bias = self._bias_generic(spot_data['prices'], fast=40, slow=80, momentum_thr=0.5)

        bias_aligned = (h1_bias == h4_bias and h1_bias != "NEUTRAL")

        # Levels
        levels = self._key_levels(spot_data['prices'], spot_data['volumes'])

        # Setup selection
        setup, mode = self._trade_setup(
            current_price=spot_data['prices'][-1],
            m15_bias=m15_bias,
            h1_bias=h1_bias,
            levels=levels,
            mm_pattern=mm_pattern
        )

        return MarketState(
            symbol=symbol,
            timestamp=time.time(),
            m15_bias=m15_bias, h1_bias=h1_bias, h4_bias=h4_bias,
            bias_aligned=bias_aligned,
            bias_strength=self._bias_strength(spot_data),
            mm_active=mm_pattern['active'], mm_side=mm_pattern['side'], mm_confidence=mm_pattern['confidence'],
            spot_pressure=spot_pressure, futures_pressure=futures_pressure,
            divergence=divergence, divergence_type=div_type,
            support=levels['support'], resistance=levels['resistance'], pivot=levels['pivot'],
            volume_profile=self._vol_profile(spot_data['volumes']),
            liquidity_zones=self._liq_zones(spot_data),
            entry=setup['entry'], stop_loss=setup['stop_loss'], take_profit=setup['take_profit'], risk_reward=setup['risk_reward'],
            setup_mode=mode
        )

    def _calc_spot_pressure(self, volumes, prices, trades):
        if len(volumes) < 10:
            return 0.0
        vwap = np.average(prices[-20:], weights=volumes[-20:])
        current = prices[-1]
        if not trades:
            return ((current - vwap) / vwap) * 100
        sz = [t['size'] for t in trades] or [1.0]
        thr = np.mean(sz) + 1.5 * np.std(sz)
        large = [t for t in trades if t['size'] > thr]
        buy_v = sum(t['size'] for t in large if t['side'] == "buy")
        sell_v = sum(t['size'] for t in large if t['side'] == "sell")
        flow = 0 if (buy_v + sell_v) == 0 else ((buy_v - sell_v) / (buy_v + sell_v)) * 100
        price = ((current - vwap) / vwap) * 100
        return flow * 0.65 + price * 0.35

    def _calc_futures_pressure(self, open_interest, funding_rate, volumes):
        if not open_interest or len(open_interest) < 2:
            oi_chg = 0.0
        else:
            base = open_interest[-2] if open_interest[-2] != 0 else 1e-9
            oi_chg = (open_interest[-1] - open_interest[-2]) / base * 100
        funding_pressure = -funding_rate * 800
        if len(volumes) > 10:
            old = max(np.mean(volumes[-10:-5]), 1e-9)
            vol_trend = (np.mean(volumes[-5:]) - old) / old * 100
        else:
            vol_trend = 0.0
        return oi_chg * 0.4 + funding_pressure * 0.35 + vol_trend * 0.25

    def _detect_divergence(self, s_press, f_press, prices):
        price_trend = (prices[-1] - prices[-10]) / prices[-10] * 100 if len(prices) > 10 else 0.0
        diff = abs(s_press - f_press)
        if diff > DIV_TH:
            if s_press > 15 and f_press < -15:
                return True, "BULLISH_DIV"
            if s_press < -15 and f_press > 15:
                return True, "BEARISH_DIV"
        if price_trend < -1.5 and s_press > 25:
            return True, "BULLISH_DIV"
        if price_trend > 1.5 and s_press < -25:
            return True, "BEARISH_DIV"
        return False, "NONE"

    def _identify_mm_pattern(self, spot_data, futures_data, divergence, div_type):
        large_orders = self._count_large(spot_data['trades'])
        absorption = self._absorption(spot_data['volumes'], spot_data['prices'])
        conf, side = 0, "NEUTRAL"
        if large_orders > 3 and absorption:
            conf += 30
            side = "ACCUMULATE" if spot_data['prices'][-1] < np.mean(spot_data['prices'][-20:]) else "DISTRIBUTE"
        if divergence:
            conf += 25
            if side == "NEUTRAL":
                side = "ACCUMULATE" if div_type == "BULLISH_DIV" else "DISTRIBUTE"
        if abs(futures_data.get('funding_rate', 0)) > 0.006:
            conf += 10
        active = conf > MM_CONF
        if not active:
            side = "NEUTRAL"
        return {"active": active, "side": side, "confidence": min(conf, 100)}

    def _bias_generic(self, prices, fast: int, slow: int, momentum_thr: float):
        if len(prices) < max(slow, fast) + 1:
            return "NEUTRAL"
        sma_f, sma_s = np.mean(prices[-fast:]), np.mean(prices[-slow:])
        mom = (prices[-1] - prices[-slow]) / prices[-slow] * 100
        if sma_f > sma_s and mom > momentum_thr:
            return "LONG"
        if sma_f < sma_s and mom < -momentum_thr:
            return "SHORT"
        return "NEUTRAL"

    def _key_levels(self, prices, volumes):
        if len(prices) < 50:
            return {'support': min(prices), 'resistance': max(prices), 'pivot': np.mean(prices)}
        lvls = np.linspace(min(prices), max(prices), 24)
        volat = []
        rng = (max(prices) - min(prices)) * 0.02
        for L in lvls:
            near = [v for p, v in zip(prices, volumes) if abs(p - L) < rng]
            volat.append(sum(near) if near else 0)
        idx = np.argsort(volat)[-3:]
        keys = sorted([lvls[i] for i in idx])
        cur = prices[-1]
        sup = max([l for l in keys if l < cur], default=min(prices))
        res = min([l for l in keys if l > cur], default=max(prices))
        return {'support': sup, 'resistance': res, 'pivot': np.mean([sup, res])}

    def _trade_setup(self, current_price, m15_bias, h1_bias, levels, mm_pattern):
        # H1-driven setup (prefer when available)
        if h1_bias == "LONG" and mm_pattern['active'] and mm_pattern['side'] in ("ACCUMULATE", "NEUTRAL"):
            entry = current_price * 0.998
            stop = levels['support'] * 0.996
            tps = [levels['pivot'], levels['resistance'] * 0.996, levels['resistance'] * 1.02]
            rr = self._rr(entry, stop, tps[1])
            return ({"entry": entry, "stop_loss": stop, "take_profit": tps, "risk_reward": rr}, "H1")
        if h1_bias == "SHORT" and mm_pattern['active'] and mm_pattern['side'] in ("DISTRIBUTE", "NEUTRAL"):
            entry = current_price * 1.002
            stop = levels['resistance'] * 1.004
            tps = [levels['pivot'], levels['support'] * 1.004, levels['support'] * 0.98]
            rr = self._rr(entry, stop, tps[1])
            return ({"entry": entry, "stop_loss": stop, "take_profit": tps, "risk_reward": rr}, "H1")

        # EARLY (M15) setup if H1 is NOT against it
        if USE_M15 and mm_pattern['active'] and h1_bias != "SHORT" and m15_bias == "LONG":
            entry = current_price * 0.999
            stop = levels['support'] * 0.996
            tps = [levels['pivot'], levels['resistance'] * 0.995, levels['resistance'] * 1.015]
            rr = self._rr(entry, stop, tps[1])
            if rr >= EARLY_RR:
                return ({"entry": entry, "stop_loss": stop, "take_profit": tps, "risk_reward": rr}, "EARLY_M15")
        if USE_M15 and mm_pattern['active'] and h1_bias != "LONG" and m15_bias == "SHORT":
            entry = current_price * 1.001
            stop = levels['resistance'] * 1.004
            tps = [levels['pivot'], levels['support'] * 1.004, levels['support'] * 0.985]
            rr = self._rr(entry, stop, tps[1])
            if rr >= EARLY_RR:
                return ({"entry": entry, "stop_loss": stop, "take_profit": tps, "risk_reward": rr}, "EARLY_M15")

        return ({"entry": 0, "stop_loss": 0, "take_profit": [0, 0, 0], "risk_reward": 0}, "NONE")

    def _rr(self, entry, stop, tp1):
        risk = abs(entry - stop)
        reward = abs(tp1 - entry)
        return reward / risk if risk > 0 else 0.0

    def _count_large(self, trades):
        if not trades:
            return 0
        sz = [t['size'] for t in trades] or [1.0]
        th = np.mean(sz) + 1.5 * np.std(sz)
        return sum(1 for t in trades if t['size'] > th)

    def _absorption(self, volumes, prices):
        if len(volumes) < 10:
            return False
        vol_spike = volumes[-1] > max(1e-9, np.mean(volumes[-10:])) * 1.8
        price_stable = abs(prices[-1] - prices[-5]) / max(1e-9, prices[-5]) < 0.0025
        return vol_spike and price_stable

    def _bias_strength(self, spot_data):
        return 50.0

    def _vol_profile(self, volumes):
        if len(volumes) < 10:
            return "UNKNOWN"
        r, o = np.mean(volumes[-5:]), np.mean(volumes[-10:-5])
        if r > o * 1.5:
            return "SPIKE"
        if r > o * 1.1:
            return "INCREASING"
        if r < o * 0.9:
            return "DECREASING"
        return "STABLE"

    def _liq_zones(self, spot_data):
        return []













































