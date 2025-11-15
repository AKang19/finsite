-- path: backend/app/sql/schema.sql
CREATE TABLE IF NOT EXISTS companies (
  id SERIAL PRIMARY KEY,
  ticker TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  sector TEXT
);

CREATE TABLE IF NOT EXISTS fundamentals (
  id SERIAL PRIMARY KEY,
  company_id INT REFERENCES companies(id),
  fiscal_year INT NOT NULL,
  fiscal_quarter INT NOT NULL,
  pe NUMERIC,
  pb NUMERIC,
  created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS fundamentals_company_idx
  ON fundamentals (company_id, fiscal_year DESC, fiscal_quarter DESC);

CREATE TABLE IF NOT EXISTS daily_price (
  id SERIAL PRIMARY KEY,
  company_id INT REFERENCES companies(id),
  trade_date DATE NOT NULL,
  close NUMERIC, -- 若你不希望 NULL，改成 close NUMERIC NOT NULL
  created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS daily_price_company_idx
  ON daily_price (company_id, trade_date DESC);
CREATE UNIQUE INDEX IF NOT EXISTS daily_price_uniq
  ON daily_price (company_id, trade_date);
