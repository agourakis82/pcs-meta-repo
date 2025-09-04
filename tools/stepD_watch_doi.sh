#!/usr/bin/env bash
set -euo pipefail

VER="${1:-}"
if [ -z "$VER" ]; then
  echo "Usage: tools/stepD_watch_doi.sh <version> [max_attempts] [interval_seconds]" >&2
  exit 1
fi
MAX_ATTEMPTS="${2:-60}"
INTERVAL="${3:-60}"

CONCEPT="10.5281/zenodo.16533374"
ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT_DIR"

attempt=0
while [ "$attempt" -lt "$MAX_ATTEMPTS" ]; do
  attempt=$((attempt+1))
  echo "[watch-doi] Attempt $attempt/$MAX_ATTEMPTS for v$VER..."
  JSON="$(curl -sS "https://zenodo.org/api/records/?q=conceptdoi:${CONCEPT}&sort=mostrecent&size=5" || true)"
  DOI="$(python3 - <<PY 2>/dev/null
import sys, json, re
try:
    j=json.load(sys.stdin)
    for rec in j.get('hits',{}).get('hits',[]):
        md=rec.get('metadata',{})
        title=str(md.get('title',''))
        version=str(md.get('version',''))
        doi=rec.get('doi') or md.get('doi') or ''
        if version=="%s" or ("v%s" in title):
            if doi:
                print(doi)
                break
except Exception:
    pass
PY
"$VER" "$VER")"
  if [ -n "$DOI" ]; then
    echo "[watch-doi] Found DOI for v$VER: $DOI"
    tools/stepC_inject_doi.sh "$DOI" "$VER" || true
    echo "[watch-doi] Attempting git push..."
    git push || echo "[watch-doi] INFO: git push failed (check credentials)"
    exit 0
  fi
  sleep "$INTERVAL"
done
echo "[watch-doi] DOI not found for v$VER after $MAX_ATTEMPTS attempts."
exit 1

