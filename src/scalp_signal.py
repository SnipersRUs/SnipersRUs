#!/usr/bin/env python3
"""
Scalp signal module for MMS trading system
Provides scalp setup analysis and probability scoring
"""
import numpy as np
from typing import Dict, Optional

def _score_prob(aligned: bool, cvd: float, ob_imb: float, funding_tilt: str, oi_delta: float, vwap_loc: str) -> float:
    """
    Score probability for scalp setup based on multiple factors
    Returns probability score 1-99
    """
    # Base probability
    prob = 40.0 if aligned else 25.0
    
    # CVD in signal direction (+buy, -sell)
    prob += min(abs(cvd) / 1e6, 20)  # Scale big numbers down
    
    # Orderbook imbalance help
    prob += max(min(abs(ob_imb) * 40, 15), 0)
    
    # Funding tilt analysis
    if funding_tilt in ("slight BULL tilt", "BULL tilt (crowded shorts)"):
        prob += 5
    if funding_tilt in ("slight BEAR tilt", "BEAR tilt (crowded longs)"):
        prob -= 5
    
    # Open interest participation
    prob += max(min(abs(oi_delta), 10), -10)
    
    # VWAP location: value entries favored
    if "value" in vwap_loc:
        prob += 5
    
    return float(max(1, min(99, round(prob))))

def scalp_setup(signal_side: str, price: float, support: float, resistance: float, vwap: float, v_up: float, v_dn: float) -> Dict:
    """
    Return a tight pullback scalp idea dict with: entry, stop, tp1, tp2, side, prob, note.
    """
    if signal_side not in ("LONG", "SHORT"):
        return {"available": False}

    if signal_side == "LONG":
        entry = max(support, v_dn) * 1.001   # Buy near value
        stop = min(support, v_dn) * 0.997
        tp1 = vwap
        tp2 = min(resistance, v_up) * 0.998
        note = "Look for buy-the-dip near VWAP- / support; bounce to VWAP/upper band."
    else:
        entry = min(resistance, v_up) * 0.999  # Sell near premium
        stop = max(resistance, v_up) * 1.003
        tp1 = vwap
        tp2 = max(support, v_dn) * 1.002
        note = "Look for sell-the-pop near VWAP+ / resistance; fade back to VWAP/lower band."

    # Sanity check
    if any(x <= 0 for x in (entry, stop, tp1, tp2)):
        return {"available": False}

    rr = abs(tp1 - entry) / max(abs(entry - stop), 1e-9)
    return {
        "available": True,
        "side": signal_side,
        "entry": float(entry),
        "stop": float(stop),
        "tp1": float(tp1),
        "tp2": float(tp2),
        "rr": float(round(rr, 2)),
        "note": note
    }

def attach_probability(idea: Dict, prob: float) -> Dict:
    """
    Attach probability score to scalp idea
    """
    if not idea.get("available"):
        return idea
    
    idea = idea.copy()
    idea["prob"] = prob
    return idea













































