# DX-CODEX External Datasets Pipeline - Complete Execution Guide

## 🎯 Overview
This guide provides step-by-step instructions to run the complete DX-CODEX external datasets pipeline, which downloads, processes, and validates GECO (ET), DERCo (EEG), OneStop (ET), and LPP (EEG) datasets alongside the existing ZuCo v1/v2 data.

## 📋 Prerequisites

1. **Configure Data Storage Location**
   ```bash
   # Edit config/data_root.yaml to set your preferred data directory
   # Current setting: /mnt/FASTDATA
   # Change to your fast disk location (e.g., /data/pcs, D:/DATA/PCS)
   ```

2. **Required Dependencies (pre-flight)**
   ```bash
   # Core
   pip install -U pandas pyarrow pyyaml requests beautifulsoup4 pandera
   
   # EEG/ET + download helpers
   pip install -U mne pymovements osfclient openneuro-py datalad git-annex
   
   # Excel reader for GECO (xlsx)
   pip install -U openpyxl
   ```

3. **Disk Space Requirements**
   - Raw data: ~2-5 GB (external directory, not tracked)
   - Processed data: ~100-500 MB (parquet files)
   - Total workspace: ~6 GB free space recommended

## 🚀 Complete Pipeline Execution

### Option 1: One-Command Pipeline (Recommended)
```bash
cd /home/agourakis82/workspace/pcs-meta-repo
make external-datasets-all
```

This single command runs the complete pipeline:
1. Downloads all external datasets (GECO, DERCo, OneStop)
2. Processes them to harmonised word_events.parquet format
3. Generates provenance and quality assessment reports

### Option 2: Step-by-Step Execution

#### Step 1: Download External Datasets
```bash
# Download all datasets at once
make fetch-all

# OR download individually:
make fetch-geco      # GECO eye-tracking corpus
make fetch-derco     # DERCo EEG reading comprehension  
make fetch-onestop   # OneStop large-scale eye-tracking
make fetch-lpp       # LPP EEG listening dataset (OpenNeuro)
```

#### Step 2: Process to Harmonised Format
```bash
# Process all datasets
make ingest-geco     # GECO → word_events.parquet
make ingest-onestop  # OneStop → word_events.parquet
make ingest-derco    # DERCo → word_events.parquet
make ingest-lpp      # LPP → word_events.parquet
```

#### Step 3: Generate Provenance & Quality Reports
```bash
# Generate SHA-256 provenance files
make provenance-fill

# Run quality assessment
make qa-external
```

## 📊 Expected Outputs

### 1. Raw Data (External Storage)
```
{data_root}/raw_external/
├── geco/                 # GECO English/Dutch novel reading ET data
├── derco/                # DERCo EEG + behavioral cloze data
└── onestop/              # OneStop large-scale ET corpus
```

### 2. Processed Data (External Storage)
```
{data_root}/processed/
├── geco_et/word_events.parquet      # ~50K-200K words, ET measures
├── derco_eeg/word_events.parquet    # ~10K-50K words, EEG + ET measures  
├── onestop_et/word_events.parquet   # ~100K-2M words, ET measures
└── lpp_eeg/word_events.parquet      # word/segment-level EEG (if events available)
```

### 3. Reports (Repository)
```
reports/provenance/
├── geco_et.yaml         # SHA-256 hashes, file counts, metadata
├── derco_eeg.yaml       # EEG data provenance
├── onestop_et.yaml      # OneStop provenance
└── lpp_eeg.yaml         # LPP EEG provenance
```

## 🔍 Quality Assessment Criteria

The pipeline validates each dataset against these criteria:

### GECO (Eye-Tracking)
- **Minimum rows**: 5,000 words
- **Required columns**: subject_id, word, ffd_ms, gd_ms, trt_ms, nfix
- **Quality checks**: No placeholder words, ET ranges 50-2000ms
- **Languages**: English, Dutch

### DERCo (EEG + Behavioral)
- **Minimum rows**: 1,000 words  
- **Required columns**: subject_id, word, eeg_metric, cloze_prob
- **Quality checks**: EEG metrics available, reasonable ranges
- **Language**: English

### OneStop (Eye-Tracking)
- **Minimum rows**: 5,000 words
- **Required columns**: subject_id, word, ffd_ms, gd_ms, trt_ms
- **Quality checks**: Large-scale corpus validation
- **Language**: English

## ⚠️ Troubleshooting

### Download Issues
```bash
# If downloads fail, try individual datasets:
make fetch-geco --force

# Check network connectivity to source sites:
# - GECO: https://expsy.ugent.be/downloads/geco/
# - DERCo: https://www.nature.com/articles/s41597-024-03915-8  
# - OneStop: https://lacclab.github.io/OneStop-Eye-Movements/
```

### Processing Issues
```bash
# Check if data directories exist:
ls -la /mnt/FASTDATA/raw_external/

# Test individual loaders:
python -c "import sys; sys.path.insert(0, '.'); from src.datasets.geco_loader import run; run()"
```

- GECO: if you see "Missing optional dependency 'openpyxl'", install it via `pip install openpyxl`.
- OneStop: loader prefers Interest Area reports and skips huge `fixations_*` files automatically; ensure `precomputed_reading_measures/ia_Paragraph.csv` is present.

### Storage Issues
```bash
# Check available disk space:
df -h /mnt/FASTDATA

# Change data root if needed:
# Edit config/data_root.yaml
```

## 📈 Success Verification

After running the complete pipeline, verify success:

```bash
# Check processed files exist:
ls -la /mnt/FASTDATA/processed/*/word_events.parquet

# Check provenance files:
ls -la reports/provenance/*.yaml

# Run QA summary:
make qa-external
```

Expected QA output:
```
✅ GECO: X,XXX words from XX subjects
✅ DERCo: X,XXX words from XX subjects  
✅ OneStop: XXX,XXX words from XXX subjects
✅ LPP: X,XXX rows from XX subjects
📊 Total: X,XXX,XXX words across all datasets
```

## 🔗 Integration with DX-CODEX

After successful completion, the harmonised datasets are ready for:

1. **Model Training**: Use word_events.parquet files for reading time prediction
2. **Cross-corpus Analysis**: Compare ET patterns across GECO, OneStop, ZuCo
3. **EEG-ET Integration**: Combine DERCo EEG with ZuCo for multimodal analysis
4. **Language Comparison**: English (all datasets) vs Dutch (GECO)

## 📄 License & Citation

Each dataset maintains its original license:
- **GECO**: Public, cite UGent source
- **DERCo**: CC BY 4.0, cite Scientific Data paper
- **OneStop**: CC BY 4.0, cite LaCC Lab

Raw data is NOT redistributed; only processed parquet files are generated locally.

## 🆘 Support

If you encounter issues:

1. Check the QA report: `make qa-external`
2. Verify configuration: `config/data_root.yaml` and `config/datasets.yaml`
3. Test individual components before running the full pipeline
4. Ensure sufficient disk space and network connectivity

---

### LPP (EEG Listening)
- Minimum rows: 1,000 rows (if word/segment events available)
- Required columns: subject_id, word (or trial_type), eeg_metric
- Quality checks: EEG metrics available, reasonable ranges
- Language: Primarily French (story), annotations may vary
**Ready to run?** Execute: `make external-datasets-all`
