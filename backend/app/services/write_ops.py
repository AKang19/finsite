# path: backend/app/services/write_ops.py
from __future__ import annotations
from typing import Optional, Iterable
from sqlalchemy import text
from sqlalchemy.engine import Engine

def ensure_company(engine: Engine, ticker: str, name: Optional[str] = None, sector: Optional[str] = None) -> int:
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO companies (ticker, name, sector)
            VALUES (:t, COALESCE(:n,:t), :s)
            ON CONFLICT (ticker) DO NOTHING
        """), {"t": ticker, "n": name, "s": sector})
        cid = conn.execute(text("SELECT id FROM companies WHERE ticker=:t"), {"t": ticker}).scalar()
    return int(cid)

def upsert_price(engine: Engine, ticker: str, trade_date: str, close: float, trigger_revalidate: bool = False) -> None:
    with engine.begin() as conn:
        cid = ensure_company(engine, ticker)
        conn.execute(text("""
            INSERT INTO daily_price (company_id, trade_date, close)
            VALUES (:cid, :d, :px)
            ON CONFLICT (company_id, trade_date)
            DO UPDATE SET close = EXCLUDED.close, created_at = now()
        """), {"cid": cid, "d": trade_date, "px": float(close)})

def delete_prices_range(engine: Engine, start: str, end: str, tickers: Optional[Iterable[str]] = None) -> None:
    with engine.begin() as conn:
        if tickers:
            conn.execute(text("""
                DELETE FROM daily_price dp
                USING companies c
                WHERE dp.company_id=c.id
                  AND dp.trade_date BETWEEN :s AND :e
                  AND c.ticker = ANY(:ts)
            """), {"s": start, "e": end, "ts": list(tickers)})
        else:
            conn.execute(text("""
                DELETE FROM daily_price dp
                USING companies c
                WHERE dp.company_id=c.id
                  AND dp.trade_date BETWEEN :s AND :e
            """), {"s": start, "e": end})

def delete_company_cascade(engine: Engine, ticker: str) -> bool:
    with engine.begin() as conn:
        cid = conn.execute(text("SELECT id FROM companies WHERE ticker=:t"), {"t": ticker}).scalar()
        if not cid:
            return False
        conn.execute(text("DELETE FROM daily_price WHERE company_id=:cid"), {"cid": cid})
        conn.execute(text("DELETE FROM fundamentals WHERE company_id=:cid"), {"cid": cid})
        conn.execute(text("DELETE FROM companies WHERE id=:cid"), {"cid": cid})
    return True

def upsert_company(engine: Engine, ticker: str, name: str | None, sector: str | None):
    sql = """
    INSERT INTO companies (ticker, name, sector)
    VALUES (:t, :n, :s)
    ON CONFLICT (ticker) DO UPDATE
      SET name = COALESCE(EXCLUDED.name, companies.name),
          sector = COALESCE(EXCLUDED.sector, companies.sector)
    """
    with engine.begin() as conn:
        conn.execute(text(sql), {"t": ticker, "n": name, "s": sector})
