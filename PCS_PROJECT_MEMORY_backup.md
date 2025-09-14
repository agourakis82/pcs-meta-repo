# PCS Project Memory Database
**Last Updated**: December 19, 2024  
**Version**: PCS v4.3 Enhanced Memory System  
**Status**: Active Memory Repository

---

## 🧠 **CORE PROJECT CONTEXT**

### **Project Identity**
- **Name**: Computational-Symbolic Psychiatry (PCS) Meta-Repository
- **Version**: v4.3 (Extended Memory Integration)
- **Lead**: Demetrios Agourakis (ORCID: 0000-0002-8596-5097)
- **Institution**: PUC-SP Graduate Program in Biomaterials & Regenerative Medicine
- **License**: Code (MIT) + Documentation (CC BY 4.0)

### **Research Objective**
Establish reproducible bridge: **HELIO exposure** → **AG5/KEC state metrics** → **SEA/VAR inference** → **ZuCo validation** → **IMRaD publication**

### **Core Framework**
**Fractal Entropy** → **Semantic Manifolds** → **Cognitive Topology** → **Clinical Applications**

---

## 📊 **DATASET MEMORY**

### **Primary Datasets (Status: Active)**
1. **SWOW (Small World of Words)**
   - **Languages**: EN (complete), ES/NL/ZH (in progress)
   - **Purpose**: Lexical association networks → graph construction
   - **Status**: English dataset fully processed, multilingual expansion ongoing
   - **Key Files**: `src/swow/` modules, `data/raw_public/swow/`

2. **ZuCo (EEG + Eye-tracking)**
   - **Versions**: v1.0, v2.0 integrated
   - **Features**: EEG/ET alignment, fixation-locked features, frequency bands
   - **Status**: Real integration completed, validation ongoing
   - **Key Files**: `src/data/zuco_loader.py`, `notebooks/03_process_zuco.ipynb`

3. **Supporting Datasets**
   - **DERCo**: Dutch Reading Corpus (EEG + Eye-tracking)
   - **GECO**: Ghent Eye-tracking Corpus
   - **OneStop**: English Reading Corpus
   - **LPP**: Le Petit Prince (EEG + fMRI)
   - **Status**: All integrated in EEG/RT pipeline

### **Dataset Processing Status**
- ✅ **SWOW English**: Complete graph construction and KEC metrics
- ✅ **ZuCo Integration**: Real data pipeline operational
- ✅ **EEG/RT Pipeline**: 4-step comprehensive processing complete
- 🔄 **Multilingual SWOW**: ES/NL/ZH processing in progress
- 🔄 **Cross-validation**: Ongoing quality assessment

---

## 🔬 **ANALYSIS METHODS MEMORY**

### **AG5/KEC Metrics (Core Framework)**
1. **Transition Entropy**: Markovized walk on semantic graphs
2. **Local Curvature**: Ollivier-Ricci curvature variants
3. **Mesoscopic Curvature**: Forman-Ricci implementations
4. **Coherence**: Community-consistent embedding proximity
5. **Implementation**: `src/swow/metrics_kec.py`, `src/kec/coherence.py`

### **Statistical Framework**
- **SEA (Event Study)**: ΔKEC around storms (Kp≥5) within ±3 days
- **VAR/ARIMAX**: Shock-response IRFs for AG5/KEC ↔ exposure
- **ZuCo Validation**: Reading cost (EEG/ET) tracks local AG5
- **Controls**: Seasonality, topic, length, frequency, morphological complexity

### **Memory Optimization**
- **Scripts**: 15+ memory-optimized analysis scripts
- **Key Files**: `scripts/memory_optimized_semantic_analysis.py`, `scripts/optimize_performance.py`
- **Techniques**: Chunked processing, GPU acceleration, efficient data types

---

## 📝 **PUBLICATION MEMORY**

### **Target Journals & Strategy**
1. **Primary Target**: Nature Human Behaviour
   - **Focus**: Manifold + cognitive topology
   - **Status**: IMRaD framework prepared
   - **Key Document**: `docs/NATURE_HUMAN_BEHAVIOUR_ENHANCEMENT_PLAN.md`

2. **Companion Publication**: Scientific Reports
   - **Focus**: Methods and toolbox documentation
   - **Status**: Technical framework ready

