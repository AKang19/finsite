# path: backend/app/etl/parsers/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

class PriceParser(ABC):
    @abstractmethod
    def fetch_close(self, ticker: str, for_date: date) -> Optional[float]:
        """回傳指定日期的收盤價；休市/無資料時回 None。"""
        raise NotImplementedError
