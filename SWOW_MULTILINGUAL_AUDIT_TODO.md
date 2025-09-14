# SWOW Multilingual Audit & English Standardization - TODO

**Project**: Complete audit of SWOW multilingual functionality and KEC metrics integration
**Goal**: Ensure all files, instructions, and notebooks are in English, including figures
**Languages**: EN, ES, ZH, NL

## Phase 1: Core Infrastructure Audit ✅ IN PROGRESS

### 1.1 SWOW Data Pipeline Verification
- [ ] Verify SWOW data loading for all 4 languages (EN, ES, ZH, NL)
- [ ] Check `src/pcs_toolbox/swow.py` functionality
- [ ] Audit `config/swow.yaml` and `config/swow_paths.yaml` configurations
- [ ] Validate data directory structure for each language

### 1.2 KEC Metrics Computation Audit
- [ ] Verify `src/pcs_toolbox/kec.py` implementation
- [ ] Test entropy computation for all languages
- [ ] Test curvature computation for all languages  
- [ ] Test coherence computation for all languages
- [ ] Validate KEC metrics output format and schema

### 1.3 Integration Pipeline Audit
- [ ] Check SWOW → Graph → KEC → Statistics flow
- [ ] Verify neurophysiological dataset integration (ZuCo, DERCo, GECO, OneStop, LPP)
- [ ] Audit `scripts/swow_zuco_pipeline.py` functionality
- [ ] Test multilingual data merging and alignment

### 1.4 Missing Files Assessment
- [ ] Identify missing `src/swow/` modules
- [ ] Document missing language-specific processing files
- [ ] List incomplete integration scripts
- [ ] Assess notebook completeness

## Phase 2: Language Standardization 🔄 PENDING

### 2.1 Portuguese → English Conversion
- [ ] Convert all Portuguese comments to English
- [ ] Translate Portuguese docstrings to English
- [ ] Update Portuguese variable names to English
- [ ] Standardize Portuguese function names to English

### 2.2 Documentation Standardization
- [ ] Convert all README files to English
- [ ] Translate configuration file comments
- [ ] Update notebook markdown cells to English
- [ ] Standardize error messages to English

### 2.3 Figure and Plot Standardization
- [ ] Convert all plot titles to English
- [ ] Update axis labels to English
- [ ] Translate legend text to English
- [ ] Standardize figure captions to English

## Phase 3: Missing Files Recovery 🔄 PENDING

### 3.1 Core SWOW Modules
- [ ] Create `src/swow/__init__.py`
- [ ] Implement `src/swow/clean_en.py`
- [ ] Implement `src/swow/clean_es.py`
- [ ] Implement `src/swow/clean_nl.py`
- [ ] Implement `src/swow/clean_zh.py`
- [ ] Create `src/swow/io.py`
- [ ] Create `src/swow/graph.py`
- [ ] Create `src/swow/metrics_kec.py`
- [ ] Create `src/swow/align.py`
- [ ] Create `src/swow/api.py`
- [ ] Create `src/swow/zh_preproc.py`

### 3.2 Integration Scripts
- [ ] Complete multilingual pipeline orchestration
- [ ] Create language-specific validation scripts
- [ ] Implement cross-language comparison tools
- [ ] Add comprehensive error handling

### 3.3 Testing Infrastructure
- [ ] Create unit tests for each language
- [ ] Implement integration tests for KEC pipeline
- [ ] Add validation tests for data quality
- [ ] Create performance benchmarks

## Phase 4: Documentation and Validation 🔄 PENDING

### 4.1 English Documentation
- [ ] Create comprehensive SWOW-KEC pipeline documentation
- [ ] Write English user guides for each language
- [ ] Document API reference in English
- [ ] Create troubleshooting guides in English

### 4.2 Validation Reports
- [ ] Generate validation reports for each language
- [ ] Create quality assessment dashboards
- [ ] Implement automated quality gates
- [ ] Add data integrity checks

### 4.3 Examples and Tutorials
- [ ] Create English-only tutorial notebooks
- [ ] Add reproducible examples for each language
- [ ] Document best practices in English
- [ ] Create quick-start guides

## Current Status: Phase 1 - Core Infrastructure Audit

**Next Steps:**
1. Verify SWOW data loading pipeline
2. Test KEC metrics computation
3. Audit integration with neurophysiological datasets
4. Assess missing files and create recovery plan

**Priority Issues Identified:**
- Missing `src/swow/` module files
- Portuguese language mixing throughout codebase
- Incomplete multilingual pipeline implementation
- Non-English figure labels and documentation

**Quality Gates:**
- All code must be in English
- All documentation must be in English  
- All figures must have English labels
- All languages (EN, ES, ZH, NL) must be fully supported
- Complete pipeline from raw data to statistics must work
