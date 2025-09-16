#!/usr/bin/env bash
set -euo pipefail

# Await KEC EN artifacts in FASTDATA and trigger modality-separated integration.

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

DATA_ROOT=$(awk '/^data_root:/ {print $2}' config/data_root.yaml)
KEC_DIR="$DATA_ROOT/L2_derived/kec/en"
TARGETS=("entropy.parquet" "curvature.parquet" "coherence.parquet")

echo "[await] FASTDATA: $DATA_ROOT"
echo "[await] KEC EN dir: $KEC_DIR"

until [[ -d "$KEC_DIR" ]]; do
  echo "[await] waiting for $KEC_DIR ..."; sleep 30;
done

while true; do
  MISSING=0
  for f in "${TARGETS[@]}"; do
    if [[ ! -f "$KEC_DIR/$f" ]]; then MISSING=1; fi
  done
  if [[ $MISSING -eq 0 ]]; then break; fi
  echo "[await] KEC not complete yet; retrying in 60s..."; sleep 60;
done

echo "[await] KEC EN complete. Running integration (EEG/RT separated)..."
export RUN_REAL=1
unset ALLOW_PLACEHOLDERS
export PYTHONPATH=.
python scripts/swow_zuco_pipeline.py --step integrate || true
echo "[await] integration step finished. Outputs under data/processed/v4.4/integration/"

