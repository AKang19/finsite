# path: backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 你原本就有的
    DATABASE_URL: str = "postgresql+psycopg://fin:finpass@postgres:5432/fin"
    ALLOW_ORIGINS: str = "http://localhost:3000"

    # （選配）第 3 階段會用到
    NEXT_REVALIDATE_URL: str | None = None
    REVALIDATE_SECRET: str | None = None

    # 🔹 ETL / worker / parser 相關（這次重點）
    PRICE_DATA_SOURCE: str = "twse"         # 對應 .env 的 PRICE_DATA_SOURCE
    MARKET_TZ: str = "Asia/Taipei"          # 對應 .env 的 MARKET_TZ
    MARKET_CLOSE_HHMM: str = "17:05"        # 對應 .env 的 MARKET_CLOSE_HHMM
    API_BASE_FOR_ETL: str | None = None     # 若用「透過 API 回補」會用到

    # 設定：讀取 .env，忽略未宣告欄位；環境變數大小寫不敏感
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

settings = Settings()
