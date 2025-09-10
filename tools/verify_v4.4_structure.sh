#!/usr/bin/env bash
set -euo pipefail
echo "[verify] structure & key files"
req_dirs=(docs src scripts notebooks data figures reports tools)
for d in "${req_dirs[@]}"; do [[ -d "$d" ]] || { echo "missing dir: $d"; exit 1; }; done

# L1 tidy
for ds in zuco_rt geco_rt onestop_rt zuco_eeg derco_eeg lpp_eeg; do
  [[ -f "data/L1_tidy/${ds}/word_events_${ds##*_}.parquet" ]] || echo "WARN: missing L1_tidy/${ds}"
done

# KEC artifacts
for lang in en es nl zh; do
  for f in entropy.parquet curvature.parquet coherence.parquet components.parquet edges.parquet kec_nodes.parquet; do
    [[ -f "data/L2_derived/kec/${lang}/${f}" ]] || echo "WARN: missing data/L2_derived/kec/${lang}/${f}"
  done
done

# Integration + models
for f in \
  data/processed/v4.4/integration/zuco_kec_rt.parquet \
  data/processed/v4.4/integration/geco_kec_rt.parquet \
  data/processed/v4.4/integration/onestop_kec_rt.parquet \
  data/processed/v4.4/integration/zuco_kec_eeg.parquet \
  data/processed/v4.4/integration/derco_kec_eeg.parquet \
  data/processed/v4.4/integration/lpp_kec_eeg.parquet \
  data/processed/v4.4/integration/zuco_kec_merged.parquet; do
  [[ -f "$f" ]] || echo "WARN: missing $f"
done

[[ -f "data/processed/v4.4/models/models_reading_coeffs.csv" ]] || echo "WARN: missing models_reading_coeffs.csv"

# Figures
for fig in F1_mean_spike_delta_kec_en.png F2_reading_vs_KEC.png F3_EEG_vs_KEC.png; do
  [[ -f "figures/v4.4/${fig}" ]] || echo "WARN: missing figures/v4.4/${fig}"
done

# QA minima
[[ -f "reports/inventory.json"  ]] || echo "WARN: missing reports/inventory.json"
[[ -f "reports/linkcheck.json"  ]] || echo "WARN: missing reports/linkcheck.json"
echo "[verify] done"
