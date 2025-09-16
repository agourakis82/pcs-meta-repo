# SWOW-KEC Statistical Treatment Comprehensive Audit Report

**Author:** PCS Meta-Repo Team  
**Date:** January 2025  
**Version:** 1.0.0  
**Repository:** pcs-meta-repo  

## Executive Summary

This report provides a comprehensive audit of the statistical treatment of SWOW (Small World of Words) data and its integration with KEC (Knowledge, Entropy, Curvature) metrics in the PCS Meta-Repository. The audit consolidates validation procedures previously scattered across multiple scripts to maximize reproducibility and transparency.

### Key Findings

- **Pipeline Status:** Complete integration pipeline identified
- **KEC Metrics:** Three core metrics (entropy, curvature, coherence) computed via graph-theoretic methods
- **Statistical Methods:** Robust OLS and Mixed-Effects models with FDR correction
- **Integration Quality:** Token-based merge with comprehensive validation framework
- **Reproducibility:** All procedures now documented in notebook format

## 1. Information Gathered

### 1.1 Core Components Identified

#### KEC Metrics Computation Modules
- **`src/pcs_toolbox/kec.py`**: Core KEC computation engine
  - `transition_entropy()`: Computes entropy per node using outgoing edge weights
  - `ricci_curvature()`: Ollivier-Ricci curvature via GraphRicciCurvature library
  - `meso_coherence()`: Community coherence via Leiden clustering modularity
  - `compute_kec_metrics()`: Main function integrating all three metrics

- **`src/swow/metrics_kec.py`**: SWOW-specific KEC wrapper
  - `compute_swow_kec_metrics()`: SWOW-tailored KEC computation
  - Validation functions with range checking and statistical summaries
  - Individual metric computation functions for modular analysis
  - Metadata integration (language, dataset labels)

#### Data Integration Pipeline
- **`tools/merge_zuco_kec.py`**: Primary merge script
  - Token normalization via `norm_token()` function
  - Left join on `token_norm` column
  - Log transformation creation for TRT/GPT measures
  - Missing value handling with `pd.NA`

- **`tools/pipeline_v43.py`**: Comprehensive pipeline orchestrator
  - Schema enforcement for KEC metrics
  - Multi-subject ZuCo data loading
  - Categorical variable harmonization
  - OLS fitting with robust standard errors
  - Benjamini-Hochberg FDR correction per response variable

#### Statistical Analysis Framework
- **`src/pcs_toolbox/analysis.py`**: Statistical modeling utilities
  - `fit_ols_clustered()`: OLS with cluster-robust standard errors
  - `fit_mixedlm()`: Mixed-effects models with random intercepts
  - `apply_fdr()`: FDR correction with grouping support
  - `bootstrap_coeffs()`: Bootstrap confidence intervals

- **`tools/validate_hstar.py`**: H* validation framework
  - Automated decision system: SUPPORTED | PARTIAL | NOT_SUPPORTED | PIPELINE_BROKEN
  - Multi-criteria validation including effect size, replication, and model fit
  - FDR correction validation and surprisal control assessment

### 1.2 Statistical Methods Employed

#### Primary Statistical Approaches
1. **Ordinary Least Squares (OLS)**
   - Robust standard errors (HC3 heteroskedasticity-consistent)
   - Cluster-robust standard errors when appropriate
   - Formula: `response ~ entropy + curvature + coherence`

2. **Mixed-Effects Linear Models (MixedLM)**
   - Random intercepts by Subject
   - REML estimation with L-BFGS optimization
   - Variance components for repeated measures

3. **Multiple Comparisons Correction**
   - Benjamini-Hochberg FDR procedure
   - Family-wise error rate control per response type
   - Separate correction for reading vs. EEG outcomes

#### Response Variables
- **Reading Measures**: TRT (Total Reading Time), FFD (First Fixation Duration), GD (Gaze Duration), GPT (Go-Past Time)
- **EEG Measures**: Theta, Alpha, Beta, Gamma frequency bands
- **Log Transformations**: `log_TRT = log1p(TRT)`, `log_GPT = log1p(GPT)`

#### Predictor Variables
- **KEC Metrics**: entropy, curvature, coherence
- **Control Variables**: log_freq (when available), surprisal measures
- **Categorical Covariates**: Dataset (v1/v2), Task (NR/TSR/SR), Subject

### 1.3 Data Integration Methodology

#### Token Normalization Process
```python
def norm_token(s: str) -> str:
    s = s.lower()
    return re.sub(r"[\W_]+", "", s)
```

#### Merge Strategy
1. **Primary Key**: `token_norm` (normalized word forms)
2. **Join Type**: Left join (ZuCo ⟵ KEC)
3. **Missing Value Strategy**: `pd.NA` for unmatched KEC metrics
4. **Schema Harmonization**: Automatic column mapping and type conversion

