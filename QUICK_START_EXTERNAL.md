# 🚀 DX-CODEX External Datasets - Quick Start Prompt

## One-Command Execution

To run the complete external datasets pipeline for GECO (ET), DERCo (EEG), OneStop (ET), and LPP (EEG):

```bash
cd /home/agourakis82/workspace/pcs-meta-repo

# Option 1: Interactive script (recommended)
./scripts/run_external_datasets_pipeline.sh

# Option 2: Direct Makefile target
make external-datasets-all

# Option 3: Manual step-by-step
make fetch-all && make ingest-geco && make ingest-onestop && make ingest-derco && make ingest-lpp && make provenance-fill && make qa-external
```

## Real-Only Mode (FASTDATA)

To compute real SWOW KEC and tidy DERCo EEG using your FASTDATA layout:

```bash
# Ensure real-only
export RUN_REAL=1; unset ALLOW_PLACEHOLDERS

# KEC (SWOW ➜ L2_derived/kec)
python -m src.cli.kec_compile --lang en,es,nl,zh --step all --resume

# DERCo EEG tidy ➜ L1_tidy/derco_eeg/word_events_eeg.parquet
python scripts/swow_zuco_pipeline.py --step tidy_eeg
```

Outputs:
- KEC per-language: `${FASTDATA}/L2_derived/kec/<lang>/` with `entropy.parquet`, `curvature.parquet`, `coherence.parquet`, `components.parquet`, `edges.parquet`, `kec_nodes.parquet`.
- DERCo EEG tidy: `${FASTDATA}/L1_tidy/derco_eeg/word_events_eeg.parquet`.

Note: Placeholders are disabled by default; enable only for CI via `export ALLOW_PLACEHOLDERS=1`.

## Configuration

1. **Data Storage** (optional): Edit `config/data_root.yaml` to set your preferred data directory
   - Current: `/mnt/FASTDATA`
   - Change to your fast disk location

2. **Dependencies** (if needed):
   ```bash
   pip install requests beautifulsoup4 pandas numpy pyyaml pyarrow
   ```

## Expected Results

- **Downloads**: ~2-5 GB raw data (external directory)
- **Processed**: ~100-500 MB harmonised parquet files
- **Reports**: SHA-256 provenance + quality assessment

## Verification

```bash
# Check processed files
ls -la /mnt/FASTDATA/processed/*/word_events.parquet

# View quality report
make qa-external

# Check provenance
ls -la reports/provenance/*.yaml
```

## Success Criteria

✅ 4 harmonised datasets: GECO, DERCo, OneStop, LPP  
✅ Quality validation passed  
✅ Provenance files generated  
✅ Ready for DX-CODEX integration  

**Ready to go?** Run: `./scripts/run_external_datasets_pipeline.sh`
