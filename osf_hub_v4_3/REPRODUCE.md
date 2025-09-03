Reproduce the SWOW→KEC→ZuCo pipeline (v4.3)

This document describes how to reproduce the Symbolic-First validation with lean, auditable steps (OLS+MixedLM+BH-FDR+bootstrap+nulls).
See also: provenance.yaml (seeds, counts) and quality_gates.sh.

Quickstart

```bash
conda env create -f environment.yml
conda activate pcs-zuco
bash quality_gates.sh reproduce
```

Outputs: F2/F3 figures; results/models_reading_coeffs.csv; results/models_reading_coeffs_fdr.csv; results/mixedlm_ffd_summary.txt.

