# EEG/RT Data Ingestion and Normalization Pipeline Audit Plan

**Author:** AI Assistant  
**Date:** January 2025  
**Version:** 1.0.0  
**Repository:** pcs-meta-repo  

## Executive Summary

This document outlines a comprehensive audit plan for the EEG/RT (Electroencephalography/Reading Time) data ingestion and normalization pipeline. The audit aims to standardize all datasets (ZuCo, DERCo, GECO, LPP, OneStop) to project standards including English documentation, proper notebook structure, and quality gates compliance.

## Information Gathered

### Current Pipeline State Analysis

**Datasets Covered:**
- **ZuCo v1/v2**: Eye-tracking and EEG data from reading experiments
- **DERCo**: EEG data in FIF format with behavioral measures  
- **GECO**: Eye-tracking data from Excel files (English/Dutch)
- **LPP**: EEG data in BIDS format (Le Petit Prince in French)
- **OneStop**: Eye-tracking data from CSV files

**Key Issues Identified:**
1. **Inconsistent Implementation**: Each loader has different approaches to data harmonization
2. **Mixed Languages**: Portuguese/English documentation throughout
3. **Schema Compliance**: Inconsistent adherence to `WORD_EVENTS_SCHEMA`
4. **Notebook Standards**: Current notebooks don't follow IMRaD structure or project style guide
5. **Quality Gates**: Not consistently applied across all datasets

**Strengths Found:**
- Well-defined contracts in `src/contracts.py`
- Established quality gates framework
- Comprehensive ZuCo processing in `src/pcs_toolbox/zuco.py`
- Good error handling in DERCo loader

## Audit Plan

### Phase 1: Data Ingestion Standardization

#### 1.1 Loader Harmonization
**Objective**: Standardize all EEG/RT loaders for consistency

**Tasks:**
- **ZuCo Loader**: Validate `src/pcs_toolbox/zuco.py` against contracts
- **DERCo Loader**: Audit `src/datasets/derco_eeg_loader.py` for schema compliance
- **GECO Loader**: Review `src/datasets/geco_loader.py` column mapping
- **LPP Loader**: Validate `src/datasets/lpp_eeg_loader.py` BIDS processing
- **OneStop Loader**: Audit `src/datasets/onestop_loader.py` CSV parsing

**Standards to Apply:**
- Consistent column naming following `WORD_EVENTS_SCHEMA`
- Uniform error handling and logging
- Standardized output format (word_events.parquet)
- Proper validation using `validate_word_events()`

#### 1.2 Schema Compliance Validation
**Objective**: Ensure all outputs conform to project contracts

**Required Columns:**
```python
WORD_EVENTS_SCHEMA = {
    "required": ["subject_id", "doc_id", "sent_id", "word_id", "word", "lang"],
    "et_optional": ["ffd_ms", "gd_ms", "trt_ms", "nfix"],
    "eeg_optional": ["eeg_metric", "theta", "alpha", "beta", "onset_ms", "offset_ms"],
}
```

**Validation Steps:**
- Run `validate_word_events()` on all loader outputs
- Apply `optional_pandera_validate()` where available
- Execute `check_dataset_quality()` with appropriate thresholds

#### 1.3 Data Quality Assurance
**Objective**: Implement consistent QA across all datasets

**Quality Metrics:**
- Minimum row counts per dataset
- Subject coverage validation
- Missing data analysis
- Outlier detection and handling

### Phase 2: Notebook Standardization

#### 2.1 Master EEG/RT Ingestion Notebook
**Objective**: Create unified notebook replacing fragmented implementations

**Structure (IMRaD Format):**
1. **Introduction**
   - Overview of EEG/RT datasets
   - Processing objectives
   - Quality standards

2. **Methods**
   - Data loading procedures
   - Harmonization algorithms
   - Validation protocols

3. **Results**
   - Processing statistics
   - Quality metrics
   - Dataset summaries

4. **Discussion**
   - Limitations and biases
   - Next steps
   - Integration recommendations