#### Quality Assurance
- Duplicate detection on merge keys
- Coverage analysis for KEC metrics
- Missing value pattern analysis
- Outlier detection via Z-score and IQR methods

## 2. Detailed Audit Plan

### 2.1 KEC Metrics Computation Audit

#### Validation Criteria
- **Range Validation**:
  - Entropy: ≥ 0, reasonable upper bound (< 10)
  - Curvature: No specific range constraints (can be negative)
  - Coherence: [-1, 1] for modularity-based measures
  
- **Computational Validation**:
  - Graph connectivity requirements
  - Edge weight normalization
  - Community detection stability
  - Numerical stability (no infinite/NaN values)

#### Implementation Issues Identified
1. **Curvature Computation**: Dependency on GraphRicciCurvature library
   - Multiprocessing limitations in sandboxed environments
   - Fallback to NaN values when computation fails
   - Single-process mode enforced for stability

2. **Coherence Proxy**: Uses modularity as coherence measure
   - Graph-level modularity copied to all nodes
   - May not capture node-specific coherence properties
   - Alternative: Node-specific community participation coefficients

#### Recommendations
- Implement alternative curvature measures (e.g., Forman-Ricci)
- Develop node-specific coherence metrics
- Add computational performance benchmarks
- Implement incremental computation for large graphs

### 2.2 Data Integration Pipeline Audit

#### Merge Quality Assessment
- **Token Coverage**: Proportion of ZuCo tokens with KEC matches
- **Completeness**: Availability of all three KEC metrics
- **Consistency**: Cross-validation of merge results
- **Temporal Stability**: Consistency across pipeline runs

#### Schema Validation
- **Column Presence**: Required columns in merged dataset
- **Data Types**: Appropriate numeric/categorical typing
- **Value Ranges**: Plausible ranges for all variables
- **Missing Patterns**: Systematic vs. random missingness

#### Integration Issues Identified
1. **Token Normalization**: Aggressive normalization may cause collisions
2. **Case Sensitivity**: Potential mismatches in original data
3. **Special Characters**: Handling of punctuation and diacritics
4. **Duplicate Handling**: Multiple entries for same normalized token

### 2.3 Statistical Methods Audit

#### Model Specification Validation
- **Predictor Selection**: Theoretical justification for KEC metrics
- **Covariate Control**: Adequate control for confounding variables
- **Model Assumptions**: Linearity, homoskedasticity, normality of residuals
- **Sample Size**: Adequate power for detecting effects

#### Multiple Comparisons Framework
- **FDR Procedure**: Correct implementation of Benjamini-Hochberg
- **Family Definition**: Appropriate grouping of tests
- **Alpha Level**: Standard 0.05 significance threshold
- **Effect Size**: Consideration beyond statistical significance

#### Statistical Issues Identified
1. **Model Selection**: Limited exploration of non-linear relationships
2. **Interaction Effects**: Potential KEC metric interactions not modeled
3. **Hierarchical Structure**: Complex nesting (subjects within datasets)
4. **Temporal Dependencies**: Sequential reading effects not modeled

### 2.4 H* Validation Framework Audit

#### Decision Criteria Assessment
- **SUPPORTED**: ≥2 reading outcomes with q≤0.05 and β>0, replication across strata, ΔR²≥0.5pp, surprisal control
- **PARTIAL**: ≥1 significant reading outcome OR EEG effects
- **NOT_SUPPORTED**: No significant effects meeting criteria
- **PIPELINE_BROKEN**: Missing required data or computational failures

#### Validation Robustness
- **Replication Requirements**: Cross-validation across datasets/tasks
- **Effect Size Thresholds**: ΔR² and AIC-based model comparison
- **Surprisal Control**: Retention of effects after linguistic control
- **Sensitivity Analysis**: Robustness to analytical choices

#### Framework Issues Identified
1. **Threshold Sensitivity**: Fixed thresholds may not generalize
2. **Multiple Criteria**: Complex decision tree may mask important effects
3. **Temporal Validation**: No longitudinal replication assessment
4. **Cross-linguistic**: Limited validation across languages

### 2.5 Data Quality Assessment

#### Coverage Analysis
- **KEC Availability**: Proportion of tokens with complete KEC triplets
- **Response Coverage**: Availability of reading/EEG measures
- **Subject Representation**: Balanced representation across participants
- **Task Distribution**: Adequate sampling across experimental conditions

#### Outlier Detection Strategy
- **Z-score Method**: |z| > 3.0 threshold for univariate outliers
- **IQR Method**: Values beyond Q1-1.5×IQR or Q3+1.5×IQR
- **Multivariate**: Mahalanobis distance for multivariate outliers
- **Influence Diagnostics**: Cook's distance and leverage for regression

#### Missing Value Analysis
- **Pattern Analysis**: MCAR, MAR, or MNAR mechanisms
- **Imputation Strategy**: Current approach uses listwise deletion
- **Sensitivity Analysis**: Impact of missing data on conclusions
- **Reporting Standards**: Transparent reporting of missing data handling

