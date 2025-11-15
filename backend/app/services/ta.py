# backend/app/services/ta.py
from __future__ import annotations
from typing import List, Optional, Dict, Any
import math

def sma(values: List[float], window: int) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    s = 0.0
    q: List[float] = []
    for v in values:
        q.append(v); s += v
        if len(q) < window:
            out.append(None)
        else:
            if len(q) > window:
                s -= q.pop(0)
            out.append(s / window)
    return out

def ema(values: List[float], span: int) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    k = 2 / (span + 1)
    prev: Optional[float] = None
    for v in values:
        prev = v if prev is None else (v * k + prev * (1 - k))
        out.append(prev)
    return out

def macd(values: List[float], fast: int=12, slow: int=26, signal: int=9):
    ef = ema(values, fast)
    es = ema(values, slow)
    dif: List[Optional[float]] = []
    for a, b in zip(ef, es):
        dif.append(None if a is None or b is None else a - b)
    sig = ema([x if x is not None else 0.0 for x in dif], signal)
    hist: List[Optional[float]] = []
    for d, s in zip(dif, sig):
        hist.append(None if d is None or s is None else d - s)
    return {"dif": dif, "signal": sig, "hist": hist}

def rsi(values: List[float], period: int=14) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    gains: List[float] = []
    losses: List[float] = []
    prev = None
    for i, v in enumerate(values):
        if prev is None:
            out.append(None); prev = v; continue
        ch = v - prev; prev = v
        gains.append(max(ch, 0.0)); losses.append(max(-ch, 0.0))
        if i < period:
            out.append(None); continue
        ag = sum(gains[-period:]) / period
        al = sum(losses[-period:]) / period
        out.append(100.0 if al == 0 else (100 - (100 / (1 + ag / al))))
    return out

def bollinger(values: List[float], window: int=20, k: float=2.0):
    mid = sma(values, window)
    up: List[Optional[float]] = []; lo: List[Optional[float]] = []
    for i in range(len(values)):
        if i + 1 < window:
            up.append(None); lo.append(None); continue
        seg = values[i-window+1:i+1]
        m = mid[i]; 
        if m is None: up.append(None); lo.append(None); continue
        var = sum((x - m) ** 2 for x in seg) / window
        sd = math.sqrt(var)
        up.append(m + k * sd); lo.append(m - k * sd)
    return {"mid": mid, "upper": up, "lower": lo}
