# FinSite

FinSite is a small full-stack playground for **Taiwan stock research**：  
collecting TWSE/TPEx data, storing it in PostgreSQL, exposing a FastAPI backend,  
and rendering basic views with a Next.js frontend.

---

## Features

- 🧮 **Fundamental & price API** with FastAPI
- 📈 **Daily price & backfill scripts** for TWSE/TPEx CSVs
- 🖥 **Next.js 16 (App Router, TypeScript)** frontend
- 🐘 **PostgreSQL** as the main data store
- 🐳 Optional **Docker Compose** setup for API + DB + scheduler

---

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy (or similar ORM), PostgreSQL
- **ETL / Jobs**: Python scripts (daily fetch, backfill, CSV upload)
- **Frontend**: Next.js 16, React, TypeScript, CSS
- **Infra**: Docker / Docker Compose (dev setup)

---

## Project Structure

High-level layout

```txt
.
├── backend/      # FastAPI API, DB layer, ETL scripts, Docker-related files
├── frontend/     # Next.js 16 app (App Router + TS)
├── data/         # Source CSVs (e.g. TWSE / TPEx company lists)
├── .gitignore
└── README.md
```

## Getting Started
### Backend (API + DB + Scheduler)
```txt
cd backend
make up
```
The API will be available at: http://localhost:8000

### Import company lists (TWSE / TPEx)
```txt
cd backend
export API_BASE=http://localhost:8000

# TWSE
python -m scripts.upload_companies_via_api ../data/上市公司列表.csv

# TPEx
python -m scripts.upload_companies_via_api ../data/上櫃公司列表.csv
```

### Frontend (Next.js dev server)
#### frontend/.env.local
```txt
API_BASE=http://localhost:8000
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_SITE_ORIGIN=http://localhost:3000
```

#### 啟動前端
```txt
cd frontend

npm install
npm run dev -- --port 3000
```
1. http://localhost:3000/ – Home
2. http://localhost:3000/stocks – 公司列表 + 簡單價格列表
3. http://localhost:3000/stocks/2330 – 基本面 + 即時價格卡片
4. http://localhost:3000/ta – 指標（MA / MACD / RSI / BB） playground

### Environment Variables
#### Backend (see backend/app/config.py for full list):

1. DATABASE_URL – PostgreSQL connection string
2. ALLOW_ORIGINS – CORS origins (e.g. http://localhost:3000)
3. API_BASE_FOR_ETL – Base URL for ETL scripts to call the API
4. BACKFILL_LOOKBACK_DAYS, DAILY_CRON, etc. – Scheduler behaviour

#### Frontend (frontend/.env.local):
1. API_BASE – API base for server-side fetches
2. NEXT_PUBLIC_API_BASE – Public API base (client + server)
3. NEXT_PUBLIC_SITE_ORIGIN – Used for mock APIs fallback