# path: backend/app/schemas.py
from pydantic import BaseModel

class FundamentalOut(BaseModel):
    ticker: str
    name: str
    sector: str | None = None
    pe: float | None = None
    pb: float | None = None

class PriceOut(BaseModel):
    ticker: str
    price: float
    ts: int

class CompanyOut(BaseModel):
    ticker: str
    name: str
    sector: str | None = None
