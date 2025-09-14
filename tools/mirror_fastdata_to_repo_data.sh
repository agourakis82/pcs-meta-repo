#!/usr/bin/env bash
set -euo pipefail

# Mirror FASTDATA structure into repo ./data via symlinks
# Links:
# - data/L2_derived/kec -> ${FASTDATA}/L2_derived/kec
# - data/L1_tidy/derco_eeg -> ${FASTDATA}/L1_tidy/derco_eeg
# - data/raw_public/swow -> ${FASTDATA}/raw_public/swow (for notebooks)

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
FORCE=${1:-}
cd "$ROOT_DIR"

echo "[mirror] repo: $ROOT_DIR"

# Resolve data_root from config/data_root.yaml (use awk to avoid python deps)
DATA_ROOT=$(awk '/^data_root:/ {print $2}' config/data_root.yaml)
if [[ -z "$DATA_ROOT" ]]; then
  echo "[mirror] ERROR: could not resolve data_root from config/data_root.yaml" >&2
  exit 1
fi

echo "[mirror] data_root: $DATA_ROOT"

# Ensure target directories exist on FASTDATA
mkdir -p "$DATA_ROOT/L2_derived/kec" || true
mkdir -p "$DATA_ROOT/L1_tidy/derco_eeg" || true
mkdir -p "$DATA_ROOT/raw_public/swow" || true
mkdir -p "$DATA_ROOT/processed/v4.4" || true
mkdir -p "$DATA_ROOT/figures/v4.4" || true

declare -A MAP
MAP["data/L2_derived/kec"]="$DATA_ROOT/L2_derived/kec"
MAP["data/L1_tidy/derco_eeg"]="$DATA_ROOT/L1_tidy/derco_eeg"
MAP["data/raw_public/swow"]="$DATA_ROOT/raw_public/swow"
MAP["data/processed/v4.4"]="$DATA_ROOT/processed/v4.4"
MAP["figures/v4.4"]="$DATA_ROOT/figures/v4.4"

for local in "${!MAP[@]}"; do
  remote="${MAP[$local]}"
  mkdir -p "$(dirname "$local")"
  if [[ -e "$local" && ! -L "$local" ]]; then
    if [[ "$FORCE" == "--force" ]]; then
      echo "[mirror] REPLACE: $local (remove existing and link)"
      rm -rf "$local"
    else
      echo "[mirror] SKIP: $local exists and is not a symlink (use --force to replace)"
      continue
    fi
  fi
  ln -sfn "$remote" "$local"
  echo "[mirror] link: $local -> $remote"
done

echo "[mirror] done"
