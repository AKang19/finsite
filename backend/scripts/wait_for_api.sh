set -euo pipefail
API_BASE="${API_BASE_FOR_ETL:-http://api:8000}"
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
  if [ $? -eq 0 ]; then
    echo "[wait] API is up"
    exit 0
  fi
  echo "[wait] API not ready, retry $i/${TRIES} ..."
  sleep $SLEEP
done
echo "[wait] API still not ready"; exit 1