3. **Supporting Materials**
   - **OSF/Zenodo**: Mirrored with DOIs
   - **Reproducibility Badges**: ORCID, DOI, License compliance

### **Quality Gates (Q1-Q10)**
- **Q1-Q3**: Technical accuracy, evidence classification, terminology
- **Q4-Q6**: Editorial structure, reproducibility, limitations
- **Q7-Q9**: Actionable DoD, impact strategy, legal compliance
- **Q10**: Alignment to PCS Supreme Goal
- **Status**: Framework implemented, ongoing compliance monitoring

---

## 🛠 **INFRASTRUCTURE MEMORY**

### **Technical Stack**
- **Environment**: Python 3.8+, Node.js v18.20.8
- **Key Dependencies**: pandas, numpy, scipy, networkx, matplotlib
- **GPU Support**: CUDA-enabled for large-scale processing
- **Memory Management**: Optimized for 16GB+ RAM systems

### **Repository Structure**
- **Source Code**: `src/` (MIT license)
- **Analysis Notebooks**: `notebooks/` (reproducible stubs)
- **Configuration**: `config/` (YAML-based settings)
- **Data Pipeline**: `data/L0_raw/` → `data/L1_tidy/` → `data/L2_derived/`
- **Quality Assurance**: `reports/`, `tests/`

### **Memory System Status**
- **MCP Server**: Built and tested (`/home/agourakis82/Documents/.blackbox/MCP/pcs-memory-server/`)
- **Node.js**: Upgraded to v18.20.8 (compatible)
- **Storage**: `~/.pcs-memory.json` (6 memories loaded)
- **Connection**: Pending VSCode restart for full activation

---

## 🚨 **CRITICAL ISSUES IDENTIFIED - CURRENT STATUS**

### **🚨 MAJOR PROBLEMS DISCOVERED**
- ❌ **ZuCo Integration**: Target variable constant (all values = 200.00)
- ❌ **Statistical Models**: R² = 1.000 artificially due to degenerate data
- ❌ **Overfitting Crisis**: 39,500 records with identical fixation_duration
- ❌ **Pipeline Broken**: Statistical analysis invalid with constant target
- ❌ **Data Quality**: Systematic problems in EEG/RT integration

### **Completed Milestones (With Issues)**
- ✅ **SWOW Multilingual**: EN/ES/NL/ZH datasets processed (KEC metrics complete)
- ⚠️ **ZuCo Integration**: Pipeline exists but produces invalid data
- ⚠️ **EEG/RT Pipeline**: Partial success (DERCo, GECO, OneStop) but ZuCo broken
- ✅ **Memory Optimization**: 15+ scripts with efficient processing
- ✅ **Quality Framework**: Q1-Q10 gates implemented, revealed critical issues
- ✅ **Node.js Upgrade**: v12.22.9 → v18.20.8 for MCP compatibility


---
=======
- 🚨 **Data Correction**: Fix ZuCo target variable degeneracy
- 🚨 **Pipeline Repair**: Investigate and fix data processing errors
- 🚨 **Validation Overhaul**: Implement robust data quality checks
- 🚨 **Statistical Reanalysis**: Redo all analyses after data correction

### **🎯 EMERGENCY PRIORITIES**
1. **🚨 URGENT**: Diagnose and fix ZuCo data processing pipeline
2. **🚨 URGENT**: Implement mandatory data quality validation
3. **🚨 URGENT**: Reprocess all integrated datasets with validation
4. **⚠️ BLOCKED**: Publication preparation (blocked until data fixed)

---
=======
### **🎯 EMERGENCY PRIORITIES**
1. **🚨 URGENT**: Diagnose and fix ZuCo data processing pipeline
2. **🚨 URGENT**: Implement mandatory data quality validation
3. **🚨 URGENT**: Reprocess all integrated datasets with validation
4. **⚠️ BLOCKED**: Publication preparation (blocked until data fixed)

---
=======
### **🚨 CRITICAL WORK STREAMS (URGENT)**
- 🚨 **Data Correction**: Fix ZuCo target variable degeneracy
- 🚨 **Pipeline Repair**: Investigate and fix data processing errors
- 🚨 **Validation Overhaul**: Implement robust data quality checks
- 🚨 **Statistical Reanalysis**: Redo all analyses after data correction

