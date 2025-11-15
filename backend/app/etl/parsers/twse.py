# path: backend/app/etl/parsers/twse.py
from __future__ import annotations
from datetime import date
from typing import Optional
import httpx

class TwseDailyParser:
    BASE_URL = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"

    def __init__(self, timeout_sec: float = 8.0, retries: int = 2):
        self.timeout_sec = timeout_sec
        self.retries = retries

    @staticmethod
    def _yyyymmdd(d: date) -> str:
        return f"{d.year:04d}{d.month:02d}{d.day:02d}"

    @staticmethod
    def _roc_to_gregorian(roc: str) -> date:
        # 例如 "114/09/02" → 2025-09-02
        y, m, d = roc.split("/")
        year = int(y) + 1911
        return date(year, int(m), int(d))

    @staticmethod
    def _to_float(x: str) -> Optional[float]:
        try:
            x = x.replace(",", "").strip()
            if x in ("", "--"):
                return None
            return float(x)
        except Exception:
            return None

    def fetch_close(self, ticker: str, for_date: date) -> Optional[float]:
        params = {"response": "json", "stockNo": ticker, "date": self._yyyymmdd(for_date)}
        headers = {
            "User-Agent": "FinSiteETL/1.0",
            "Accept": "application/json",
        }
        last_exc = None
        for _ in range(self.retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_sec, headers=headers) as client:
                    r = client.get(self.BASE_URL, params=params)
                    r.raise_for_status()
                    j = r.json()
                    data = j.get("data") or []
                    for row in data:
                        if not row or len(row) < 6:
                            continue
                        roc_date = row[0]
                        close_str = row[5]  # 第 6 欄為收盤價（1-based）
                        g_date = self._roc_to_gregorian(roc_date)
                        if g_date == for_date:
                            return self._to_float(close_str)
                    return None
            except Exception as e:
                last_exc = e
                continue
        return None
