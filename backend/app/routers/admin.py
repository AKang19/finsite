# app/routers/admin.py
from __future__ import annotations
from fastapi import APIRouter, Body, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy import text
from app.db import engine
from app.services import read_ops, write_ops

router = APIRouter(prefix="/api/admin", tags=["admin"])

class CompanyIn(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None

class PriceIn(BaseModel):
    ticker: str
    trade_date: str
    close: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None

@router.get("/db/ping")
def db_ping():
    try:
        with engine.begin() as conn:
            v = conn.execute(text("SELECT 1")).scalar()
        return {"ok": True, "select1": v}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"db ping failed: {e}")

@router.post("/ensure_schema", status_code=204)
def ensure_schema():
    """
    Idempotent schema creation using plain DDL; no psycopg, no DO $$.
    Safe to call multiple times.
    """
    try:
        with engine.begin() as conn:
            # 1) companies（若你早就有，這行不會重建）
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS companies (
                    id      SERIAL PRIMARY KEY,
                    ticker  TEXT NOT NULL,
                    name    TEXT,
                    sector  TEXT
                );
            """))
            # 確保代號唯一
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS ux_companies_ticker
                ON companies(ticker);
            """))
            # 2) daily_price（OHLCV + PK）
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS daily_price (
                    company_id INTEGER NOT NULL,
                    trade_date DATE    NOT NULL,
                    open   NUMERIC(12,2),
                    high   NUMERIC(12,2),
                    low    NUMERIC(12,2),
                    close  NUMERIC(12,2),
                    volume BIGINT,
                    PRIMARY KEY (company_id, trade_date)
                );
            """))
            # 3) （可選）外鍵：若你的流量很大可先省略；要開就用這段
            conn.execute(text("""
                DO $$
                BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_type='FOREIGN KEY'
                      AND table_name='daily_price'
                      AND constraint_name='fk_daily_price_company'
                  ) THEN
                    ALTER TABLE daily_price
                      ADD CONSTRAINT fk_daily_price_company
                      FOREIGN KEY (company_id) REFERENCES companies(id)
                      ON DELETE CASCADE;
                  END IF;
                END $$;
            """))
        return
    except Exception as e:
        # 在 logs 看得到完整原因
        import logging, traceback
        logging.exception("ensure_schema failed")
        raise HTTPException(status_code=500, detail=f"ensure_schema failed: {e}")

@router.post("/prices/bulk", status_code=204)
def bulk_upsert_prices(items: List[PriceIn] = Body(...)):
    for it in items:
        # 先走 close-only；若五欄都有就改呼叫 upsert_ohlcv
        if it.close is None:
            raise HTTPException(status_code=400, detail="close is required")
        write_ops.upsert_price(engine, it.ticker, it.trade_date, float(it.close), trigger_revalidate=False)
    return

@router.post("/companies/bulk", status_code=204)
def bulk_upsert_companies(items: List[CompanyIn] = Body(...)):
    if not items:
        raise HTTPException(status_code=400, detail="no items")
    for it in items:
        write_ops.upsert_company(engine, it.ticker, it.name, it.sector)
    return
