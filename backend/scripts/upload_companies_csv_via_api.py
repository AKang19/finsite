# /app/scripts/upload_companies_csv_via_api.py
#!/usr/bin/env python
import argparse, csv, json, os, sys, time, io, re
import urllib.request

ALIASES = {
    "ticker": ["ticker","Ticker","證券代號","代號","股票代碼","stock_id","code","有價證券代號及名稱","證券代號及名稱"],
    "name":   ["name","Name","公司簡稱","公司名稱","公司名","short_name","fullname"],
    "sector": ["sector","Sector","產業別","產業","industry","category"],
}

API_TIMEOUT = 60

def post_json(url: str, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
        return resp.status, resp.read().decode("utf-8","ignore")

def _norm_key(header, want, override=None):
    if override:
        for h in header:
            if h.strip() == override.strip():
                return h
        return None
    lower = {h.lower(): h for h in header}
    for cand in ALIASES[want]:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None

def _decode_bytes(raw: bytes) -> str:
    for enc in ("utf-8-sig","utf-8","cp950","big5"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise UnicodeError("Unknown CSV encoding; save as UTF-8 please.")

def _split_code_name(val: str):
    # 支援半形/全形空白；也容忍前置/後置空白
    if not val: return None, None
    s = str(val).strip().replace("\u3000"," ")
    # 典型格式：「1101 台泥」→ code=1101, name=台泥
    m = re.match(r"^\s*([0-9A-Za-z]+)\s+(.*)$", s)
    if m:
        code, name = m.group(1).strip(), m.group(2).strip()
        return code, name or None
    # 萬一沒有空白，就當成整欄是代號
    return s, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-base", default=os.environ.get("API_BASE","http://localhost:8000"))
    ap.add_argument("--csv", required=True)
    ap.add_argument("--batch", type=int, default=1000)
    # 可手動指定欄位名稱（選填）
    ap.add_argument("--ticker-col")
    ap.add_argument("--name-col")
    ap.add_argument("--sector-col")
    args = ap.parse_args()

    raw = open(args.csv, "rb").read()
    text = _decode_bytes(raw)
    f = io.StringIO(text)
    r = csv.DictReader(f)
    header = r.fieldnames or []
    if not header:
        print("CSV has no header.", file=sys.stderr); sys.exit(2)

    tcol = _norm_key(header, "ticker", args.ticker_col)
    ncol = _norm_key(header, "name",   args.name_col)
    scol = _norm_key(header, "sector", args.sector_col)

    if not tcol:
        print(f"Cannot find ticker column. Header={header}", file=sys.stderr)
        sys.exit(2)

    rows=[]
    for row in r:
        raw_ticker = (row.get(tcol) or "").strip()
        if not raw_ticker:
            continue

        # 如果 ticker 欄其實是「代號+名稱」混合欄（像「1101 台泥」）
        if tcol in ("有價證券代號及名稱","證券代號及名稱") or (ncol is None and " " in raw_ticker):
            code, name_in = _split_code_name(raw_ticker)
            ticker = code
            name = name_in
        else:
            ticker = raw_ticker
            name = (row.get(ncol).strip() if ncol and row.get(ncol) else None)

        sector = (row.get(scol).strip() if scol and row.get(scol) else None)

        if ticker:
            rows.append({"ticker": ticker, "name": name, "sector": sector})

    print(f"[info] parsed rows: {len(rows)} (ticker-col={tcol}, name-col={ncol}, sector-col={scol})")
    if not rows:
        print("No rows to upload. Abort.", file=sys.stderr); sys.exit(1)

    url = f"{args.api_base.rstrip('/')}/api/admin/companies/bulk"
    for i in range(0, len(rows), args.batch):
        chunk = rows[i:i+args.batch]
        st, body = post_json(url, chunk)
        print(f"[{i:>6}/{len(rows)}] -> {st}")
        if st >= 300:
            print(body); sys.exit(1)
        time.sleep(0.2)

if __name__ == "__main__":
    main()
