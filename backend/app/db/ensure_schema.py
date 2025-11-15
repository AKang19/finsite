# path: app/db/ensure_schema.py
from contextlib import contextmanager
import os
import psycopg2

def _get_db_conn():
    # 從 DATABASE_URL 讀取連線字串，例如：
    # postgresql+psycopg2://fin:finpass@postgres:5432/fin
    # psycopg2 不吃 "+psycopg2"，這裡做轉換
    url = os.environ.get("DATABASE_URL", "")
    if "+psycopg2" in url:
        url = url.replace("+psycopg2", "")
    return psycopg2.connect(url)

@contextmanager
def _cursor():
    conn = _get_db_conn()
    try:
        with conn, conn.cursor() as cur:
            yield cur
    finally:
        conn.close()

def ensure_schema():
    """確保 daily_price 具備 open/high/low/close/volume 與唯一索引。
       可重複執行、安全無副作用。"""
    with _cursor() as cur:
        # 確保表存在（如果你的專案一定有 migration 建表，可移除這段）
        cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_price (
            company_id   INTEGER NOT NULL,
            trade_date   DATE    NOT NULL,
            close        NUMERIC(12,2),
            PRIMARY KEY (company_id, trade_date)
        );
        """)

        # 補欄位（若存在則跳過）
        cur.execute("""
        ALTER TABLE daily_price
          ADD COLUMN IF NOT EXISTS open   NUMERIC(12,2),
          ADD COLUMN IF NOT EXISTS high   NUMERIC(12,2),
          ADD COLUMN IF NOT EXISTS low    NUMERIC(12,2),
          ADD COLUMN IF NOT EXISTS volume BIGINT;
        """)

        # 確保唯一索引（有主鍵就已涵蓋；若你用 UNIQUE INDEX 也可保留）
        cur.execute("""
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE schemaname = 'public'
              AND indexname = 'ux_daily_price_company_date'
          ) THEN
            CREATE UNIQUE INDEX ux_daily_price_company_date
              ON daily_price (company_id, trade_date);
          END IF;
        END $$;
        """)

        # 你要的其他結構也可在這裡補
