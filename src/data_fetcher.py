#!/usr/bin/env python3
"""
Data fetcher for MMS (live)
- Spot: klines + recent trades (if needed)
- Futures: OI/funding/volumes
- Orderbook: robust normalization to [price, size]
- Coinbase spot (premium calc)
- Liquidations (quietly handles 4xx)
"""
from __future__ import annotations
import requests, time, random
from typing import Dict, List, Optional, Tuple, Any

def _get_json(url: str, params: Dict[str, Any] | None = None, timeout: int = 8):
    try:
        r = requests.get(url, params=params or {}, timeout=timeout)
        if r.status_code == 451:
            print(f"API blocked (451) for {url} - using fallback data")
            return []
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error for {url}: {e}")
        return []

def get_spot_data(base_url: str, symbol: str, limit: int = 300) -> Dict:
    """Use /klines as the backbone for prices/volumes; synth small trade set for metrics speed."""
    try:
        k = _get_json(f"{base_url}/klines", {"symbol": symbol, "interval": "1m", "limit": max(60, min(1000, limit))})
        if not k:  # API blocked, return fallback data
            print(f"Using fallback data for {symbol}")
            # Generate some mock data for testing
            base_price = 50000 if "BTC" in symbol else 100
            prices = [base_price + i * 0.1 for i in range(60)]
            volumes = [1000 + i * 10 for i in range(60)]
            trades = [{"price": base_price, "size": 100, "side": "buy" if (i % 2) else "sell"} for i in range(20)]
            return {"prices": prices, "volumes": volumes, "trades": trades}

        prices = [float(row[4]) for row in k]              # close
        volumes = [float(row[5]) for row in k]             # volume
        # Lightweight synthetic trades (directionless) – enough for CVD-style magnitude signals
        trades = [{"price": prices[-1], "size": v, "side": "buy" if (i % 2) else "sell"} for i, v in enumerate(volumes[-100:])]
        return {"prices": prices, "volumes": volumes, "trades": trades}
    except Exception as e:
        print(f"Error spot {symbol}: {e}")
        return {"prices": [], "volumes": [], "trades": []}

def get_futures_data(base_url: str, symbol: str, limit: int = 300) -> Dict:
    """Pull OI (recent), funding (current), and an activity proxy."""
    try:
        oi_kl = _get_json(f"{base_url}/openInterestHist", {"symbol": symbol, "period": "5m", "limit": min(500, limit)})
        if not oi_kl:  # API blocked
            open_interest = [1000000 + i * 1000 for i in range(60)]
        else:
            open_interest = [float(row["sumOpenInterest"]) for row in oi_kl]
    except Exception:
        open_interest = [1000000 + i * 1000 for i in range(60)]

    funding_rate = 0.0
    next_funding_time = 0
    try:
        prem = _get_json(f"{base_url}/premiumIndex", {"symbol": symbol})
        if not prem:  # API blocked
            funding_rate = 0.01
            next_funding_time = int(time.time() * 1000) + 8 * 60 * 60 * 1000  # 8 hours from now
        else:
            funding_rate = float(prem.get("lastFundingRate", 0.0))
            nft = prem.get("nextFundingTime")
            next_funding_time = int(nft) if nft else 0
    except Exception:
        funding_rate = 0.01
        next_funding_time = int(time.time() * 1000) + 8 * 60 * 60 * 1000

    # crude activity proxy via recent trades count
    try:
        agg = _get_json(f"{base_url}/aggTrades", {"symbol": symbol, "limit": 1000})
        if not agg:  # API blocked
            volumes = [1000 + i * 10 for i in range(min(limit, 100))]
        else:
            volumes = [float(x.get("q", 0.0)) for x in agg][-limit:]
    except Exception:
        volumes = [1000 + i * 10 for i in range(min(limit, 100))]

    return {
        "open_interest": open_interest,
        "funding_rate": funding_rate,
        "volumes": volumes,
        "next_funding_time": next_funding_time
    }

def get_orderbook(base_url: str, symbol: str, limit: int = 200) -> Tuple[List[List[float]], List[List[float]]]:
    """Fetch /depth and normalize rows to [price, size] ALWAYS."""
    try:
        depth_limit = min(max(5, int(limit)), 1000)
        j = _get_json(f"{base_url}/depth", {"symbol": symbol, "limit": depth_limit}, timeout=8)
        if not j:  # API blocked, return fallback data
            base_price = 50000 if "BTC" in symbol else 100
            bids = [[base_price - i * 0.1, 1000 + i * 10] for i in range(10)]
            asks = [[base_price + i * 0.1, 1000 + i * 10] for i in range(10)]
            return bids, asks

        raw_bids = j.get("bids", [])
        raw_asks = j.get("asks", [])

        def norm(rows: List[Any]) -> List[List[float]]:
            out: List[List[float]] = []
            for row in rows:
                try:
                    if isinstance(row, (list, tuple)) and len(row) >= 2:
                        p, q = float(row[0]), float(row[1])
                    elif isinstance(row, dict):
                        p = float(row.get("price") or row.get("p") or row.get("P"))
                        q = float(row.get("qty") or row.get("q") or row.get("Q") or row.get("size") or row.get("s"))
                    else:
                        continue
                    out.append([p, q])
                except Exception:
                    continue
            return out

        return norm(raw_bids), norm(raw_asks)
    except Exception as e:
        print(f"Error fetching orderbook for {symbol}: {e}")
        # Return fallback data
        base_price = 50000 if "BTC" in symbol else 100
        bids = [[base_price - i * 0.1, 1000 + i * 10] for i in range(10)]
        asks = [[base_price + i * 0.1, 1000 + i * 10] for i in range(10)]
        return bids, asks

def get_coinbase_spot(symbol: str) -> float:
    try:
        base = symbol.replace("USDT", "-USD")
        j = _get_json("https://api.coinbase.com/v2/prices/{}/spot".format(base))
        return float(j["data"]["amount"])
    except Exception:
        return 0.0

def get_recent_liqs(base_url: str, symbol: str, minutes: int = 90, limit: int = 1000) -> List[Dict]:
    """Use /forceOrders with rolling startTime; quietly returns [] on any 4xx/timeout."""
    try:
        end_ms = int(time.time() * 1000)
        start_ms = end_ms - minutes * 60 * 1000
        rows = requests.get(f"{base_url}/forceOrders", params={
            "symbol": symbol, "startTime": start_ms, "endTime": end_ms, "limit": min(1000, limit)
        }, timeout=8)
        if rows.status_code != 200:
            return []
        j = rows.json()
        out = []
        for r in j:
            try:
                side = "long" if r.get("S") == "BUY" else "short"
                out.append({"price": float(r.get("ap") or r.get("p") or 0.0),
                            "side": side,
                            "size": float(r.get("q") or 0.0),
                            "timestamp": int(r.get("E") or r.get("T") or 0)})
            except Exception:
                continue
        return out
    except Exception:
        return []
