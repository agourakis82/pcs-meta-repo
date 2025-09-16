#!/usr/bin/env bash
set -euo pipefail

# Run the v4.4 pipeline in REAL mode end-to-end for what is wired.
# - Uses FASTDATA from config/data_root.yaml
# - Computes SWOW KEC for en,es,nl,zh
# - Tidy EEG for DERCo (writes L1_tidy/derco_eeg/word_events_eeg.parquet)
# - Does not enable placeholders unless explicitly requested

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

echo "[v4.4] REAL pipeline start"

# Ensure repo paths mirror FASTDATA
tools/mirror_fastdata_to_repo_data.sh --force

# Real-only policy
export RUN_REAL=1
unset ALLOW_PLACEHOLDERS

# Compute KEC for all languages
echo "[v4.4] Computing SWOW KEC (en,es,nl,zh)…"
python -m src.cli.kec_compile --lang en,es,nl,zh --step all --resume || {
  echo "[v4.4] ERROR: KEC compile failed" >&2; exit 1;
}

# Tidy EEG (DERCo real)
echo "[v4.4] Tidy EEG (DERCo)…"
python scripts/swow_zuco_pipeline.py --step tidy_eeg || {
  echo "[v4.4] WARN: tidy_eeg step had issues; continuing" >&2;
}

echo "[v4.4] Expected outputs (FASTDATA):"
DR=$(awk '/^data_root:/ {print $2}' config/data_root.yaml)
echo "  - ${DR}/L2_derived/kec/{en,es,nl,zh}/(entropy|curvature|coherence|components|edges|kec_nodes).parquet"
echo "  - ${DR}/L1_tidy/derco_eeg/word_events_eeg.parquet"

echo "[v4.4] Done. Use tools/cleanup_placeholders_v44.sh to remove any placeholder artifacts."

