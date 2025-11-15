# path: backend/scripts/init_db.py
import os
from pathlib import Path
from sqlalchemy import text
from app.db import engine

BASE_DIR = Path(__file__).resolve().parents[1]
schema_path = BASE_DIR / "app" / "sql" / "schema.sql"
seed_path = BASE_DIR / "app" / "sql" / "seed.sql"

def run_sql_file(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    # 以分號切開，逐段執行（簡單安全）
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))

if __name__ == "__main__":
    print(">> Creating schema ...")
    run_sql_file(schema_path)
    print(">> Seeding data ...")
    run_sql_file(seed_path)
    print(">> Done.")
