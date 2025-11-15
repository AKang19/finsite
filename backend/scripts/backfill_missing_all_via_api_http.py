# backend/scripts/backfill_missing_all_via_api_http.py
import os
from datetime import date, timedelta
from app.clients import admin_client
from app.etl.daily_price_parser import fetch_close_for

LOOKBACK = int(os.getenv("BACKFILL_LOOKBACK_DAYS", "7"))

def daterange(d1: date, d2: date):
    cur = d1
    while cur <= d2:
        yield cur
        cur += timedelta(days=1)

def main():
    end = date.today()
    start = end - timedelta(days=LOOKBACK)
    companies = admin_client.list_companies(limit=100000)
    tickers = [c["ticker"] for c in companies]
    for t in tickers:
        batch = []
        for d in daterange(start, end):
            px = fetch_close_for(t, d)
            if px is None: continue
            batch.append({"ticker": t, "trade_date": d.isoformat(), "close": float(px)})
            if len(batch) >= 1000:
                admin_client.bulk_upsert_prices(batch); batch.clear()
        if batch: admin_client.bulk_upsert_prices(batch)
        print(f"[ok] {t}")
    print("done.")

if __name__ == "__main__":
    main()