### **🎯 EMERGENCY PRIORITIES**
1. **🚨 URGENT**: Diagnose and fix ZuCo data processing pipeline
2. **🚨 URGENT**: Implement mandatory data quality validation
3. **🚨 URGENT**: Reprocess all integrated datasets with validation
4. **⚠️ BLOCKED**: Publication preparation (blocked until data fixed)

---
=======

---
=======
- 🚨 **Data Correction**: Fix ZuCo target variable degeneracy
- 🚨 **Pipeline Repair**: Investigate and fix data processing errors
- 🚨 **Validation Overhaul**: Implement robust data quality checks
- 🚨 **Statistical Reanalysis**: Redo all analyses after data correction

### **🎯 EMERGENCY PRIORITIES**
1. **🚨 URGENT**: Diagnose and fix ZuCo data processing pipeline
2. **🚨 URGENT**: Implement mandatory data quality validation
3. **🚨 URGENT**: Reprocess all integrated datasets with validation
4. **⚠️ BLOCKED**: Publication preparation (blocked until data fixed)

---
=======
### **🎯 EMERGENCY PRIORITIES**
1. **🚨 URGENT**: Diagnose and fix ZuCo data processing pipeline
2. **🚨 URGENT**: Implement mandatory data quality validation
3. **🚨 URGENT**: Reprocess all integrated datasets with validation
4. **⚠️ BLOCKED**: Publication preparation (blocked until data fixed)

---
=======

---

## 🚨 **CRITICAL ISSUES LOG**

### **Data Quality Problems**
- `overfitting-crisis` - ZuCo target variable constant (fixation_duration = 200.00)
- `pipeline-broken` - Statistical analysis invalid due to degenerate data
- `integration-failure` - Token normalization causing data collisions
- `validation-gaps` - Missing mandatory data quality checks

### **Technical Issues**
- `curvature-computation` - GraphRicciCurvature library failures
- `missing-datasets` - LPP dataset unavailable, ZuCo tasks missing
- `schema-inconsistencies` - Data type and structure problems
- `computational-instability` - Memory and processing failures

### **Statistical Problems**
- `model-assumptions-violated` - Constant target breaks all assumptions
- `fdr-correction-invalid` - Multiple comparisons correction meaningless
- `effect-sizes-artificial` - Inflated due to data degeneracy
- `cross-validation-misleading` - Results not interpretable

---

## 🔍 **SEARCH TAGS & CATEGORIES**

### **Research Categories**
- `project_overview` - Core PCS research context
- `datasets` - SWOW, ZuCo, DERCo, GECO, OneStop, LPP
- `analysis_methods` - AG5/KEC metrics, statistical frameworks
- `quality_gates` - Q1-Q10 compliance monitoring
- `publications` - Journal strategy, manuscript progress (BLOCKED)
- `infrastructure` - Technical setup, memory systems
- `critical_issues` - Data quality problems and pipeline failures

### **Key Tags**
- `SWOW`, `ZuCo`, `AG5`, `KEC`, `curvature`, `entropy`
- `EEG`, `eye-tracking`, `reading-cost`, `semantic-manifolds`
- `Nature-Human-Behaviour`, `Scientific-Reports`, `reproducibility`
- `memory-optimization`, `GPU-acceleration`, `multilingual`
- `overfitting-crisis`, `data-quality`, `pipeline-repair`, `validation-overhaul`

---

## 📋 **MEMORY USAGE INSTRUCTIONS**

### **Adding New Memories**
1. **Research Progress**: Update relevant sections with new findings
2. **Dataset Status**: Modify dataset processing status
3. **Analysis Results**: Add to analysis methods section
4. **Publication Updates**: Track manuscript and submission progress

### **Searching Memories**
1. **Use Ctrl+F**: Search by tags, categories, or keywords
2. **Section Navigation**: Jump to relevant memory categories
3. **Cross-References**: Follow links between related memories

### **Memory Maintenance**
1. **Regular Updates**: Update progress weekly
2. **Version Control**: Track changes through git commits
3. **Backup**: Maintain copies of critical memory states

---

**This file-based memory system provides immediate context preservation while the MCP memory server connection is being established. All information is searchable and maintainable through standard text editing.**