**Technical Requirements:**
- English documentation throughout
- Proper preflight checks
- Deterministic outputs with seeds
- Sample/full run modes
- QA assertions

#### 2.2 Statistical Analysis Notebook
**Objective**: Complete the statistical pipeline with proper structure

**Content:**
- Descriptive statistics for all datasets
- Comparative analysis between modalities
- Statistical validation methods
- Reproducible analysis workflows

#### 2.3 Quality Assurance Notebook
**Objective**: Comprehensive validation and QA procedures

**Features:**
- Cross-dataset validation
- Schema compliance checking
- Performance benchmarking
- Error reporting and diagnostics

### Phase 3: Quality Gates Implementation

#### 3.1 English Documentation
**Objective**: Convert all Portuguese content to English

**Scope:**
- Notebook markdown cells
- Code comments
- Variable names
- Error messages
- Documentation strings

#### 3.2 IMRaD Structure Implementation
**Objective**: Apply proper scientific structure to all notebooks

**Requirements:**
- Clear section headers
- Logical flow from intro to discussion
- Proper citations and references
- Reproducible methodology

#### 3.3 Reproducibility Standards
**Objective**: Ensure deterministic and reproducible outputs

**Implementation:**
- Fixed random seeds (42)
- Environment version checks
- Deterministic file paths
- Consistent output formats

## Dependencies and Files to Edit

### Core Files:
- `src/datasets/derco_eeg_loader.py` - EEG loader standardization
- `src/datasets/geco_loader.py` - Eye-tracking loader updates
- `src/datasets/lpp_eeg_loader.py` - BIDS format improvements
- `src/datasets/onestop_loader.py` - CSV parsing enhancements
- `src/pcs_toolbox/zuco.py` - ZuCo processing validation

### Notebooks to Create/Update:
- `notebooks/07_eeg_rt_ingestion_master.ipynb` - Master ingestion notebook
- `notebooks/08_eeg_rt_statistical_analysis.ipynb` - Statistical pipeline
- `notebooks/09_eeg_rt_quality_assurance.ipynb` - QA procedures

### Supporting Files:
- `src/contracts.py` - Enhanced validation functions
- `notebooks/_fragments.py` - Shared notebook utilities
- `config/datasets.yaml` - Dataset configuration

## Success Criteria

### Phase 1 Success Metrics:
- [ ] All loaders pass schema validation
- [ ] Consistent output format across datasets
- [ ] Quality thresholds met for all datasets
- [ ] Error handling standardized

### Phase 2 Success Metrics:
- [ ] Master notebook executes without errors
- [ ] Statistical analysis produces valid results
- [ ] QA notebook identifies and reports issues
- [ ] All notebooks follow IMRaD structure

### Phase 3 Success Metrics:
- [ ] No Portuguese text in codebase
- [ ] All quality gates (Q1-Q10) satisfied
- [ ] Reproducible outputs achieved
- [ ] Documentation meets project standards

## Follow-up Steps

1. **Integration Testing**: Validate compatibility with existing SWOW pipeline
2. **Performance Optimization**: Benchmark and optimize for large datasets
3. **User Documentation**: Create comprehensive user guides
4. **Continuous Integration**: Add automated testing for all loaders
5. **Community Feedback**: Gather input from project stakeholders

## Risk Assessment

**High Risk:**
- Data format changes breaking existing workflows
- Performance degradation with large datasets

**Medium Risk:**
- Incomplete schema compliance in edge cases
- Integration issues with downstream analysis

**Low Risk:**
- Documentation translation errors
- Minor formatting inconsistencies

## Timeline Estimate

- **Phase 1**: 2-3 days (loader standardization)
- **Phase 2**: 2-3 days (notebook creation)
- **Phase 3**: 1-2 days (quality gates)
- **Testing & Integration**: 1-2 days

**Total Estimated Time**: 6-10 days

## Conclusion

This audit plan provides a comprehensive approach to standardizing the EEG/RT data ingestion and normalization pipeline. By following this plan, the project will achieve consistent, reproducible, and well-documented data processing workflows that meet all established quality standards.
