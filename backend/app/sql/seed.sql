-- companies
INSERT INTO companies (ticker, name, sector)
VALUES ('2330', '台積電', '半導體')
ON CONFLICT (ticker) DO NOTHING;

-- fundamentals（只插一次：DO NOTHING；若想覆寫改成 DO UPDATE）
INSERT INTO fundamentals (company_id, fiscal_year, fiscal_quarter, pe, pb)
SELECT id, 2025, 2, 25.3, 6.2
FROM companies WHERE ticker='2330'
ON CONFLICT (company_id, fiscal_year, fiscal_quarter) DO NOTHING;

-- daily_price（只插一次：DO NOTHING；若想覆寫改成 DO UPDATE）
INSERT INTO daily_price (company_id, trade_date, close)
SELECT id, CURRENT_DATE, 820
FROM companies WHERE ticker='2330'
ON CONFLICT (company_id, trade_date) DO NOTHING;