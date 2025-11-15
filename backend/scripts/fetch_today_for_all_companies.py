# backend/scripts/fetch_today_for_all_companies.py
import datetime as dt

from sqlalchemy import text

from app.db import engine
from app.etl.parsers.twse import fetch_price_for  # 假設你原本就有這種函式

TODAY = dt.date.today()


def main():
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT ticker FROM companies")).fetchall()
        tickers = [r[0] for r in rows]

    for t in tickers:
        # 這裡要接你原本 ETL 的抓價邏輯
        # 假設會回傳 {date: ..., open: ..., high: ..., low: ..., close: ..., volume: ...}
        try:
            price = fetch_price_for(t, TODAY)
        except Exception as e:
            print(f"fetch {t} failed: {e}")
            continue

        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO daily_price (ticker, trade_date, open, high, low, close, volume)
                    VALUES (:t, :d, :o, :h, :l, :c, :v)
                    ON CONFLICT (ticker, trade_date) DO NOTHING
                    """
                ),
                {
                    "t": t,
                    "d": TODAY,
                    "o": price.open,
                    "h": price.high,
                    "l": price.low,
                    "c": price.close,
                    "v": price.volume,
                },
            )
        print(f"saved {t}")
    print("done.")
