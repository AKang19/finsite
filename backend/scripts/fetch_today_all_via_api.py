# path: backend/scripts/fetch_today_all_via_api.py
import os
import sys
from pathlib import Path
from datetime import date
from typing import List
import httpx

# 讓 "from app...." 可以 import 到
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db import engine  # noqa: E402
from app.services.write_ops import upsert_price  # noqa: E402
from app.etl.daily_price_parser import fetch_close_for  # noqa: E402

API_BASE = os.getenv("API_BASE", "http://api:8000")
TICKER_FILTER = os.getenv("TICKER_FILTER")  # 例如 "2330,2317" 限縮測試用

def get_all_tickers() -> List[str]:
    url = f"{API_BASE}/api/admin/companies"
    out: List[str] = []
    limit, offset = 1000, 0
    with httpx.Client(timeout=10.0) as client:
      while True:
        r = client.get(url, params={"limit": limit, "offset": offset})
        r.raise_for_status()
        arr = r.json()
        if not arr:
            break
        out.extend([x["ticker"] for x in arr])
        if len(arr) < limit:
            break
        offset += limit
    if TICKER_FILTER:
        allow = {t.strip() for t in TICKER_FILTER.split(",") if t.strip()}
        out = [t for t in out if t in allow]
    return sorted(set(out))

if __name__ == "__main__":
    today = date.today()
    tickers = get_all_tickers()
    print(f"[daily-all] {len(tickers)} symbols")

    filled, skipped = 0, 0
    for t in tickers:
        px = fetch_close_for(t, today)
        if px is None:
            skipped += 1
            print(f"[skip] {t} {today} no data (holiday/closed)")
            continue
        upsert_price(engine, t, today.isoformat(), float(px), trigger_revalidate=False)
        filled += 1
        print(f"[ok] {t} {today} close={px}")

    print(f"[daily-all done] filled={filled}, skipped={skipped}")
