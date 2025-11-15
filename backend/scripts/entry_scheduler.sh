#!/usr/bin/env bash
set -euo pipefail

TZ="${TZ:-Asia/Taipei}"
DAILY_CRON="${DAILY_CRON:-5 17 * * 1-5}"
LOOKBACK="${BACKFILL_LOOKBACK_DAYS:-7}"
API_BASE_FOR_ETL="${API_BASE_FOR_ETL:-http://api:8000}"
export TZ

LOG_DIR="/app/logs"
PY="/usr/local/bin/python"
APP_DIR="/app"

mkdir -p "$LOG_DIR"
touch "$LOG_DIR/cron_backfill.log" "$LOG_DIR/cron_fetch.log"

# 1) 等 API 起來
/bin/sh -lc "/app/scripts/wait_for_api.sh ${API_BASE_FOR_ETL}"

# 2) 用 API 修表
curl -fsS -X POST "${API_BASE_FOR_ETL}/api/admin/ensure_schema"

echo "[INFO] One-shot backfill on start (LOOKBACK=${LOOKBACK})..."
set +e
(cd "$APP_DIR" && BACKFILL_LOOKBACK_DAYS="$LOOKBACK" "$PY" "$APP_DIR/scripts/backfill_missing_all_via_api_http.py") >> "$LOG_DIR/cron_backfill.log" 2>&1
RET=$?
set -e
echo "[INFO] One-shot backfill exit code: $RET (see $LOG_DIR/cron_backfill.log)"

crontab - <<EOF
SHELL=/bin/sh
PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
${DAILY_CRON} cd ${APP_DIR} && ${PY} ${APP_DIR}/scripts/daily_fetch_all_via_api.py >> ${LOG_DIR}/cron_fetch.log 2>&1
EOF

echo "[INFO] Installed user crontab:"; crontab -l || true
echo "--------------------------------"

if command -v cron >/dev/null 2>&1; then
  exec cron -f
else
  if crond -h 2>&1 | grep -q "\-L"; then
    exec crond -f -l 8 -L /var/log/cron.log
  else
    exec crond -f -l 8
  fi
fi
