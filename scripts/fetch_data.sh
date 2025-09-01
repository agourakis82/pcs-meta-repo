#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(pwd)"
RAW_DIR="$ROOT_DIR/data/raw_public"
SWOW_EN_DIR="$RAW_DIR/swow/en"
SWOW_ES_DIR="$RAW_DIR/swow/es"
ZUCO_V1_DIR="$RAW_DIR/zuco/v1"
ZUCO_V2_DIR="$RAW_DIR/zuco/v2"

mkdir -p "$SWOW_EN_DIR" "$SWOW_ES_DIR" "$ZUCO_V1_DIR" "$ZUCO_V2_DIR"

echo "[1/4] Checking osfclient ..."
if ! command -v osf >/dev/null 2>&1; then
  echo "osfclient not found. Install with: pip install osfclient"
  exit 1
fi

echo "[2/4] Cloning ZuCo 1.0 (OSF project q3zws) ..."
# You can 'clone' once; subsequent runs will skip existing files.
osf -p q3zws clone "$ZUCO_V1_DIR" || true

echo "[3/4] Cloning ZuCo 2.0 (OSF project 2urht) ..."
osf -p 2urht clone "$ZUCO_V2_DIR" || true

echo "[4/4] SWOW scaffolding"
# --- SWOW (manual/optional direct URLs) ---
# Place your SWOW-EN CSVs into $SWOW_EN_DIR (drag&drop or curl them).
# Examples (update the URLs to the latest CSV endpoints if available):
# curl -L "https://example.com/swow_en_full.csv" -o "$SWOW_EN_DIR/swow_en_full.csv"
# curl -L "https://example.com/swow_es_full.csv" -o "$SWOW_ES_DIR/swow_es_full.csv"

# Write initial provenance stubs
PROV_DIR="$ROOT_DIR/data/provenance"
mkdir -p "$PROV_DIR"
cat > "$PROV_DIR/provenance_zuco.yaml" << 'YAML'
dataset: zuco
sources:
  - osf: q3zws   # ZuCo 1.0
  - osf: 2urht   # ZuCo 2.0
ingest_date: 2025-08-31
raw_dirs:
  - data/raw_public/zuco/v1
  - data/raw_public/zuco/v2
hashes: []      # will be filled by compute_checksums.sh
version_pins:
  python: "3.11"
  packages:
    osfclient: ">=0.0"
YAML

cat > "$PROV_DIR/provenance_swow.yaml" << 'YAML'
dataset: swow
languages: [en, es]
ingest_date: 2025-08-31
raw_dirs:
  - data/raw_public/swow/en
  - data/raw_public/swow/es
source_url: https://smallworldofwords.org/en/project/research
license_upstream: "see SWOW website"
hashes: []      # will be filled by compute_checksums.sh
YAML

echo "Done. Next: bash scripts/compute_checksums.sh"
