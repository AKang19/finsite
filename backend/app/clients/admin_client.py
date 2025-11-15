# backend/app/clients/admin_client.py
from __future__ import annotations
import os
from typing import List, Dict, Any, Optional
import httpx

API_BASE = os.getenv("API_BASE_FOR_ETL", os.getenv("API_BASE", "http://api:8000"))

def list_companies(limit: int = 100000) -> List[Dict[str, Any]]:
    with httpx.Client(timeout=20) as c:
        r = c.get(f"{API_BASE}/api/admin/companies", params={"limit": limit})
        r.raise_for_status()
        return r.json()

def bulk_upsert_companies(items: List[Dict[str, Any]]) -> None:
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{API_BASE}/api/admin/companies/bulk", json=items)
        r.raise_for_status()

def bulk_upsert_prices(items: List[Dict[str, Any]]) -> None:
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{API_BASE}/api/admin/prices/bulk", json=items)
        r.raise_for_status()

def ensure_schema_via_api() -> None:
    with httpx.Client(timeout=30) as c:
        r = c.post(f"{API_BASE}/api/admin/ensure_schema")
        r.raise_for_status()