## 3. Implementation Recommendations

### 3.1 Notebook-Based Pipeline Conversion

#### Priority Notebooks to Create
1. **`04_swow_kec_statistical_audit.ipynb`**: Complete audit implementation
2. **`05_kec_metrics_validation.ipynb`**: KEC computation validation
3. **`06_integration_quality_assessment.ipynb`**: Merge quality analysis
4. **`07_statistical_modeling_pipeline.ipynb`**: Model fitting and validation
5. **`08_h_star_validation_framework.ipynb`**: Automated validation system

#### Notebook Structure Standards
- **Reproducibility**: Fixed random seeds, version documentation
- **Modularity**: Reusable functions with clear interfaces
- **Documentation**: Comprehensive markdown explanations
- **Validation**: Built-in quality checks and assertions
- **Visualization**: Diagnostic plots and summary tables

### 3.2 Enhanced Validation Procedures

#### KEC Metrics Validation
```python
def validate_kec_computation(graph, kec_df):
    """Comprehensive KEC metrics validation"""
    validation_results = {
        'graph_properties': validate_graph_structure(graph),
        'entropy_validation': validate_entropy_computation(kec_df),
        'curvature_validation': validate_curvature_computation(kec_df),
        'coherence_validation': validate_coherence_computation(kec_df),
        'cross_metric_correlations': compute_metric_correlations(kec_df)
    }
    return validation_results
```

#### Integration Quality Assessment
```python
def assess_integration_quality(zuco_df, kec_df, merged_df):
    """Comprehensive integration quality assessment"""
    quality_metrics = {
        'coverage_analysis': compute_coverage_statistics(merged_df),
        'merge_validation': validate_merge_integrity(zuco_df, kec_df, merged_df),
        'token_normalization': assess_normalization_quality(merged_df),
        'missing_patterns': analyze_missing_patterns(merged_df),
        'outlier_detection': detect_multivariate_outliers(merged_df)
    }
    return quality_metrics
```

### 3.3 Statistical Robustness Enhancements

#### Model Diagnostics
- **Residual Analysis**: Normality, homoskedasticity, independence
- **Influence Diagnostics**: Cook's distance, DFBETAS, leverage
- **Model Comparison**: AIC, BIC, cross-validation metrics
- **Assumption Testing**: Formal tests for model assumptions

#### Sensitivity Analysis
- **Bootstrap Validation**: Non-parametric confidence intervals
- **Cross-Validation**: K-fold validation for model stability
- **Robustness Checks**: Alternative model specifications
- **Outlier Sensitivity**: Results with/without outliers

### 3.4 Reproducibility Framework

#### Version Control Integration
- **Data Provenance**: Complete lineage tracking
- **Code Versioning**: Git integration with notebooks
- **Environment Management**: Conda/pip requirements specification
- **Result Archiving**: Systematic storage of analysis outputs

#### Documentation Standards
- **Method Documentation**: Detailed statistical methodology
- **Parameter Documentation**: All hyperparameters and thresholds
- **Decision Documentation**: Rationale for analytical choices
- **Limitation Documentation**: Known limitations and assumptions

## 4. Conclusions and Next Steps

### 4.1 Current State Assessment

The SWOW-KEC statistical treatment pipeline represents a sophisticated approach to integrating semantic network metrics with neurophysiological reading data. The current implementation demonstrates:

**Strengths:**
- Theoretically grounded KEC metrics computation
- Robust statistical modeling with appropriate corrections
- Comprehensive validation framework
- Modular, extensible codebase

**Areas for Improvement:**
- Scattered validation procedures need consolidation
- Limited documentation of analytical choices
- Computational robustness issues with curvature calculation
- Missing sensitivity analyses and robustness checks

### 4.2 Priority Actions

1. **Immediate (Week 1-2)**:
   - Convert validation scripts to notebook format
   - Implement comprehensive audit notebook
   - Document all analytical decisions and thresholds

2. **Short-term (Month 1)**:
   - Enhance KEC computation robustness
   - Implement alternative curvature measures
   - Add comprehensive model diagnostics

3. **Medium-term (Months 2-3)**:
   - Cross-linguistic validation framework
   - Longitudinal replication studies
   - Advanced missing data handling

4. **Long-term (Months 4-6)**:
   - Machine learning integration
   - Causal inference framework
   - Real-time validation dashboard

### 4.3 Success Metrics

- **Reproducibility**: 100% of analyses executable from notebooks
- **Transparency**: Complete documentation of all procedures
- **Robustness**: Validation across multiple datasets and conditions
- **Efficiency**: Automated quality checks and validation
- **Impact**: Increased citation and adoption of methodology

This audit provides a roadmap for enhancing the SWOW-KEC statistical treatment pipeline while maintaining scientific rigor and maximizing reproducibility. The transition to notebook-based workflows will significantly improve the accessibility and reliability of these important analyses.
