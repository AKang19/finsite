# path: backend/scripts/bootstrap_scheduler.sh
#!/usr/bin/env bash
set -euo pipefail

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOOKBACK="${BACKFILL_LOOKBACK_DAYS:-90}"
CRON_EXPR="${DAILY_CRON:-5 17 * * 1-5}"
API_BASE_FOR_ETL="${API_BASE_FOR_ETL:-http://127.0.0.1:8000}"

chmod +x "$WORKDIR/scripts/setup_scheduler.sh"

echo "→ Installing scheduler (WORKDIR=$WORKDIR, LOOKBACK=$LOOKBACK, CRON='$CRON_EXPR', API=$API_BASE_FOR_ETL)"
WORKDIR="$WORKDIR" BACKFILL_LOOKBACK_DAYS="$LOOKBACK" DAILY_CRON="$CRON_EXPR" API_BASE_FOR_ETL="$API_BASE_FOR_ETL" \
  "$WORKDIR/scripts/setup_scheduler.sh" install

echo "→ Current crontab:"
crontab -l || true
