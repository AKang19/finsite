#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backfill missing daily prices with robust TWSE fetch:
- Use an anchor date within the month (<= today) instead of month-end
- Add User-Agent to avoid sporadic blocks
- Fallback to legacy /exchangeReport endpoint when RWD is empty/fails
- Parse ROC date (e.g., '114/10/15') to Gregorian
- Upsert OHLCV (if any field missing, fall back to close/0)
Environment:
  BACKFILL_LOOKBACK_DAYS (default: 7)
  DATABASE_URL (e.g. postgresql+psycopg2://fin:finpass@postgres:5432/fin)
"""

import os
import sys
import json
import math
import time
import calendar
import datetime as dt
import urllib.request
import psycopg2


# ------------------------- HTTP & TWSE helpers -------------------------

def _http_get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_month_data(stock_no: str, anchor_date: dt.date) -> dict:
    """
    Return a TWSE month payload by using an anchor date within the same month
    (and no later than today). RWD first, fallback to legacy.
    """
    today = dt.date.today()
    if anchor_date > today:
        anchor_date = today
    yyyymmdd = anchor_date.strftime("%Y%m%d")

    # Try RWD first
    u1 = (
        "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY"
        f"?date={yyyymmdd}&stockNo={stock_no}&response=json"
    )
    try:
        j = _http_get(u1)
        if j.get("data"):
            return j
    except Exception:
        pass

    # Fallback: legacy endpoint
    u2 = (
        "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
        f"?response=json&date={yyyymmdd}&stockNo={stock_no}"
    )
    return _http_get(u2)


def _to_decimal(s: str):
    """ Parse TWSE number string with commas; return float or None """
    if s is None:
        return None
    s = s.strip().replace(",", "")
    if s in {"", "-", "—"}:
        return None
    try:
        return float(s)
    except Exception:
        return None


def _to_int(s: str):
    """ Parse TWSE volume as int; return int or 0 """
    v = _to_decimal(s)
    if v is None or math.isnan(v):
        return 0
    return int(v)


def _roc_to_gregorian(dstr: str) -> dt.date:
    """
    TWSE date format: '114/10/15' -> 2025-10-15
    """
    roc, m, d = dstr.split("/")
    y = int(roc) + 1911
    return dt.date(y, int(m), int(d))


def parse_twse_rows_to_map(payload: dict) -> dict:
    """
    Convert TWSE monthly payload to {date: {open, high, low, close, volume}}
    - fields order by spec: 日期, 成交股數, 成交金額, 開盤價, 最高價, 最低價, 收盤價, 漲跌價差, 成交筆數
    """
    rows = payload.get("data", []) or []
    m = {}
    for r in rows:
        try:
            d = _roc_to_gregorian(r[0])
        except Exception:
            continue
        vol = _to_int(r[1])
        o = _to_decimal(r[3])
        h = _to_decimal(r[4])
        l = _to_decimal(r[5])
        c = _to_decimal(r[6])
        # 某些欄位可能為 None，至少確保 close 存在
        if c is None and o is None and h is None and l is None:
            # 無法使用
            continue
        if o is None:
            o = c
        if h is None:
            h = c
        if l is None:
            l = c
        if c is None:
            # 少數極端情況，全部缺，跳過
            continue
        m[d] = dict(open=o, high=h, low=l, close=c, volume=vol)
    return m


# ------------------------- DB helpers -------------------------

def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("[FATAL] DATABASE_URL not set", file=sys.stderr)
        sys.exit(2)
    # psycopg2 does not accept '+psycopg2' in scheme, remove it if present
    return url.replace("+psycopg2", "")


def _conn():
    return psycopg2.connect(_db_url())


def get_all_tickers(cur) -> list[str]:
    cur.execute("SELECT ticker FROM companies ORDER BY ticker")
    return [t for (t,) in cur.fetchall()]


def upsert_company(cur, ticker: str, name: str | None = None):
    cur.execute(
        """
        INSERT INTO companies (ticker, name)
        VALUES (%s, %s)
        ON CONFLICT (ticker) DO NOTHING
        """,
        (ticker, name or ticker),
    )


def existing_trade_dates(cur, ticker: str, start_date: dt.date, end_date: dt.date) -> set[dt.date]:
    cur.execute(
        """
        SELECT dp.trade_date
        FROM daily_price dp
        JOIN companies c ON c.id = dp.company_id
        WHERE c.ticker = %s AND dp.trade_date BETWEEN %s AND %s
        """,
        (ticker, start_date, end_date),
    )
    return {r[0] for r in cur.fetchall()}


def upsert_price(cur, ticker: str, d: dt.date, o: float, h: float, l: float, c: float, v: int):
    cur.execute(
        """
        INSERT INTO daily_price (company_id, trade_date, open, high, low, close, volume)
        SELECT id, %s, %s, %s, %s, %s, %s
        FROM companies WHERE ticker = %s
        ON CONFLICT (company_id, trade_date) DO UPDATE
        SET open = EXCLUDED.open,
            high = EXCLUDED.high,
            low  = EXCLUDED.low,
            close= EXCLUDED.close,
            volume=EXCLUDED.volume
        """,
        (d, o, h, l, c, v, ticker),
    )


# ------------------------- Main backfill -------------------------

def daterange_weekdays(start: dt.date, end: dt.date):
    cur = start
    while cur <= end:
        if cur.weekday() < 5:  # Mon-Fri
            yield cur
        cur += dt.timedelta(days=1)


def main():
    lookback_days = int(os.environ.get("BACKFILL_LOOKBACK_DAYS", "7"))
    today = dt.date.today()
    start = today - dt.timedelta(days=lookback_days)
    end = today

    print(f"[backfill] window {start} ~ {end} (weekdays only)")

    conn = _conn()
    conn.autocommit = True
    cur = conn.cursor()

    tickers = get_all_tickers(cur)
    print(f"[backfill] total symbols = {len(tickers)}")

    filled_total = 0
    skipped_total = 0

    for ticker in tickers:
        # 確保公司存在
        upsert_company(cur, ticker)

        # 找此視窗內已存在的交易日
        exist = existing_trade_dates(cur, ticker, start, end)
        missing = [d for d in daterange_weekdays(start, end) if d not in exist]
        if not missing:
            print(f"[{ticker}] no missing dates in window")
            continue

        print(f"[{ticker}] missing {len(missing)} days -> " + ", ".join(str(d) for d in missing))

        # 依月份分組，避免同月份打多次 API
        by_month: dict[tuple[int, int], list[dt.date]] = {}
        for d in missing:
            by_month.setdefault((d.year, d.month), []).append(d)

        month_cache: dict[tuple[int, int], dict[dt.date, dict]] = {}
        for (y, m), days in sorted(by_month.items()):
            # anchor 選該月內且不超過今天的某一天（用 min(月最後一天, 今天) 也可）
            anchor = min(dt.date(y, m, max(1, min(days).day)), today)
            try:
                payload = fetch_month_data(ticker, anchor)
                mp = parse_twse_rows_to_map(payload)
            except Exception as e:
                print(f"  ! {y}-{m:02d} fetch error: {e!r}")
                mp = {}
            month_cache[(y, m)] = mp

        # 寫入
        filled = 0
        skipped = 0
        for d in missing:
            mp = month_cache.get((d.year, d.month), {})
            row = mp.get(d)
            if not row:
                print(f"  - {d} upstream no data (holiday/未上市/休市?) -> skip")
                skipped += 1
                continue
            o, h, l, c, v = row["open"], row["high"], row["low"], row["close"], row["volume"]
            try:
                upsert_price(cur, ticker, d, o, h, l, c, v)
                print(f"  + {d} close={c}")
                filled += 1
            except Exception as e:
                print(f"  ! {d} error: {e}")
        filled_total += filled
        skipped_total += skipped

    cur.close()
    conn.close()

    print(f"[backfill all done] filled={filled_total}, skipped={skipped_total}")


if __name__ == "__main__":
    main()
