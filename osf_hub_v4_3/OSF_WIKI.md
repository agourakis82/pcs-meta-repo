# 🧠 Symbolic Manifolds & Entropic Dynamics — OSF Hub (v4.3)
**Scope.** Symbolic-First validation (SWOW→KEC→ZuCo). **HELIO deferred.** Public datasets only; no PII.  
**Links.** Zenodo v4.3: https://doi.org/10.5281/zenodo.17039429 · Concept: https://doi.org/10.5281/zenodo.16533374 · GitHub: https://github.com/agourakis82/pcs-meta-repo

## Methods (lean & interpretable)
OLS (HC-robust SEs) · MixedLM (random intercepts) · BH-FDR · Bootstrap · **Degree-preserving null graphs (N≥1000)**

## Minimum bundle
F2/F3 · `results/models_reading_coeffs.csv` · `results/models_reading_coeffs_fdr.csv` · `results/mixedlm_ffd_summary.txt`

## Governance
CC BY 4.0 (text) · MIT (code) · seeds pinned in `provenance.yaml` · **Q1–Q10** · **no-broken-links**

## Reproducibility Checklist
1) Env  
```bash
conda env create -f environment.yml
conda activate pcs-zuco
```

2) Run (end-to-end)

```bash
bash quality_gates.sh reproduce
```

3) Seeds — pinned in provenance.yaml  
4) Nulls — N≥1000 degree-preserving shuffles  
5) Reporting — CSVs + summaries in results/  
6) Figures — results/figures/metrics/F2_*, F3_*  

7) QA (optional)

```bash
bash quality_gates.sh check
```

