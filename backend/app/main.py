# path: backend/app/main.py
from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from .db import engine
from .config import settings
from .schemas import CompanyOut, FundamentalOut, PriceOut
from typing import List, Optional
from app.services import read_ops, write_ops
from app.routers.admin import router as admin_router
from app.routers.public import router as public_router
import time
import logging

log = logging.getLogger("fin-api")
app = FastAPI(title="FinSite API (Stage 2)")

app.include_router(public_router)
app.include_router(admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOW_ORIGINS, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root(): return {"service": "FinSite API", "docs": "/docs", "health": "/healthz"}
@app.get("/healthz")
def healthz(): return {"ok": True}
@app.get("/health/db")
def health_db():
    from sqlalchemy import text
    with engine.connect() as conn:
        v = conn.execute(text("SELECT 1")).scalar()
    return {"db": "ok", "select1": int(v)}

# ----- Public -----
@app.get("/api/stocks/{ticker}/fundamental", response_model=FundamentalOut)
def get_fundamental(ticker: str):
    data = read_ops.latest_fundamental(engine, ticker)
    if not data: raise HTTPException(status_code=404, detail="ticker not found")
    return data

@app.get("/api/stocks/{ticker}/price", response_model=PriceOut)
def get_price(ticker: str):
    px = read_ops.latest_price(engine, ticker)
    if px is None: raise HTTPException(status_code=404, detail="price not found or NULL")
    return {"ticker": ticker, "price": float(px), "ts": int(time.time()*1000)}

# ----- Admin -----
@app.get("/api/admin/companies", response_model=List[CompanyOut])
def list_companies(q: Optional[str] = None, limit: int = 1000, offset: int = 0):
    return read_ops.list_companies(engine, q, limit, offset)

@app.get("/api/admin/stocks/{ticker}/last_price_date")
def api_last_price_date(ticker: str):
    s = read_ops.last_price_date(engine, ticker)
    return {"ticker": ticker, "last_trade_date": s}

@app.post("/api/admin/companies", response_model=CompanyOut, status_code=201)
def create_company(
    ticker: str = Body(..., embed=True),
    name: Optional[str] = Body(None),
    sector: Optional[str] = Body(None),
):
    write_ops.ensure_company(engine, ticker, name, sector)
    arr = read_ops.list_companies(engine, q=ticker, limit=1, offset=0)
    if not arr: raise HTTPException(status_code=500, detail="failed to create company")
    return arr[0]

@app.delete("/api/admin/companies/{ticker}", status_code=204)
def delete_company(ticker: str):
    if not write_ops.delete_company_cascade(engine, ticker):
        raise HTTPException(status_code=404, detail="not found")
    return

@app.delete("/api/admin/prices", status_code=204)
def delete_prices(
    start: str = Query(..., description="YYYY-MM-DD inclusive"),
    end: str = Query(..., description="YYYY-MM-DD inclusive"),
    tickers: Optional[str] = Query(None, description="comma-separated tickers"),
):
    write_ops.delete_prices_range(engine, start, end, tickers.split(",") if tickers else None)
    return
