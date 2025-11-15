# path: backend/app/etl/daily_price_parser.py
from __future__ import annotations
import os
from datetime import date
from typing import Optional
from app.etl.parsers.base import PriceParser
from app.etl.parsers.twse import TwseDailyParser

_DATA_SOURCE = os.getenv("PRICE_DATA_SOURCE", "twse").lower()

def _build_parser() -> PriceParser:
    if _DATA_SOURCE == "twse":
        return TwseDailyParser()
    return TwseDailyParser()

_parser: PriceParser = _build_parser()

def fetch_close_for(ticker: str, for_date: date) -> Optional[float]:
    return _parser.fetch_close(ticker, for_date)
