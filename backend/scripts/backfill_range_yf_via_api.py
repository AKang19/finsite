#!/usr/bin/env python
import argparse, os, sys, json, time
import datetime as dt
import urllib.request

import yfinance as yf

def http_get(url: str):
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.status, resp.read().decode("utf-8","ignore")

def post_json(url: str, obj):
    data = json.dumps(obj).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.status, resp.read().decode("utf-8","ignore")

def fetch_companies(api_base: str, limit: int=100000):
    status, body = http_get(f"{api_base}/api/admin/companies?limit={limit}")
    if status != 200:
        raise RuntimeError(f"companies list failed: {status} {body[:200]}")
    return json.loads(body)

def to_iso(d: dt.date) -> str:
    return d.strftime("%Y-%m-%d")

def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-base", default=os.environ.get("API_BASE","http://localhost:8000"))
    ap.add_argument("--from", dest="date_from", required=True, help="YYYY-MM-DD")
    ap.add_argument("--to", dest="date_to", required=True, help="YYYY-MM-DD")
    ap.add_argument("--limit", type=int, default=100000, help="最多處理幾檔")
    ap.add_argument("--batch", type=int, default=500, help="每批上傳幾筆日K")
    ap.add_argument("--ticker-prefix", default="", help="只處理以該字首開頭的代碼（選用）")
    args = ap.parse_args()

    api = args.api_base.rstrip("/")
    comps = fetch_companies(api, args.limit)
    tickers = [c["ticker"] for c in comps if c.get("ticker","").startswith(args.ticker_prefix)]
    print(f"[info] companies: {len(tickers)}")

    # yfinance 代碼轉換（台股常見: 2330.TW）
    def to_yf(t: str) -> str:
        return t if any(ch.isalpha() for ch in t) else f"{t}.TW"

    url_bulk = f"{api}/api/admin/prices/bulk"
    date_from = args.date_from
    date_to = args.date_to

    for idx, t in enumerate(tickers, 1):
        yf_t = to_yf(t)
        try:
            df = yf.download(yf_t, start=date_from, end=(dt.date.fromisoformat(date_to) + dt.timedelta(days=1)).isoformat(), progress=False, interval="1d", auto_adjust=False)
            if df is None or df.empty:
                print(f"[warn] no data for {t} ({yf_t})"); continue
            df = df.reset_index()  # Date, Open, High, Low, Close, Adj Close, Volume
            # 組成 /prices/bulk 的 payload
            arr=[]
            for _, row in df.iterrows():
                d = row["Date"]
                trade_date = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10]
                arr.append({
                    "ticker": t,
                    "trade_date": trade_date,
                    "open": float(row["Open"]) if row["Open"]==row["Open"] else None,
                    "high": float(row["High"]) if row["High"]==row["High"] else None,
                    "low":  float(row["Low"])  if row["Low"]==row["Low"] else None,
                    "close":float(row["Close"])if row["Close"]==row["Close"] else None,
                    "volume": int(row["Volume"]) if row["Volume"]==row["Volume"] else None,
                })

            for chunk in chunked(arr, args.batch):
                status, body = post_json(url_bulk, chunk)
                if status >= 300:
                    print(f"[error] bulk {t} -> {status} {body[:200]}")
                    sys.exit(1)
                time.sleep(0.2)
            print(f"[ok] {idx:>5}/{len(tickers)} {t} ({len(arr)} rows)")
        except Exception as e:
            print(f"[err] {idx:>5}/{len(tickers)} {t}: {e}")

if __name__ == "__main__":
    main()
