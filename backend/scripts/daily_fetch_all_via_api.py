# backend/scripts/daily_fetch_all_via_api.py
import sys
from datetime import date
from app.clients import admin_client
from app.etl.daily_price_parser import fetch_close_for

def main():
    today = date.today()
    companies = admin_client.list_companies(limit=100000)
    tickers = [c["ticker"] for c in companies]
    print(f"[daily] {len(tickers)} symbols")

    batch = []
    for t in tickers:
        px = fetch_close_for(t, today)
        if px is None:
            print(f"[skip] {t} {today} no data"); continue
        batch.append({"ticker": t, "trade_date": today.isoformat(), "close": float(px)})
        if len(batch) >= 1000:
            admin_client.bulk_upsert_prices(batch); batch.clear(); print("...bulk committed")
    if batch: admin_client.bulk_upsert_prices(batch)
    print("done.")

if __name__ == "__main__":
    main()
