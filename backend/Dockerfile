# path: backend/Dockerfile
FROM python:3.11-slim

# --- 基本環境 ---
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Taipei

WORKDIR /app

# 系統相依 + cron + 工具
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential libpq-dev \
      cron curl procps ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/*

# 設定時區
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 先只複製 requirements 以利快取
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r /app/requirements.txt

# 再複製程式碼
COPY . /app

# 去除 CRLF（所有 .sh）+ 放置 scheduler 啟動器到 PATH + 權限
RUN find /app -type f -name "*.sh" -exec sed -i 's/\r$//' {} \; \
 && install -m 0755 /app/scripts/entry_scheduler.sh /usr/local/bin/entry_scheduler.sh

# 預設給「api」用的啟動（scheduler 會在 compose 以 entrypoint 覆蓋）
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
