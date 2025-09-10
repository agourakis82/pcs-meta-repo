# RUNBOOK (minimal) — PCS-Meta-Repo v4.4

## 0) Environment & initial QA
```
conda env create -f environment.yml && conda activate pcs-meta-repo
pre-commit install
ruff check . && ruff format --check .
python tools/repo_lint.py
python scripts/compute_checksums.py  # inventory + checksums (reports/data/CHECKS)
```

## 1) Fetch real datasets (no raw redistribution)
```
bash scripts/fetch_data.sh              # SWOW (EN/ES/NL/ZH), ZuCo v1/v2, GECO, OneStop, DERCo, LPP
python scripts/compute_checksums.py     # SHA-256 → data/CHECKS/checksums.csv
```

## 2) L0→L1 (tidy, modal split)
```
python -m scripts.swow_zuco_pipeline --step tidy_rt  --datasets zuco_rt,geco_et,onestop_et
python -m scripts.swow_zuco_pipeline --step tidy_eeg --datasets zuco_eeg,derco_eeg,lpp_eeg
```

## 3) L2 (KEC multilingual)
```
python -m src.cli.kec_compile --lang en,es,nl,zh --step all --device auto --resume
```

## 4) Integration SWOW↔(EEG/RT)
```
python scripts/swow_zuco_pipeline.py --step integrate
```

## 5) Models (RT~KEC; EEG~KEC)
```
python scripts/swow_zuco_pipeline.py --step models_rt
python scripts/swow_zuco_pipeline.py --step models_eeg
Rscript scripts/r_mixedlm_check.R      # optional/robust
```

## 6) Figures (v4.4)
```
python -m src.figures.make_figures --version v4.4
```

## 7) QA & Release
```
python tools/repo_lint.py
python scripts/compute_checksums.py
bash tools/verify_v4.4_structure.sh || true
# DOI: update CITATION.cff + .zenodo.json; create tag v4.4.x; deposit on Zenodo
```

## Expected outputs
- /data/L1_tidy/{zuco_rt,geco_rt,onestop_rt}/word_events_rt.parquet
- /data/L1_tidy/{zuco_eeg,derco_eeg,lpp_eeg}/word_events_eeg.parquet
- /data/L2_derived/kec/<lang>/{entropy,curvature,coherence,components,edges,kec_nodes}.parquet
- /data/processed/v4.4/integration/{zuco_kec_rt.parquet, zuco_kec_eeg.parquet, zuco_kec_merged.parquet}
- data/processed/v4.4/models/models_reading_coeffs.csv
- figures/v4.4/{F1_mean_spike_delta_kec_en.png, F2_reading_vs_KEC.png, F3_EEG_vs_KEC.png}
- reports/{lint*.json, linkcheck.json, inventory.json, provenance/*.yaml}

