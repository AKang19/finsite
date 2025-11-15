# services/series_ops.py
from typing import Dict, Any
from sqlalchemy.engine import Engine
from .read_ops import get_close_series
from .ta import sma, macd as ta_macd, rsi, bollinger

def fetch_series(engine: Engine, ticker: str, date_from: str, date_to: str):
    return get_close_series(engine, ticker, date_from, date_to)

def build_indicators(engine: Engine, ticker: str, date_from: str, date_to: str,
                     ma_windows=None, macd_cfg=(12,26,9), rsi_period=14, bb_cfg=(20,2)) -> Dict[str, Any]:
    rows = get_close_series(engine, ticker, date_from, date_to)
    dates = [r["date"] for r in rows]
    closes = [float(r["close"]) for r in rows]
    out: Dict[str, Any] = {"dates": dates}
    if ma_windows:
        out["ma"] = {str(w): sma(closes, w) for w in ma_windows}
    if macd_cfg:
        f,s,sg = macd_cfg
        out["macd"] = ta_macd(closes, f, s, sg)
    if rsi_period:
        out["rsi"] = rsi(closes, rsi_period)
    if bb_cfg:
        w,k = bb_cfg
        out["bb"] = bollinger(closes, int(w), float(k))
    return out
