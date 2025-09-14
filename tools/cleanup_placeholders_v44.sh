#!/usr/bin/env bash
set -euo pipefail

# Cleanup zero-byte placeholder artifacts for v4.4 under repo data paths
# Default root: ./data and ./figures/v4.4
# Usage:
#   tools/cleanup_placeholders_v44.sh            # dry run
#   tools/cleanup_placeholders_v44.sh --apply    # delete files

APPLY=0
if [[ "${1:-}" == "--apply" ]]; then
  APPLY=1
fi

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

echo "[cleanup] Scanning for zero-byte placeholders…"

mapfile -t FILES < <(find data -type f -size 0 -print 2>/dev/null || true)
mapfile -t FIGS  < <(find figures/v4.4 -type f -size 0 -print 2>/dev/null || true)

COUNT=$(( ${#FILES[@]} + ${#FIGS[@]} ))
if (( COUNT == 0 )); then
  echo "[cleanup] No zero-byte files found."
  exit 0
fi

echo "[cleanup] Found $COUNT file(s):"
printf '  %s\n' "${FILES[@]}" "${FIGS[@]}"

if (( APPLY == 1 )); then
  echo "[cleanup] Deleting…"
  for f in "${FILES[@]}" "${FIGS[@]}"; do
    [[ -n "$f" ]] && rm -f "$f"
  done
  echo "[cleanup] Done."
else
  echo "[cleanup] Dry run. Pass --apply to delete."
fi

