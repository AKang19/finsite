# backend/scripts/upload_companies_via_api.py
import csv, sys, os
from pathlib import Path
from app.clients import admin_client

def main(csv_path: str, batch: int = 500):
    p = Path(csv_path)
    if not p.exists():
        print(f"CSV not found: {csv_path}"); sys.exit(1)

    def norm(row):
        return {
            "ticker": (row.get("ticker") or row.get("代號") or "").strip(),
            "name": (row.get("name") or row.get("名稱") or "").strip() or None,
            "sector": (row.get("sector") or row.get("產業別") or "").strip() or None,
        }

    items = []
    with p.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            obj = norm(r)
            if obj["ticker"]:
                items.append(obj)

    i = 0
    while i < len(items):
        admin_client.bulk_upsert_companies(items[i:i+batch])
        i += batch
        print(f"uploaded {i}/{len(items)}")
    print("done.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -m scripts.upload_companies_via_api /path/to/上市公司.csv")
        sys.exit(1)
    main(sys.argv[1])
