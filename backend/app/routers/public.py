# backend/app/routers/public.py
from __future__ import annotations
from fastapi import APIRouter, Query
from app.db import engine

router = APIRouter(prefix="/api", tags=["public"])

from app.services.series_ops import fetch_series, build_indicators
from app.db import engine

@router.get("/stocks/{ticker}/series")
def get_series(ticker: str, date_from: str = Query(..., alias="from"), date_to: str = Query(..., alias="to")):
    return fetch_series(engine, ticker, date_from, date_to)

@router.get("/stocks/{ticker}/indicators")
def get_indicators(ticker: str, date_from: str = Query(..., alias="from"), date_to: str = Query(..., alias="to"),
                   ma: str | None = "5,20,60", macd: str = "12,26,9", rsiperiod: int = 14, bb: str | None = "20,2"):
    ma_windows = [int(x) for x in ma.split(",")] if ma else None
    macd_cfg = tuple(int(x) for x in macd.split(",")) if macd else None
    bb_cfg = tuple(float(x) for x in bb.split(",")) if bb else None
    return build_indicators(engine, ticker, date_from, date_to, ma_windows, macd_cfg, rsiperiod, bb_cfg)
