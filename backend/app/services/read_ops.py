# path: backend/app/services/read_ops.py
from __future__ import annotations
from typing import Optional, List, Dict, Any
from sqlalchemy import text
from sqlalchemy.engine import Engine

def list_companies(engine: Engine, q: Optional[str], limit: int, offset: int) -> List[Dict[str, Any]]:
    with engine.begin() as conn:
        if q:
            rows = conn.execute(text("""
                SELECT ticker, name, sector
                FROM companies
                WHERE ticker ILIKE :kw OR name ILIKE :kw
                ORDER BY ticker ASC
                LIMIT :limit OFFSET :offset
            """), {"kw": f"%{q}%", "limit": limit, "offset": offset}).mappings().all()
        else:
            rows = conn.execute(text("""
                SELECT ticker, name, sector
                FROM companies
                ORDER BY ticker ASC
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset}).mappings().all()
    return [dict(r) for r in rows]

def last_price_date(engine: Engine, ticker: str) -> Optional[str]:
    with engine.begin() as conn:
        row = conn.execute(text("""
            SELECT dp.trade_date
            FROM companies c
            JOIN daily_price dp ON dp.company_id = c.id
            WHERE c.ticker = :t
            ORDER BY dp.trade_date DESC
            LIMIT 1
        """), {"t": ticker}).mappings().first()
    return row["trade_date"].isoformat() if row else None

def latest_price(engine: Engine, ticker: str) -> Optional[float]:
    with engine.begin() as conn:
        row = conn.execute(text("""
            SELECT dp.close
            FROM companies c
            JOIN LATERAL (
                SELECT close FROM daily_price
                WHERE company_id = c.id
                ORDER BY trade_date DESC
                LIMIT 1
            ) dp ON TRUE
            WHERE c.ticker = :t
        """), {"t": ticker}).mappings().first()
    return float(row["close"]) if row and row["close"] is not None else None

def latest_fundamental(engine: Engine, ticker: str) -> Optional[dict]:
    with engine.begin() as conn:
        row = conn.execute(text("""
            SELECT c.ticker, c.name, c.sector, f.pe, f.pb
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT pe, pb
                FROM fundamentals f
                WHERE f.company_id = c.id
                ORDER BY fiscal_year DESC, fiscal_quarter DESC
                LIMIT 1
            ) f ON TRUE
            WHERE c.ticker = :t
        """), {"t": ticker}).mappings().first()
    return dict(row) if row else None


def get_close_series(engine: Engine, ticker: str, date_from: str, date_to: str) -> List[Dict[str, Any]]:
    sql = """
        SELECT dp.trade_date::text AS date, dp.close::float AS close
        FROM daily_price dp
        JOIN companies c ON c.id = dp.company_id
        WHERE c.ticker = :t AND dp.trade_date BETWEEN :f AND :to
        ORDER BY dp.trade_date
    """
    with engine.begin() as conn:
        rows = conn.execute(text(sql), {"t": ticker, "f": date_from, "to": date_to}).mappings().all()
    return [dict(r) for r in rows]
