#!/usr/bin/env bash
set -euo pipefail

# === 可調參數（也可用環境變數覆寫） ===
WORKDIR_DEFAULT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKDIR="${WORKDIR:-$WORKDIR_DEFAULT}"         # 專案 backend 目錄
LOOKBACK="${BACKFILL_LOOKBACK_DAYS:-90}"       # 開機回補 N 天（沒資料時）
DAILY_CRON="${DAILY_CRON:-5 17 * * 1-5}"       # 每日跑時間（預設 17:05 週一~週五）
API_BASE_FOR_ETL="${API_BASE_FOR_ETL:-http://127.0.0.1:8000}" # exec 版使用本機 127.0.0.1

DOCKER_BIN="$(command -v docker || true)"
if [[ -z "$DOCKER_BIN" ]]; then
  echo "ERROR: docker 不在 PATH，請先安裝 Docker Desktop 並確保可執行 'docker'。" >&2
  exit 1
fi

LOG_DIR="$WORKDIR/logs"
WAIT_SH="$WORKDIR/scripts/wait_for_api.sh"

ensure_wait_sh() {
  if [[ ! -x "$WAIT_SH" ]]; then
    mkdir -p "$WORKDIR/scripts"
    cat > "$WAIT_SH" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
API_BASE="${API_BASE_FOR_ETL:-http://127.0.0.1:8000}"
TRIES=30
SLEEP=4
for i in $(seq 1 $TRIES); do
  python - <<PY 2>/dev/null
import urllib.request, sys
try:
    urllib.request.urlopen("${API_BASE}/healthz", timeout=3).read()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
  rc=$?
  if [ "$rc" -eq 0 ]; then echo "[wait] API is up"; exit 0; fi
  echo "[wait] API not ready, retry $i/${TRIES} ..."
  sleep $SLEEP
done
echo "[wait] API still not ready"; exit 1
SH
    chmod +x "$WAIT_SH"
  fi
}

render_cron() {
  cat <<CRON
SHELL=/bin/zsh
PATH=/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin
CRON_TZ=Asia/Taipei

# 心跳：每分鐘一行，用來確認 cron 有在跑
* * * * * date "+%F %T %Z" >> ${LOG_DIR}/cron_beat.log

# 開機：起 API -> 等健康 -> 回補（保持你原本的 wait；可留 API_BASE_FOR_ETL）
@reboot cd ${WORKDIR} && docker compose up -d api && \
API_BASE_FOR_ETL=${API_BASE_FOR_ETL} ${WAIT_SH} && \
BACKFILL_LOOKBACK_DAYS=${LOOKBACK} docker compose exec -T \
  -e PYTHONPATH=/app -e API_BASE=http://127.0.0.1:8000 \
  -e BACKFILL_LOOKBACK_DAYS \
  api python /app/scripts/backfill_missing_all_via_api.py >> ${LOG_DIR}/cron_backfill.log 2>&1

# 每日 17:05 抓價（關鍵：傳 API_BASE=http://127.0.0.1:8000）
${DAILY_CRON} cd ${WORKDIR} && \
docker compose exec -T -e PYTHONPATH=/app -e API_BASE=http://127.0.0.1:8000 \
  api python /app/scripts/fetch_today_all_via_api.py >> ${LOG_DIR}/cron_fetch.log 2>&1
CRON
}


install_cron() {
  mkdir -p "$LOG_DIR"
  touch "$LOG_DIR/cron_backfill.log" "$LOG_DIR/cron_fetch.log"
  ensure_wait_sh
  render_cron > /tmp/finsite.cron
  crontab /tmp/finsite.cron
  rm -f /tmp/finsite.cron
  echo "[ok] crontab installed. Use: crontab -l"
}

uninstall_cron() {
  crontab -r || true
  echo "[ok] crontab removed."
}

show_cron() {
  echo "# --- Rendered cron ---"
  render_cron
}

usage() {
  cat <<USAGE
Usage: $(basename "$0") [install|uninstall|show]
Env:
  WORKDIR=/Users/you/finsite/backend   # 專案 backend 目錄（預設自動偵測）
  BACKFILL_LOOKBACK_DAYS=90            # 開機回補天數（預設 90）
  DAILY_CRON="5 17 * * 1-5"            # 每日排程（cron 表達式）
  API_BASE_FOR_ETL=http://127.0.0.1:8000
USAGE
}

cmd="${1:-}"
case "$cmd" in
  install)   install_cron ;;
  uninstall) uninstall_cron ;;
  show)      show_cron ;;
  *)         usage; exit 1 ;;
esac
