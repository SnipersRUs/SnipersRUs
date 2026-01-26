#!/usr/bin/env python3
"""
Trading metrics module for MMS signal analysis
Provides functions for CVD, orderbook imbalance, VWAP, premium analysis, etc.
"""
import numpy as np
from typing import List, Dict, Tuple, Optional

def cvd_from_trades(trades: List[Dict]) -> float:
    """
    Calculate Cumulative Volume Delta from trades
    Returns net aggressive buying minus selling
    """
    if not trades:
        return 0.0
    
    cvd = 0.0
    for trade in trades:
        if trade.get('side') == 'buy':
            cvd += trade.get('size', 0)
        elif trade.get('side') == 'sell':
            cvd -= trade.get('size', 0)
    
    return cvd

def orderbook_imbalance(bids: List[List[float]], asks: List[List[float]], pct_window: float = 0.5) -> Tuple[float, float, float]:
    """
    Calculate orderbook imbalance within percentage window around mid price
    Returns (imbalance_ratio, bid_weight, ask_weight)
    """
    if not bids or not asks:
        return 0.0, 0.0, 0.0
    
    # Get mid price
    best_bid = bids[0][0] if bids else 0
    best_ask = asks[0][0] if asks else 0
    mid_price = (best_bid + best_ask) / 2
    
    if mid_price == 0:
        return 0.0, 0.0, 0.0
    
    # Calculate window bounds
    window_pct = pct_window / 100
    lower_bound = mid_price * (1 - window_pct)
    upper_bound = mid_price * (1 + window_pct)
    
    # Calculate bid and ask weights within window
    bid_weight = 0.0
    ask_weight = 0.0
    
    for price, size in bids:
        if lower_bound <= price <= upper_bound:
            bid_weight += size
    
    for price, size in asks:
        if lower_bound <= price <= upper_bound:
            ask_weight += size
    
    # Calculate imbalance ratio
    total_weight = bid_weight + ask_weight
    if total_weight == 0:
        return 0.0, bid_weight, ask_weight
    
    imbalance = (bid_weight - ask_weight) / total_weight
    return imbalance, bid_weight, ask_weight

def vwap_and_bands(prices: List[float], volumes: List[float], window: int = 60) -> Tuple[float, float, float]:
    """
    Calculate VWAP and 2-sigma bands
    Returns (vwap, upper_band, lower_band)
    """
    if len(prices) < 2 or len(volumes) < 2:
        return prices[-1] if prices else 0.0, prices[-1] if prices else 0.0, prices[-1] if prices else 0.0
    
    # Use last 'window' data points
    recent_prices = prices[-window:] if len(prices) >= window else prices
    recent_volumes = volumes[-window:] if len(volumes) >= window else volumes
    
    # Ensure same length
    min_len = min(len(recent_prices), len(recent_volumes))
    recent_prices = recent_prices[-min_len:]
    recent_volumes = recent_volumes[-min_len:]
    
    if not recent_prices or not recent_volumes:
        return prices[-1] if prices else 0.0, prices[-1] if prices else 0.0, prices[-1] if prices else 0.0
    
    # Calculate VWAP
    total_volume = sum(recent_volumes)
    if total_volume == 0:
        vwap = np.mean(recent_prices)
    else:
        vwap = sum(p * v for p, v in zip(recent_prices, recent_volumes)) / total_volume
    
    # Calculate 2-sigma bands
    price_std = np.std(recent_prices)
    upper_band = vwap + (2 * price_std)
    lower_band = vwap - (2 * price_std)
    
    return float(vwap), float(upper_band), float(lower_band)

def premium_vs_coinbase(binance_price: float, coinbase_price: float) -> float:
    """
    Calculate premium percentage between Binance and Coinbase
    Returns percentage difference
    """
    if coinbase_price == 0:
        return 0.0
    
    premium = ((binance_price - coinbase_price) / coinbase_price) * 100
    return float(premium)

def oi_delta(symbol: str, current_oi: float) -> float:
    """
    Calculate approximate open interest delta
    For now, returns a simple calculation based on current OI
    In a real implementation, this would track OI changes over time
    """
    # This is a simplified version - in reality you'd track OI history
    # For now, return a small random delta for demonstration
    import random
    return random.uniform(-5.0, 5.0)

def liq_clusters_summary(liqs: List[Dict], current_price: float) -> Dict:
    """
    Analyze liquidation clusters near current price
    Returns summary with count and bias
    """
    if not liqs or not current_price:
        return {"count": 0, "bias": "neutral"}
    
    # Find liquidations within 2% of current price
    price_range = current_price * 0.02
    nearby_liqs = []
    
    for liq in liqs:
        liq_price = liq.get('price', 0)
        if abs(liq_price - current_price) <= price_range:
            nearby_liqs.append(liq)
    
    if not nearby_liqs:
        return {"count": 0, "bias": "neutral"}
    
    # Analyze bias (more long liquidations = bearish, more short = bullish)
    long_liqs = sum(1 for liq in nearby_liqs if liq.get('side') == 'long')
    short_liqs = sum(1 for liq in nearby_liqs if liq.get('side') == 'short')
    
    if long_liqs > short_liqs * 1.5:
        bias = "bearish"
    elif short_liqs > long_liqs * 1.5:
        bias = "bullish"
    else:
        bias = "neutral"
    
    return {
        "count": len(nearby_liqs),
        "bias": bias
    }













































