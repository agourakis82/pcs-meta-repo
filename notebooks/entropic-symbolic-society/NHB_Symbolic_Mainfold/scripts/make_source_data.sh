#!/usr/bin/env bash
# make_source_data.sh
# Convenience wrapper: fill source_fig2_entropy_curvature.csv from entropy_curvature_all.csv

set -euo pipefail

IN="${1:-entropy_curvature_all.csv}"
OUT="${2:-source_fig2_entropy_curvature.csv}"
BETA="${3:-}"        # optional, e.g. 1.0
MAPCSV="${4:-}"      # optional rename map CSV: from,to

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$IN" ]]; then
  echo "ERROR: input not found: $IN" >&2
  exit 2
fi

CMD=( python "${HERE}/integrate_entropy_curvature.py" --in "$IN" --out "$OUT" )
if [[ -n "$BETA" ]]; then
  CMD+=( --select-beta "$BETA" )
fi
if [[ -n "$MAPCSV" ]]; then
  CMD+=( --rename-regimes "$MAPCSV" )
fi

echo ">> ${CMD[@]}"
"${CMD[@]}"
echo "Done."
